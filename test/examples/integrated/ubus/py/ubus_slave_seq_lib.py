#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela
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

from ubus_transfer import *
from uvm.seq import UVMSequence
from uvm.base import sv
from uvm.macros import *

#//------------------------------------------------------------------------------
#//
#// SEQUENCE: simple_response_seq
#//
#//------------------------------------------------------------------------------

#class simple_response_seq extends uvm_sequence #(ubus_transfer)
#   ubus_slave_sequencer p_sequencer
#
#  function new(string name="simple_response_seq")
#    super.new(name)
#  endfunction
#
#//  `uvm_object_utils(simple_response_seq)
#
#  `uvm_object_utils(simple_response_seq)
#
#  ubus_transfer util_transfer
#
#  virtual task body()
#     $cast(p_sequencer, m_sequencer)
#
#    `uvm_info(get_type_name(),
#      $sformatf("%s starting...",
#      get_sequence_path()), UVM_MEDIUM)
#    forever begin
#      p_sequencer.addr_ph_port.peek(util_transfer)
#
#      // Need to raise/drop objection before each item because we don't want
#      // to be stopped in the middle of a transfer.
#      uvm_test_done.raise_objection(this)
#      `uvm_do_with(req,
#        { req.read_write == util_transfer.read_write
#          req.size == util_transfer.size
#          req.error_pos == 1000; } )
#      uvm_test_done.drop_objection(this)
#    end
#  endtask : body
#
#endclass : simple_response_seq
#
#

#//------------------------------------------------------------------------------
#//
#// SEQUENCE: slave_memory_seq
#//
#//------------------------------------------------------------------------------


#class slave_memory_seq extends uvm_sequence #(ubus_transfer)
class slave_memory_seq(UVMSequence):
    #
    def __init__(self, name="slave_memory_seq"):
        UVMSequence.__init__(self, name)
        #  ubus_transfer util_transfer
        self.util_transfer = ubus_transfer()
        self.m_mem = {}
        self.req = ubus_transfer()

    #  `uvm_declare_p_sequencer(ubus_slave_sequencer)

    def pre_do(self, is_item):
        # Update the properties that are relevant to both read and write
        self.req.size       = self.util_transfer.size
        self.req.addr       = self.util_transfer.addr
        self.req.read_write = self.util_transfer.read_write
        self.req.error_pos  = 1000
        self.req.transmit_delay = 0
        self.req.data = [0] * self.util_transfer.size
        self.req.wait_state = [0] * self.util_transfer.size
        for i in range(self.util_transfer.size):
            self.req.wait_state[i] = 2
            # For reads, populate req with the random "readback" data of the size
            # requested in util_transfer
            if (self.req.read_write == READ):
                new_addr = self.util_transfer.addr + i
                if new_addr not in self.m_mem.exists:
                    self.m_mem[new_addr] = sv.urandom()
                self.req.data[i] = self.m_mem[new_addr]
        #  endtask

    def post_do(self, this_item):
        # For writes, update the m_mem associative array
        if (self.util_transfer.read_write == WRITE):
            for i in range(self.req.size):
                self.m_mem[self.req.addr + i] = self.req.data[i]

    @cocotb.coroutine
    def body(self):
        #p = None  # uvm_phase
        uvm_info(self.get_type_name(), sv.sformatf("%s starting...",
            self.get_sequence_path()), UVM_MEDIUM)

        #$cast(req, create_item(ubus_transfer::get_type(), p_sequencer, "req"))
        #p = self.get_starting_phase()

        while True:
            util_transfer = []
            yield self.p_sequencer.addr_ph_port.peek(util_transfer)
            util_transfer = util_transfer[0]

            # Need to raise/drop objection before each item because we don't want
            # to be stopped in the middle of a transfer.
            #p.raise_objection(self)

            yield self.start_item(self.req)
            yield self.finish_item(self.req)

            #p.drop_objection(self)
        #  endtask : body
        #

    #endclass : slave_memory_seq
uvm_object_utils(slave_memory_seq)
