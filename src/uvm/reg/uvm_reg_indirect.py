#// -------------------------------------------------------------
#//    Copyright 2010 Synopsys, Inc.
#//    Copyright 2010 Cadence Design Systems, Inc.
#//    Copyright 2011 Mentor Graphics Corporation
#//    Copyright 2019 Tuomas Poikela (tpoikela)
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

import cocotb

from .uvm_reg import UVMReg
from .uvm_reg_model import (UVM_WRITE, UVM_NOT_OK)
from .uvm_reg_item import UVMRegItem
from .uvm_reg_sequence import UVMRegFrontdoor
from ..base.uvm_resource_db import UVMResourceDb
from ..base.sv import sv
from ..macros import uvm_fatal, uvm_error

#typedef class uvm_reg_indirect_ftdr_seq

#//-----------------------------------------------------------------
#// CLASS: uvm_reg_indirect_data
#// Indirect data access abstraction class
#//
#// Models the behavior of a register used to indirectly access
#// a register array, indexed by a second ~address~ register.
#//
#// This class should not be instantiated directly.
#// A type-specific class extension should be used to
#// provide a factory-enabled constructor and specify the
#// ~n_bits~ and coverage models.
#//-----------------------------------------------------------------


class UVMRegIndirectData(UVMReg):


    #   // Function: new
    #   // Create an instance of this class
    #   //
    #   // Should not be called directly,
    #   // other than via super.new().
    #   // The value of ~n_bits~ must match the number of bits
    #   // in the indirect register array.
    #   function new(string name = "uvm_reg_indirect",
    #                int unsigned n_bits,
    #                int has_cover)
    def __init__(self, name="uvm_reg_indirect", n_bits=0, has_cover=False):
        UVMReg.__init__(self, name,n_bits,has_cover)
        self.m_idx = None
        self.m_tbl = []
        #endfunction: new

    def build(self):
        pass


    #   // Function: configure
    #   // Configure the indirect data register.
    #   //
    #   // The ~idx~ register specifies the index,
    #   // in the ~reg_a~ register array, of the register to access.
    #   // The ~idx~ must be written to first.
    #   // A read or write operation to this register will subsequently
    #   // read or write the indexed register in the register array.
    #   //
    #   // The number of bits in each register in the register array must be
    #   // equal to ~n_bits~ of this register.
    #   //
    #   // See <uvm_reg::configure()> for the remaining arguments.
    #   function void configure (uvm_reg idx,
    #                            uvm_reg reg_a[],
    #                            uvm_reg_block blk_parent,
    #                            uvm_reg_file regfile_parent = null)
    def configure(self, idx, reg_a, blk_parent, regfile_parent=None):
        super().configure(blk_parent, regfile_parent, "")
        self.m_idx = idx
        self.m_tbl = reg_a

        # Not testable using pre-defined sequences
        UVMResourceDb.set("REG::" + self.get_full_name(), "NO_REG_TESTS", 1)

        # Add a frontdoor to each indirectly-accessed register
        # for every address map this register is in.
        # foreach (m_maps[map]):
        for _map in self.m_maps:
            self.add_frontdoors(_map)


    #   /*local*/ virtual function void add_map(uvm_reg_map map)
    def add_map(self, _map):
        super().add_map(_map)
        self.add_frontdoors(_map)
    #   endfunction


    #   local function void add_frontdoors(uvm_reg_map map)
    def add_frontdoors(self, _map):
        for i in range(len(self.m_tbl)):
            fd = None  # uvm_reg_indirect_ftdr_seq
            if self.m_tbl[i] is None:
                uvm_error(self.get_full_name(),
                         sv.sformatf("Indirect register #%0d is NULL", i))
                continue
            fd = uvm_reg_indirect_ftdr_seq(self.m_idx, i, self)
            if self.m_tbl[i].is_in_map(_map):
                self.m_tbl[i].set_frontdoor(fd, _map)
            else:
                _map.add_reg(self.m_tbl[i], -1, "RW", 1, fd)


    #   virtual function void do_predict (uvm_reg_item      rw,
    #                                     uvm_predict_e     kind = UVM_PREDICT_DIRECT,
    #                                     uvm_reg_byte_en_t be = -1)
    #      if (m_idx.get() >= m_tbl.size()):
    #         `uvm_error(get_full_name(), sv.sformatf("Address register %s has a value (%0d) greater than the maximum indirect register array size (%0d)", m_idx.get_full_name(), m_idx.get(), m_tbl.size()))
    #         rw.status = UVM_NOT_OK
    #         return
    #      end
    #
    #      //NOTE limit to 2**32 registers
    #      begin
    #         int unsigned idx = m_idx.get()
    #         m_tbl[idx].do_predict(rw, kind, be)
    #      end
    #   endfunction

    #
    #
    #   virtual function uvm_reg_map get_local_map(uvm_reg_map map, string caller="")
    def get_local_map(self, _map, caller=""):
        return self.m_idx.get_local_map(_map,caller)

    #
    #   //
    #   // Just for good measure, to catch and short-circuit non-sensical uses
    #   //
    #   virtual function void add_field  (uvm_reg_field field)
    def add_field(self, field):
        uvm_error(self.get_full_name(), "Cannot add field to an indirect data access register")


    #   virtual function void set (uvm_reg_data_t  value,
    #                              string          fname = "",
    #                              int             lineno = 0)
    #      `uvm_error(get_full_name(), "Cannot set() an indirect data access register")
    #   endfunction

    #
    #   virtual function uvm_reg_data_t  get(string  fname = "",
    #                                        int     lineno = 0)
    #      `uvm_error(get_full_name(), "Cannot get() an indirect data access register")
    #      return 0
    #   endfunction

    #
    #   virtual function uvm_reg get_indirect_reg(string  fname = "",
    #                                        int     lineno = 0)
    #      int unsigned idx = m_idx.get_mirrored_value()
    #      return(m_tbl[idx])
    #   endfunction

    #
    #   virtual function bit needs_update()
    #      return 0
    #   endfunction


    #   virtual task write(output uvm_status_e      status,
    #                      input  uvm_reg_data_t    value,
    #                      input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                      input  uvm_reg_map       map = null,
    #                      input  uvm_sequence_base parent = null,
    #                      input  int               prior = -1,
    #                      input  uvm_object        extension = null,
    #                      input  string            fname = "",
    #                      input  int               lineno = 0)
    #
    #      if (path == UVM_DEFAULT_PATH):
    #         uvm_reg_block blk = get_parent()
    #         path = blk.get_default_path()
    #      end
    #
    #      if (path == UVM_BACKDOOR):
    #         `uvm_warning(get_full_name(), "Cannot backdoor-write an indirect data access register. Switching to frontdoor.")
    #         path = UVM_FRONTDOOR
    #      end
    #
    #      // Can't simply call super.write() because it'll call set()
    #      begin
    #         uvm_reg_item rw
    #
    #         XatomicX(1)
    #
    #         rw = uvm_reg_item::type_id::create("write_item",,get_full_name())
    #         rw.element      = this
    #         rw.element_kind = UVM_REG
    #         rw.kind         = UVM_WRITE
    #         rw.value[0]     = value
    #         rw.path         = path
    #         rw.map          = map
    #         rw.parent       = parent
    #         rw.prior        = prior
    #         rw.extension    = extension
    #         rw.fname        = fname
    #         rw.lineno       = lineno
    #
    #         do_write(rw)
    #
    #         status = rw.status
    #
    #         XatomicX(0)
    #      end
    #   endtask


    #   virtual task read(output uvm_status_e      status,
    #                     output uvm_reg_data_t    value,
    #                     input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                     input  uvm_reg_map       map = null,
    #                     input  uvm_sequence_base parent = null,
    #                     input  int               prior = -1,
    #                     input  uvm_object        extension = null,
    #                     input  string            fname = "",
    #                     input  int               lineno = 0)
    #
    #      if (path == UVM_DEFAULT_PATH):
    #         uvm_reg_block blk = get_parent()
    #         path = blk.get_default_path()
    #      end
    #
    #      if (path == UVM_BACKDOOR):
    #         `uvm_warning(get_full_name(), "Cannot backdoor-read an indirect data access register. Switching to frontdoor.")
    #         path = UVM_FRONTDOOR
    #      end
    #
    #      super.read(status, value, path, map, parent, prior, extension, fname, lineno)
    #   endtask

    #
    #   virtual task poke(output uvm_status_e      status,
    #                     input  uvm_reg_data_t    value,
    #                     input  string            kind = "",
    #                     input  uvm_sequence_base parent = null,
    #                     input  uvm_object        extension = null,
    #                     input  string            fname = "",
    #                     input  int               lineno = 0)
    #      `uvm_error(get_full_name(), "Cannot poke() an indirect data access register")
    #      status = UVM_NOT_OK
    #   endtask

    #
    #   virtual task peek(output uvm_status_e      status,
    #                     output uvm_reg_data_t    value,
    #                     input  string            kind = "",
    #                     input  uvm_sequence_base parent = null,
    #                     input  uvm_object        extension = null,
    #                     input  string            fname = "",
    #                     input  int               lineno = 0)
    #      `uvm_error(get_full_name(), "Cannot peek() an indirect data access register")
    #      status = UVM_NOT_OK
    #   endtask

    #
    #   virtual task update(output uvm_status_e      status,
    #                       input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                       input  uvm_reg_map       map = null,
    #                       input  uvm_sequence_base parent = null,
    #                       input  int               prior = -1,
    #                       input  uvm_object        extension = null,
    #                       input  string            fname = "",
    #                       input  int               lineno = 0)
    #      status = UVM_IS_OK
    #   endtask

    #
    #   virtual task mirror(output uvm_status_e      status,
    #                       input uvm_check_e        check  = UVM_NO_CHECK,
    #                       input uvm_path_e         path = UVM_DEFAULT_PATH,
    #                       input uvm_reg_map        map = null,
    #                       input uvm_sequence_base  parent = null,
    #                       input int                prior = -1,
    #                       input  uvm_object        extension = null,
    #                       input string             fname = "",
    #                       input int                lineno = 0)
    #      status = UVM_IS_OK

    #   endtask
    #
    #endclass : uvm_reg_indirect_data


