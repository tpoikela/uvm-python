#//
#// -------------------------------------------------------------
#//    Copyright 2004-2009 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
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

from ..base.uvm_object import UVMObject
from ..base.uvm_pool import UVMPool, UVMObjectStringPool
from ..base.uvm_queue import UVMQueue
from ..base.uvm_globals import (uvm_check_output_args, uvm_zero_delay, uvm_report_enabled,
    uvm_report_info)
from ..base.uvm_object_globals import UVM_DEBUG, UVM_HIGH, UVM_INFO
from ..base.sv import sv
from ..macros.uvm_message_defines import uvm_error, uvm_info, uvm_warning, uvm_fatal
from .uvm_reg_model import (UVM_BACKDOOR, UVM_BURST_READ, UVM_BURST_WRITE, UVM_DEFAULT_PATH,
                            UVM_FRONTDOOR, UVM_IS_OK, UVM_MEM, UVM_NOT_OK, UVM_NO_COVERAGE,
                            UVM_READ, UVM_WRITE, uvm_hdl_concat2string, uvm_hdl_path_concat,
                            uvm_reg_cvr_rsrc_db)
from .uvm_reg_item import UVMRegItem
from .uvm_reg_map import UVMRegMap
from .uvm_mem_mam import UVMMemMam, UVMMemMamCfg
from .uvm_reg_cbs import UVMMemCbIter

from ..dpi.uvm_hdl import uvm_hdl

ERR_MEM_BD_READ = ("Backdoor read of register %s with multiple HDL copies: "
    + "values are not the same: %0h at path '%s', and %0h at path '%s'. Returning first value.")


#   typedef enum {UNKNOWNS, ZEROES, ONES, ADDRESS, VALUE, INCR, DECR} init_e
UNKNOWNS = 0
ZEROES = 1
ONES = 2
ADDRESS = 3
VALUE = 4
INCR = 5
DECR = 6


