#// 
#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
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

from uvm import *


class reg_IntSrc(UVMReg):
    def __init__(self, name = "IntSrc"):
        super().__init__(name,9,UVM_NO_COVERAGE)
        self.TxEmpty = None
        self.TxLow = None
        self.TxFull = None
        self.RxEmpty = None
        self.RxHigh = None
        self.RxFull = None
        self.SA = None

    def build(self):
        self.TxEmpty = UVMRegField.type_id.create("TxEmpty",None, self.get_full_name())
        self.TxLow   = UVMRegField.type_id.create("TxLow",None, self.get_full_name())
        self.TxFull  = UVMRegField.type_id.create("TxFull",None, self.get_full_name())
        self.RxEmpty = UVMRegField.type_id.create("RxEmpty",None, self.get_full_name())
        self.RxHigh  = UVMRegField.type_id.create("RxHigh",None, self.get_full_name())
        self.RxFull  = UVMRegField.type_id.create("RxFull",None, self.get_full_name())
        self.SA      = UVMRegField.type_id.create("OOSA",None, self.get_full_name())

        self.TxEmpty.configure(self, 1, 0, "RO", 1, 1, 1, 0, 0)
        self.TxLow.configure(self, 1, 1, "RO", 1, 1, 1, 0, 0)
        self.TxFull.configure(self, 1, 2, "RO", 1, 0, 1, 0, 0)
        self.RxEmpty.configure(self, 1, 4, "RO", 1, 1, 1, 0, 0)
        self.RxHigh.configure(self, 1, 5, "RO", 1, 0, 1, 0, 0)
        self.RxFull.configure(self, 1, 6, "RO", 1, 0, 1, 0, 0)
        self.SA.configure(self, 1, 8, "W1C", 1, 0, 1, 0, 0)

uvm_object_utils(reg_IntSrc)



class reg_IntMask(UVMReg):
    #
    #   UVMRegField TxEmpty
    #   UVMRegField TxLow
    #   UVMRegField TxFull
    #   UVMRegField RxEmpty
    #   UVMRegField RxHigh
    #   UVMRegField RxFull
    #   UVMRegField SA
    #
    def __init__(self, name = "IntMask"):
        super().__init__(name,9,UVM_NO_COVERAGE)
    #   endfunction
    #
    def build(self):
        self.TxEmpty = UVMRegField.type_id.create("TxEmpty",None, self.get_full_name())
        self.TxLow   = UVMRegField.type_id.create("TxLow",None, self.get_full_name())
        self.TxFull  = UVMRegField.type_id.create("TxFull",None, self.get_full_name())
        self.RxEmpty = UVMRegField.type_id.create("RxEmpty",None, self.get_full_name())
        self.RxHigh  = UVMRegField.type_id.create("RxHigh",None, self.get_full_name())
        self.RxFull  = UVMRegField.type_id.create("RxFull",None, self.get_full_name())
        self.SA      = UVMRegField.type_id.create("OOSA",None, self.get_full_name())

        self.TxEmpty.configure(self, 1, 0, "RW", 0, 0, 1, 0, 0)
        self.TxLow.configure(self, 1, 1, "RW", 0, 0, 1, 0, 0)
        self.TxFull.configure(self, 1, 2, "RW", 0, 0, 1, 0, 0)
        self.RxEmpty.configure(self, 1, 4, "RW", 0, 0, 1, 0, 0)
        self.RxHigh.configure(self, 1, 5, "RW", 0, 0, 1, 0, 0)
        self.RxFull.configure(self, 1, 6, "RW", 0, 0, 1, 0, 0)
        self.SA.configure(self, 1, 8, "RW", 0, 0, 1, 0, 0)

uvm_object_utils(reg_IntMask)

#
#
class reg_TxStatus(UVMReg):
    #
    #   UVMRegField TxEn
    #
    def __init__(self, name = "TxStatus"):
        super().__init__(name,1,UVM_NO_COVERAGE)
    #   endfunction
    #
    def build(self):
        self.TxEn = UVMRegField.type_id.create("TxEn",None, self.get_full_name())
        self.TxEn.configure(self, 1, 0, "RW", 0, 0, 1, 0, 0)

uvm_object_utils(reg_TxStatus)


