#//
#//------------------------------------------------------------------------------
#//   Copyright 2011 Mentor Graphics Corporation
#//   Copyright 2011 Synopsys, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use self file except in
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
#
#`ifndef REG_SLAVE
#`define REG_SLAVE
#
#class reg_slave_ID(uvm_reg):
    #
    #   uvm_reg_field REVISION_ID
    #   uvm_reg_field CHIP_ID
    #   uvm_reg_field PRODUCT_ID
    #
    #   def __init__(self, name = "slave_ID")
    #      super().__init__(name,32,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build_phase(self, phase):
    #      self.REVISION_ID = uvm_reg_field.type_id.create("REVISION_ID")
    #          self.CHIP_ID = uvm_reg_field.type_id.create("CHIP_ID")
    #       self.PRODUCT_ID = uvm_reg_field.type_id.create("PRODUCT_ID")
    #
    #      self.REVISION_ID.configure(self, 8,  0, "RO",   0, 8'h03, 1, 0, 1)
    #          self.CHIP_ID.configure(self, 8,  8, "RO",   0, 8'h5A, 1, 0, 1)
    #       self.PRODUCT_ID.configure(self, 10, 16,"RO", 0, 10'h176, 1, 0, 1)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_slave_ID)
    #   
    #endclass
#
#
#class reg_slave_INDEX(uvm_reg):
    #
    #   uvm_reg_field value
    #   
    #   def __init__(self, name = "slave_INDEX")
    #      super().__init__(name,8,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build_phase(self, phase):
    #      self.value = uvm_reg_field.type_id.create("value")
    #      self.value.configure(self, 8, 0, "RW", 0, 32'h0, 1, 0, 1)
    #   endfunction
    #
    #   `uvm_object_utils(reg_slave_INDEX)
    #
    #endclass
#
#
#class reg_slave_DATA(uvm_reg_indirect_data):
    #
    #   def __init__(self, name = "slave_DATA")
    #      super().__init__(name,32,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   `uvm_object_utils(reg_slave_DATA)
    #
    #endclass
#
#
#class reg_slave_SOCKET(uvm_reg):
    #
    #   rand uvm_reg_field IP
    #   rand uvm_reg_field PORT
    #   
    #   def __init__(self, name = "slave_ADDR")
    #      super().__init__(name,64,UVM_NO_COVERAGE)
    #   endfunction: new
    #
    #   def build_phase(self, phase):
    #      self.IP   = uvm_reg_field.type_id.create("IP")
    #      self.PORT = uvm_reg_field.type_id.create("PORT")
    #      
    #        self.IP.configure(self, 48,  0, "RW", 0, 48'h0, 1, 0, 1)
    #      self.PORT.configure(self, 16, 48, "RW", 0, 16'h0, 1, 0, 1)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_slave_SOCKET)
    #   
    #endclass
#
#
#class reg_slave_SESSION(uvm_reg_file):
    #
    #   rand reg_slave_SOCKET SRC
    #   rand reg_slave_SOCKET DST
    #   
    #   def __init__(self, name = "slave_SESSION")
    #      super().__init__(name)
    #   endfunction: new
    #
    #   def build_phase(self, phase):
    #      self.SRC = reg_slave_SOCKET.type_id.create("SRC")
    #      self.DST = reg_slave_SOCKET.type_id.create("DST")
    #
    #      self.SRC.configure(get_block(), self, "SRC")
    #      self.DST.configure(get_block(), self, "DST")
    #
    #      self.SRC.build()
    #      self.DST.build()
    #   endfunction
    #
    #   virtual function void map(uvm_reg_map    mp,
    #                             uvm_reg_addr_t offset)
    #      mp.add_reg(SRC, offset+ 0x00)
    #      mp.add_reg(DST, offset+ 0x08)
    #   endfunction
    #   
    #   virtual function void set_offset(uvm_reg_map    mp,
    #                               uvm_reg_addr_t offset)
    #      SRC.set_offset(mp, offset+ 0x00)
    #      DST.set_offset(mp, offset+ 0x08)
    #   endfunction
    #   
    #   `uvm_object_utils(reg_slave_SESSION)
    #   
    #endclass
#
#
#class reg_slave_TABLES(uvm_reg):
    #
    #   rand uvm_reg_field value
    #   
    #   def __init__(self, name = "slave_TABLES")
    #      super().__init__(name,32,UVM_NO_COVERAGE)
    #   endfunction
    #
    #   def build_phase(self, phase):
    #      self.value = uvm_reg_field.type_id.create("value")
    #      self.value.configure(self, 32, 0, "RW", 0, 32'h0, 1, 0, 1)
    #   endfunction
    #
    #   `uvm_object_utils(reg_slave_TABLES)
    #   
    #endclass
#
#
#class mem_slave_DMA_RAM(uvm_mem):
    #
    #   def __init__(self, name = "slave_DMA_RAM")
    #      super().__init__(name, 0x400,32,"RW",UVM_NO_COVERAGE)
    #   endfunction
    #   
    #   `uvm_object_utils(mem_slave_DMA_RAM)
    #   
    #endclass
