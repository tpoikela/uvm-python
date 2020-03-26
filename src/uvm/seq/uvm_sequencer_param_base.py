#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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
#//------------------------------------------------------------------------------

from .uvm_sequencer_base import UVMSequencerBase
from .uvm_sequencer_analysis_fifo import UVMSequencerAnalysisFIFO
from ..base.uvm_queue import UVMQueue
from ..tlm1.uvm_tlm_fifos import UVMTLMFIFO
from ..tlm1 import (UVMAnalysisExport)
from ..macros.uvm_message_defines import uvm_fatal
from ..base.uvm_globals import *
from ..base.sv import sv

ERR_MSG2 = ("Concurrent calls to get_next_item() not supported. Consider "
    + "using a semaphore to ensure that concurrent processes take turns in the driver")

INFO_MSG1 = ("Dropping response for sequence %0d, sequence not found.  Probable"
    + "cause: sequence exited or has been killed")



class UVMSequencerParamBase(UVMSequencerBase):
    """

    CLASS: uvm_sequencer_param_base #(REQ,RSP)

    Extends <uvm_sequencer_base> with an API depending on specific
    request (REQ) and response (RSP) types.

    Port (UVMAnalysisExport): rsp_export

    Drivers or monitors can connect to this port to send responses
    to the sequencer.  Alternatively, a driver can send responses
    via its seq_item_port::

      seq_item_port.item_done(response)
      seq_item_port.put(response)
      rsp_port.write(response)   <--- via this export

    The rsp_port in the driver and/or monitor must be connected to the
    rsp_export in this sequencer in order to send responses through the
    response analysis port.
    """


    def __init__(self, name, parent):
        """
        Creates and initializes an instance of this class using the normal
        constructor arguments for uvm_component: name is the name of the instance,
        and parent is the handle to the hierarchical parent, if any.

        Args:
            name:
            parent:
        """
        UVMSequencerBase.__init__(self, name, parent)
        self.m_last_req_buffer = UVMQueue()
        self.m_last_rsp_buffer = UVMQueue()
        self.m_num_last_reqs = 1
        self.num_last_items = self.m_num_last_reqs
        self.m_num_last_rsps = 1
        self.m_num_reqs_sent = 0
        self.m_num_rsps_received = 0

        # TODO Adding self as 2nd arg makes the sim fail, it does not advance
        # properly. This is uvm_phase issue most likely
        #self.m_req_fifo = UVMTLMFIFO(name + "__" + "m_req_fifo", None)
        self.m_req_fifo = UVMTLMFIFO(name + "__" + "m_req_fifo", self)  # uvm_tlm_fifo
        self.m_req_fifo.print_enabled = False
        self.rsp_export = UVMAnalysisExport("rsp_export", self)
        self.sqr_rsp_analysis_fifo = UVMSequencerAnalysisFIFO("sqr_rsp_analysis_fifo", self)
        self.sqr_rsp_analysis_fifo.print_enabled = 0


    def send_request(self, sequence_ptr, t, rerandomize=False):
        """
        The send_request function may only be called after a wait_for_grant call.
        This call will send the request item, t,  to the sequencer pointed to by
        sequence_ptr. The sequencer will forward it to the driver. If rerandomize
        is set, the item will be randomized before being sent to the driver.

        Args:
            sequence_ptr (UVMSequenceBase):
            t (UVMSequenceItem):
            rerandomize (bool):
        """
        param_t = None  # REQ

        if sequence_ptr is None:
            self.uvm_report_fatal("SNDREQ", "Send request sequence_ptr is null", UVM_NONE)

        if sequence_ptr.m_wait_for_grant_semaphore < 1:
            self.uvm_report_fatal("SNDREQ", "Send request called without wait_for_grant", UVM_NONE)
        sequence_ptr.m_wait_for_grant_semaphore -= 1

        #if ($cast(param_t, t)):
        param_t = t
        if rerandomize is True:
            if param_t.randomize() is False:
                self.uvm_report_warning("SQRSNDREQ", "Failed to rerandomize sequence item in send_request")
        if param_t.get_transaction_id() == -1:
            param_t.set_transaction_id(sequence_ptr.m_next_transaction_id)
            sequence_ptr.m_next_transaction_id += 1
        self.m_last_req_push_front(param_t)
        #end else begin
        #  uvm_report_fatal(get_name(),$sformatf("send_request failed to cast sequence item"), UVM_NONE)
        #end

        param_t.set_sequence_id(sequence_ptr.m_get_sqr_sequence_id(self.m_sequencer_id, 1))
        t.set_sequencer(self)
        if self.m_req_fifo.try_put(param_t) is False:
            uvm_fatal(self.get_full_name(), ERR_MSG2)

        self.m_num_reqs_sent += 1
        # Grant any locks as soon as possible
        self.grant_queued_locks()


    def get_current_item(self):
        """
        Returns the request_item currently being executed by the sequencer. If the
        sequencer is not currently executing an item, this method will return `null`.

        The sequencer is executing an item from the time that get_next_item or peek
        is called until the time that get or item_done is called.

        Note that a driver that only calls get() will never show a current item,
        since the item is completed at the same time as it is requested.

        Returns:
            UVMSequenceItem: Request item currently being executed
        """
        t = []
        if not self.m_req_fifo.try_peek(t):
            return None
        return t[0]


    def get_num_reqs_sent(self):
        """
        Returns the number of requests that have been sent by this sequencer.

        Returns:
            int: Number of requests sent.
        """
        return self.m_num_reqs_sent


    #  // Function: set_num_last_reqs
    #  //
    #  // Sets the size of the last_requests buffer.  Note that the maximum buffer
    #  // size is 1024.  If max is greater than 1024, a warning is issued, and the
    #  // buffer is set to 1024.  The default value is 1.
    #  //
    #  extern function void set_num_last_reqs(int unsigned max)
    def set_num_last_reqs(self, max_val):
        if max_val > 1024:
            self.uvm_report_warning("HSTOB",
                sv.sformatf("Invalid last size; 1024 is the maximum and will be used"))
            max_val = 1024

        # shrink the buffer if necessary
        while ((self.m_last_req_buffer.size() != 0) and
                (self.m_last_req_buffer.size() > max_val)):
            self.m_last_req_buffer.pop_back()

        self.m_num_last_reqs = max_val
        self.num_last_items = max_val


    def get_num_last_reqs(self):
        """
          Function: get_num_last_reqs

          Returns the size of the last requests buffer, as set by set_num_last_reqs.

         extern function int unsigned get_num_last_reqs()
        Returns:
        """
        return self.m_num_last_reqs


    #  // Function: last_req
    #  //
    #  // Returns the last request item by default.  If n is not 0, then it will get
    #  // the n�th before last request item.  If n is greater than the last request
    #  // buffer size, the function will return ~null~.
    #  //
    #  function REQ last_req(int unsigned n = 0)
    #    if(n > m_num_last_reqs):
    #      uvm_report_warning("HSTOB",
    #        $sformatf("Invalid last access (%0d), the max history is %0d", n,
    #        m_num_last_reqs))
    #      return null
    #    end
    #    if(n == m_last_req_buffer.size())
    #      return null
    #
    #    return m_last_req_buffer[n]
    #  endfunction


    #  //-----------------
    #  // Group: Responses
    #  //-----------------


    def get_num_rsps_received(self):
        """
        Returns the number of responses received thus far by this sequencer.

        Returns:
        """
        return self.m_num_rsps_received



    #  // Function: set_num_last_rsps
    #  //
    #  // Sets the size of the last_responses buffer.  The maximum buffer size is
    #  // 1024. If max is greater than 1024, a warning is issued, and the buffer is
    #  // set to 1024.  The default value is 1.
    #  //
    #  extern function void set_num_last_rsps(int unsigned max)


    def get_num_last_rsps(self):
        """
          Function: get_num_last_rsps

          Returns the max size of the last responses buffer, as set by
          set_num_last_rsps.

         extern function int unsigned get_num_last_rsps()
        Returns:
        """
        return self.m_num_last_rsps


    #  // Function: last_rsp
    #  //
    #  // Returns the last response item by default.  If n is not 0, then it will
    #  // get the nth-before-last response item.  If n is greater than the last
    #  // response buffer size, the function will return ~null~.
    #  //
    #  function RSP last_rsp(int unsigned n = 0)
    #    if(n > m_num_last_rsps):
    #      uvm_report_warning("HSTOB",
    #        $sformatf("Invalid last access (%0d), the max history is %0d", n,
    #        m_num_last_rsps))
    #      return null
    #    end
    #    if(n == m_last_rsp_buffer.size())
    #      return null
    #
    #    return m_last_rsp_buffer[n]
    #  endfunction


    #  // Internal methods and variables; do not use directly, not part of standard


    def m_last_rsp_push_front(self, item):
        """
         /* local */ extern function void m_last_rsp_push_front(RSP item)
        Args:
            item:
        """
        if self.m_num_last_rsps == 0:
            return

        if self.m_last_rsp_buffer.size() == self.m_num_last_rsps:
            self.m_last_rsp_buffer.pop_back()
        #
        self.m_last_rsp_buffer.push_front(item)

    def put_response(self, t):
        """
         /* local */ extern function void put_response (RSP t)
        Args:
            t:
        """
        sequence_ptr = None  # #  uvm_sequence_base

        if t is None:
            self.uvm_report_fatal("SQRPUT", "Driver put a null response", UVM_NONE)

        self.m_last_rsp_push_front(t)
        self.m_num_rsps_received += 1

        # Check that set_id_info was called
        if t.get_sequence_id() == -1:
            #`ifndef CDNS_NO_SQR_CHK_SEQ_ID
            self.uvm_report_fatal("SQRPUT", "Driver put a response with null sequence_id", UVM_NONE)
            #`endif
            return

        sequence_ptr = self.m_find_sequence(t.get_sequence_id())

        if sequence_ptr is not None:
            # If the response_handler is enabled for this sequence, then call the response handler
            if sequence_ptr.get_use_response_handler() == 1:
                sequence_ptr.response_handler(t)
                return
            sequence_ptr.put_response(t)
        else:
            self.uvm_report_info("Sequencer", sv.sformatf(INFO_MSG1, t.get_sequence_id()))
        #endfunction

    def build_phase(self, phase):
        """
         /* local */ extern virtual function void build_phase(uvm_phase phase)
        Args:
            phase:
        """
        super().build_phase(phase)
        self.sqr_rsp_analysis_fifo.sequencer_ptr = self

    def connect_phase(self, phase):
        """
         /* local */ extern virtual function void connect_phase(uvm_phase phase)
        Args:
            phase:
        """
        super().connect_phase(phase)
        self.rsp_export.connect(self.sqr_rsp_analysis_fifo.analysis_export)


    #  /* local */ extern virtual function void do_print (uvm_printer printer)

    #  /* local */ extern virtual function void analysis_write(uvm_sequence_item t)

    def m_last_req_push_front(self, item):
        """
         /* local */ extern function void m_last_req_push_front(REQ item)
        Args:
            item:
        """
        if self.m_num_last_reqs == 0:
            return

        if self.m_last_req_buffer.size() == self.m_num_last_reqs:
            self.m_last_req_buffer.pop_back()

        self.m_last_req_buffer.push_front(item)


