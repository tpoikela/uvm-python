#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2013 Cisco Systems, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

from .uvm_sequence_base import UVMSequenceBase
from ..macros.uvm_message_defines import uvm_fatal


class UVMSequence(UVMSequenceBase):
    """
    The UVMSequence class provides the interfaces necessary in order to create
    streams of sequence items and/or other sequences.
    """

    def __init__(self, name="uvm_sequence"):
        """
        Variable: req

        The sequence contains a field of the request type called req.  The user
        can use this field, if desired, or create another field to use.  The
        default `do_print` will print this field.

        Variable: rsp

        The sequence contains a field of the response type called rsp.  The user
        can use this field, if desired, or create another field to use.   The
        default `do_print` will print this field.

        Creates and initializes a new sequence object.

        Args:
            name:
        """
        UVMSequenceBase.__init__(self, name)
        self.req = None
        self.rsp = None
        self.param_sequencer = None

    #  // Function: send_request
    #  //
    #  // This method will send the request item to the sequencer, which will forward
    #  // it to the driver.  If the rerandomize bit is set, the item will be
    #  // randomized before being sent to the driver. The send_request function may
    #  // only be called after <uvm_sequence_base::wait_for_grant> returns.
    #
    #  function void send_request(uvm_sequence_item request, bit rerandomize = 0)
    #    REQ m_request
    #
    #    if (m_sequencer == null) begin
    #      uvm_report_fatal("SSENDREQ", "Null m_sequencer reference", UVM_NONE)
    #    end
    #    if (!$cast(m_request, request)) begin
    #      uvm_report_fatal("SSENDREQ", "Failure to cast uvm_sequence_item to request", UVM_NONE)
    #    end
    #    m_sequencer.send_request(this, m_request, rerandomize)
    #  endfunction


    #  // Function: get_current_item
    #  //
    #  // Returns the request item currently being executed by the sequencer. If the
    #  // sequencer is not currently executing an item, this method will return ~null~.
    #  //
    #  // The sequencer is executing an item from the time that get_next_item or peek
    #  // is called until the time that get or item_done is called.
    #  //
    #  // Note that a driver that only calls get will never show a current item,
    #  // since the item is completed at the same time as it is requested.
    #
    #  function REQ get_current_item()
    #    if (!$cast(param_sequencer, m_sequencer))
    #      uvm_report_fatal("SGTCURR", "Failure to cast m_sequencer to the parameterized sequencer", UVM_NONE)
    #    return (param_sequencer.get_current_item())
    #  endfunction


    #  // Task: get_response
    #  //
    #  // By default, sequences must retrieve responses by calling get_response.
    #  // If no transaction_id is specified, this task will return the next response
    #  // sent to this sequence.  If no response is available in the response queue,
    #  // the method will block until a response is received.
    #  //
    #  // If a transaction_id is parameter is specified, the task will block until
    #  // a response with that transaction_id is received in the response queue.
    #  //
    #  // The default size of the response queue is 8.  The get_response method must
    #  // be called soon enough to avoid an overflow of the response queue to prevent
    #  // responses from being dropped.
    #  //
    #  // If a response is dropped in the response queue, an error will be reported
    #  // unless the error reporting is disabled via
    #  // set_response_queue_error_report_disabled.
    async def get_response(self, response, transaction_id=-1):
        """
        Args:
            response:
            transaction_id:
        """
        if response is None:
            uvm_fatal("RESP IS NONE", "response arg must be an empty list")
        rsp = []
        await self.get_base_response(rsp, transaction_id)
        response.append(rsp[0])


    def put_response(self, response_item):
        """
        Internal method.

        Args:
            response_item (UVMSequenceItem): Response item
        """
        #response
        #if (!$cast(response, response_item)) begin
        #    uvm_report_fatal("PUTRSP", "Failure to cast response in put_response", UVM_NONE)
        self.put_base_response(response_item)


    def do_print(self, printer):
        """
        Function- do_print

        Args:
            printer (UVMPrinter): Printer used for printing
        """
        super().do_print(printer)
        printer.print_object("req", self.req)
        printer.print_object("rsp", self.rsp)