class UVMMem(UVMObject):
    """
    Memory abstraction base class

    A memory is a collection of contiguous locations.
    A memory may be accessible via more than one address map.
    
    Unlike registers, memories are not mirrored because of the potentially
    large data space: tests that walk the entire memory space would negate
    any benefit from sparse memory modelling techniques.
    Rather than relying on a mirror, it is recommended that
    backdoor access be used instead.
    """



    #   local uvm_object_string_pool
    #               #(uvm_queue #(uvm_hdl_path_concat)) m_hdl_paths_pool
    #

    m_max_size = 0

    #   //----------------------
    #   // Group: Initialization
    #   //----------------------

    #   // Function: new
    #   //
    #   // Create a new instance and type-specific configuration
    #   //
    #   // Creates an instance of a memory abstraction class with the specified
    #   // name.
    #   //
    #   // ~size~ specifies the total number of memory locations.
    #   // ~n_bits~ specifies the total number of bits in each memory location.
    #   // ~access~ specifies the access policy of this memory and may be
    #   // one of "RW for RAMs and "RO" for ROMs.
    #   //
    #   // ~has_coverage~ specifies which functional coverage models are present in
    #   // the extension of the register abstraction class.
    #   // Multiple functional coverage models may be specified by adding their
    #   // symbolic names, as defined by the <uvm_coverage_model_e> type.
    #   //
    #   extern function new (string           name,
    #                        longint unsigned size,
    #                        int unsigned     n_bits,
    #                        string           access = "RW",
    #                        int              has_coverage = UVM_NO_COVERAGE)
    def __init__(self, name, size, n_bits, access="RW",
            has_coverage=UVM_NO_COVERAGE):
        UVMObject.__init__(self, name)
        self.m_locked = 0
        if n_bits == 0:
            uvm_error("RegModel", "Memory '" + self.get_full_name() + "' cannot have 0 bits")
            n_bits = 1

        self.m_fname = ""
        self.m_parent = None
        self.m_size      = size
        self.m_n_bits    = n_bits
        self.m_backdoor  = None
        self.m_access    = access.upper()
        self.m_has_cover = has_coverage
        self.m_hdl_paths_pool = UVMObjectStringPool("hdl_paths", UVMQueue)
        self.m_read_in_progress = False
        self.m_write_in_progress = False
        self.m_is_powered_down = False
        self.m_cover_on = 0

        self.m_vregs = UVMPool()  # [uvm_vreg]
        self.m_maps = UVMPool()  # bit[uvm_reg_map]
        if (n_bits > UVMMem.m_max_size):
            UVMMem.m_max_size = n_bits

        #   // variable: mam
        #   //
        #   // Memory allocation manager
        #   //
        #   // Memory allocation manager for the memory corresponding to this
        #   // abstraction class instance.
        #   // Can be used to allocate regions of consecutive addresses of
        #   // specific sizes, such as DMA buffers,
        #   // or to locate virtual register array.
        #   //
        self.mam = None  # uvm_mem_mam


    #   // Function: configure
    #   //
    #   // Instance-specific configuration
    #   //
    #   // Specify the parent block of this memory.
    #   //
    #   // If this memory is implemented in a single HDL variable,
    #   // its name is specified as the ~hdl_path~.
    #   // Otherwise, if the memory is implemented as a concatenation
    #   // of variables (usually one per bank), then the HDL path
    #   // must be specified using the <add_hdl_path()> or
    #   // <add_hdl_path_slice()> method.
    #   //
    #   extern function void configure (uvm_reg_block parent,
    #                                   string        hdl_path = "")
    def configure(self, parent, hdl_path=""):

        if parent is None:
            uvm_fatal("REG/None_PARENT","configure: parent argument is None")
        self.m_parent = parent

        if (self.m_access != "RW" and self.m_access != "RO"):
            uvm_error("RegModel", "Memory '" + self.get_full_name() + "' can only be RW or RO")
            self.m_access = "RW"

        cfg = UVMMemMamCfg()  # uvm_mem_mam_cfg
        cfg.n_bytes      = int((self.m_n_bits-1) / 8) + 1
        cfg.start_offset = 0
        cfg.end_offset   = self.m_size-1
        cfg.mode     = UVMMemMam.GREEDY
        cfg.locality = UVMMemMam.BROAD

        self.mam = UVMMemMam(self.get_full_name(), cfg, self)
        self.m_parent.add_mem(self)

        if hdl_path != "":
            self.add_hdl_path_slice(hdl_path, -1, -1)
        #endfunction: configure


    #
    #
    #   // Function: set_offset
    #   //
    #   // Modify the offset of the memory
    #   //
    #   // The offset of a memory within an address map is set using the
    #   // <uvm_reg_map::add_mem()> method.
    #   // This method is used to modify that offset dynamically.
    #   //
    #   // Note: Modifying the offset of a memory will make the abstract model
    #   // diverge from the specification that was used to create it.
    #   //
    #   extern virtual function void set_offset (uvm_reg_map    map,
    #                                            uvm_reg_addr_t offset,
    #                                            bit            unmapped = 0)
    #

    #
    #   /*local*/ extern virtual function void set_parent(uvm_reg_block parent)

    #   /*local*/ extern function void add_map(uvm_reg_map map)
    def add_map(self, _map):
        self.m_maps[_map] = 1

    #   /*local*/ extern function void Xlock_modelX()
    def Xlock_modelX(self):
        self.m_locked = 1

    #   /*local*/ extern function void Xadd_vregX(uvm_vreg vreg)
    def Xadd_vregX(self, vreg):
        self.m_vregs[vreg] = 1


    #   /*local*/ extern function void Xdelete_vregX(uvm_vreg vreg)


    #   //---------------------
    #   // Group: Introspection
    #   //---------------------
    #
    #   // Function: get_name
    #   //
    #   // Get the simple name
    #   //
    #   // Return the simple object name of this memory.
    #   //


    #   // Function: get_full_name
    #   //
    #   // Get the hierarchical name
    #   //
    #   // Return the hierarchal name of this memory.
    #   // The base of the hierarchical name is the root block.
    #   //
    #   extern virtual function string get_full_name()
    def get_full_name(self):
        if self.m_parent is None:
            return self.get_name()

        return self.m_parent.get_full_name() + "." + self.get_name()


    #   // Function: get_parent
    #   //
    #   // Get the parent block
    #   //
    #   extern virtual function uvm_reg_block get_parent ()
    def get_parent(self):
        return self.get_block()

    #   extern virtual function uvm_reg_block get_block  ()
    def get_block(self):
        return self.m_parent

    #
    #   // Function: get_n_maps
    #   //
    #   // Returns the number of address maps this memory is mapped in
    #   //
    #   extern virtual function int get_n_maps ()
    def get_n_maps(self):
        return self.m_maps.num()



    #   // Function: is_in_map
    #   //
    #   // Return TRUE if this memory is in the specified address ~map~
    #   //
    #   extern function bit is_in_map (uvm_reg_map map)
    #
    #
    #   // Function: get_maps
    #   //
    #   // Returns all of the address ~maps~ where this memory is mapped
    #   //
    #   extern virtual function void get_maps (ref uvm_reg_map maps[$])
    def get_maps(self, maps):
        for map_ in self.m_maps.key_list():
            maps.append(map_)


    #   /*local*/ extern function uvm_reg_map get_local_map   (uvm_reg_map map,
    #                                                          string caller = "")
    def get_local_map(self, _map, caller=""):
        if (_map is None):
            return self.get_default_map()
        if _map in self.m_maps:
            return _map

        for l in self.m_maps:
            local_map = l  # uvm_reg_map
            parent_map = local_map.get_parent_map()

            while parent_map is not None:
                if (parent_map == _map):
                    return local_map
                parent_map = parent_map.get_parent_map()

        cname = ""
        if caller != "":
            cname = " (called from " + caller + ")"
        uvm_warning("RegModel",
            "Memory '" + self.get_full_name() + "' is not contained within map '"
            + _map.get_full_name() + "'" + cname)
        return None
        #endfunction


    #   /*local*/ extern function uvm_reg_map get_default_map (string caller = "")
    def get_default_map(self, caller=""):

        # if mem is not associated with any may, return ~None~
        if self.m_maps.num() == 0:
            cname = ""
            if caller != "":
                cname = " (called from " + caller + ")"
            uvm_warning("RegModel",
                    "Memory '" + self.get_full_name() + "' is not registered with any map"
                    + cname)
            return None


        # if only one map, choose that
        default_map = None
        if self.m_maps.num() == 1:
            get_default_map = self.m_maps.first()

        # try to choose one based on default_map in parent blocks.
        for l in self.m_maps:
            _map = l  # uvm_reg_map
            blk = _map.get_parent()  # uvm_reg_block
            default_map = blk.get_default_map()  # uvm_reg_map
            if default_map is not None:
                local_map = self.get_local_map(default_map)
                if local_map is not None:
                    return local_map

        # if that fails, choose the first in self mem's maps
        get_default_map = self.m_maps.first()
        return get_default_map


    #   // Function: get_rights
    #   //
    #   // Returns the access rights of this memory.
    #   //
    #   // Returns "RW", "RO" or "WO".
    #   // The access rights of a memory is always "RW",
    #   // unless it is a shared memory
    #   // with access restriction in a particular address map.
    #   //
    #   // If no address map is specified and the memory is mapped in only one
    #   // address map, that address map is used. If the memory is mapped
    #   // in more than one address map, the default address map of the
    #   // parent block is used.
    #   //
    #   // If an address map is specified and
    #   // the memory is not mapped in the specified
    #   // address map, an error message is issued
    #   // and "RW" is returned.
    #   //
    #   extern virtual function string get_rights (uvm_reg_map map = None)
    def get_rights(self, _map=None):
        #
        info = None  # uvm_reg_map_info

        # No right restrictions if not shared
        if (self.m_maps.num() <= 1):
            return "RW"

        _map = self.get_local_map(_map,"get_rights()")
        if _map is None:
            return "RW"

        info = _map.get_mem_map_info(self)
        return info.rights
        #endfunction: get_rights



    #   // Function: get_access
    #   //
    #   // Returns the access policy of the memory when written and read
    #   // via an address map.
    #   //
    #   // If the memory is mapped in more than one address map,
    #   // an address ~map~ must be specified.
    #   // If access restrictions are present when accessing a memory
    #   // through the specified address map, the access mode returned
    #   // takes the access restrictions into account.
    #   // For example, a read-write memory accessed
    #   // through a domain with read-only restrictions would return "RO".
    #   //
    #   extern virtual function string get_access(uvm_reg_map map = None)
    def get_access(self, _map=None):
        get_access = self.m_access
        if (self.get_n_maps() == 1):
            return get_access
        _map = self.get_local_map(_map, "get_access()")
        if _map is None:
            return get_access

        # // Is the memory restricted in this map?
        rights = self.get_rights(_map)
        if rights == "RW":
            # // No restrictions
            return get_access
        elif rights == "RO":
            if get_access in ["RW", "RO"]:
                get_access = "RO"
            elif get_access == "WO":
                uvm_error("RegModel", "WO memory '" + self.get_full_name()
                    + "' restricted to RO in map '" + _map.get_full_name() + "'")
            else:
                uvm_error("RegModel", "Memory '" + self.get_full_name()
                    + "' has invalid access mode, '" + get_access + "'")

        elif rights == "WO":
            if get_access in ["RW", "WO"]:
                get_access = "WO"
            elif get_access == "RO":
                uvm_error("RegModel", "RO memory '" + self.get_full_name()
                    + "' restricted to WO in map '" + _map.get_full_name() + "'")
            else:
                uvm_error("RegModel", "Memory '" + self.get_full_name()
                    + "' has invalid access mode, '" + get_access + "'")
        else:
            uvm_error("RegModel", "Shared memory '" + self.get_full_name()
                + "' is not shared in map '" + _map.get_full_name() + "'")

    #   // Function: get_size
    #   //
    #   // Returns the number of unique memory locations in this memory.
    #   //
    #   extern function longint unsigned get_size()
    def get_size(self):
        return self.m_size

    #   // Function: get_n_bytes
    #   //
    #   // Return the width, in number of bytes, of each memory location
    #   //
    #   extern function int unsigned get_n_bytes()
    def get_n_bytes(self):
        return int((self.m_n_bits - 1) / 8) + 1


    #   // Function: get_n_bits
    #   //
    #   // Returns the width, in number of bits, of each memory location
    #   //
    #   extern function int unsigned get_n_bits()
    def get_n_bits(self):
        return self.m_n_bits

    #   // Function: get_max_size
    #   //
    #   // Returns the maximum width, in number of bits, of all memories
    #   //
    @classmethod
    def get_max_size(cls):
        return UVMMem.m_max_size


    #   // Function: get_virtual_registers
    #   //
    #   // Return the virtual registers in this memory
    #   //
    #   // Fills the specified array with the abstraction class
    #   // for all of the virtual registers implemented in this memory.
    #   // The order in which the virtual registers are located in the array
    #   // is not specified.
    #   //
    #   extern virtual function void get_virtual_registers(ref uvm_vreg regs[$])
    #
    #
    #   // Function: get_virtual_fields
    #   //
    #   // Return  the virtual fields in the memory
    #   //
    #   // Fills the specified dynamic array with the abstraction class
    #   // for all of the virtual fields implemented in this memory.
    #   // The order in which the virtual fields are located in the array is
    #   // not specified.
    #   //
    #   extern virtual function void get_virtual_fields(ref uvm_vreg_field fields[$])
    #
    #
    #   // Function: get_vreg_by_name
    #   //
    #   // Find the named virtual register
    #   //
    #   // Finds a virtual register with the specified name
    #   // implemented in this memory and returns
    #   // its abstraction class instance.
    #   // If no virtual register with the specified name is found, returns ~None~.
    #   //
    #   extern virtual function uvm_vreg get_vreg_by_name(string name)
    #
    #
    #   // Function: get_vfield_by_name
    #   //
    #   // Find the named virtual field
    #   //
    #   // Finds a virtual field with the specified name
    #   // implemented in this memory and returns
    #   // its abstraction class instance.
    #   // If no virtual field with the specified name is found, returns ~None~.
    #   //
    #   extern virtual function uvm_vreg_field  get_vfield_by_name(string name)
    #
    #
    #   // Function: get_vreg_by_offset
    #   //
    #   // Find the virtual register implemented at the specified offset
    #   //
    #   // Finds the virtual register implemented in this memory
    #   // at the specified ~offset~ in the specified address ~map~
    #   // and returns its abstraction class instance.
    #   // If no virtual register at the offset is found, returns ~None~.
    #   //
    #   extern virtual function uvm_vreg get_vreg_by_offset(uvm_reg_addr_t offset,
    #                                                       uvm_reg_map    map = None)
    #
    #
    #   // Function: get_offset
    #   //
    #   // Returns the base offset of a memory location
    #   //
    #   // Returns the base offset of the specified location in this memory
    #   // in an address ~map~.
    #   //
    #   // If no address map is specified and the memory is mapped in only one
    #   // address map, that address map is used. If the memory is mapped
    #   // in more than one address map, the default address map of the
    #   // parent block is used.
    #   //
    #   // If an address map is specified and
    #   // the memory is not mapped in the specified
    #   // address map, an error message is issued.
    #   //
    #   extern virtual function uvm_reg_addr_t  get_offset (uvm_reg_addr_t offset = 0,
    #                                                       uvm_reg_map    map = None)
    #
    #
    #   // Function: get_address
    #   //
    #   // Returns the base external physical address of a memory location
    #   //
    #   // Returns the base external physical address of the specified location
    #   // in this memory if accessed through the specified address ~map~.
    #   //
    #   // If no address map is specified and the memory is mapped in only one
    #   // address map, that address map is used. If the memory is mapped
    #   // in more than one address map, the default address map of the
    #   // parent block is used.
    #   //
    #   // If an address map is specified and
    #   // the memory is not mapped in the specified
    #   // address map, an error message is issued.
    #   //
    #   extern virtual function uvm_reg_addr_t  get_address(uvm_reg_addr_t  offset = 0,
    #                                                       uvm_reg_map   map = None)
    #
    #
    #   // Function: get_addresses
    #   //
    #   // Identifies the external physical address(es) of a memory location
    #   //
    #   // Computes all of the external physical addresses that must be accessed
    #   // to completely read or write the specified location in this memory.
    #   // The addressed are specified in little endian order.
    #   // Returns the number of bytes transferred on each access.
    #   //
    #   // If no address map is specified and the memory is mapped in only one
    #   // address map, that address map is used. If the memory is mapped
    #   // in more than one address map, the default address map of the
    #   // parent block is used.
    #   //
    #   // If an address map is specified and
    #   // the memory is not mapped in the specified
    #   // address map, an error message is issued.
    #   //
    #   extern virtual function int get_addresses(uvm_reg_addr_t     offset = 0,
    #                                             uvm_reg_map        map=None,
    #                                             ref uvm_reg_addr_t addr[])
    #

    #   //------------------
    #   // Group: HDL Access
    #   //------------------


    #   // Task: write
    #   //
    #   // Write the specified value in a memory location
    #   //
    #   // Write ~value~ in the memory location that corresponds to this
    #   // abstraction class instance at the specified ~offset~
    #   // using the specified access ~path~.
    #   // If the memory is mapped in more than one address map,
    #   // an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   // If a back-door access path is used, the effect of writing
    #   // the register through a physical access is mimicked. For
    #   // example, a read-only memory will not be written.
    #   //
    #   extern virtual task write(output uvm_status_e       status,
    #                             input  uvm_reg_addr_t     offset,
    #                             input  uvm_reg_data_t     value,
    #                             input  uvm_path_e         path   = UVM_DEFAULT_PATH,
    #                             input  uvm_reg_map        map = None,
    #                             input  uvm_sequence_base  parent = None,
    #                             input  int                prior = -1,
    #                             input  uvm_object         extension = None,
    #                             input  string             fname = "",
    #                             input  int                lineno = 0)
    async def write(self, status, offset, value, path=UVM_DEFAULT_PATH, _map=None, parent=None,
            prior=-1, extension=None, fname="", lineno=0):
        uvm_check_output_args([status])

        # create an abstract transaction for this operation
        rw = UVMRegItem.type_id.create("mem_write",None,self.get_full_name())
        rw.element      = self
        rw.element_kind = UVM_MEM
        rw.kind         = UVM_WRITE
        rw.offset       = offset
        rw.value[0]     = value
        rw.path         = path
        rw.map          = _map
        rw.parent       = parent
        rw.prior        = prior
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno

        await self.do_write(rw)
        status.append(rw.status)


    #   // Task: read
    #   //
    #   // Read the current value from a memory location
    #   //
    #   // Read and return ~value~ from the memory location that corresponds to this
    #   // abstraction class instance at the specified ~offset~
    #   // using the specified access ~path~.
    #   // If the register is mapped in more than one address map,
    #   // an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   //
    #   extern virtual task read(output uvm_status_e        status,
    #                            input  uvm_reg_addr_t      offset,
    #                            output uvm_reg_data_t      value,
    #                            input  uvm_path_e          path   = UVM_DEFAULT_PATH,
    #                            input  uvm_reg_map         map = None,
    #                            input  uvm_sequence_base   parent = None,
    #                            input  int                 prior = -1,
    #                            input  uvm_object          extension = None,
    #                            input  string              fname = "",
    #                            input  int                 lineno = 0)
    async def read(self, status, offset, value, path=UVM_DEFAULT_PATH, _map=None,
            parent=None, prior=-1, extension=None, fname="", lineno=0):
        uvm_check_output_args([status, value])

        rw = UVMRegItem.type_id.create("mem_read",None,self.get_full_name())
        rw.element      = self
        rw.element_kind = UVM_MEM
        rw.kind         = UVM_READ
        rw.value[0]     = 0
        rw.offset       = offset
        rw.path         = path
        rw.map          = _map
        rw.parent       = parent
        rw.prior        = prior
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno

        await self.do_read(rw)

        status.append(rw.status)
        value.append(rw.value[0])



    #   // Task: burst_write
    #   //
    #   // Write the specified values in memory locations
    #   //
    #   // Burst-write the specified ~values~ in the memory locations
    #   // beginning at the specified ~offset~.
    #   // If the memory is mapped in more than one address map,
    #   // an address ~map~ must be specified if not using the backdoor.
    #   // If a back-door access path is used, the effect of writing
    #   // the register through a physical access is mimicked. For
    #   // example, a read-only memory will not be written.
    #   //
    #   extern virtual task burst_write(output uvm_status_e      status,
    #                                   input  uvm_reg_addr_t    offset,
    #                                   input  uvm_reg_data_t    value[],
    #                                   input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                                   input  uvm_reg_map       map = None,
    #                                   input  uvm_sequence_base parent = None,
    #                                   input  int               prior = -1,
    #                                   input  uvm_object        extension = None,
    #                                   input  string            fname = "",
    #                                   input  int               lineno = 0)
    async def burst_write(self, status, offset, value, path=UVM_DEFAULT_PATH,
        _map=None, parent=None, prior=-1, extension=None, fname="",
            lineno=0):
        uvm_check_output_args([status])
        rw = UVMRegItem.type_id.create("mem_burst_write", None, self.get_full_name())
        rw.element      = self
        rw.element_kind = UVM_MEM
        rw.kind         = UVM_BURST_WRITE
        rw.offset       = offset
        rw.value        = value
        rw.path         = path
        rw.map          = _map
        rw.parent       = parent
        rw.prior        = prior
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno
        await self.do_write(rw)
        status.append(rw.status)



    #   // Task: burst_read
    #   //
    #   // Read values from memory locations
    #   //
    #   // Burst-read into ~values~ the data the memory locations
    #   // beginning at the specified ~offset~.
    #   // If the memory is mapped in more than one address map,
    #   // an address ~map~ must be specified if not using the backdoor.
    #   // If a back-door access path is used, the effect of writing
    #   // the register through a physical access is mimicked. For
    #   // example, a read-only memory will not be written.
    #   //
    #   extern virtual task burst_read(output uvm_status_e      status,
    #                                  input  uvm_reg_addr_t    offset,
    #                                  ref    uvm_reg_data_t    value[],
    #                                  input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                                  input  uvm_reg_map       map = None,
    #                                  input  uvm_sequence_base parent = None,
    #                                  input  int               prior = -1,
    #                                  input  uvm_object        extension = None,
    #                                  input  string            fname = "",
    #                                  input  int               lineno = 0)
    async def burst_read(self, status, offset,
    value, path=UVM_DEFAULT_PATH, _map=None, parent=None, prior=-1, extension=None, fname="",
            lineno=0):
        uvm_check_output_args([status, value])
        rw = UVMRegItem.type_id.create("mem_burst_read", None, self.get_full_name())
        rw.element      = self
        rw.element_kind = UVM_MEM
        rw.kind         = UVM_BURST_READ
        rw.offset       = offset
        rw.value        = value
        rw.path         = path
        rw.map          = _map
        rw.parent       = parent
        rw.prior        = prior
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno

        await self.do_read(rw)
        status.append(rw.status)
        for val in rw.value:
            value.append(val)


    #   // Task: poke
    #   //
    #   // Deposit the specified value in a memory location
    #   //
    #   // Deposit the value in the DUT memory location corresponding to this
    #   // abstraction class instance at the specified ~offset~, as-is,
    #   // using a back-door access.
    #   //
    #   // Uses the HDL path for the design abstraction specified by ~kind~.
    #   //
    #   extern virtual task poke(output uvm_status_e       status,
    #                            input  uvm_reg_addr_t     offset,
    #                            input  uvm_reg_data_t     value,
    #                            input  string             kind = "",
    #                            input  uvm_sequence_base  parent = None,
    #                            input  uvm_object         extension = None,
    #                            input  string             fname = "",
    #                            input  int                lineno = 0)
    def poke(self, status,
            offset, value, kind="", parent=None, extension=None, fname="", lineno=0):
        uvm_check_output_args([status])
        bkdr = self.get_backdoor()  # uvm_reg_backdoor
        rw = None  # uvm_reg_item

        self.m_fname = fname
        self.m_lineno = lineno

        if bkdr is None and self.has_hdl_path(kind) is False:
            uvm_error("RegModel", "No backdoor access available in memory '"
                      + self.get_full_name() + "'")
            status.append(UVM_NOT_OK)
            return

        # create an abstract transaction for this operation
        rw = UVMRegItem.type_id.create("mem_poke_item", None, self.get_full_name())
        rw.element      = self
        rw.path         = UVM_BACKDOOR
        rw.element_kind = UVM_MEM
        rw.kind         = UVM_READ
        rw.offset       = offset
        rw.value[0]     = value & ((1 << self.m_n_bits)-1)
        rw.bd_kind      = kind
        rw.parent       = parent
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno

        if bkdr is not None:
            bkdr.write(rw)
        else:
            self.backdoor_write(rw)

        status.append(rw.status)

        uvm_info("RegModel", sv.sformatf("Poked memory '%s[%0d]' with value 'h%h",
            self.get_full_name(), offset, value), UVM_HIGH)


    #   // Task: peek
    #   //
    #   // Read the current value from a memory location
    #   //
    #   // Sample the value in the DUT memory location corresponding to this
    #   // abstraction class instance at the specified ~offset~
    #   // using a back-door access.
    #   // The memory location value is sampled, not modified.
    #   //
    #   // Uses the HDL path for the design abstraction specified by ~kind~.
    #   //
    #   extern virtual task peek(output uvm_status_e       status,
    #                            input  uvm_reg_addr_t     offset,
    #                            output uvm_reg_data_t     value,
    #                            input  string             kind = "",
    #                            input  uvm_sequence_base  parent = None,
    #                            input  uvm_object         extension = None,
    #                            input  string             fname = "",
    #                            input  int                lineno = 0)
    def peek(self, status, offset, value, kind="", parent=None, extension=None, fname="",
            lineno=0):
        uvm_check_output_args([status, value])
        bkdr = self.get_backdoor()  # uvm_reg_backdoor
        rw = None  # uvm_reg_item

        self.m_fname = fname
        self.m_lineno = lineno

        if bkdr is None and self.has_hdl_path(kind) is False:
            uvm_error("RegModel", "No backdoor access available in memory '"
                      + self.get_full_name() + "'")
            status.append(UVM_NOT_OK)
            return

        # create an abstract transaction for this operation
        rw = UVMRegItem.type_id.create("mem_peek_item", None, self.get_full_name())
        rw.element      = self
        rw.path         = UVM_BACKDOOR
        rw.element_kind = UVM_MEM
        rw.kind         = UVM_READ
        rw.offset       = offset
        rw.bd_kind      = kind
        rw.parent       = parent
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno

        if bkdr is not None:
            bkdr.read(rw)
        else:
            self.backdoor_read(rw)

        status.append(rw.status)
        value.append(rw.value[0])

        uvm_info("RegModel", sv.sformatf("Peeked memory '%s[%0d]' has value '%s'",
            self.get_full_name(), offset, str(value)), UVM_HIGH)


    #   extern protected function bit Xcheck_accessX (input uvm_reg_item rw,
    #                                                 output uvm_reg_map_info map_info,
    #                                                 input string caller)
    def Xcheck_accessX(self, rw, map_info, caller):
        uvm_check_output_args([map_info])

        if rw.offset >= self.m_size:
            uvm_error(self.get_type_name(),
               sv.sformatf("Offset 'h%0h exceeds size of memory, 'h%0h",
                 rw.offset, self.m_size))
            rw.status = UVM_NOT_OK
            return 0

        if rw.path == UVM_DEFAULT_PATH:
            rw.path = self.m_parent.get_default_path()

        if rw.path == UVM_BACKDOOR:
           if self.get_backdoor() is None and  self.has_hdl_path() is False:
               uvm_warning("RegModel",
                 "No backdoor access available for memory '" + self.get_full_name()
                 + "' . Using frontdoor instead.")
               rw.path = UVM_FRONTDOOR
           else:
               rw.map = UVMRegMap.backdoor()

        if rw.path != UVM_BACKDOOR:
            rw.local_map = self.get_local_map(rw.map,caller)

            if rw.local_map is None:
                uvm_error(self.get_type_name(),
                    "No transactor available to physically access memory from map '"
                    + rw.map.get_full_name() + "'")
                rw.status = UVM_NOT_OK
                return 0

            _map_info_data = rw.local_map.get_mem_map_info(self)
            map_info.append(_map_info_data)

            if _map_info_data.frontdoor is None:

                if (_map_info_data.unmapped):
                    uvm_error("RegModel", "Memory '" + self.get_full_name()
                              + "' unmapped in map '" + rw.map.get_full_name()
                              + "' and does not have a user-defined frontdoor")
                    rw.status = UVM_NOT_OK
                    return 0

                if len(rw.value) > 1:
                    if self.get_n_bits() > rw.local_map.get_n_bytes()*8:
                        uvm_error("RegModel",
                             sv.sformatf("Cannot burst a %0d-bit memory through a narrower data path (%0d bytes)",
                             self.get_n_bits(), rw.local_map.get_n_bytes()*8))
                        rw.status = UVM_NOT_OK
                        return 0

                    if rw.offset + len(rw.value) > self.m_size:
                        uvm_error("RegModel",
                           sv.sformatf("Burst of size 'd%0d starting at offset 'd%0d exceeds size of memory, 'd%0d",
                               len(rw.value), rw.offset, self.m_size))
                        return 0

            if rw.map is None:
                rw.map = rw.local_map

        return 1


    #   extern virtual task do_write (uvm_reg_item rw)
    async def do_write(self, rw):  # task
        cbs = UVMMemCbIter(self)
        arr_map_info = []  # uvm_reg_map_info

        self.m_fname  = rw.fname
        self.m_lineno = rw.lineno

        if self.Xcheck_accessX(rw, arr_map_info, "burst_write()") is False:
            await uvm_zero_delay()
            return

        self.m_write_in_progress = True
        rw.status = UVM_IS_OK

        # PRE-WRITE CBS
        await self.pre_write(rw)
        #   for (uvm_reg_cbs cb=cbs.first(); cb is not None; cb=cbs.next())
        #      cb.pre_write(rw)
        cb = cbs.first()
        while cb is not None:
            await cb.pre_write(rw)
            cb = cbs.next()

        if rw.status != UVM_IS_OK:
            self.m_write_in_progress = False
            return

        rw.status = UVM_NOT_OK

        # FRONTDOOR
        if rw.path == UVM_FRONTDOOR:
            map_info = arr_map_info[0]

            system_map = rw.local_map.get_root_map()
            if map_info.frontdoor is not None:
                fd = map_info.frontdoor  # uvm_reg_frontdoor
                fd.rw_info = rw
                if fd.sequencer is None:
                    fd.sequencer = system_map.get_sequencer()
                await fd.start(fd.sequencer, rw.parent)
            else:
                await rw.local_map.do_write(rw)

            if rw.status != UVM_NOT_OK:
                _min = rw.offset
                _max = rw.offset + len(rw.value) + 1
                for idx in range(_min, _max):
                    self.XsampleX(map_info.mem_range.stride * idx, 0, rw.map)
                    self.m_parent.XsampleX(map_info.offset +
                            (map_info.mem_range.stride * idx), 0, rw.map)

        else:
            #raise Exception("Backdoor access not implemented yet for UVMMem!")
            # // BACKDOOR TODO
            # // Mimick front door access, i.e. do not write read-only memories
            if self.get_access(rw.map) == "RW":
                bkdr = self.get_backdoor()  # uvm_reg_backdoor
                if bkdr is not None:
                    await bkdr.write(rw)
                else:
                    # await self.backdoor_write(rw)
                    self.backdoor_write(rw)
            else:
                rw.status = UVM_IS_OK

        #   // POST-WRITE CBS
        await self.post_write(rw)
        cb = cbs.first()
        while cb is not None:
            await cb.post_write(rw)
            cb = cbs.next()

        # REPORT
        if uvm_report_enabled(UVM_HIGH, UVM_INFO, "RegModel"):
            path_s = ""
            value_s = ""
            pre_s = ""
            range_s = ""
            if rw.path == UVM_FRONTDOOR:
                path_s = "map " + rw.map.get_full_name()
                if map_info.frontdoor is not None:
                    path_s = "user frontdoor"
            else:
                path_s = "DPI backdoor"
                if self.get_backdoor() is not None:
                    path_s = "user backdoor"

            if len(rw.value) > 1:
                value_s = "='{"
                pre_s = "Burst "
                for i in range(len(rw.value)):
                    value_s = value_s + sv.sformatf("%0h,",rw.value[i])
                value_s = value_s[:-1] + "}"
                range_s = sv.sformatf("[%0d:%0d]",rw.offset,rw.offset+len(rw.value))
            else:
                value_s = sv.sformatf("=%0h",rw.value[0])
                range_s = sv.sformatf("[%0d]",rw.offset)
            uvm_report_info("RegModel", pre_s + "Wrote memory via " + path_s + ": " +
                    self.get_full_name() + range_s + value_s, UVM_HIGH)
        self.m_write_in_progress = False


    #   extern virtual task do_read  (uvm_reg_item rw)
    async def do_read(self, rw):  # task
        cbs = UVMMemCbIter(self)
        arr_map_info = []  # uvm_reg_map_info

        self.m_fname = rw.fname
        self.m_lineno = rw.lineno

        if self.Xcheck_accessX(rw, arr_map_info, "burst_read()") is False:
            await uvm_zero_delay()
            return

        self.m_read_in_progress = True
        rw.status = UVM_IS_OK
        #
        # PRE-READ CBS
        await self.pre_read(rw)
        cb = cbs.first()
        while cb is not None:
            cb.pre_read(rw)
            cb = cbs.next()

        if rw.status != UVM_IS_OK:
            self.m_read_in_progress = False
            return

        rw.status = UVM_NOT_OK

        # FRONTDOOR
        if rw.path == UVM_FRONTDOOR:
            map_info = arr_map_info[0]
            system_map = rw.local_map.get_root_map()

            if (map_info.frontdoor is not None):
                fd = map_info.frontdoor  # uvm_reg_frontdoor
                fd.rw_info = rw
                if fd.sequencer is None:
                    fd.sequencer = system_map.get_sequencer()
                await fd.start(fd.sequencer, rw.parent)
            else:
                await rw.local_map.do_read(rw)

            if rw.status != UVM_NOT_OK:
                _min = rw.offset
                _max = rw.offset + len(rw.value) + 1
                for idx in range(_min, _max):
                    self.XsampleX(map_info.mem_range.stride * idx, 1, rw.map)
                    self.m_parent.XsampleX(map_info.offset +
                            (map_info.mem_range.stride * idx), 1, rw.map)
        # // BACKDOOR
        else:
            bkdr = self.get_backdoor()  # uvm_reg_backdoor
            if bkdr is not None:
                await bkdr.read(rw)
            else:
                # await self.backdoor_read(rw)
                self.backdoor_read(rw)

        # POST-READ CBS
        await self.post_read(rw)
        cb = cbs.first()
        while cb is not None:
            await cb.post_read(rw)
            cb = cbs.next()

        # REPORT
        if uvm_report_enabled(UVM_HIGH, UVM_INFO, "RegModel"):
            path_s = ""
            value_s = ""
            pre_s = ""
            range_s = ""
            if rw.path == UVM_FRONTDOOR:
                path_s = "map " + rw.map.get_full_name()
                map_info = arr_map_info[0]
                if map_info.frontdoor is not None:
                    path_s = "user frontdoor"
            else:
                path_s = "DPI backdoor"
                if self.get_backdoor() is not None:
                    path_s = "user backdoor"

            if len(rw.value) > 1:
                value_s = "='{"
                pre_s = "Burst "
                for i in range(len(rw.value)):
                    value_s = value_s + sv.sformatf("%0h,", int(rw.value[i]))
                value_s = value_s[:-1] + "}"
                range_s = sv.sformatf("[%0d:%0d]",rw.offset,rw.offset+len(rw.value))
            else:
                value_s = sv.sformatf("=%0h", int(rw.value[0]))
                range_s = sv.sformatf("[%0d]", rw.offset)

            uvm_report_info("RegModel", pre_s + "Read memory via " + path_s + ": "
                    + self.get_full_name() + range_s + value_s, UVM_HIGH)

        self.m_read_in_progress = False
        #
        #endtask: do_read


    #   //-----------------
    #   // Group: Frontdoor
    #   //-----------------


    #   // Function: set_frontdoor
    #   //
    #   // Set a user-defined frontdoor for this memory
    #   //
    #   // By default, memories are mapped linearly into the address space
    #   // of the address maps that instantiate them.
    #   // If memories are accessed using a different mechanism,
    #   // a user-defined access
    #   // mechanism must be defined and associated with
    #   // the corresponding memory abstraction class
    #   //
    #   // If the memory is mapped in multiple address maps, an address ~map~
    #   // must be specified.
    #   //
    #   extern function void set_frontdoor(uvm_reg_frontdoor ftdr,
    #                                      uvm_reg_map map = None,
    #                                      string fname = "",
    #                                      int lineno = 0)

    #
    #
    #   // Function: get_frontdoor
    #   //
    #   // Returns the user-defined frontdoor for this memory
    #   //
    #   // If ~None~, no user-defined frontdoor has been defined.
    #   // A user-defined frontdoor is defined
    #   // by using the <uvm_mem::set_frontdoor()> method.
    #   //
    #   // If the memory is mapped in multiple address maps, an address ~map~
    #   // must be specified.
    #   //
    #   extern function uvm_reg_frontdoor get_frontdoor(uvm_reg_map map = None)

    #
    #
    #   //----------------
    #   // Group: Backdoor
    #   //----------------

    #
    #   // Function: set_backdoor
    #   //
    #   // Set a user-defined backdoor for this memory
    #   //
    #   // By default, memories are accessed via the built-in string-based
    #   // DPI routines if an HDL path has been specified using the
    #   // <uvm_mem::configure()> or <uvm_mem::add_hdl_path()> method.
    #   // If this default mechanism is not suitable (e.g. because
    #   // the memory is not implemented in pure SystemVerilog)
    #   // a user-defined access
    #   // mechanism must be defined and associated with
    #   // the corresponding memory abstraction class
    #   //
    #   extern function void set_backdoor (uvm_reg_backdoor bkdr,
    #                                      string fname = "",
    #                                      int lineno = 0)
    def set_backdoor(self, bkdr, fname="", lineno=0):
        self.m_fname = fname
        self.m_lineno = lineno
        self.m_backdoor = bkdr


    #   // Function: get_backdoor
    #   //
    #   // Returns the user-defined backdoor for this memory
    #   //
    #   // If ~None~, no user-defined backdoor has been defined.
    #   // A user-defined backdoor is defined
    #   // by using the <uvm_reg::set_backdoor()> method.
    #   //
    #   // If ~inherit~ is TRUE, returns the backdoor of the parent block
    #   // if none have been specified for this memory.
    #   //
    #   extern function uvm_reg_backdoor get_backdoor(bit inherited = 1)
    def get_backdoor(self, inherited=1):
        #
        if self.m_backdoor is None and inherited:
            blk = self.get_parent()  # uvm_reg_block
            bkdr = None  # uvm_reg_backdoor
            while blk is not None:
                bkdr = blk.get_backdoor()
                if bkdr is not None:
                    self.m_backdoor = bkdr
                    break
                blk = blk.get_parent()
        #
        return self.m_backdoor
        #endfunction: get_backdoor



    #   // Function: clear_hdl_path
    #   //
    #   // Delete HDL paths
    #   //
    #   // Remove any previously specified HDL path to the memory instance
    #   // for the specified design abstraction.
    #   //
    #   extern function void clear_hdl_path (string kind = "RTL")

    #
    #
    #   // Function: add_hdl_path
    #   //
    #   // Add an HDL path
    #   //
    #   // Add the specified HDL path to the memory instance for the specified
    #   // design abstraction. This method may be called more than once for the
    #   // same design abstraction if the memory is physically duplicated
    #   // in the design abstraction
    #   //
    #   extern function void add_hdl_path (uvm_hdl_path_slice slices[],
    #                                      string kind = "RTL")
    #
    #

    #   // Function: add_hdl_path_slice
    #   //
    #   // Add the specified HDL slice to the HDL path for the specified
    #   // design abstraction.
    #   // If ~first~ is TRUE, starts the specification of a duplicate
    #   // HDL implementation of the memory.
    #   //
    #   extern function void add_hdl_path_slice(string name,
    #                                           int offset,
    #                                           int size,
    #                                           bit first = 0,
    #                                           string kind = "RTL")
    def add_hdl_path_slice(self, name, offset, size, first=0, kind="RTL"):
        paths = self.m_hdl_paths_pool.get(kind)  # #    uvm_queue #(uvm_hdl_path_concat)
        concat = None  #    uvm_hdl_path_concat

        if first or paths.size() == 0:
            concat = uvm_hdl_path_concat()
            paths.push_back(concat)
        else:
            concat = paths.get(paths.size()-1)

        concat.add_path(name, offset, size)
    #endfunction


    #
    #
    #   // Function: has_hdl_path
    #   //
    #   // Check if a HDL path is specified
    #   //
    #   // Returns TRUE if the memory instance has a HDL path defined for the
    #   // specified design abstraction. If no design abstraction is specified,
    #   // uses the default design abstraction specified for the parent block.
    #   //
    #   extern function bit  has_hdl_path (string kind = "")
    def has_hdl_path(self, kind=""):
        if kind == "":
            kind = self.m_parent.get_default_hdl_path()
        return self.m_hdl_paths_pool.exists(kind)
        #endfunction


    #   // Function: get_hdl_path
    #   //
    #   // Get the incremental HDL path(s)
    #   //
    #   // Returns the HDL path(s) defined for the specified design abstraction
    #   // in the memory instance.
    #   // Returns only the component of the HDL paths that corresponds to
    #   // the memory, not a full hierarchical path
    #   //
    #   // If no design abstraction is specified, the default design abstraction
    #   // for the parent block is used.
    #   //
    #   extern function void get_hdl_path (ref uvm_hdl_path_concat paths[$],
    #                                      input string kind = "")

    #
    #
    #   // Function: get_full_hdl_path
    #   //
    #   // Get the full hierarchical HDL path(s)
    #   //
    #   // Returns the full hierarchical HDL path(s) defined for the specified
    #   // design abstraction in the memory instance.
    #   // There may be more than one path returned even
    #   // if only one path was defined for the memory instance, if any of the
    #   // parent components have more than one path defined for the same design
    #   // abstraction
    #   //
    #   // If no design abstraction is specified, the default design abstraction
    #   // for each ancestor block is used to get each incremental path.
    #   //
    #   extern function void get_full_hdl_path (ref uvm_hdl_path_concat paths[$],
    #                                           input string kind = "",
    #                                           input string separator = ".")
    def get_full_hdl_path(self, paths, kind="", separator="."):

        if kind == "":
            kind = self.m_parent.get_default_hdl_path()

        if self.has_hdl_path(kind) is False:
            uvm_error("RegModel",
                "Memory does not have hdl path defined for abstraction '" + kind + "'")
            return

        hdl_paths = self.m_hdl_paths_pool.get(kind)
        parent_paths = []  # string[$]
        self.m_parent.get_full_hdl_path(parent_paths, kind, separator)

        for i in range(len(hdl_paths)):
            hdl_concat = hdl_paths.get(i)

            for j in range(len(parent_paths)):
                t = uvm_hdl_path_concat()

                for k in range(len(hdl_concat.slices)):
                    if hdl_concat.slices[k].path == "":
                        t.add_path(parent_paths[j])
                    else:
                        t.add_path(parent_paths[j] + separator
                            + hdl_concat.slices[k].path,
                                  hdl_concat.slices[k].offset,
                                  hdl_concat.slices[k].size)
                paths.append(t)


    #   // Function: get_hdl_path_kinds
    #   //
    #   // Get design abstractions for which HDL paths have been defined
    #   //
    #   extern function void get_hdl_path_kinds (ref string kinds[$])


    #   // Function: backdoor_read
    #   //
    #   // User-define backdoor read access
    #   //
    #   // Override the default string-based DPI backdoor access read
    #   // for this memory type.
    #   // By default calls <uvm_mem::backdoor_read_func()>.
    #   //
    #   extern virtual protected task backdoor_read(uvm_reg_item rw)
    def backdoor_read(self, rw):
        rw.status = self.backdoor_read_func(rw)


    #   // Function: backdoor_write
    #   //
    #   // User-defined backdoor read access
    #   //
    #   // Override the default string-based DPI backdoor access write
    #   // for this memory type.
    #   //
    #   extern virtual task backdoor_write(uvm_reg_item rw)
    def backdoor_write(self, rw):
        paths = []
        ok = 1
        self.get_full_hdl_path(paths,rw.bd_kind)

        for mem_idx in range(len(rw.value)):
            idx = str(rw.offset + mem_idx)
            for i in range(len(paths)):
                hdl_concat = paths[i]  # uvm_hdl_path_concat
                for j in range(len(hdl_concat.slices)):
                    uvm_info("RegModel", sv.sformatf("backdoor_write to %s ", hdl_concat.slices[j].path),UVM_DEBUG)

                    if (hdl_concat.slices[j].offset < 0):
                        ok &= uvm_hdl.uvm_hdl_deposit(hdl_concat.slices[j].path
                                + "[" + idx + "]", rw.value[mem_idx])
                        continue

                    _slice = 0
                    _slice = rw.value[mem_idx] >> hdl_concat.slices[j].offset
                    _slice &= (1 << hdl_concat.slices[j].size)-1
                    ok &= uvm_hdl.uvm_hdl_deposit(hdl_concat.slices[j].path +
                            "[" + idx + "]", _slice)
        rw.status = UVM_NOT_OK
        if ok:
            rw.status = UVM_IS_OK
        #endtask


    #   // Function: backdoor_read_func
    #   //
    #   // User-defined backdoor read access
    #   //
    #   // Override the default string-based DPI backdoor access read
    #   // for this memory type.
    #   //
    #   extern virtual function uvm_status_e backdoor_read_func(uvm_reg_item rw)
    def backdoor_read_func(self, rw):

        paths = []  # uvm_hdl_path_concat [$]
        val = 0x0
        ok = 1

        self.get_full_hdl_path(paths, rw.bd_kind)

        # foreach (rw.value[mem_idx]):
        for mem_idx in range(len(rw.value)):
            idx = str(rw.offset + mem_idx)
            for i in range(len(paths)):
                hdl_concat = paths[i]  # uvm_hdl_path_concat
                val = 0
                for j in range(len(hdl_concat.slices)):
                    hdl_path = hdl_concat.slices[j].path + "[" + idx + "]"
                    uvm_info("RegModel", "backdoor_read from " + hdl_path, UVM_DEBUG)

                    if hdl_concat.slices[j].offset < 0:
                        arr = []
                        ok &= uvm_hdl.uvm_hdl_read(hdl_path, arr)
                        val = arr[0]
                        continue

                    _slice = 0
                    k = hdl_concat.slices[j].offset
                    ok &= uvm_hdl.uvm_hdl_read(hdl_path, _slice)

                    # TODO Loops all bits one by one
                    for n in range(hdl_concat.slices[j].size):
                        slice_n_bit = (_slice >> n) & 0x1
                        # Need to set slice_n_bit in pos k
                        val |= (slice_n_bit << k) & (1 << k)
                        k += 1
                        # _slice >>= 1

                val &= (1 << self.m_n_bits)-1

                if i == 0:
                    rw.value[mem_idx] = val

                if val != rw.value[mem_idx]:
                    uvm_error("RegModel", sv.sformatf(ERR_MEM_BD_READ,
                       self.get_full_name(), rw.value[mem_idx], uvm_hdl_concat2string(paths[0]),
                       val, uvm_hdl_concat2string(paths[i])))
                    return UVM_NOT_OK

        rw.status = UVM_NOT_OK
        if ok:
            rw.status = UVM_IS_OK
        return rw.status
        #endfunction



    #   //-----------------
    #   // Group: Callbacks
    #   //-----------------
    #   `uvm_register_cb(uvm_mem, uvm_reg_cbs)


    #   // Task: pre_write
    #   //
    #   // Called before memory write.
    #   //
    #   // If the ~offset~, ~value~, access ~path~,
    #   // or address ~map~ are modified, the updated offset, data value,
    #   // access path or address map will be used to perform the memory operation.
    #   // If the ~status~ is modified to anything other than <UVM_IS_OK>,
    #   // the operation is aborted.
    #   //
    #   // The registered callback methods are invoked after the invocation
    #   // of this method.
    #   //
    async def pre_write(self, rw):
        await uvm_zero_delay()

    #   // Task: post_write
    #   //
    #   // Called after memory write.
    #   //
    #   // If the ~status~ is modified, the updated status will be
    #   // returned by the memory operation.
    #   //
    #   // The registered callback methods are invoked before the invocation
    #   // of this method.
    #   //
    #   virtual task post_write(uvm_reg_item rw); endtask
    async def post_write(self, rw):
        await uvm_zero_delay()


    #   // Task: pre_read
    #   //
    #   // Called before memory read.
    #   //
    #   // If the ~offset~, access ~path~ or address ~map~ are modified,
    #   // the updated offset, access path or address map will be used to perform
    #   // the memory operation.
    #   // If the ~status~ is modified to anything other than <UVM_IS_OK>,
    #   // the operation is aborted.
    #   //
    #   // The registered callback methods are invoked after the invocation
    #   // of this method.
    #   //
    #   virtual task pre_read(uvm_reg_item rw); endtask
    async def pre_read(self, rw):
        await uvm_zero_delay()


    #   // Task: post_read
    #   //
    #   // Called after memory read.
    #   //
    #   // If the readback data or ~status~ is modified,
    #   // the updated readback //data or status will be
    #   // returned by the memory operation.
    #   //
    #   // The registered callback methods are invoked before the invocation
    #   // of this method.
    #   //
    #   virtual task post_read(uvm_reg_item rw); endtask
    async def post_read(self, rw):
        await uvm_zero_delay()


    #   //----------------
    #   // Group: Coverage
    #   //----------------

    #   // Function: build_coverage
    #   //
    #   // Check if all of the specified coverage model must be built.
    #   //
    #   // Check which of the specified coverage model must be built
    #   // in this instance of the memory abstraction class,
    #   // as specified by calls to <uvm_reg::include_coverage()>.
    #   //
    #   // Models are specified by adding the symbolic value of individual
    #   // coverage model as defined in <uvm_coverage_model_e>.
    #   // Returns the sum of all coverage models to be built in the
    #   // memory model.
    #   //
    #   extern protected function uvm_reg_cvr_t build_coverage(uvm_reg_cvr_t models)
    def build_coverage(self, models):
        build_coverage = UVM_NO_COVERAGE
        cov_arr = []
        uvm_reg_cvr_rsrc_db.read_by_name("uvm_reg::" + self.get_full_name(),
                "include_coverage", cov_arr, self)
        build_coverage = cov_arr[0]
        return build_coverage & models


    #   // Function: add_coverage
    #   //
    #   // Specify that additional coverage models are available.
    #   //
    #   // Add the specified coverage model to the coverage models
    #   // available in this class.
    #   // Models are specified by adding the symbolic value of individual
    #   // coverage model as defined in <uvm_coverage_model_e>.
    #   //
    #   // This method shall be called only in the constructor of
    #   // subsequently derived classes.
    #   //
    #   extern virtual protected function void add_coverage(uvm_reg_cvr_t models)
    def add_coverage(self, models):
        self.m_has_cover |= models


    #   // Function: has_coverage
    #   //
    #   // Check if memory has coverage model(s)
    #   //
    #   // Returns TRUE if the memory abstraction class contains a coverage model
    #   // for all of the models specified.
    #   // Models are specified by adding the symbolic value of individual
    #   // coverage model as defined in <uvm_coverage_model_e>.
    #   //
    #   extern virtual function bit has_coverage(uvm_reg_cvr_t models)
    def has_coverage(self, models):
        return ((self.m_has_cover & models) == models)


    #   // Function: set_coverage
    #   //
    #   // Turns on coverage measurement.
    #   //
    #   // Turns the collection of functional coverage measurements on or off
    #   // for this memory.
    #   // The functional coverage measurement is turned on for every
    #   // coverage model specified using <uvm_coverage_model_e> symbolic
    #   // identifiers.
    #   // Multiple functional coverage models can be specified by adding
    #   // the functional coverage model identifiers.
    #   // All other functional coverage models are turned off.
    #   // Returns the sum of all functional
    #   // coverage models whose measurements were previously on.
    #   //
    #   // This method can only control the measurement of functional
    #   // coverage models that are present in the memory abstraction classes,
    #   // then enabled during construction.
    #   // See the <uvm_mem::has_coverage()> method to identify
    #   // the available functional coverage models.
    #   //
    #   extern virtual function uvm_reg_cvr_t set_coverage(uvm_reg_cvr_t is_on)
    def set_coverage(self, is_on):
        if is_on == UVM_NO_COVERAGE:
            self.m_cover_on = is_on
            return self.m_cover_on

        self.m_cover_on = self.m_has_cover & is_on
        return self.m_cover_on


    #   // Function: get_coverage
    #   //
    #   // Check if coverage measurement is on.
    #   //
    #   // Returns TRUE if measurement for all of the specified functional
    #   // coverage models are currently on.
    #   // Multiple functional coverage models can be specified by adding the
    #   // functional coverage model identifiers.
    #   //
    #   // See <uvm_mem::set_coverage()> for more details.
    #   //
    #   extern virtual function bit get_coverage(uvm_reg_cvr_t is_on)
    def get_coverage(self, is_on):
        if self.has_coverage(is_on) == 0:
            return 0
        return ((self.m_cover_on & is_on) == is_on)


    #   // Function: sample
    #   //
    #   // Functional coverage measurement method
    #   //
    #   // This method is invoked by the memory abstraction class
    #   // whenever an address within one of its address map
    #   // is successfully read or written.
    #   // The specified offset is the offset within the memory,
    #   // not an absolute address.
    #   //
    #   // Empty by default, this method may be extended by the
    #   // abstraction class generator to perform the required sampling
    #   // in any provided functional coverage model.
    #   //
    #   protected virtual function void  sample(uvm_reg_addr_t offset,
    #                                           bit            is_read,
    #                                           uvm_reg_map    map)
    def sample(self, offset, is_read, _map):
        pass


    def XsampleX(self, addr, is_read, _map):
        self.sample(addr, is_read, _map)


    #   // Core ovm_object operations
    #
    #   extern virtual function void do_print (uvm_printer printer)
    #   extern virtual function string convert2string()
    #   extern virtual function uvm_object clone()
    #   extern virtual function void do_copy   (uvm_object rhs)
    #   extern virtual function bit do_compare (uvm_object  rhs,
    #                                          uvm_comparer comparer)
    #   extern virtual function void do_pack (uvm_packer packer)
    #   extern virtual function void do_unpack (uvm_packer packer)
    #
    #
    #endclass: uvm_mem

