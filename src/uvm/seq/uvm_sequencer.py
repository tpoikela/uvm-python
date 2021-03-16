#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2014 NVIDIA Corporation
#//   Copyright 2019 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------

#rm from cocotb.triggers import Timer

from typing import List

from .uvm_sequencer_param_base import UVMSequencerParamBase
from ..tlm1.uvm_sqr_connections import UVMSeqItemPullImp
from ..macros import uvm_component_utils, uvm_info
from ..base.uvm_globals import uvm_check_output_args, uvm_zero_delay
from ..base.uvm_object_globals import *

FATAL_MSG1 = ("Item_done() called with no outstanding requests." +
    " Each call to item_done() must be paired with a previous call to "
    + " get_next_item().")


class UVMSequencer(UVMSequencerParamBase):
    """
    Group: Sequencer Interface
    This is an interface for communicating with sequencers.

    The interface is defined as::

      Requests:
       async def get_next_item      (output REQ request)
       async def try_next_item      (output REQ request)
       async def get                (output REQ request)
       async def peek               (output REQ request)
      Responses:
       def item_done          (input RSP response=null)
       async def put                (input RSP response)
      Sync Control:
       async def          wait_for_sequences()
       def  has_do_available()

    See `UVMSqrIfBase` for information about this interface.
    """

    def __init__(self, name, parent=None):
        """
        Standard component constructor that creates an instance of this class
        using the given `name` and `parent`, if any.

        Args:
            name:
            parent:
        """
        UVMSequencerParamBase.__init__(self, name, parent)
        #  // Variable: seq_item_export
        #  // This export provides access to this sequencer's implementation of the
        #  // sequencer interface.
        self.seq_item_export = UVMSeqItemPullImp("seq_item_export", self)
        self.sequence_item_requested = False
        self.get_next_item_called = False

    def stop_sequences(self):
        """
        Tells the sequencer to kill all sequences and child sequences currently
        operating on the sequencer, and remove all requests, locks and responses
        that are currently queued.  This essentially resets the sequencer to an
        idle state.
        """
        super().stop_sequences()
        self.sequence_item_requested  = 0
        self.get_next_item_called     = 0
        # Empty the request fifo
        if self.m_req_fifo.used():
            uvm_report_info(self.get_full_name(),
                "Sequences stopped. Removing request from sequencer fifo")
            t = []
            while self.m_req_fifo.try_get(t):
                t = []

    #  extern virtual function string get_type_name()



    async def get_next_item(self, t):
        """
        Retrieves the next available item from a sequence.

        Args:
            t (list): Empty list into which item is appended
        """
        uvm_check_output_args([t])
        # req_item = None

        # If a sequence_item has already been requested, then get_next_item()
        # should not be called again until item_done() has been called.

        if self.get_next_item_called is True:
            self.uvm_report_error(self.get_full_name(),
                "Get_next_item called twice without item_done or get in between", UVM_NONE)

        if self.sequence_item_requested is False:
            await self.m_select_sequence()

        # Set flag indicating that the item has been requested to ensure that item_done or get
        # is called between requests
        self.sequence_item_requested = True
        self.get_next_item_called = True
        await self.m_req_fifo.peek(t)

    async def try_next_item(self, t: List):
        """
        Retrieves the next available item from a sequence if one is available.

        Args:
            t (List): Empty list into which item is appended
        """
        if self.get_next_item_called == 1:
            uvm_report_error(self.get_full_name(),
                "get_next_item/try_next_item called twice without item_done or get in between",
                UVM_NONE)
            return

        # allow state from last transaction to settle such that sequences'
        # relevancy can be determined with up-to-date information
        await self.wait_for_sequences()

        # choose the sequence based on relevancy
        selected_sequence = self.m_choose_next_request()

        # return if none available
        if selected_sequence == -1:
            # t = None
            return

        # now, allow chosen sequence to resume
        self.m_set_arbitration_completed(self.arb_sequence_q[selected_sequence].request_id)
        seq = self.arb_sequence_q[selected_sequence].sequence_ptr
        self.arb_sequence_q.delete(selected_sequence)
        self.m_update_lists()
        self.sequence_item_requested = True
        self.get_next_item_called = 1

        # give it one NBA to put a new item in the fifo
        await self.wait_for_sequences()

        # attempt to get the item; if it fails, produce an error and return
        if not self.m_req_fifo.try_peek(t):
            uvm_report_error("TRY_NEXT_BLOCKED", ("try_next_item: the selected sequence '" +
                seq.get_full_name() + "' did not produce an item within an NBA delay. " +
                "Sequences should not consume time between calls to start_item and finish_item. " +
                "Returning null item."), UVM_NONE)

    def item_done(self, item=None):
        """
        Indicates that the request is completed.

        Args:
            item:
        """
        t = []
        # Set flag to allow next get_next_item or peek to get a new sequence_item
        self.sequence_item_requested = False
        self.get_next_item_called = False

        if self.m_req_fifo.try_get(t) is False:
            self.uvm_report_fatal(self.get_full_name(), FATAL_MSG1)
        else:
            t = t[0]
            self.m_wait_for_item_sequence_id = t.get_sequence_id()
            self.m_wait_for_item_transaction_id = t.get_transaction_id()

        if item is not None:
            self.seq_item_export.put_response(item)

        # Grant any locks as soon as possible
        self.grant_queued_locks()


    async def put(self, t):
        """
        Sends a response back to the sequence that issued the request.

        Args:
            t (UVMSequenceItem): Response item.
        """
        self.put_response(t)
        await uvm_zero_delay()


    async def get(self, t: List):
        """
        Retrieves the next available item from a sequence.

        Args:
            t (List): List to hold the response
        """
        if self.sequence_item_requested == 0:
            await self.m_select_sequence()
        self.sequence_item_requested = 1
        await self.m_req_fifo.peek(t)
        self.item_done()


    async def peek(self, t: List):
        """
        Returns the current request item if one is in the FIFO.

        Args:
            t (List): List for the output request.
        """
        if self.sequence_item_requested == 0:
            await self.m_select_sequence()

        # Set flag indicating that the item has been requested to ensure that item_done or get
        # is called between requests
        self.sequence_item_requested = 1
        await self.m_req_fifo.peek(t)


    #  /// Documented here for clarity, implemented in uvm_sequencer_base
    #
    #  // Task: wait_for_sequences
    #  // Waits for a sequence to have a new item available.
    #  //
    #
    #  // Function: has_do_available
    #  // Returns 1 if any sequence running on this sequencer is ready to supply
    #  // a transaction, 0 otherwise.
    #  //
    #
    #  //-----------------
    #  // Internal Methods
    #  //-----------------
    #  // Do not use directly, not part of standard
    #
    #  extern function void         item_done_trigger(RSP item = null)
    #  function RSP                 item_done_get_trigger_data()
    #    return last_rsp(0)
    #  endfunction
    #  extern protected virtual function int m_find_number_driver_connections()


uvm_component_utils(UVMSequencer)


#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#
#
#
#function string uvm_sequencer::get_type_name()
#  return "uvm_sequencer"
#endfunction
#
#
#//-----------------
#// Internal Methods
#//-----------------
#
#// m_find_number_driver_connections
#// --------------------------------
#// Counting the number of of connections is done at end of
#// elaboration and the start of run.  If the user neglects to
#// call super in one or the other, the sequencer will still
#// have the correct value
#
#function int uvm_sequencer::m_find_number_driver_connections()
#  uvm_port_component_base provided_to_port_list[string]
#  uvm_port_component_base seq_port_base
#
#  // Check that the seq_item_pull_port is connected
#  seq_port_base = seq_item_export.get_comp()
#  seq_port_base.get_provided_to(provided_to_port_list)
#  return provided_to_port_list.num()
#endfunction
#
#
#
#


#// item_done_trigger
#// -----------------
#
#function void uvm_sequencer::item_done_trigger(RSP item = null)
#  item_done(item)
#endfunction