class reg_TxLWM(UVMReg):
    #
    #   UVMRegField TxLWM
    #
    def __init__(self, name = "TxLWM"):
        super().__init__(name,5,UVM_NO_COVERAGE)
    #   endfunction
    #
    def build(self):
        self.TxLWM = UVMRegField.type_id.create("TxLWM",None, self.get_full_name())
        self.TxLWM.configure(self, 5, 0, "RW", 0, 8, 1, 0, 0)

uvm_object_utils(reg_TxLWM)


class reg_RxStatus(UVMReg):
    #
    #   UVMRegField RxEn
    #   UVMRegField Align
    #
    def __init__(self, name = "RxStatus"):
       super().__init__(name,2,UVM_NO_COVERAGE)

    #
    def build(self):
        self.RxEn = UVMRegField.type_id.create("RxEn",None, self.get_full_name())
        self.RxEn.configure(self, 1, 0, "RW", 0, 0, 1, 0, 0)

        self.Align = UVMRegField.type_id.create("Align",None, self.get_full_name())
        self.Align.configure(self, 1, 1, "RO", 0, 0, 1, 0, 0)

uvm_object_utils(reg_RxStatus)


class reg_RxHWM(UVMReg):
    #
    #   UVMRegField RxHWM
    #
    def __init__(self, name = "RxHWM"):
        super().__init__(name,5,UVM_NO_COVERAGE)
    #
    def build(self):
        self.RxHWM = UVMRegField.type_id.create("RxHWM",None, self.get_full_name())
        self.RxHWM.configure(self, 5, 0, "RW", 0, 16, 1, 0, 0)

uvm_object_utils(reg_RxHWM)


class reg_TxRx(UVMReg):
    #
    #   UVMRegField TxRx
    #      
    def __init__(self, name = "TxRx"):
        super().__init__(name,8,UVM_NO_COVERAGE)
    #   endfunction
    #
    def build(self):
        self.TxRx = UVMRegField.type_id.create("TxRx",None, self.get_full_name())
        self.TxRx.configure(self, 8, 0, "RW", 1, 0x00, 1, 0, 0)
    #   endfunction
    #   
uvm_object_utils(reg_TxRx)
    #   
    #endclass


class reg_dut(UVMRegBlock):


    def __init__(self, name = "dut"):
        super().__init__(name, UVM_NO_COVERAGE)
        self.IntSrc = None
        self.IntMask = None
        self.TxStatus = None
        self.TxLWM = None
        self.RxStatus = None
        self.RxHWM = None
        self.TxRx = None


    def build(self):
        self.IntSrc = reg_IntSrc.type_id.create("IntSrc",None,self.get_full_name())
        self.IntMask = reg_IntMask.type_id.create("IntMask",None, self.get_full_name())
        self.TxStatus = reg_TxStatus.type_id.create("TxStatus",None, self.get_full_name())
        self.TxLWM = reg_TxLWM.type_id.create("TxLWM",None, self.get_full_name())
        self.RxStatus = reg_RxStatus.type_id.create("RxStatus",None, self.get_full_name())
        self.RxHWM = reg_RxHWM.type_id.create("RxHWM",None, self.get_full_name())
        self.TxRx = reg_TxRx.type_id.create("TxRx",None, self.get_full_name())

        self.IntSrc.configure(self)
        self.IntMask.configure(self)
        self.TxStatus.configure(self)
        self.TxLWM.configure(self)
        self.RxStatus.configure(self)
        self.RxHWM.configure(self)
        self.TxRx.configure(self)

        self.IntSrc.build()
        self.IntMask.build()
        self.TxStatus.build()
        self.TxLWM.build()
        self.RxStatus.build()
        self.RxHWM.build()
        self.TxRx.build()

        # define default map
        self.default_map = self.create_map("default_map", 0x0, 4, UVM_LITTLE_ENDIAN, 1)
        self.default_map.add_reg(self.IntSrc,   0x0000, "RW")
        self.default_map.add_reg(self.IntMask,  0x0004, "RW")
        self.default_map.add_reg(self.TxStatus, 0x0010, "RW")
        self.default_map.add_reg(self.TxLWM,    0x0014, "RW")
        self.default_map.add_reg(self.RxStatus, 0x0020, "RW")
        self.default_map.add_reg(self.RxHWM,    0x0024, "RW")
        self.default_map.add_reg(self.TxRx,     0x0100, "RW")


uvm_object_utils(reg_dut)