class uvm_reg_indirect_ftdr_seq(UVMRegFrontdoor):
    #   local uvm_reg m_addr_reg
    #   local uvm_reg m_data_reg
    #   local int     m_idx
    #
    def __init__(self, addr_reg, idx, data_reg):
        super().__init__("uvm_reg_indirect_ftdr_seq")
        self.m_addr_reg = addr_reg
        self.m_idx      = idx
        self.m_data_reg = data_reg
        #   endfunction: new

    @cocotb.coroutine
    def body(self):

        rw = None  # uvm_reg_item

        arr = []
        if sv.cast(arr, self.rw_info.clone(), UVMRegItem):
            rw = arr[0]
        else:
            uvm_fatal("CAST_FAIL", "Expected UVMRegItem, got " + str(self.rw_info))

        rw.element = self.m_addr_reg
        rw.kind    = UVM_WRITE
        rw.value[0] = self.m_idx

        yield self.m_addr_reg.XatomicX(1, rw)
        yield self.m_data_reg.XatomicX(1, rw)

        yield self.m_addr_reg.do_write(rw)

        if rw.status == UVM_NOT_OK:
            return

        arr = []
        if sv.cast(arr, self.rw_info.clone(), UVMRegItem):
            rw = arr[0]
        rw.element = self.m_data_reg

        if self.rw_info.kind == UVM_WRITE:
            yield self.m_data_reg.do_write(rw)
        else:
            yield self.m_data_reg.do_read(rw)
            self.rw_info.value[0] = rw.value[0]

        yield self.m_addr_reg.XatomicX(0)
        yield self.m_data_reg.XatomicX(0)

        self.rw_info.status = rw.status
        #   endtask
        #
