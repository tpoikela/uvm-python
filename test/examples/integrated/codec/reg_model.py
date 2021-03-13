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



#class reg_IntMask(uvm_reg):
    #
    #   uvm_reg_field TxEmpty
    #   uvm_reg_field TxLow
    #   uvm_reg_field TxFull
    #   uvm_reg_field RxEmpty
    #   uvm_reg_field RxHigh
    #   uvm_reg_field RxFull
    #   uvm_reg_field SA
    #
    #   def __init__(self, name = "IntMask")
    #      super().__init__(name,9,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build(self):
    #      TxEmpty = uvm_reg_field.type_id.create("TxEmpty",None, self.get_full_name())
    #      TxLow   = uvm_reg_field.type_id.create("TxLow",None, self.get_full_name())
    #      TxFull  = uvm_reg_field.type_id.create("TxFull",None, self.get_full_name())
    #      RxEmpty = uvm_reg_field.type_id.create("RxEmpty",None, self.get_full_name())
    #      RxHigh  = uvm_reg_field.type_id.create("RxHigh",None, self.get_full_name())
    #      RxFull  = uvm_reg_field.type_id.create("RxFull",None, self.get_full_name())
    #      SA      = uvm_reg_field.type_id.create("OOSA",None, self.get_full_name())
    #
    #      TxEmpty.configure(self, 1, 0, "RW", 0, 1'b0, 1, 0, 0)
    #        TxLow.configure(self, 1, 1, "RW", 0, 1'b0, 1, 0, 0)
    #       TxFull.configure(self, 1, 2, "RW", 0, 1'b0, 1, 0, 0)
    #      RxEmpty.configure(self, 1, 4, "RW", 0, 1'b0, 1, 0, 0)
    #       RxHigh.configure(self, 1, 5, "RW", 0, 1'b0, 1, 0, 0)
    #       RxFull.configure(self, 1, 6, "RW", 0, 1'b0, 1, 0, 0)
    #           SA.configure(self, 1, 8, "RW", 0, 1'b0, 1, 0, 0)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_IntMask)
    #   
    #endclass
#
#
#class reg_TxStatus(uvm_reg):
    #
    #   uvm_reg_field TxEn
    #
    #   def __init__(self, name = "TxStatus")
    #      super().__init__(name,1,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build(self):
    #      TxEn = uvm_reg_field.type_id.create("TxEn",None, self.get_full_name())
    #      TxEn.configure(self, 1, 0, "RW", 0, 1'b0, 1, 0, 0)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_TxStatus)
    #   
    #endclass
#
#
#class reg_TxLWM(uvm_reg):
    #
    #   uvm_reg_field TxLWM
    #
    #   def __init__(self, name = "TxLWM")
    #      super().__init__(name,5,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build(self):
    #      TxLWM = uvm_reg_field.type_id.create("TxLWM",None, self.get_full_name())
    #      TxLWM.configure(self, 5, 0, "RW", 0, 5'd8, 1, 0, 0)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_TxLWM)
    #   
    #endclass
#
#
#class reg_RxStatus(uvm_reg):
    #
    #   uvm_reg_field RxEn
    #   uvm_reg_field Align
    #
    #   def __init__(self, name = "RxStatus")
    #      super().__init__(name,2,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build(self):
    #      RxEn = uvm_reg_field.type_id.create("RxEn",None, self.get_full_name())
    #      RxEn.configure(self, 1, 0, "RW", 0, 1'b0, 1, 0, 0)
    #
    #      Align = uvm_reg_field.type_id.create("Align",None, self.get_full_name())
    #      Align.configure(self, 1, 1, "RO", 0, 1'b0, 1, 0, 0)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_RxStatus)
    #   
    #endclass
#
#
#class reg_RxHWM(uvm_reg):
    #
    #   uvm_reg_field RxHWM
    #
    #   def __init__(self, name = "RxHWM")
    #      super().__init__(name,5,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build(self):
    #      RxHWM = uvm_reg_field.type_id.create("RxHWM",None, self.get_full_name())
    #      RxHWM.configure(self, 5, 0, "RW", 0, 5'd16, 1, 0, 0)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_RxHWM)
    #   
    #endclass
#
#
#class reg_TxRx(uvm_reg):
    #
    #   uvm_reg_field TxRx
    #      
    #   def __init__(self, name = "TxRx")
    #      super().__init__(name,8,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build(self):
    #      TxRx = uvm_reg_field.type_id.create("TxRx",None, self.get_full_name())
    #      TxRx.configure(self, 8, 0, "RW", 1, 8'h00, 1, 0, 0)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_TxRx)
    #   
    #endclass


class reg_dut(UVMRegBlock):


    def __init__(self, name = "dut"):
        super().__init__(name,UVM_NO_COVERAGE)
        self.IntSrc = None
        self.IntMask = None
        self.TxStatus = None
        self.TxLWM = None
        self.RxStatus = None
        self.RxHWM = None
        self.TxRx = None


    def build(self):
        self.IntSrc = reg_IntSrc.type_id.create("IntSrc",None,self.get_full_name())
        #      IntMask = reg_IntMask.type_id.create("IntMask",None, self.get_full_name())
        #     TxStatus = reg_TxStatus.type_id.create("TxStatus",None, self.get_full_name())
        #        TxLWM = reg_TxLWM.type_id.create("TxLWM",None, self.get_full_name())
        #     RxStatus = reg_RxStatus.type_id.create("RxStatus",None, self.get_full_name())
        #        RxHWM = reg_RxHWM.type_id.create("RxHWM",None, self.get_full_name())
        #         TxRx = reg_TxRx.type_id.create("TxRx",None, self.get_full_name())

        self.IntSrc.configure(self)
        #      IntMask.configure(self)
        #     TxStatus.configure(self)
        #        TxLWM.configure(self)
        #     RxStatus.configure(self)
        #        RxHWM.configure(self)
        #         TxRx.configure(self)

        self.IntSrc.build()
        #      IntMask.build()
        #     TxStatus.build()
        #        TxLWM.build()
        #     RxStatus.build()
        #        RxHWM.build()
        #         TxRx.build()

        # define default map
        self.default_map = self.create_map("default_map",  0x0, 4, UVM_LITTLE_ENDIAN, 1)
        self.default_map.add_reg(self.IntSrc,   0x0000, "RW")
        #      default_map.add_reg(IntMask,  0x0004, "RW")
        #      default_map.add_reg(TxStatus, 0x0010, "RW")
        #      default_map.add_reg(TxLWM,    0x0014, "RW")
        #      default_map.add_reg(RxStatus, 0x0020, "RW")
        #      default_map.add_reg(RxHWM,    0x0024, "RW")
        #      default_map.add_reg(TxRx,     0x0100, "RW")


uvm_object_utils(reg_dut)
