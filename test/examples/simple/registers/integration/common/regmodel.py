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

from uvm.reg import UVMReg, UVMRegField
from uvm.base import sv
from uvm.macros import uvm_object_utils
from uvm.reg.uvm_mem import UVMMem
from uvm.reg.uvm_reg_block import UVMRegBlock
from uvm.reg.uvm_reg_model import UVM_NO_COVERAGE, UVM_LITTLE_ENDIAN


class dut_ID(UVMReg):


    def __init__(self, name="dut_ID"):
        super().__init__(name,32, UVM_NO_COVERAGE)
        self.REVISION_ID = None
        self.CHIP_ID = None
        self.PRODUCT_ID = None


    def build(self):
        self.REVISION_ID = UVMRegField.type_id.create("REVISION_ID")
        self.CHIP_ID = UVMRegField.type_id.create("CHIP_ID")
        self.PRODUCT_ID = UVMRegField.type_id.create("PRODUCT_ID")
        self.REVISION_ID.configure(self, 8, 0, "RO", 0, 0x03, 1, 0, 1)
        self.CHIP_ID.configure(self, 8, 8, "RO", 0, 0x5A, 1, 0, 1)
        self.PRODUCT_ID.configure(self, 10, 16,"RO", 0, 0x176, 1, 0, 1)


uvm_object_utils(dut_ID)



class dut_DATA(UVMReg):


    def __init__(self, name="dut_DATA"):
        super().__init__(name,32, UVM_NO_COVERAGE)
        self.value = None


    def build(self):
        self.value = UVMRegField.type_id.create("value")
        self.value.configure(self, 32, 0, "RW", 1, 0x0, 1, 0, 1)


uvm_object_utils(dut_DATA)



class dut_SOCKET(UVMReg):

    #   rand UVMRegField IP
    #   rand UVMRegField PORT

    def __init__(self, name="dut_ADDR"):
        super().__init__(name, 64, UVM_NO_COVERAGE)
        self.IP = None
        self.PORT = None


    def build(self):
        self.IP = UVMRegField.type_id.create("value")
        self.PORT = UVMRegField.type_id.create("value")
        self.IP.configure(self, 48, 0, "RW", 0, 0x0, 1, 0, 1)
        self.PORT.configure(self, 16, 48, "RW", 0, 0x0, 1, 0, 1)
        self.rand('IP')
        self.rand('PORT')


uvm_object_utils(dut_SOCKET)


class dut_RAM(UVMMem):

    def __init__(self, name="dut_RAM"):
        super().__init__(name, 8, 32, "RW", UVM_NO_COVERAGE)


uvm_object_utils(dut_RAM)



class dut_regmodel(UVMRegBlock):

    #   rand dut_ID       ID
    #   rand dut_DATA     DATA

    #   rand dut_SOCKET   SOCKET[256]

    #   rand dut_RAM      RAM


    def __init__(self, name="slave"):
        super().__init__(name, UVM_NO_COVERAGE)
        self.SOCKET = []
        self.nsockets = 16


    def build(self):
        # create
        self.ID        = dut_ID.type_id.create("ID")
        self.DATA      = dut_DATA.type_id.create("DATA")
        for i in range(self.nsockets):
            socket = dut_SOCKET.type_id.create(sv.sformatf("SOCKET[%0d]", i))
            self.SOCKET.append(socket)

        self.RAM   = dut_RAM.type_id.create("DMA_RAM")

        # configure/build registers
        self.ID.configure(self, None, "ID")
        self.ID.build()
        self.DATA.configure(self, None, "DATA")
        self.DATA.build()
        for i in range(len(self.SOCKET)):
            self.SOCKET[i].configure(self, None, sv.sformatf("SOCKET[%0d]", i))
            self.SOCKET[i].build()

        self.RAM.configure(self, "DMA")

        # define default map/add register to map
        self.default_map = self.create_map("default_map", 0x0, 4, UVM_LITTLE_ENDIAN, 1)
        self.default_map.add_reg(self.ID, 0x0, "RW")
        self.default_map.add_reg(self.DATA, 0x24, "RW")
        for i in range(len(self.SOCKET)):
            self.default_map.add_reg(self.SOCKET[i], 0x1000 + 16 * i, "RW")
        self.default_map.add_mem(self.RAM, 0x2000, "RW")


uvm_object_utils(dut_regmodel)
