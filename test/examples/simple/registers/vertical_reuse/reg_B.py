#//
#//------------------------------------------------------------------------------
#//   Copyright 2011 Mentor Graphics Corporation
#//   Copyright 2011 Cadence Design Systems, Inc.
#//   Copyright 2011 Synopsys, Inc.
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
#//------------------------------------------------------------------------------


from uvm.reg.uvm_reg import *
from uvm.macros import *
from uvm.reg.uvm_reg_block import *
from uvm.reg.uvm_reg_field import *
from uvm.reg.uvm_reg_model import *
from uvm.base.uvm_resource_db import UVMResourceDb

class reg_B_R(UVMReg):

    def __init__(self, name="B_R"):
        super().__init__(name, 8, UVM_NO_COVERAGE)
        self.F = None


    def build(self):
        self.F = UVMRegField.type_id.create("F")
        self.F.configure(self, 8, 0, "RW", 0, 0x0, 1, 0, 1)


uvm_object_utils(reg_B_R)


class reg_fld_B_CTL_CTL():
    NOP = 0b00
    INC = 0b01
    DEC = 0b10
    CLR = 0b11


class reg_B_CTL(UVMReg):
    #   rand uvm_reg_field CTL
    #
    def __init__(self, name = "B_CTL"):
        super().__init__(name,8,UVM_NO_COVERAGE)
        self.CTL = None

    def build(self):
        self.CTL = UVMRegField.type_id.create("CTL")
        self.CTL.configure(self, 2, 0, "WO", 0, 0x0, 1, 0, 1)
        UVMResourceDb.set("REG::" + self.get_full_name(), "NO_REG_TESTS", 1)


uvm_object_utils(reg_B_CTL)


class reg_block_B(UVMRegBlock):
    #   rand reg_B_R R
    #   rand reg_B_CTL CTL
    #   rand uvm_reg_field F
    #
    def __init__(self, name="B"):
        super().__init__(name,UVM_NO_COVERAGE)
        self.R = None  # reg_B_R
        self.F = None  # uvm_reg_field
        #self.s = None  # CTL_value
        self.CTL = None  # reg_B_CTL
        #   endfunction: new

    def build(self):

        # create regs
        self.R   = reg_B_R.type_id.create("R")
        self.CTL = reg_B_CTL.type_id.create("CTL")

        # build regs
        self.R.build()
        self.R.configure(self, None)
        self.CTL.build()
        self.CTL.configure(self, None)

        # create map
        self.default_map = self.create_map("default_map", 0x0, 1, UVM_LITTLE_ENDIAN)
        self.default_map.add_reg(self.R, 0x0, "RW")
        self.default_map.add_reg(self.CTL, 0x1, "RW")

        # assign field aliases
        self.F = self.R.F



uvm_object_utils(reg_block_B)