#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#// do_print
#// --------
#
#function void uvm_sequencer_param_base::do_print (uvm_printer printer)
#  super.do_print(printer)
#  printer.print_field_int("num_last_reqs", m_num_last_reqs, $bits(m_num_last_reqs), UVM_DEC)
#  printer.print_field_int("num_last_rsps", m_num_last_rsps, $bits(m_num_last_rsps), UVM_DEC)
#endfunction
#
#
#
#// analysis_write
#// --------------
#
#function void uvm_sequencer_param_base::analysis_write(uvm_sequence_item t)
#  RSP response
#
#  if (!$cast(response, t)):
#    uvm_report_fatal("ANALWRT", "Failure to cast analysis port write item", UVM_NONE)
#  end
#  put_response(response)
#endfunction
#
#
#
#
#
#
#// set_num_last_rsps
#// -----------------
#
#function void uvm_sequencer_param_base::set_num_last_rsps(int unsigned max)
#  if(max > 1024):
#    uvm_report_warning("HSTOB",
#      $sformatf("Invalid last size; 1024 is the maximum and will be used"))
#    max = 1024
#  end
#
#  //shrink the buffer
#  while((m_last_rsp_buffer.size() != 0) && (m_last_rsp_buffer.size() > max)):
#    void'(m_last_rsp_buffer.pop_back())
#  end
#
#  m_num_last_rsps = max
#
#endfunction
