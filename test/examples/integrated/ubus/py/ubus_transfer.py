#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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

from uvm.seq import UVMSequenceItem
from uvm.macros import *
from uvm.base.sv import sv

#//----------------------------------------------------------------------------
#//
#// ubus transfer enums, parameters, and events
#//
#//----------------------------------------------------------------------------

# ubus_read_write_enum;
NOP = 0
READ = 1
WRITE = 2

#//----------------------------------------------------------------------------
#//
#// CLASS: ubus_transfer
#//
#//----------------------------------------------------------------------------


class ubus_transfer(UVMSequenceItem):


    # TODO add these constraints
    #  constraint c_data_wait_size {
    #    data.size() == size;
    #    wait_state.size() == size;
    #  }

    def __init__(self, name="ubus_transfer_inst"):
        UVMSequenceItem.__init__(self, name)
        self.addr = 0
        self.rand("addr", range(0, 65536 - 1))
        self.read_write = 0
        self.rand("read_write", [READ, WRITE])
        self.size = 0
        self.rand("size", [1, 2, 4, 8])
        self.data = []
        #self.rand("data")
        self.wait_state = []
        #self.rand("wait_state")
        self.error_pos = 0
        #c_data_wait_size = lambda data, size: len(data) == size
        #self.constraint(c_data_wait_size)
        #self.rand("error_pos")
        self.transmit_delay = 0
        self.rand("transmit_delay", range(0, 11))
        self.master = ""
        self.slave = ""

    def post_randomize(self):
        self.wait_state = []
        self.data = []
        for i in range(self.size):
            self.wait_state.append(sv.urandom_range(0, 1))
            self.data.append(sv.urandom_range(1, 1 << 8))


    def do_copy(self, rhs):
        self.addr = rhs.addr
        self.read_write = rhs.read_write
        self.size = rhs.size
        for val in rhs.data:
            self.data.append(val)
        for val in rhs.wait_state:
            self.wait_state.append(val)

    def do_clone(self):
        new_obj = ubus_transfer()
        new_obj.copy(self)
        return new_obj

    def convert2string(self):
        rw_str = "READ"
        if self.read_write == WRITE:
            rw_str = "WRITE"
        elif self.read_write == NOP:
            rw_str = "NOP"
        res = "ID: " + str(self.m_transaction_id)
        res += ", addr: " + str(self.addr) + ", read_write: " + rw_str
        res += ", size: " + str(self.size) + ", wait_state: " + str(self.wait_state)
        res += "\ndata: "
        for d in self.data:
            res += hex(d) + ','
        res += "\n"
        return res


uvm_object_utils(ubus_transfer)

# TODO implement the field macros
#  `uvm_object_utils_begin(ubus_transfer)
#    `uvm_field_int      (addr,           UVM_DEFAULT)
#    `uvm_field_enum     (ubus_read_write_enum, read_write, UVM_DEFAULT)
#    `uvm_field_int      (size,           UVM_DEFAULT)
#    `uvm_field_array_int(data,           UVM_DEFAULT)
#    `uvm_field_array_int(wait_state,     UVM_DEFAULT)
#    `uvm_field_int      (error_pos,      UVM_DEFAULT)
#    `uvm_field_int      (transmit_delay, UVM_DEFAULT)
#    `uvm_field_string   (master,         UVM_DEFAULT|UVM_NOCOMPARE)
#    `uvm_field_string   (slave,          UVM_DEFAULT|UVM_NOCOMPARE)
#  `uvm_object_utils_end