#
#
#class reg_block_slave(uvm_reg_block):
    #
    #   reg_slave_ID     ID
    #   reg_slave_INDEX  INDEX
    #   reg_slave_DATA   DATA
    #
    #   rand reg_slave_SESSION  SESSION[256]
    #   
    #   rand reg_slave_TABLES   TABLES[256]
    #   
    #   mem_slave_DMA_RAM  DMA_RAM
    #
    #   uvm_reg_field REVISION_ID
    #   uvm_reg_field CHIP_ID
    #   uvm_reg_field PRODUCT_ID
    #
    #   def __init__(self, name = "slave")
    #      super().__init__(name,UVM_NO_COVERAGE)
    #    self.REVISION_ID = None  # type: uvm_reg_field
    #    self.CHIP_ID = None  # type: uvm_reg_field
    #    self.PRODUCT_ID = None  # type: uvm_reg_field
    #    self.value = None  # type: uvm_reg_field
    #    self.IP = None  # type: uvm_reg_field
    #    self.PORT = None  # type: uvm_reg_field
    #    self.SRC = None  # type: reg_slave_SOCKET
    #    self.DST = None  # type: reg_slave_SOCKET
    #    self.value = None  # type: uvm_reg_field
    #    self.ID = None  # type: reg_slave_ID
    #    self.INDEX = None  # type: reg_slave_INDEX
    #    self.DATA = None  # type: reg_slave_DATA
    #    self.SESSION = None  # type: reg_slave_SESSION
    #    self.TABLES = None  # type: reg_slave_TABLES
    #    self.DMA_RAM = None  # type: mem_slave_DMA_RAM
    #    self.REVISION_ID = None  # type: uvm_reg_field
    #    self.CHIP_ID = None  # type: uvm_reg_field
    #    self.PRODUCT_ID = None  # type: uvm_reg_field
    #   endfunction
    #
    #   def build_phase(self, phase):
    #
    #      // create
    #      ID        = reg_slave_ID.type_id.create("ID")
    #      INDEX     = reg_slave_INDEX.type_id.create("INDEX")
    #      DATA      = reg_slave_DATA.type_id.create("DATA")
    #      foreach (SESSION[i])
    #         SESSION[i] = reg_slave_SESSION.type_id.create(sv.sformatf("SESSION[%0d]",i))
    #      foreach (TABLES[i])
    #         TABLES[i] = reg_slave_TABLES.type_id.create(sv.sformatf("TABLES[%0d]",i))
    #      DMA_RAM   = mem_slave_DMA_RAM.type_id.create("DMA_RAM")
    #
    #      // configure
    #      ID.configure(self,None,"ID")
    #      ID.build()
    #      INDEX.configure(self,None,"INDEX")
    #      INDEX.build()
    #      foreach (SESSION[i]):
    #         SESSION[i].configure(self,None,sv.sformatf("SESSION[%0d]",i))
    #         SESSION[i].build()
    #      end
    #      foreach (TABLES[i]):
    #         TABLES[i].configure(self,None,sv.sformatf("TABLES[%0d]",i))
    #         TABLES[i].build()
    #      end
    #      // the SV LRM IEEE2009 is not clear if an array of class handles can be assigned to another array if the element types 
    #      // are assignment compatible OR if the LRM states the element types have to be 'equal' (the LRM states equal types)
    #      // IUS requires per LRM 'equivalent' element types and does not accept assignment compatible types
    #`ifdef INCA
    #      begin
    #      	uvm_reg r[256]
    #	foreach(TABLES[i])
    #		r[i]=TABLES[i]
    #
    #	DATA.configure(INDEX, r, self, None)
    #      end
    #`else
    #      DATA.configure(INDEX, TABLES, self, None)
    #`endif
    #     
    #      DATA.build()
    #      
    #      DMA_RAM.configure(self,"")
    #
    #      // define default map
    #      default_map = create_map("default_map",  0x0, 4, UVM_LITTLE_ENDIAN)
    #      default_map.add_reg(ID,     0x0,  "RW")
    #      default_map.add_reg(INDEX,  0x20, "RW")
    #      default_map.add_reg(DATA,   0x24, "RW")
    #      foreach (SESSION[i])
    #         SESSION[i].map(default_map,  0x1000 + 16 * i)
    #
    #      default_map.add_mem(DMA_RAM,  0x2000, "RW")
    #      
    #      // field handle aliases
    #      REVISION_ID = ID.REVISION_ID
    #      CHIP_ID     = ID.CHIP_ID
    #      PRODUCT_ID  = ID.PRODUCT_ID
    #   endfunction
    #   
    #   `uvm_object_utils(reg_block_slave)
    #   
    #endclass : reg_block_slave
#
#
from uvm.reg.uvm_reg import *
from uvm.macros import *
from uvm.base.uvm_reg_indirect_data import *
from uvm.reg.uvm_reg_file import *
from uvm.reg.uvm_mem import *
from uvm.reg.uvm_reg_block import *
#`endif
