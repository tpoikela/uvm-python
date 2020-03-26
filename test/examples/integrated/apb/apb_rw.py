#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//

from uvm.seq.uvm_sequence_item import UVMSequenceItem
from uvm.macros import *
from uvm.reg.uvm_reg_adapter import *
from uvm.reg.uvm_reg_model import *
from uvm.base.uvm_object_globals import *


class apb_rw(UVMSequenceItem):

    READ = 0
    WRITE = 1

    def __init__(self, name="apb_rw"):
        super().__init__(name)
        self.addr = 0  # bit
        self.data = 0  # logic
        self.kind = apb_rw.READ  # kind_e
        self.rand("kind", [apb_rw.READ, apb_rw.WRITE])


    def convert2string(self):
        kind = "READ"
        if self.kind == 1:
            kind = "WRITE"
        return sv.sformatf("kind=%s addr=%0h data=%0h",
                kind, self.addr, self.data)

    #endclass: apb_rw
uvm_object_utils_begin(apb_rw)
uvm_field_int("addr", UVM_ALL_ON | UVM_NOPACK)
uvm_field_int("data", UVM_ALL_ON | UVM_NOPACK)
uvm_object_utils_end(apb_rw)


class reg2apb_adapter(UVMRegAdapter):


    def __init__(self, name="reg2apb_adapter"):
        super().__init__(name)

    def reg2bus(self, rw):
        apb = apb_rw.type_id.create("apb_rw")
        apb.kind = apb_rw.WRITE
        if (rw.kind == UVM_READ):
            apb.kind = apb_rw.READ
        apb.addr = rw.addr
        apb.data = rw.data
        return apb


    def bus2reg(self, bus_item, rw):  # rw must be ref
        apb = None
        arr = []
        if (not sv.cast(arr,bus_item, apb_rw)):
            uvm_fatal("NOT_APB_TYPE", "Provided bus_item is not of the correct type")
            return

        apb = arr[0]
        rw.kind = UVM_WRITE
        if (apb.kind == apb_rw.READ):
            rw.kind = UVM_READ
        rw.addr = apb.addr
        rw.data = apb.data
        rw.status = UVM_IS_OK
        return rw
    #  endfunction
    #
    #endclass
uvm_object_utils(reg2apb_adapter)