#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#
#
#
#
#
#// set_offset
#
#function void uvm_mem::set_offset (uvm_reg_map    map,
#                                   uvm_reg_addr_t offset,
#                                   bit unmapped = 0)
#
#   uvm_reg_map orig_map = map
#
#   if (m_maps.num() > 1 && map is None):
#      `uvm_error("RegModel",{"set_offset requires a non-None map when memory '",
#                 get_full_name(),"' belongs to more than one map."})
#      return
#   end
#
#   map = get_local_map(map,"set_offset()")
#
#   if (map is None)
#     return
#
#   map.m_set_mem_offset(this, offset, unmapped)
#endfunction
#
#
#// is_in_map
#
#function bit uvm_mem::is_in_map(uvm_reg_map map)
#   if (m_maps.exists(map))
#     return 1
#   foreach (m_maps[l]):
#    uvm_reg_map local_map=l
#     uvm_reg_map parent_map = local_map.get_parent_map()
#
#     while (parent_map != None):
#       if (parent_map == map)
#         return 1
#       parent_map = parent_map.get_parent_map()
#     end
#   end
#   return 0
#endfunction
#
#
#// get_default_map
#
#function uvm_reg_map uvm_mem::get_default_map(string caller="")
#
#   // if mem is not associated with any may, return ~None~
#   if (m_maps.num() == 0):
#      `uvm_warning("RegModel",
#        {"Memory '",get_full_name(),"' is not registered with any map",
#         (caller == "" ? "": {" (called from ",caller,")"})})
#      return None
#   end
#
#   // if only one map, choose that
#   if (m_maps.num() == 1):
#     void'(m_maps.first(get_default_map))
#   end
#
#   // try to choose one based on default_map in parent blocks.
#   foreach (m_maps[l]):
#     uvm_reg_map map = l
#     uvm_reg_block blk = map.get_parent()
#     uvm_reg_map default_map = blk.get_default_map()
#     if (default_map != None):
#       uvm_reg_map local_map = get_local_map(default_map)
#       if (local_map != None)
#         return local_map
#     end
#   end
#
#   // if that fails, choose the first in this mem's maps
#
#   void'(m_maps.first(get_default_map))
#
#endfunction
#
#
#
#
#// get_offset
#
#function uvm_reg_addr_t uvm_mem::get_offset(uvm_reg_addr_t offset = 0,
#                                            uvm_reg_map map = None)
#
#   uvm_reg_map_info map_info
#   uvm_reg_map orig_map = map
#
#   map = get_local_map(map,"get_offset()")
#
#   if (map is None)
#     return -1
#
#   map_info = map.get_mem_map_info(this)
#
#   if (map_info.unmapped):
#      `uvm_warning("RegModel", {"Memory '",get_name(),
#                   "' is unmapped in map '",
#                   ((orig_map is None) ? map.get_full_name() : orig_map.get_full_name()),"'"})
#      return -1
#   end
#
#   return map_info.offset
#
#endfunction: get_offset
#
#
#
#// get_virtual_registers
#
#function void uvm_mem::get_virtual_registers(ref uvm_vreg regs[$])
#  foreach (m_vregs[vreg])
#     regs.append(vreg)
#endfunction
#
#
#// get_virtual_fields
#
#function void uvm_mem::get_virtual_fields(ref uvm_vreg_field fields[$])
#
#  foreach (m_vregs[l])
#  begin
#    uvm_vreg vreg = l
#    vreg.get_fields(fields)
#  end
#endfunction: get_virtual_fields
#
#
#// get_vfield_by_name
#
#function uvm_vreg_field uvm_mem::get_vfield_by_name(string name)
#  // Return first occurrence of vfield matching name
#  uvm_vreg_field vfields[$]
#
#  get_virtual_fields(vfields)
#
#  foreach (vfields[i])
#    if (vfields[i].get_name() == name)
#      return vfields[i]
#
#  `uvm_warning("RegModel", {"Unable to find virtual field '",name,
#                       "' in memory '",get_full_name(),"'"})
#   return None
#endfunction: get_vfield_by_name
#
#
#// get_vreg_by_name
#
#function uvm_vreg uvm_mem::get_vreg_by_name(string name)
#
#  foreach (m_vregs[l])
#  begin
#    uvm_vreg vreg = l
#    if (vreg.get_name() == name)
#      return vreg
#  end
#
#  `uvm_warning("RegModel", {"Unable to find virtual register '",name,
#                       "' in memory '",get_full_name(),"'"})
#  return None
#
#endfunction: get_vreg_by_name
#
#
#// get_vreg_by_offset
#
#function uvm_vreg uvm_mem::get_vreg_by_offset(uvm_reg_addr_t offset,
#                                              uvm_reg_map map = None)
#   `uvm_error("RegModel", "uvm_mem::get_vreg_by_offset() not yet implemented")
#   return None
#endfunction: get_vreg_by_offset
#
#
#
#// get_addresses
#
#function int uvm_mem::get_addresses(uvm_reg_addr_t offset = 0,
#                                    uvm_reg_map map=None,
#                                    ref uvm_reg_addr_t addr[])
#
#   uvm_reg_map_info map_info
#   uvm_reg_map system_map
#   uvm_reg_map orig_map = map
#
#   map = get_local_map(map,"get_addresses()")
#
#   if (map is None)
#     return 0
#
#   map_info = map.get_mem_map_info(this)
#
#   if (map_info.unmapped):
#      `uvm_warning("RegModel", {"Memory '",get_name(),
#                   "' is unmapped in map '",
#                   ((orig_map is None) ? map.get_full_name() : orig_map.get_full_name()),"'"})
#      return 0
#   end
#
#   addr = map_info.addr
#
#   foreach (addr[i])
#      addr[i] = addr[i] + map_info.mem_range.stride * offset
#
#   return map.get_n_bytes()
#
#endfunction
#
#
#// get_address
#
#function uvm_reg_addr_t uvm_mem::get_address(uvm_reg_addr_t offset = 0,
#                                             uvm_reg_map map = None)
#   uvm_reg_addr_t  addr[]
#   void'(get_addresses(offset, map, addr))
#   return addr[0]
#endfunction
#
#
#//-----------
#// HDL ACCESS
#//-----------
#
#
#
#
#
#
#//-------
#// ACCESS
#//-------
#
#
#
#
#
#//-----------------
#// Group- Frontdoor
#//-----------------
#
#// set_frontdoor
#
#function void uvm_mem::set_frontdoor(uvm_reg_frontdoor ftdr,
#                                     uvm_reg_map       map = None,
#                                     string            fname = "",
#                                     int               lineno = 0)
#   uvm_reg_map_info map_info
#   m_fname = fname
#   m_lineno = lineno
#
#   map = get_local_map(map, "set_frontdoor()")
#
#   if (map is None):
#      `uvm_error("RegModel", {"Memory '",get_full_name(),
#                 "' not found in map '", map.get_full_name(),"'"})
#      return
#   end
#
#   map_info = map.get_mem_map_info(this)
#   map_info.frontdoor = ftdr
#
#endfunction: set_frontdoor
#
#
#// get_frontdoor
#
#function uvm_reg_frontdoor uvm_mem::get_frontdoor(uvm_reg_map map = None)
#   uvm_reg_map_info map_info
#
#   map = get_local_map(map, "set_frontdoor()")
#
#   if (map is None):
#      `uvm_error("RegModel", {"Memory '",get_full_name(),
#                 "' not found in map '", map.get_full_name(),"'"})
#      return None
#   end
#
#   map_info = map.get_mem_map_info(this)
#   return map_info.frontdoor
#
#endfunction: get_frontdoor
#
#
#//----------------
#// Group- Backdoor
#//----------------
#
#
#
#
#
#// clear_hdl_path
#
#function void uvm_mem::clear_hdl_path(string kind = "RTL")
#  if (kind == "ALL"):
#    m_hdl_paths_pool = new("hdl_paths")
#    return
#  end
#
#  if (kind == "")
#    kind = m_parent.get_default_hdl_path()
#
#  if (!m_hdl_paths_pool.exists(kind)):
#    `uvm_warning("RegModel",{"Unknown HDL Abstraction '",kind,"'"})
#    return
#  end
#
#  m_hdl_paths_pool.delete(kind)
#endfunction
#
#
#// add_hdl_path
#
#function void uvm_mem::add_hdl_path(uvm_hdl_path_slice slices[], string kind = "RTL")
#    uvm_queue #(uvm_hdl_path_concat) paths = m_hdl_paths_pool.get(kind)
#    uvm_hdl_path_concat concat = new()
#
#    concat.set(slices)
#    paths.push_back(concat);
#endfunction
#
#
#
#
#
#
#// get_hdl_path
#
#function void uvm_mem::get_hdl_path(ref uvm_hdl_path_concat paths[$],
#                                    input string kind = "")
#
#  uvm_queue #(uvm_hdl_path_concat) hdl_paths
#
#  if (kind == "")
#     kind = m_parent.get_default_hdl_path()
#
#  if (!has_hdl_path(kind)):
#    `uvm_error("RegModel",
#        {"Memory does not have hdl path defined for abstraction '",kind,"'"})
#    return
#  end
#
#  hdl_paths = m_hdl_paths_pool.get(kind)
#
#  for (int i=0; i<hdl_paths.size();i++):
#     uvm_hdl_path_concat t = hdl_paths.get(i)
#     paths.push_back(t)
#  end
#
#endfunction
#
#
#// get_hdl_path_kinds
#
#function void uvm_mem::get_hdl_path_kinds (ref string kinds[$])
#  string kind
#  kinds.delete()
#  if (!m_hdl_paths_pool.first(kind))
#    return
#  do
#    kinds.push_back(kind)
#  while (m_hdl_paths_pool.next(kind))
#endfunction
#
#
#
#// set_parent
#
#function void uvm_mem::set_parent(uvm_reg_block parent)
#  m_parent = parent
#endfunction
#
#
#
#
#// convert2string
#
#function string uvm_mem::convert2string()
#
#   string res_str
#   string prefix
#
#   $sformat(convert2string, "%sMemory %s -- %0dx%0d bits", prefix,
#            get_full_name(), get_size(), get_n_bits())
#
#   if (m_maps.num()==0)
#     convert2string = {convert2string, "  (unmapped)\n"}
#   else
#     convert2string = {convert2string, "\n"}
#   foreach (m_maps[map]):
#     uvm_reg_map parent_map = map
#     int unsigned offset
#     while (parent_map != None):
#       uvm_reg_map this_map = parent_map
#       uvm_endianness_e endian_name
#       parent_map = this_map.get_parent_map()
#       endian_name=this_map.get_endian()
#
#       offset = parent_map is None ? this_map.get_base_addr(UVM_NO_HIER) :
#                                     parent_map.get_submap_offset(this_map)
#       prefix = {prefix, "  "}
#       $sformat(convert2string, "%sMapped in '%s' -- buswidth %0d bytes, %s, offset 'h%0h, size 'h%0h, %s\n", prefix,
#            this_map.get_full_name(), this_map.get_n_bytes(), endian_name.name(), offset,get_size(),get_access(this_map))
#     end
#   end
#   prefix = "  "
#   if (m_read_in_progress == 1'b1):
#      if (m_fname != "" && m_lineno != 0)
#         $sformat(res_str, "%s:%0d ",m_fname, m_lineno)
#      convert2string = {convert2string, "  ", res_str,
#                       "currently executing read method"};
#   end
#   if ( m_write_in_progress == 1'b1):
#      if (m_fname != "" && m_lineno != 0)
#         $sformat(res_str, "%s:%0d ",m_fname, m_lineno)
#      convert2string = {convert2string, "  ", res_str,
#                       "currently executing write method"};
#   end
#endfunction
#
#
#// do_print
#
#function void uvm_mem::do_print (uvm_printer printer)
#  super.do_print(printer)
#  //printer.print_generic(" ", " ", -1, convert2string())
#  printer.print_field_int("n_bits",get_n_bits(),32, UVM_UNSIGNED)
#  printer.print_field_int("size",get_size(),32, UVM_UNSIGNED)
#endfunction
#
#
#// clone
#
#function uvm_object uvm_mem::clone()
#  `uvm_fatal("RegModel","RegModel memories cannot be cloned")
#  return None
#endfunction
#
#// do_copy
#
#function void uvm_mem::do_copy(uvm_object rhs)
#  `uvm_fatal("RegModel","RegModel memories cannot be copied")
#endfunction
#
#
#// do_compare
#
#function bit uvm_mem::do_compare (uvm_object  rhs,
#                                        uvm_comparer comparer)
#  `uvm_warning("RegModel","RegModel memories cannot be compared")
#  return 0
#endfunction
#
#
#// do_pack
#
#function void uvm_mem::do_pack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel memories cannot be packed")
#endfunction
#
#
#// do_unpack
#
#function void uvm_mem::do_unpack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel memories cannot be unpacked")
#endfunction
#
#
#
#
#// Xdelete_vregX
#
#function void uvm_mem::Xdelete_vregX(uvm_vreg vreg)
#   if (m_vregs.exists(vreg))
#     m_vregs.delete(vreg)
#endfunction
#
#
