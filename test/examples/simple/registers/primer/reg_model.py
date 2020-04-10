#//
#//----------------------------------------------------------------------------
#//   Copyright 2011 Mentor Graphics Corporation
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
#//----------------------------------------------------------------------------

from uvm.reg.uvm_reg import UVMReg
from uvm.macros import uvm_object_utils
from uvm.base.sv import sv
from uvm.reg.uvm_reg_indirect import *
from uvm.reg.uvm_reg_field import UVMRegField
from uvm.reg.uvm_reg_file import *
from uvm.reg.uvm_mem import *
from uvm.reg.uvm_reg_block import *


class reg_slave_ID(UVMReg):


    def __init__(self, name="slave_ID"):
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


uvm_object_utils(reg_slave_ID)


class reg_slave_INDEX(UVMReg):


    def __init__(self, name="slave_INDEX"):
        super().__init__(name,8,UVM_NO_COVERAGE)


    def build(self):
        self.value = UVMRegField.type_id.create("value")
        self.value.configure(self, 8, 0, "RW", 0, 0x0, 1, 0, 1)


uvm_object_utils(reg_slave_INDEX)


class reg_slave_DATA(UVMRegIndirectData):

    def __init__(self, name="slave_DATA"):
        super().__init__(name,32, UVM_NO_COVERAGE)


uvm_object_utils(reg_slave_DATA)



class reg_slave_SOCKET(UVMReg):

    # TODO reg randomisation on sv side
    #   rand UVMRegField IP
    #   rand UVMRegField PORT

    def __init__(self, name="slave_ADDR"):
        super().__init__(name,64, UVM_NO_COVERAGE)
        self.IP = None
        self.PORT = None


    def build(self):
        self.IP   = UVMRegField.type_id.create("IP")
        self.PORT = UVMRegField.type_id.create("PORT")
        self.IP.configure(self, 48, 0, "RW", 0, 0x0, 1, 0, 1)
        self.PORT.configure(self, 16, 48, "RW", 0, 0x0, 1, 0, 1)


uvm_object_utils(reg_slave_SOCKET)


class reg_slave_SESSION(UVMRegFile):

    #   rand reg_slave_SOCKET SRC
    #   rand reg_slave_SOCKET DST

    def __init__(self, name="slave_SESSION"):
        super().__init__(name)


    def build(self):
        self.SRC = reg_slave_SOCKET.type_id.create("SRC")
        self.DST = reg_slave_SOCKET.type_id.create("DST")

        self.SRC.configure(self.get_block(), self, "SRC")
        self.DST.configure(self.get_block(), self, "DST")

        self.SRC.build()
        self.DST.build()


    def map(self, mp, offset):
        mp.add_reg(self.SRC, offset + 0x00)
        mp.add_reg(self.DST, offset + 0x08)


    def set_offset(self, mp, offset):
        self.SRC.set_offset(mp, offset + 0x00)
        self.DST.set_offset(mp, offset + 0x08)


uvm_object_utils(reg_slave_SESSION)


class reg_slave_TABLES(UVMReg):
    #
    #   rand UVMRegField value
    #
    def __init__(self, name="slave_TABLES"):
        super().__init__(name,32, UVM_NO_COVERAGE)
        self.value = None


    def build(self):
        self.value = UVMRegField.type_id.create("value")
        self.value.configure(self, 32, 0, "RW", 0, 0x0, 1, 0, 1)


uvm_object_utils(reg_slave_TABLES)


class mem_slave_DMA_RAM(UVMMem):
    #
    def __init__(self, name="slave_DMA_RAM"):
        super().__init__(name, 0x400, 32,"RW", UVM_NO_COVERAGE)


uvm_object_utils(mem_slave_DMA_RAM)


class reg_block_slave(UVMRegBlock):

    #   reg_slave_ID     ID
    #   reg_slave_INDEX  INDEX
    #   reg_slave_DATA   DATA

    #   rand reg_slave_SESSION  SESSION[256]

    #   rand reg_slave_TABLES   TABLES[256]

    #   mem_slave_DMA_RAM  DMA_RAM

    #   UVMRegField REVISION_ID
    #   UVMRegField CHIP_ID
    #   UVMRegField PRODUCT_ID

    def __init__(self, name="slave"):
        super().__init__(name, UVM_NO_COVERAGE)

        self.ID = None  # type: reg_slave_ID
        self.INDEX = None  # type: reg_slave_INDEX
        self.DATA = None  # type: reg_slave_DATA
        self.SESSION = []  # type: reg_slave_SESSION
        self.TABLES = []  # type: reg_slave_TABLES
        self.DMA_RAM = None  # type: mem_slave_DMA_RAM
        self.REVISION_ID = None  # type: UVMRegField
        self.CHIP_ID = None  # type: UVMRegField
        self.PRODUCT_ID = None  # type: UVMRegField
        self.nsession = 256


    def build(self):
        # create
        self.ID        = reg_slave_ID.type_id.create("ID")
        self.INDEX     = reg_slave_INDEX.type_id.create("INDEX")
        self.DATA      = reg_slave_DATA.type_id.create("DATA")
        for i in range(self.nsession):
            rslave_sess = reg_slave_SESSION.type_id.create(sv.sformatf("SESSION[%0d]",i))
            self.SESSION.append(rslave_sess)
            rslave_tables = reg_slave_TABLES.type_id.create(sv.sformatf("TABLES[%0d]",i))
            self.TABLES.append(rslave_tables)

        self.DMA_RAM   = mem_slave_DMA_RAM.type_id.create("DMA_RAM")
        #UVMResourceDb.set("REG::" + self.DMA_RAM.get_full_name() + ".*", "NO_REG_TESTS", 1, self)

        # configure
        self.ID.configure(self,None,"ID")
        self.ID.build()
        self.INDEX.configure(self,None,"INDEX")
        self.INDEX.build()
        for i in range(len(self.SESSION)):
            self.SESSION[i].configure(self,None,sv.sformatf("SESSION[%0d]",i))
            self.SESSION[i].build()

        for i in range(len(self.TABLES)):
            self.TABLES[i].configure(self, None, sv.sformatf("TABLES[%0d]",i))
            self.TABLES[i].build()

        self.DATA.configure(self.INDEX, self.TABLES, self, None)
        self.DATA.build()
        self.DMA_RAM.configure(self,"")

        # define default map
        self.default_map = self.create_map("default_map", 0x0, 4, UVM_LITTLE_ENDIAN)
        self.default_map.add_reg(self.ID, 0x0, "RW")
        self.default_map.add_reg(self.INDEX, 0x20, "RW")
        self.default_map.add_reg(self.DATA, 0x24, "RW")
        for i in range(len(self.SESSION)):
            self.SESSION[i].map(self.default_map, 0x1000 + 16 * i)

        self.default_map.add_mem(self.DMA_RAM, 0x2000, "RW")

        # field handle aliases
        self.REVISION_ID = self.ID.REVISION_ID
        self.CHIP_ID     = self.ID.CHIP_ID
        self.PRODUCT_ID  = self.ID.PRODUCT_ID


uvm_object_utils(reg_block_slave)
