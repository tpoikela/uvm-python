#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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

from uvm.base.uvm_object import UVMObject
from uvm.macros import *
from uvm import sv

RANGE_32B = range(0, (1 << 32) - 1)


class packet(UVMObject):
    #    rand int addr
    #    rand int data

    # Use the macro in a class to implement factory registration along with other
    # utilities (create, get_type_name). For only factory registration, use
    # the macro `uvm_object_registry(packet,"packet").

    # Base constraints TODO
    #    constraint c1 { addr inside { [ 0x0: 0x40], [ 0x100: 0x200], [ 0x1000:  0x1fff], [ 0x4000:  0x4fff] }; }
    #    constraint c2 { (addr <=  0x40) -> (data inside { [10:20] } ); }
    #    constraint c3 { (addr >=  0x100  and  addr <=  0x200) -> (data inside { [100:200] } ); }
    #    constraint c4 { (addr >=  0x1000  and  addr <=  0x1fff) -> (data inside { [300:400] } ); }
    #    constraint c5 { (addr >=  0x4000  and  addr <=  0x4fff) -> (data inside { [600:800] } ); }


    # do printing, comparing, etc. These functions can also be automated inside
    # the `uvm_object_utils_begin/end macros if desired. Below show the manual 
    # approach.
    def do_print(self, printer):
        printer.print_field("addr", self.addr, sv.bits(self.addr))
        printer.print_field("data", self.data, sv.bits(self.data))

    def do_compare(self, rhs, comparer):
        rhs_ = None
        if rhs is None:
            return 0
        do_compare = 1
        do_compare &= comparer.compare_field("addr", self.addr, rhs_.addr,
            sv.bits(self.addr))
        do_compare &= comparer.compare_field("data", self.data, rhs_.data,
            sv.bits(self.data))
        return do_compare

    def do_copy(self, rhs):
        rhs_ = rhs
        if rhs is None:
            return
        self.addr = rhs_.addr
        self.data = rhs_.data

    def __init__(self, name="packet"):
        super().__init__(name)
        self.addr = 0
        self.rand('addr', RANGE_32B)
        self.data = 0
        self.rand('data', RANGE_32B)


uvm_object_utils(packet)
