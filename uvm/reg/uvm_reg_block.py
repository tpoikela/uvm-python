#
# -------------------------------------------------------------
#    Copyright 2004-2011 Synopsys, Inc.
#    Copyright 2010-2011 Mentor Graphics Corporation
#    Copyright 2010-2011 Cadence Design Systems, Inc.
#    Copyright 2019 Tuomas Poikela
#    All Rights Reserved Worldwide
#
#    Licensed under the Apache License, Version 2.0 (the
#    "License"); you may not use this file except in
#    compliance with the License.  You may obtain a copy of
#    the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in
#    writing, software distributed under the License is
#    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#    CONDITIONS OF ANY KIND, either express or implied.  See
#    the License for the specific language governing
#    permissions and limitations under the License.
#
#    Original SV code has been adapter to Python.
# -------------------------------------------------------------

from ..base.uvm_object import UVMObject
from ..base.uvm_pool import *
from .uvm_reg_model import *
from .uvm_reg_map import UVMRegMap
from .uvm_mem import UVMMem
from .uvm_reg_field import UVMRegField
from .uvm_reg import UVMReg
from ..macros import (uvm_error, uvm_warning, uvm_fatal, UVM_REG_DATA_WIDTH)

#------------------------------------------------------------------------
# Class: uvm_reg_block
#
# Block abstraction base class
#
# A block represents a design hierarchy. It can contain registers,
# register files, memories and sub-blocks.
#
# A block has one or more address maps, each corresponding to a physical
# interface on the block.
#
#------------------------------------------------------------------------

ERR_MSG1 = "There are %0d root register models named %s. The names of the root register models have to be unique"

ERR_MSG3 = "Register model requires that UVM_REG_DATA_WIDTH be defined as %0d or greater. Currently defined as %0d"

class UVMRegBlock(UVMObject):
    m_roots = {}  # static bit[uvm_reg_block]
    id = 0
    #   local int unsigned   blks[uvm_reg_block]
    #   local int unsigned   vregs[uvm_vreg]
    #   local int unsigned   mems[uvm_mem]
    #
    #   // Variable: default_path
    #   // Default access path for the registers and memories in this block.
    #   uvm_path_e      default_path = UVM_DEFAULT_PATH
    #
    #   local uvm_object_string_pool #(uvm_queue #(string)) hdl_paths_pool
    #   local string         root_hdl_paths[string]
    #
    #   local int            has_cover
    #   local int            cover_on
    #   local string         fname
    #   local int            lineno
    #
    #
    #   //----------------------
    #   // Group: Initialization
    #   //----------------------
    #
    #   // Function: new
    #   //
    #   // Create a new instance and type-specific configuration
    #   //
    #   // Creates an instance of a block abstraction class with the specified
    #   // name.
    #   //
    #   // ~has_coverage~ specifies which functional coverage models are present in
    #   // the extension of the block abstraction class.
    #   // Multiple functional coverage models may be specified by adding their
    #   // symbolic names, as defined by the <uvm_coverage_model_e> type.
    #   //
    #   function new(string name="", int has_coverage=UVM_NO_COVERAGE)
    def __init__(self, name="", has_coverage=UVM_NO_COVERAGE):
        UVMObject.__init__(self, name)
        self.hdl_paths_pool = UVMObjectStringPool("hdl_paths")
        self.has_cover = has_coverage
        # Root block until registered with a parent
        UVMRegBlock.m_roots[self] = 0
        self.locked = False
        self.maps = UVMPool()  # bit[UVMRegMap]
        self.regs = UVMPool()  #int unsigned[uvm_reg]
        self.blks = UVMPool()
        self.mems = UVMPool()
        self.root_hdl_paths = UVMPool()
        self.backdoor = None
        self.default_hdl_path = "RTL"
        self.parent = None
        self.default_path = UVM_DEFAULT_PATH

    #
    #   // Function: configure
    #   //
    #   // Instance-specific configuration
    #   //
    #   // Specify the parent block of this block.
    #   // A block without parent is a root block.
    #   //
    #   // If the block file corresponds to a hierarchical RTL structure,
    #   // its contribution to the HDL path is specified as the ~hdl_path~.
    #   // Otherwise, the block does not correspond to a hierarchical RTL
    #   // structure (e.g. it is physically flattened) and does not contribute
    #   // to the hierarchical HDL path of any contained registers or memories.
    #   //
    #   extern function void configure(uvm_reg_block parent=null,
    #                                  string hdl_path="")


    #   // Function: create_map
    #   //
    #   // Create an address map in this block
    #   //
    #   // Create an address map with the specified ~name~, then
    #   // configures it with the following properties.
    #   //
    #   // base_addr - the base address for the map. All registers, memories,
    #   //             and sub-blocks within the map will be at offsets to this
    #   //             address
    #   //
    #   // n_bytes   - the byte-width of the bus on which this map is used
    #   //
    #   // endian    - the endian format. See <uvm_endianness_e> for possible
    #   //             values
    #   //
    #   // byte_addressing - specifies whether consecutive addresses refer are 1 byte
    #   //             apart (TRUE) or ~n_bytes~ apart (FALSE). Default is TRUE.
    #   //
    #   //| APB = create_map("APB", 0, 1, UVM_LITTLE_ENDIAN, 1)
    #   //
    #   extern virtual function UVMRegMap create_map(string name,
    #                                                  uvm_reg_addr_t base_addr,
    #                                                  int unsigned n_bytes,
    #                                                  uvm_endianness_e endian,
    #                                                  bit byte_addressing = 1)
    def create_map(self, name, base_addr, n_bytes, endian,
            byte_addressing=True):
        #   UVMRegMap  map
        if self.locked is True:
            uvm_error("RegModel", "Cannot add map to locked model")
            return None

        _map = UVMRegMap.type_id.create(name, None, self.get_full_name())
        _map.configure(self,base_addr,n_bytes,endian,byte_addressing)

        self.maps[_map] = True
        if self.maps.num() == 1:
            self.default_map = _map
        return _map
    #endfunction

    #   // Function: check_data_width
    #   //
    #   // Check that the specified data width (in bits) is less than
    #   // or equal to the value of `UVM_REG_DATA_WIDTH
    #   //
    #   // This method is designed to be called by a static initializer
    #   //
    #   //| class my_blk extends uvm_reg_block
    #   //|   local static bit m_data_width = check_data_width(356)
    #   //|   ...
    #   //| endclass
    #   //
    #   extern protected static function bit check_data_width(int unsigned width)

    #   // Function: set_default_map
    #   //
    #   // Defines the default address map
    #   //
    #   // Set the specified address map as the <default_map> for this
    #   // block. The address map must be a map of this address block.
    #   //
    #   extern function void set_default_map (UVMRegMap map)


    #   // Variable: default_map
    #   //
    #   // Default address map
    #   //
    #   // Default address map for this block, to be used when no
    #   // address map is specified for a register operation and that
    #   // register is accessible from more than one address map.
    #   //
    #   // It is also the implicit address map for a block with a single,
    #   // unnamed address map because it has only one physical interface.
    #   //
    #   UVMRegMap default_map

    #
    #   extern function UVMRegMap get_default_map ()
    #

    #   extern virtual function void set_parent(uvm_reg_block parent)

    #
    #   /*local*/ extern function void add_block (uvm_reg_block blk)

    #   /*local*/ extern function void add_map   (UVMRegMap map)

    # add_reg
    def add_reg(self, rg):
        if self.is_locked():
            uvm_report_error("RegModel", "Cannot add register to locked block model")
            return

        if rg in self.regs:
            uvm_report_error("RegModel", ("Register '" + rg.get_name()
              + "' has already been registered with block '"
              + self.get_name() + "'"))
            return

        self.regs[rg] = UVMRegBlock.id
        UVMRegBlock.id += 1

    #   /*local*/ extern function void add_vreg  (uvm_vreg vreg)

    #   /*local*/ extern function void add_mem   (uvm_mem  mem)

    #   // Function: lock_model
    #   //
    #   // Lock a model and build the address map.
    #   //
    #   // Recursively lock an entire register model
    #   // and build the address maps to enable the
    #   // <UVMRegMap::get_reg_by_offset()> and
    #   // <UVMRegMap::get_mem_by_offset()> methods.
    #   //
    #   // Once locked, no further structural changes,
    #   // such as adding registers or memories,
    #   // can be made.
    #   //
    #   // It is not possible to unlock a model.
    #   //
    #   extern virtual function void lock_model()
    def lock_model(self):
        if self.is_locked():
            return
        self.locked = 1

        for rr in self.regs.key_list():
            rr.Xlock_modelX()

        for mem in self.mems.key_list():
            mem.Xlock_modelX()

        for blk in self.blks.key_list():
            blk.lock_model()

        # TODO finish this
        if (self.parent is None):
            max_size = UVMReg.get_max_size()
            if (UVMRegField.get_max_size() > max_size):
                max_size = UVMRegField.get_max_size()

            if (UVMMem.get_max_size() > max_size):
                max_size = UVMMem.get_max_size()

            if (max_size > UVM_REG_DATA_WIDTH):
                uvm_fatal("RegModel", sv.sformatf(ERR_MSG3, max_size, UVM_REG_DATA_WIDTH))

            self.Xinit_address_mapsX()

            # Check that root register models have unique names

            # Has this name has been checked before?
            if (UVMRegBlock.m_roots[self] != 1):
                n = 0
                #foreach (UVMRegBlock.m_roots[_blk]):
                for _blk in UVMRegBlock.m_roots:
                    blk = _blk  # uvm_reg_block
                    if (blk.get_name() == self.get_name()):
                        UVMRegBlock.m_roots[blk] = 1
                        n += 1

                if (n > 1):
                    uvm_error("UVM/REG/DUPLROOT", sv.sformatf(ERR_MSG1, n, self.get_name()))
        #
        #endfunction: lock_model

    #   // Function: is_locked
    #   //
    #   // Return TRUE if the model is locked.
    #   //
    def is_locked(self):
        return self.locked

    #   //---------------------
    #   // Group: Introspection
    #   //---------------------
    #
    #
    #   // Function: get_name
    #   //
    #   // Get the simple name
    #   //
    #   // Return the simple object name of this block.
    #   //
    #
    #
    #   // Function: get_full_name
    #   //
    #   // Get the hierarchical name
    #   //
    #   // Return the hierarchal name of this block.
    #   // The base of the hierarchical name is the root block.
    #   //
    #   extern virtual function string get_full_name()
    def get_full_name(self):
        if (self.parent is None):
            return self.get_name()

        return self.parent.get_full_name() + "." + self.get_name()
        #endfunction: get_full_name


    #   // Function: get_parent
    #   //
    #   // Get the parent block
    #   //
    #   // If this a top-level block, returns ~null~.
    #   //
    #   extern virtual function uvm_reg_block get_parent()
    def get_parent(self):
        return self.parent

    #
    #
    #   // Function: get_root_blocks
    #   //
    #   // Get the all root blocks
    #   //
    #   // Returns an array of all root blocks in the simulation.
    #   //
    #   extern static  function void get_root_blocks(ref uvm_reg_block blks[$])


    #   // Function: find_blocks
    #   //
    #   // Find the blocks whose hierarchical names match the
    #   // specified ~name~ glob.
    #   // If a ~root~ block is specified, the name of the blocks are
    #   // relative to that block, otherwise they are absolute.
    #   //
    #   // Returns the number of blocks found.
    #   //
    #   extern static function int find_blocks(input string        name,
    #                                          ref   uvm_reg_block blks[$],
    #                                          input uvm_reg_block root = null,
    #                                          input uvm_object    accessor = null)
    #
    #
    #   // Function: find_block
    #   //
    #   // Find the first block whose hierarchical names match the
    #   // specified ~name~ glob.
    #   // If a ~root~ block is specified, the name of the blocks are
    #   // relative to that block, otherwise they are absolute.
    #   //
    #   // Returns the first block found or ~null~ otherwise.
    #   // A warning is issued if more than one block is found.
    #   //
    #   extern static function uvm_reg_block find_block(input string        name,
    #                                                   input uvm_reg_block root = null,
    #                                                   input uvm_object    accessor = null)
    #
    #

    #   // Function: get_blocks
    #   //
    #   // Get the sub-blocks
    #   //
    #   // Get the blocks instantiated in this blocks.
    #   // If ~hier~ is TRUE, recursively includes any sub-blocks.
    #   //
    #   extern virtual function void get_blocks (ref uvm_reg_block  blks[$],
    #                                            input uvm_hier_e hier=UVM_HIER)
    def get_blocks(self, blks, hier=UVM_HIER):
        for blk_ in self.blks.key_list():
            blk = blk_
            blks.append(blk)
            if (hier == UVM_HIER):
                blk.get_blocks(blks)
        #endfunction: get_blocks

    #
    #

    #   // Function: get_maps
    #   //
    #   // Get the address maps
    #   //
    #   // Get the address maps instantiated in this block.
    #   //
    #   extern virtual function void get_maps (ref UVMRegMap maps[$])
    def get_maps(self, maps):
        for key in self.maps.key_list():
            maps.append(key)

    #
    #
    #   // Function: get_registers
    #   //
    #   // Get the registers
    #   //
    #   // Get the registers instantiated in this block.
    #   // If ~hier~ is TRUE, recursively includes the registers
    #   // in the sub-blocks.
    #   //
    #   // Note that registers may be located in different and/or multiple
    #   // address maps. To get the registers in a specific address map,
    #   // use the <UVMRegMap::get_registers()> method.
    #   //
    #   extern virtual function void get_registers (ref uvm_reg regs[$],
    #                                               input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_fields
    #   //
    #   // Get the fields
    #   //
    #   // Get the fields in the registers instantiated in this block.
    #   // If ~hier~ is TRUE, recursively includes the fields of the registers
    #   // in the sub-blocks.
    #   //
    #   extern virtual function void get_fields (ref uvm_reg_field  fields[$],
    #                                            input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_memories
    #   //
    #   // Get the memories
    #   //
    #   // Get the memories instantiated in this block.
    #   // If ~hier~ is TRUE, recursively includes the memories
    #   // in the sub-blocks.
    #   //
    #   // Note that memories may be located in different and/or multiple
    #   // address maps. To get the memories in a specific address map,
    #   // use the <UVMRegMap::get_memories()> method.
    #   //
    #   extern virtual function void get_memories (ref uvm_mem mems[$],
    #                                              input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_virtual_registers
    #   //
    #   // Get the virtual registers
    #   //
    #   // Get the virtual registers instantiated in this block.
    #   // If ~hier~ is TRUE, recursively includes the virtual registers
    #   // in the sub-blocks.
    #   //
    #   extern virtual function void get_virtual_registers(ref uvm_vreg regs[$],
    #                                                input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_virtual_fields
    #   //
    #   // Get the virtual fields
    #   //
    #   // Get the virtual fields from the virtual registers instantiated
    #   // in this block.
    #   // If ~hier~ is TRUE, recursively includes the virtual fields
    #   // in the virtual registers in the sub-blocks.
    #   //
    #   extern virtual function void get_virtual_fields (ref uvm_vreg_field fields[$],
    #                                                 input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_block_by_name
    #   //
    #   // Finds a sub-block with the specified simple name.
    #   //
    #   // The name is the simple name of the block, not a hierarchical name.
    #   // relative to this block.
    #   // If no block with that name is found in this block, the sub-blocks
    #   // are searched for a block of that name and the first one to be found
    #   // is returned.
    #   //
    #   // If no blocks are found, returns ~null~.
    #   //
    #   extern virtual function uvm_reg_block get_block_by_name (string name);
    #
    #
    #   // Function: get_map_by_name
    #   //
    #   // Finds an address map with the specified simple name.
    #   //
    #   // The name is the simple name of the address map, not a hierarchical name.
    #   // relative to this block.
    #   // If no map with that name is found in this block, the sub-blocks
    #   // are searched for a map of that name and the first one to be found
    #   // is returned.
    #   //
    #   // If no address maps are found, returns ~null~.
    #   //
    #   extern virtual function UVMRegMap get_map_by_name (string name)
    #
    #
    #   // Function: get_reg_by_name
    #   //
    #   // Finds a register with the specified simple name.
    #   //
    #   // The name is the simple name of the register, not a hierarchical name.
    #   // relative to this block.
    #   // If no register with that name is found in this block, the sub-blocks
    #   // are searched for a register of that name and the first one to be found
    #   // is returned.
    #   //
    #   // If no registers are found, returns ~null~.
    #   //
    #   extern virtual function uvm_reg get_reg_by_name (string name)
    def get_reg_by_name(self, name):

        for rg in self.regs.key_list():
            if rg.get_name() == name:
                return rg

        for blk_ in self.blks.key_list():
            # blk = blk_  # uvm_reg_block
            subregs = []  # uvm_reg[$]
            blk_.get_registers(subregs, UVM_HIER)

            for j in range(len(subregs)):
                if subregs[j].get_name() == name:
                    return subregs[j]

        uvm_warning("RegModel", "Unable to locate register '" + name +
                        "' in block '" + self.get_full_name() + "'")
        return None
        #endfunction: get_reg_by_name


    #   // Function: get_field_by_name
    #   //
    #   // Finds a field with the specified simple name.
    #   //
    #   // The name is the simple name of the field, not a hierarchical name.
    #   // relative to this block.
    #   // If no field with that name is found in this block, the sub-blocks
    #   // are searched for a field of that name and the first one to be found
    #   // is returned.
    #   //
    #   // If no fields are found, returns ~null~.
    #   //
    #   extern virtual function uvm_reg_field get_field_by_name (string name)
    #
    #
    #   // Function: get_mem_by_name
    #   //
    #   // Finds a memory with the specified simple name.
    #   //
    #   // The name is the simple name of the memory, not a hierarchical name.
    #   // relative to this block.
    #   // If no memory with that name is found in this block, the sub-blocks
    #   // are searched for a memory of that name and the first one to be found
    #   // is returned.
    #   //
    #   // If no memories are found, returns ~null~.
    #   //
    #   extern virtual function uvm_mem get_mem_by_name (string name)
    #
    #
    #   // Function: get_vreg_by_name
    #   //
    #   // Finds a virtual register with the specified simple name.
    #   //
    #   // The name is the simple name of the virtual register,
    #   // not a hierarchical name.
    #   // relative to this block.
    #   // If no virtual register with that name is found in this block,
    #   // the sub-blocks are searched for a virtual register of that name
    #   // and the first one to be found is returned.
    #   //
    #   // If no virtual registers are found, returns ~null~.
    #   //
    #   extern virtual function uvm_vreg get_vreg_by_name (string name)
    #
    #
    #   // Function: get_vfield_by_name
    #   //
    #   // Finds a virtual field with the specified simple name.
    #   //
    #   // The name is the simple name of the virtual field,
    #   // not a hierarchical name.
    #   // relative to this block.
    #   // If no virtual field with that name is found in this block,
    #   // the sub-blocks are searched for a virtual field of that name
    #   // and the first one to be found is returned.
    #   //
    #   // If no virtual fields are found, returns ~null~.
    #   //
    #   extern virtual function uvm_vreg_field get_vfield_by_name (string name)
    #
    #
    #   //----------------
    #   // Group: Coverage
    #   //----------------
    #
    #
    #   // Function: build_coverage
    #   //
    #   // Check if all of the specified coverage model must be built.
    #   //
    #   // Check which of the specified coverage model must be built
    #   // in this instance of the block abstraction class,
    #   // as specified by calls to <uvm_reg::include_coverage()>.
    #   //
    #   // Models are specified by adding the symbolic value of individual
    #   // coverage model as defined in <uvm_coverage_model_e>.
    #   // Returns the sum of all coverage models to be built in the
    #   // block model.
    #   //
    #   extern protected function uvm_reg_cvr_t build_coverage(uvm_reg_cvr_t models)
    #
    #
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
    #
    #
    #   // Function: has_coverage
    #   //
    #   // Check if block has coverage model(s)
    #   //
    #   // Returns TRUE if the block abstraction class contains a coverage model
    #   // for all of the models specified.
    #   // Models are specified by adding the symbolic value of individual
    #   // coverage model as defined in <uvm_coverage_model_e>.
    #   //
    #   extern virtual function bit has_coverage(uvm_reg_cvr_t models)
    #
    #
    #   // Function: set_coverage
    #   //
    #   // Turns on coverage measurement.
    #   //
    #   // Turns the collection of functional coverage measurements on or off
    #   // for this block and all blocks, registers, fields and memories within it.
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
    #   // coverage models that are present in the various abstraction classes,
    #   // then enabled during construction.
    #   // See the <uvm_reg_block::has_coverage()> method to identify
    #   // the available functional coverage models.
    #   //
    #   extern virtual function uvm_reg_cvr_t set_coverage(uvm_reg_cvr_t is_on)
    #
    #
    #   // Function: get_coverage
    #   //
    #   // Check if coverage measurement is on.
    #   //
    #   // Returns TRUE if measurement for all of the specified functional
    #   // coverage models are currently on.
    #   // Multiple functional coverage models can be specified by adding the
    #   // functional coverage model identifiers.
    #   //
    #   // See <uvm_reg_block::set_coverage()> for more details.
    #   //
    #   extern virtual function bit get_coverage(uvm_reg_cvr_t is_on = UVM_CVR_ALL)
    #
    #
    #   // Function: sample
    #   //
    #   // Functional coverage measurement method
    #   //
    #   // This method is invoked by the block abstraction class
    #   // whenever an address within one of its address map
    #   // is successfully read or written.
    #   // The specified offset is the offset within the block,
    #   // not an absolute address.
    #   //
    #   // Empty by default, this method may be extended by the
    #   // abstraction class generator to perform the required sampling
    #   // in any provided functional coverage model.
    #   //
    #   protected virtual function void  sample(uvm_reg_addr_t offset,
    #                                           bit            is_read,
    #                                           UVMRegMap    map)
    #   endfunction
    #
    #
    #   // Function: sample_values
    #   //
    #   // Functional coverage measurement method for field values
    #   //
    #   // This method is invoked by the user
    #   // or by the <uvm_reg_block::sample_values()> method of the parent block
    #   // to trigger the sampling
    #   // of the current field values in the
    #   // block-level functional coverage model.
    #   // It recursively invokes the <uvm_reg_block::sample_values()>
    #   // and <uvm_reg::sample_values()> methods
    #   // in the blocks and registers in this block.
    #   //
    #   // This method may be extended by the
    #   // abstraction class generator to perform the required sampling
    #   // in any provided field-value functional coverage model.
    #   // If this method is extended, it MUST call super.sample_values().
    #   //
    #   extern virtual function void sample_values()
    #
    #   /*local*/ extern function void XsampleX(uvm_reg_addr_t addr,
    #                                           bit            is_read,
    #                                           UVMRegMap    map)
    #
    #
    #   //--------------
    #   // Group: Access
    #   //--------------
    #

    #   // Function: get_default_path
    #   //
    #   // Default access path
    #   //
    #   // Returns the default access path for this block.
    #   //
    #   extern virtual function uvm_path_e get_default_path()
    def get_default_path(self):
        if (self.default_path != UVM_DEFAULT_PATH):
            return self.default_path
        if (self.parent is not None):
            return self.parent.get_default_path()
        return UVM_FRONTDOOR
        #endfunction


    #   // Function: reset
    #   //
    #   // Reset the mirror for this block.
    #   //
    #   // Sets the mirror value of all registers in the block and sub-blocks
    #   // to the reset value corresponding to the specified reset event.
    #   // See <uvm_reg_field::reset()> for more details.
    #   // Does not actually set the value of the registers in the design,
    #   // only the values mirrored in their corresponding mirror.
    #   //
    #   extern virtual function void reset(string kind = "HARD")
    def reset(self, kind="HARD"):
        #
        for rg_ in self.regs.key_list():
            rg = rg_
            rg.reset(kind)

        for blk_ in self.blks.key_list():
            blk = blk_  # uvm_reg_block
            blk.reset(kind)
        #endfunction

    #
    #
    #   // Function: needs_update
    #   //
    #   // Check if DUT registers need to be written
    #   //
    #   // If a mirror value has been modified in the abstraction model
    #   // without actually updating the actual register
    #   // (either through randomization or via the <uvm_reg::set()> method,
    #   // the mirror and state of the registers are outdated.
    #   // The corresponding registers in the DUT need to be updated.
    #   //
    #   // This method returns TRUE if the state of at least one register in
    #   // the block or sub-blocks needs to be updated to match the mirrored
    #   // values.
    #   // The mirror values, or actual content of registers, are not modified.
    #   // For additional information, see <uvm_reg_block::update()> method.
    #   //
    #   extern virtual function bit needs_update()
    #
    #
    #   // Task: update
    #   //
    #   // Batch update of register.
    #   //
    #   // Using the minimum number of write operations, updates the registers
    #   // in the design to match the mirrored values in this block and sub-blocks.
    #   // The update can be performed using the physical
    #   // interfaces (front-door access) or back-door accesses.
    #   // This method performs the reverse operation of <uvm_reg_block::mirror()>.
    #   //
    #   extern virtual task update(output uvm_status_e       status,
    #                              input  uvm_path_e         path = UVM_DEFAULT_PATH,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #
    #   // Task: mirror
    #   //
    #   // Update the mirrored values
    #   //
    #   // Read all of the registers in this block and sub-blocks and update their
    #   // mirror values to match their corresponding values in the design.
    #   // The mirroring can be performed using the physical interfaces
    #   // (front-door access) or back-door accesses.
    #   // If the ~check~ argument is specified as <UVM_CHECK>,
    #   // an error message is issued if the current mirrored value
    #   // does not match the actual value in the design.
    #   // This method performs the reverse operation of <uvm_reg_block::update()>.
    #   //
    #   extern virtual task mirror(output uvm_status_e       status,
    #                              input  uvm_check_e        check = UVM_NO_CHECK,
    #                              input  uvm_path_e         path  = UVM_DEFAULT_PATH,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #
    #   // Task: write_reg_by_name
    #   //
    #   // Write the named register
    #   //
    #   // Equivalent to <get_reg_by_name()> followed by <uvm_reg::write()>
    #   //
    #   extern virtual task write_reg_by_name(
    #                              output uvm_status_e        status,
    #                              input  string              name,
    #                              input  uvm_reg_data_t      data,
    #                              input  uvm_path_e     path = UVM_DEFAULT_PATH,
    #                              input  UVMRegMap         map = null,
    #                              input  uvm_sequence_base   parent = null,
    #                              input  int                 prior = -1,
    #                              input  uvm_object          extension = null,
    #                              input  string              fname = "",
    #                              input  int                 lineno = 0)
    #
    #
    #   // Task: read_reg_by_name
    #   //
    #   // Read the named register
    #   //
    #   // Equivalent to <get_reg_by_name()> followed by <uvm_reg::read()>
    #   //
    #   extern virtual task read_reg_by_name(
    #                              output uvm_status_e       status,
    #                              input  string             name,
    #                              output uvm_reg_data_t     data,
    #                              input  uvm_path_e    path = UVM_DEFAULT_PATH,
    #                              input  UVMRegMap        map = null,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #
    #   // Task: write_mem_by_name
    #   //
    #   // Write the named memory
    #   //
    #   // Equivalent to <get_mem_by_name()> followed by <uvm_mem::write()>
    #   //
    #   extern virtual task write_mem_by_name(
    #                              output uvm_status_e       status,
    #                              input  string             name,
    #                              input  uvm_reg_addr_t     offset,
    #                              input  uvm_reg_data_t     data,
    #                              input  uvm_path_e    path = UVM_DEFAULT_PATH,
    #                              input  UVMRegMap        map = null,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #
    #   // Task: read_mem_by_name
    #   //
    #   // Read the named memory
    #   //
    #   // Equivalent to <get_mem_by_name()> followed by <uvm_mem::read()>
    #   //
    #   extern virtual task read_mem_by_name(
    #                              output uvm_status_e       status,
    #                              input  string             name,
    #                              input  uvm_reg_addr_t     offset,
    #                              output uvm_reg_data_t     data,
    #                              input  uvm_path_e    path = UVM_DEFAULT_PATH,
    #                              input  UVMRegMap        map = null,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #
    #   extern virtual task readmemh(string filename)
    #   extern virtual task writememh(string filename)
    #
    #
    #

    #   //----------------
    #   // Group: Backdoor
    #   //----------------

    #   // Function: get_backdoor
    #   //
    #   // Get the user-defined backdoor for all registers in this block
    #   //
    #   // Return the user-defined backdoor for all register in this
    #   // block and all sub-blocks -- unless overridden by a backdoor set
    #   // in a lower-level block or in the register itself.
    #   //
    #   // If ~inherited~ is TRUE, returns the backdoor of the parent block
    #   // if none have been specified for this block.
    #   //
    #   extern function uvm_reg_backdoor get_backdoor(bit inherited = 1)
    def get_backdoor(self, inherited=True):
        if (self.backdoor is None and inherited):
            blk = self.get_parent()
            while (blk is not None):
                bkdr = blk.get_backdoor()
                if (bkdr is not None):
                    return bkdr
                blk = blk.get_parent()
        return self.backdoor
        #endfunction: get_backdoor


    #   // Function: set_backdoor
    #   //
    #   // Set the user-defined backdoor for all registers in this block
    #   //
    #   // Defines the backdoor mechanism for all registers instantiated
    #   // in this block and sub-blocks, unless overridden by a definition
    #   // in a lower-level block or register.
    #   //
    #   extern function void set_backdoor (uvm_reg_backdoor bkdr,
    #                                      string fname = "",
    #                                      int lineno = 0)
    #
    #
    #   // Function:  clear_hdl_path
    #   //
    #   // Delete HDL paths
    #   //
    #   // Remove any previously specified HDL path to the block instance
    #   // for the specified design abstraction.
    #   //
    #   extern function void clear_hdl_path (string kind = "RTL")
    #
    #
    #   // Function:  add_hdl_path
    #   //
    #   // Add an HDL path
    #   //
    #   // Add the specified HDL path to the block instance for the specified
    #   // design abstraction. This method may be called more than once for the
    #   // same design abstraction if the block is physically duplicated
    #   // in the design abstraction
    #   //
    #   extern function void add_hdl_path (string path, string kind = "RTL")
    #
    #
    #   // Function:   has_hdl_path
    #   //
    #   // Check if a HDL path is specified
    #   //
    #   // Returns TRUE if the block instance has a HDL path defined for the
    #   // specified design abstraction. If no design abstraction is specified,
    #   // uses the default design abstraction specified for this block or
    #   // the nearest block ancestor with a specified default design abstraction.
    #   //
    #   extern function bit has_hdl_path (string kind = "")
    #
    #
    #   // Function:  get_hdl_path
    #   //
    #   // Get the incremental HDL path(s)
    #   //
    #   // Returns the HDL path(s) defined for the specified design abstraction
    #   // in the block instance.
    #   // Returns only the component of the HDL paths that corresponds to
    #   // the block, not a full hierarchical path
    #   //
    #   // If no design abstraction is specified, the default design abstraction
    #   // for this block is used.
    #   //
    #   extern function void get_hdl_path (ref string paths[$], input string kind = "")
    #
    #
    #   // Function:  get_full_hdl_path
    #   //
    #   // Get the full hierarchical HDL path(s)
    #   //
    #   // Returns the full hierarchical HDL path(s) defined for the specified
    #   // design abstraction in the block instance.
    #   // There may be more than one path returned even
    #   // if only one path was defined for the block instance, if any of the
    #   // parent components have more than one path defined for the same design
    #   // abstraction
    #   //
    #   // If no design abstraction is specified, the default design abstraction
    #   // for each ancestor block is used to get each incremental path.
    #   //
    #   extern function void get_full_hdl_path (ref string paths[$],
    #                                           input string kind = "",
    #                                           string separator = ".")
    #
    #
    #   // Function: set_default_hdl_path
    #   //
    #   // Set the default design abstraction
    #   //
    #   // Set the default design abstraction for this block instance.
    #   //
    #   extern function void   set_default_hdl_path (string kind)
    #
    #
    #   // Function:  get_default_hdl_path
    #   //
    #   // Get the default design abstraction
    #   //
    #   // Returns the default design abstraction for this block instance.
    #   // If a default design abstraction has not been explicitly set for this
    #   // block instance, returns the default design abstraction for the
    #   // nearest block ancestor.
    #   // Returns "" if no default design abstraction has been specified.
    #   //
    #   extern function string get_default_hdl_path ()
    #

    #   // Function: set_hdl_path_root
    #   //
    #   // Specify a root HDL path
    #   //
    #   // Set the specified path as the absolute HDL path to the block instance
    #   // for the specified design abstraction.
    #   // This absolute root path is prepended to all hierarchical paths
    #   // under this block. The HDL path of any ancestor block is ignored.
    #   // This method overrides any incremental path for the
    #   // same design abstraction specified using <add_hdl_path>.
    #   //
    #   extern function void set_hdl_path_root (string path, string kind = "RTL")
    # set_hdl_path_root
    def set_hdl_path_root(self, path, kind="RTL"):
        if (kind == ""):
            kind = self.get_default_hdl_path()
        self.root_hdl_paths[kind] = path

    #   // Function: is_hdl_path_root
    #   //
    #   // Check if this block has an absolute path
    #   //
    #   // Returns TRUE if an absolute HDL path to the block instance
    #   // for the specified design abstraction has been defined.
    #   // If no design abstraction is specified, the default design abstraction
    #   // for this block is used.
    #   //
    #   extern function bit is_hdl_path_root (string kind = "")
    #
    #
    #   extern virtual function void   do_print      (uvm_printer printer)
    #   extern virtual function void   do_copy       (uvm_object rhs)
    #   extern virtual function bit    do_compare    (uvm_object  rhs,
    #                                                 uvm_comparer comparer)
    #   extern virtual function void   do_pack       (uvm_packer packer)
    #   extern virtual function void   do_unpack     (uvm_packer packer)
    #   extern virtual function string convert2string ()
    #   extern virtual function uvm_object clone()
    #
    #   extern local function void Xinit_address_mapsX()
    #
    #endclass: uvm_reg_block

#------------------------------------------------------------------------
#
#---------------
# Initialization
#---------------
#
# check_data_width
#
#function bit uvm_reg_block::check_data_width(int unsigned width)
#   if (width <= $bits(uvm_reg_data_t)) return 1
#
#   `uvm_fatal("RegModel", $sformatf("Register model requires that UVM_REG_DATA_WIDTH be defined as %0d or greater. Currently defined as %0d", width, `UVM_REG_DATA_WIDTH))
#
#   return 0
#endfunction
#
#
# new
#
#
# configure
#
#function void uvm_reg_block::configure(uvm_reg_block parent=null, string hdl_path="")
#  self.parent = parent;
#  if (parent is not None)
#    self.parent.add_block(this)
#  add_hdl_path(hdl_path)
#
#  uvm_resource_db#(uvm_reg_block)::set("uvm_reg::*", get_full_name(), this)
#endfunction
#
#
# add_block
#
#function void uvm_reg_block::add_block (uvm_reg_block blk)
#   if (self.is_locked()):
#      `uvm_error("RegModel", "Cannot add subblock to locked block model")
#      return
#   end
#   if (self.blks.exists(blk)):
#      `uvm_error("RegModel", {"Subblock '",blk.get_name(),
#         "' has already been registered with block '",get_name(),"'"})
#       return
#   end
#   blks[blk] = UVMRegBlock.id
#   UVMRegBlock.id += 1
#   if (UVMRegBlock.m_roots.exists(blk)) UVMRegBlock.m_roots.delete(blk)
#endfunction
#
#
#
#
# add_vreg
#
#function void uvm_reg_block::add_vreg(uvm_vreg vreg)
#   if (self.is_locked()):
#      `uvm_error("RegModel", "Cannot add virtual register to locked block model")
#      return
#   end
#
#   if (self.vregs.exists(vreg)):
#      `uvm_error("RegModel", {"Virtual register '",vreg.get_name(),
#         "' has already been registered with block '",get_name(),"'"})
#       return
#   end
#   vregs[vreg] = UVMRegBlock.id
#   UVMRegBlock.id += 1
#endfunction: add_vreg
#
#
# add_mem
#
#function void uvm_reg_block::add_mem(uvm_mem mem)
#   if (self.is_locked()):
#      `uvm_error("RegModel", "Cannot add memory to locked block model")
#      return
#   end
#
#   if (self.mems.exists(mem)):
#      `uvm_error("RegModel", {"Memory '",mem.get_name(),
#         "' has already been registered with block '",get_name(),"'"})
#       return
#   end
#   mems[mem] = UVMRegBlock.id
#   UVMRegBlock.id += 1
#endfunction: add_mem
#
#
# set_parent
#
#function void uvm_reg_block::set_parent(uvm_reg_block parent)
#  if (this != parent)
#    self.parent = parent
#endfunction
#
#
#
#
#
#
#--------------------------
# Get Hierarchical Elements
#--------------------------
#
#
# get_fields
#
#function void uvm_reg_block::get_fields(ref uvm_reg_field fields[$],
#                                        input uvm_hier_e hier=UVM_HIER)
#
#   foreach (regs[rg_]):
#     uvm_reg rg = rg_
#     rg.get_fields(fields)
#   end
#
#   if (hier == UVM_HIER)
#     foreach (blks[blk_])
#     begin
#       uvm_reg_block blk = blk_
#       blk.get_fields(fields)
#     end
#
#endfunction: get_fields
#
#
# get_virtual_fields
#
#function void uvm_reg_block::get_virtual_fields(ref uvm_vreg_field fields[$],
#                                                input uvm_hier_e hier=UVM_HIER)
#
#   foreach (vregs[vreg_]):
#     uvm_vreg vreg = vreg_
#     vreg.get_fields(fields)
#   end
#
#   if (hier == UVM_HIER)
#     foreach (blks[blk_]):
#       uvm_reg_block blk = blk_
#       blk.get_virtual_fields(fields)
#     end
#endfunction: get_virtual_fields
#
#
# get_registers
#
#function void uvm_reg_block::get_registers(ref uvm_reg regs[$],
#                                           input uvm_hier_e hier=UVM_HIER)
#   foreach (self.regs[rg])
#     regs.push_back(rg)
#
#   if (hier == UVM_HIER)
#     foreach (blks[blk_]):
#       uvm_reg_block blk = blk_
#       blk.get_registers(regs)
#     end
#endfunction: get_registers
#
#
# get_virtual_registers
#
#function void uvm_reg_block::get_virtual_registers(ref uvm_vreg regs[$],
#                                                   input uvm_hier_e hier=UVM_HIER)
#
#   foreach (vregs[rg])
#     regs.push_back(rg)
#
#   if (hier == UVM_HIER)
#     foreach (blks[blk_]):
#       uvm_reg_block blk = blk_
#       blk.get_virtual_registers(regs)
#     end
#endfunction: get_virtual_registers
#
#
# get_memories
#
#function void uvm_reg_block::get_memories(ref uvm_mem mems[$],
#                                          input uvm_hier_e hier=UVM_HIER)
#
#   foreach (self.mems[mem_]):
#     uvm_mem mem = mem_
#     mems.push_back(mem)
#   end
#
#   if (hier == UVM_HIER)
#     foreach (blks[blk_]):
#       uvm_reg_block blk = blk_
#       blk.get_memories(mems)
#     end
#
#endfunction: get_memories
#
#
#
#
# get_root_blocks
#
#function void uvm_reg_block::get_root_blocks(ref uvm_reg_block blks[$])
#
#   foreach (UVMRegBlock.m_roots[blk]):
#      blks.push_back(blk)
#   end
#
#endfunction: get_root_blocks
#
#
# find_blocks
#
#function int uvm_reg_block::find_blocks(input string        name,
#                                        ref   uvm_reg_block blks[$],
#                                        input uvm_reg_block root = null,
#                                        input uvm_object    accessor = null)
#
#   uvm_resource_pool rpl = uvm_resource_pool::get()
#   uvm_resource_types::rsrc_q_t rs
#
#   blks.delete()
#
#   if (root is not None) name = {root.get_full_name(), ".", name}
#
#   rs = rpl.lookup_regex(name, "uvm_reg::")
#   for (int i = 0; i < rs.size(); i++):
#      uvm_resource#(uvm_reg_block) blk
#      if (!$cast(blk, rs.get(i))) continue
#      blks.push_back(blk.read(accessor))
#   end
#
#   return blks.size()
#endfunction
#
#
# find_blocks
#
#function uvm_reg_block uvm_reg_block::find_block(input string        name,
#                                                 input uvm_reg_block root = null,
#                                                 input uvm_object    accessor = null)
#
#   uvm_reg_block blks[$]
#   if (!find_blocks(name, blks, root, accessor))
#      return null
#
#   if (blks.size() > 1):
#      `uvm_warning("MRTH1BLK",
#                   {"More than one block matched the name \"", name, "\"."})
#   end
#
#
#   return blks[0]
#endfunction
#
#
#
#------------
# Get-By-Name
#------------
#
# get_block_by_name
#
#function uvm_reg_block uvm_reg_block::get_block_by_name(string name)
#
#   if (get_name() == name)
#     return this
#
#   foreach (blks[blk_]):
#     uvm_reg_block blk = blk_
#
#     if (blk.get_name() == name)
#       return blk
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#      uvm_reg_block subblks[$]
#      blk_.get_blocks(subblks, UVM_HIER)
#
#      foreach (subblks[j])
#         if (subblks[j].get_name() == name)
#            return subblks[j]
#   end
#
#   `uvm_warning("RegModel", {"Unable to locate block '",name,
#                "' in block '",get_full_name(),"'"})
#   return null
#
#endfunction: get_block_by_name
#
#
#
#
# get_vreg_by_name
#
#function uvm_vreg uvm_reg_block::get_vreg_by_name(string name)
#
#   foreach (vregs[rg_]):
#     uvm_vreg rg = rg_
#     if (rg.get_name() == name)
#       return rg
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#      uvm_vreg subvregs[$]
#      blk_.get_virtual_registers(subvregs, UVM_HIER)
#
#      foreach (subvregs[j])
#         if (subvregs[j].get_name() == name)
#            return subvregs[j]
#   end
#
#   `uvm_warning("RegModel", {"Unable to locate virtual register '",name,
#                "' in block '",get_full_name(),"'"})
#   return null
#
#endfunction: get_vreg_by_name
#
#
# get_mem_by_name
#
#function uvm_mem uvm_reg_block::get_mem_by_name(string name)
#
#   foreach (mems[mem_]):
#     uvm_mem mem = mem_
#     if (mem.get_name() == name)
#       return mem
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#      uvm_mem submems[$]
#      blk_.get_memories(submems, UVM_HIER)
#
#      foreach (submems[j])
#         if (submems[j].get_name() == name)
#            return submems[j]
#   end
#
#   `uvm_warning("RegModel", {"Unable to locate memory '",name,
#                "' in block '",get_full_name(),"'"})
#   return null
#
#endfunction: get_mem_by_name
#
#
# get_field_by_name
#
#function uvm_reg_field uvm_reg_block::get_field_by_name(string name)
#
#   foreach (regs[rg_]):
#      uvm_reg rg = rg_
#      uvm_reg_field fields[$]
#
#      rg.get_fields(fields)
#      foreach (fields[i])
#        if (fields[i].get_name() == name)
#          return fields[i]
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#      uvm_reg subregs[$]
#      blk_.get_registers(subregs, UVM_HIER)
#
#      foreach (subregs[j]):
#         uvm_reg_field fields[$]
#         subregs[j].get_fields(fields)
#         foreach (fields[i])
#            if (fields[i].get_name() == name)
#               return fields[i]
#      end
#   end
#
#   `uvm_warning("RegModel", {"Unable to locate field '",name,
#                "' in block '",get_full_name(),"'"})
#
#   return null
#
#endfunction: get_field_by_name
#
#
# get_vfield_by_name
#
#function uvm_vreg_field uvm_reg_block::get_vfield_by_name(string name)
#
#   foreach (vregs[rg_]):
#      uvm_vreg rg =rg_
#      uvm_vreg_field fields[$]
#
#      rg.get_fields(fields)
#      foreach (fields[i])
#        if (fields[i].get_name() == name)
#          return fields[i]
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#      uvm_vreg subvregs[$]
#      blk_.get_virtual_registers(subvregs, UVM_HIER)
#
#      foreach (subvregs[j]):
#         uvm_vreg_field fields[$]
#         subvregs[j].get_fields(fields)
#         foreach (fields[i])
#            if (fields[i].get_name() == name)
#               return fields[i]
#      end
#   end
#
#   `uvm_warning("RegModel", {"Unable to locate virtual field '",name,
#                "' in block '",get_full_name(),"'"})
#
#   return null
#
#endfunction: get_vfield_by_name
#
#
#
#-------------
# Coverage API
#-------------
#
# set_coverage
#
#function uvm_reg_cvr_t uvm_reg_block::set_coverage(uvm_reg_cvr_t is_on)
#   self.cover_on = self.has_cover & is_on
#
#   foreach (regs[rg_]):
#     uvm_reg rg = rg_
#     void'(rg.set_coverage(is_on))
#   end
#
#   foreach (mems[mem_]):
#     uvm_mem mem = mem_
#     void'(mem.set_coverage(is_on))
#   end
#
#   foreach (blks[blk_]):
#     uvm_reg_block blk = blk_
#     void'(blk.set_coverage(is_on))
#   end
#
#   return self.cover_on
#endfunction: set_coverage
#
#
# sample_values
#
#function void uvm_reg_block::sample_values()
#   foreach (regs[rg_]):
#      uvm_reg rg = rg_
#      rg.sample_values()
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#      blk.sample_values()
#   end
#endfunction
#
#
# XsampleX
#
#function void uvm_reg_block::XsampleX(uvm_reg_addr_t addr,
#                                      bit            is_read,
#                                      UVMRegMap    map)
#   sample(addr, is_read, map)
#   if (parent is not None):
#      // ToDo: Call XsampleX in the parent block
#      //       with the offset and map within that block's context
#   end
#endfunction
#
#
#function uvm_reg_cvr_t uvm_reg_block::build_coverage(uvm_reg_cvr_t models)
#   build_coverage = UVM_NO_COVERAGE
#   void'(uvm_reg_cvr_rsrc_db::read_by_name({"uvm_reg::", get_full_name()},
#                                           "include_coverage",
#                                           build_coverage, this))
#   return build_coverage & models
#endfunction: build_coverage
#
#
# add_coverage
#
#function void uvm_reg_block::add_coverage(uvm_reg_cvr_t models)
#   self.has_cover |= models
#endfunction: add_coverage
#
#
# has_coverage
#
#function bit uvm_reg_block::has_coverage(uvm_reg_cvr_t models)
#   return ((self.has_cover & models) == models)
#endfunction: has_coverage
#
#
# get_coverage
#
#function bit uvm_reg_block::get_coverage(uvm_reg_cvr_t is_on = UVM_CVR_ALL)
#   if (self.has_coverage(is_on) == 0) return 0
#   return ((self.cover_on & is_on) == is_on)
#endfunction: get_coverage
#
#
#----------------
# Run-Time Access
#----------------
#
#
#
#
# needs_update
#
#function bit uvm_reg_block::needs_update()
#   needs_update = 0
#
#   foreach (regs[rg_]):
#     uvm_reg rg = rg_
#     if (rg.needs_update())
#       return 1
#   end
#   foreach (blks[blk_]):
#     uvm_reg_block blk =blk_
#     if (blk.needs_update())
#       return 1
#   end
#endfunction: needs_update
#
#
# update
#
#task uvm_reg_block::update(output uvm_status_e  status,
#                           input  uvm_path_e    path = UVM_DEFAULT_PATH,
#                           input  uvm_sequence_base  parent = null,
#                           input  int                prior = -1,
#                           input  uvm_object         extension = null,
#                           input  string             fname = "",
#                           input  int                lineno = 0)
#   status = UVM_IS_OK
#
#   if (!needs_update()):
#     `uvm_info("RegModel", $sformatf("%s:%0d - RegModel block %s does not need updating",
#                    fname, lineno, self.get_name()), UVM_HIGH)
#      return
#   end
#
#   `uvm_info("RegModel", $sformatf("%s:%0d - Updating model block %s with %s path",
#                    fname, lineno, self.get_name(), path.name ), UVM_HIGH)
#
#   foreach (regs[rg_]):
#      uvm_reg rg = rg_
#      if (rg.needs_update()):
#         rg.update(status, path, null, parent, prior, extension)
#         if (status != UVM_IS_OK && status != UVM_HAS_X):
#           `uvm_error("RegModel", $sformatf("Register \"%s\" could not be updated",
#                                        rg.get_full_name()))
#           return
#         end
#      end
#   end
#
#   foreach (blks[blk_]):
#     uvm_reg_block blk = blk_
#     blk.update(status,path,parent,prior,extension,fname,lineno)
#   end
#endtask: update
#
#
# mirror
#
#task uvm_reg_block::mirror(output uvm_status_e       status,
#                           input  uvm_check_e        check = UVM_NO_CHECK,
#                           input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                           input  uvm_sequence_base  parent = null,
#                           input  int                prior = -1,
#                           input  uvm_object         extension = null,
#                           input  string             fname = "",
#                           input  int                lineno = 0)
#   uvm_status_e final_status = UVM_IS_OK
#
#   foreach (regs[rg_]):
#      uvm_reg rg = rg_
#      rg.mirror(status, check, path, null,
#                parent, prior, extension, fname, lineno)
#      if (status != UVM_IS_OK && status != UVM_HAS_X):
#         final_status = status
#      end
#   end
#
#   foreach (blks[blk_]):
#      uvm_reg_block blk = blk_
#
#      blk.mirror(status, check, path, parent, prior, extension, fname, lineno)
#      if (status != UVM_IS_OK && status != UVM_HAS_X):
#         final_status = status
#      end
#   end
#
#endtask: mirror
#
#
# write_reg_by_name
#
#task uvm_reg_block::write_reg_by_name(output uvm_status_e   status,
#                                      input  string              name,
#                                      input  uvm_reg_data_t      data,
#                                      input  uvm_path_e     path = UVM_DEFAULT_PATH,
#                                      input  UVMRegMap      map = null,
#                                      input  uvm_sequence_base   parent = null,
#                                      input  int                 prior = -1,
#                                      input  uvm_object          extension = null,
#                                      input  string              fname = "",
#                                      input  int                 lineno = 0)
#   uvm_reg rg
#   self.fname = fname
#   self.lineno = lineno
#
#   status = UVM_NOT_OK
#   rg = self.get_reg_by_name(name)
#   if (rg is not None)
#     rg.write(status, data, path, map, parent, prior, extension)
#
#endtask: write_reg_by_name
#
#
# read_reg_by_name
#
#task uvm_reg_block::read_reg_by_name(output uvm_status_e  status,
#                                     input  string             name,
#                                     output uvm_reg_data_t     data,
#                                     input  uvm_path_e    path = UVM_DEFAULT_PATH,
#                                     input  UVMRegMap     map = null,
#                                     input  uvm_sequence_base  parent = null,
#                                     input  int                prior = -1,
#                                     input  uvm_object         extension = null,
#                                     input  string             fname = "",
#                                     input  int                lineno = 0)
#   uvm_reg rg
#   self.fname = fname
#   self.lineno = lineno
#
#   status = UVM_NOT_OK
#   rg = self.get_reg_by_name(name)
#   if (rg is not None)
#     rg.read(status, data, path, map, parent, prior, extension)
#endtask: read_reg_by_name
#
#
# write_mem_by_name
#
#task uvm_reg_block::write_mem_by_name(output uvm_status_e  status,
#                                          input  string             name,
#                                          input  uvm_reg_addr_t     offset,
#                                          input  uvm_reg_data_t     data,
#                                          input  uvm_path_e    path = UVM_DEFAULT_PATH,
#                                          input  UVMRegMap     map = null,
#                                          input  uvm_sequence_base  parent = null,
#                                          input  int                prior = -1,
#                                          input  uvm_object         extension = null,
#                                          input  string             fname = "",
#                                          input  int                lineno = 0)
#   uvm_mem mem
#   self.fname = fname
#   self.lineno = lineno
#
#   status = UVM_NOT_OK
#   mem = get_mem_by_name(name)
#   if (mem is not None)
#     mem.write(status, offset, data, path, map, parent, prior, extension)
#endtask: write_mem_by_name
#
#
# read_mem_by_name
#
#task uvm_reg_block::read_mem_by_name(output uvm_status_e  status,
#                                         input  string             name,
#                                         input  uvm_reg_addr_t     offset,
#                                         output uvm_reg_data_t     data,
#                                         input  uvm_path_e    path = UVM_DEFAULT_PATH,
#                                         input  UVMRegMap     map = null,
#                                         input  uvm_sequence_base  parent = null,
#                                         input  int                prior = -1,
#                                         input  uvm_object         extension = null,
#                                         input  string             fname = "",
#                                         input  int                lineno = 0)
#   uvm_mem mem
#   self.fname = fname
#   self.lineno = lineno
#
#   status = UVM_NOT_OK
#   mem = get_mem_by_name(name)
#   if (mem is not None)
#     mem.read(status, offset, data, path, map, parent, prior, extension)
#endtask: read_mem_by_name
#
#
# readmemh
#
#task uvm_reg_block::readmemh(string filename)
#   // TODO
#endtask: readmemh
#
#
# writememh
#
#task uvm_reg_block::writememh(string filename)
#   // TODO
#endtask: writememh
#
#
#---------------
# Map Management
#---------------
#
#
#
# add_map
#
#function void uvm_reg_block::add_map(UVMRegMap map)
#
#   if (self.locked):
#      `uvm_error("RegModel", "Cannot add map to locked model")
#      return
#   end
#
#   if (self.maps.exists(map)):
#      `uvm_error("RegModel", {"Map '",map.get_name(),
#                 "' already exists in '",get_full_name(),"'"})
#      return
#   end
#
#   self.maps[map] = 1
#   if (maps.num() == 1)
#     default_map = map
#
#endfunction: add_map
#
#
# get_map_by_name
#
#function UVMRegMap uvm_reg_block::get_map_by_name(string name)
#   UVMRegMap maps[$]
#
#   self.get_maps(maps)
#
#   foreach (maps[i])
#     if (maps[i].get_name() == name)
#       return maps[i]
#
#   foreach (maps[i]):
#      UVMRegMap submaps[$]
#      maps[i].get_submaps(submaps, UVM_HIER)
#
#      foreach (submaps[j])
#         if (submaps[j].get_name() == name)
#            return submaps[j]
#   end
#
#
#   `uvm_warning("RegModel", {"Map with name '",name,"' does not exist in block"})
#   return null
#endfunction
#
#
# set_default_map
#
#function void uvm_reg_block::set_default_map(UVMRegMap map)
#  if (!maps.exists(map))
#   `uvm_warning("RegModel", {"Map '",map.get_full_name(),"' does not exist in block"})
#  default_map = map
#endfunction
#
#
# get_default_map
#
#function UVMRegMap uvm_reg_block::get_default_map()
#  return default_map
#endfunction
#
#
#
# Xinit_address_mapsX
#
#function void uvm_reg_block::Xinit_address_mapsX()
#   foreach (maps[map_]):
#      UVMRegMap map = map_
#      map.Xinit_address_mapX()
#   end
#      //map.Xverify_map_configX()
#endfunction
#
#
#----------------
# Group- Backdoor
#----------------
#
# set_backdoor
#
#function void uvm_reg_block::set_backdoor(uvm_reg_backdoor bkdr,
#                                          string               fname = "",
#                                          int                  lineno = 0)
#   bkdr.fname = fname
#   bkdr.lineno = lineno
#   if (self.backdoor is not None &&
#       self.backdoor.has_update_threads()):
#      `uvm_warning("RegModel", "Previous register backdoor still has update threads running. Backdoors with active mirroring should only be set before simulation starts.")
#   end
#   self.backdoor = bkdr
#endfunction: set_backdoor
#
#
#
# clear_hdl_path
#
#function void uvm_reg_block::clear_hdl_path(string kind = "RTL")
#
#  if (kind == "ALL"):
#    hdl_paths_pool = new("hdl_paths")
#    return
#  end
#
#  if (kind == "")
#    kind = get_default_hdl_path()
#
#  if (!hdl_paths_pool.exists(kind)):
#    `uvm_warning("RegModel",{"Unknown HDL Abstraction '",kind,"'"})
#    return
#  end
#
#  hdl_paths_pool.delete(kind)
#endfunction
#
#
# add_hdl_path
#
#function void uvm_reg_block::add_hdl_path(string path, string kind = "RTL")
#
#  uvm_queue #(string) paths
#
#  paths = hdl_paths_pool.get(kind)
#
#  paths.push_back(path)
#
#endfunction
#
#
# has_hdl_path
#
#function bit  uvm_reg_block::has_hdl_path(string kind = "")
#  if (kind == ""):
#    kind = get_default_hdl_path()
#  end
#  return hdl_paths_pool.exists(kind)
#endfunction
#
#
# get_hdl_path
#
#function void uvm_reg_block::get_hdl_path(ref string paths[$], input string kind = "")
#
#  uvm_queue #(string) hdl_paths
#
#  if (kind == "")
#    kind = get_default_hdl_path()
#
#  if (!has_hdl_path(kind)):
#    `uvm_error("RegModel",{"Block does not have hdl path defined for abstraction '",kind,"'"})
#    return
#  end
#
#  hdl_paths = hdl_paths_pool.get(kind)
#
#  for (int i=0; i<hdl_paths.size();i++)
#    paths.push_back(hdl_paths.get(i))
#
#endfunction
#
#
# get_full_hdl_path
#
#function void uvm_reg_block::get_full_hdl_path(ref string paths[$],
#                                               input string kind = "",
#                                               string separator = ".")
#
#   if (kind == "")
#      kind = get_default_hdl_path()
#
#   paths.delete()
#   if (is_hdl_path_root(kind)):
#      if (root_hdl_paths[kind] != "")
#         paths.push_back(root_hdl_paths[kind])
#      return
#   end
#
#   if (!has_hdl_path(kind)):
#      `uvm_error("RegModel",{"Block does not have hdl path defined for abstraction '",kind,"'"})
#      return
#   end
#
#   begin
#      uvm_queue #(string) hdl_paths = hdl_paths_pool.get(kind)
#      string parent_paths[$]
#
#      if (parent is not None)
#         parent.get_full_hdl_path(parent_paths, kind, separator)
#
#      for (int i=0; i<hdl_paths.size();i++):
#         string hdl_path = hdl_paths.get(i)
#
#         if (parent_paths.size() == 0):
#            if (hdl_path != "")
#               paths.push_back(hdl_path)
#
#            continue
#         end
#
#         foreach (parent_paths[j])  begin
#            if (hdl_path == "")
#               paths.push_back(parent_paths[j])
#            else
#               paths.push_back({ parent_paths[j], separator, hdl_path })
#         end
#      end
#   end
#
#endfunction
#
#
# get_default_hdl_path
#
#function string uvm_reg_block::get_default_hdl_path()
#  if (default_hdl_path == "" && parent is not None)
#    return parent.get_default_hdl_path()
#  return default_hdl_path
#endfunction
#
#
# set_default_hdl_path
#
#function void uvm_reg_block::set_default_hdl_path(string kind)
#
#  if (kind == ""):
#    if (parent is None):
#      `uvm_error("RegModel",{"Block has no parent. ",
#           "Must specify a valid HDL abstraction (kind)"})
#    end
#    kind = parent.get_default_hdl_path()
#  end
#
#  default_hdl_path = kind
#endfunction
#
#
#
#
# is_hdl_path_root
#
#function bit  uvm_reg_block::is_hdl_path_root (string kind = "")
#  if (kind == "")
#    kind = get_default_hdl_path()
#
#  return root_hdl_paths.exists(kind)
#endfunction
#
#
#----------------------------------
# Group- Basic Object Operations
#----------------------------------
#
# do_print
#function void uvm_reg_block::do_print (uvm_printer printer)
#  super.do_print(printer)
#
#  foreach(blks[i]):
#     uvm_reg_block b = i
#     uvm_object obj = b
#     printer.print_object(obj.get_name(), obj)
#  end
#
#  foreach(regs[i]):
#     uvm_reg r = i
#     uvm_object obj = r
#     printer.print_object(obj.get_name(), obj)
#  end
#
#  foreach(vregs[i]):
#     uvm_vreg r = i
#     uvm_object obj = r
#     printer.print_object(obj.get_name(), obj)
#  end
#
#  foreach(mems[i]):
#     uvm_mem m = i
#     uvm_object obj = m
#     printer.print_object(obj.get_name(), obj)
#  end
#
#  foreach(maps[i]):
#     UVMRegMap m = i
#     uvm_object obj = m
#     printer.print_object(obj.get_name(), obj)
#  end
#
#endfunction
#
#
#
# clone
#
#function uvm_object uvm_reg_block::clone()
#  `uvm_fatal("RegModel","RegModel blocks cannot be cloned")
#  return null
#endfunction
#
# do_copy
#
#function void uvm_reg_block::do_copy(uvm_object rhs)
#  `uvm_fatal("RegModel","RegModel blocks cannot be copied")
#endfunction
#
#
# do_compare
#
#function bit uvm_reg_block::do_compare (uvm_object  rhs,
#                                        uvm_comparer comparer)
#  `uvm_warning("RegModel","RegModel blocks cannot be compared")
#  return 0
#endfunction
#
#
# do_pack
#
#function void uvm_reg_block::do_pack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel blocks cannot be packed")
#endfunction
#
#
# do_unpack
#
#function void uvm_reg_block::do_unpack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel blocks cannot be unpacked")
#endfunction
#
#
# convert2string
#
#function string uvm_reg_block::convert2string()
#   string image
#   string maps[]
#   string blk_maps[]
#   bit         single_map
#   uvm_endianness_e endian
#   string prefix = "  "
#
#`ifdef TODO
#   single_map = 1
#   if (map == ""):
#      self.get_maps(maps)
#      if (maps.size() > 1) single_map = 0
#   end
#
#   if (single_map):
#      $sformat(image, "%sBlock %s", prefix, self.get_full_name())
#
#      if (map != "")
#        $sformat(image, "%s.%s", image, map)
#
#      endian = self.get_endian(map)
#
#      $sformat(image, "%s -- %0d bytes (%s)", image,
#               self.get_n_bytes(map), endian.name())
#
#      foreach (blks[i]):
#         string img
#         img = blks[i].convert2string({prefix, "   "}, blk_maps[i])
#         image = {image, "\n", img}
#      end
#
#   end
#   else begin
#      $sformat(image, "%Block %s", prefix, self.get_full_name())
#      foreach (maps[i]):
#         string img
#         endian = self.get_endian(maps[i])
#         $sformat(img, "%s   Map \"%s\" -- %0d bytes (%s)",
#                  prefix, maps[i],
#                  self.get_n_bytes(maps[i]), endian.name())
#         image = {image, "\n", img}
#
#         self.get_blocks(blks, blk_maps, maps[i])
#         foreach (blks[j]):
#            img = blks[j].convert2string({prefix, "      "},
#                                    blk_maps[j])
#            image = {image, "\n", img}
#         end
#
#         self.get_subsys(sys, blk_maps, maps[i])
#         foreach (sys[j]):
#            img = sys[j].convert2string({prefix, "      "},
#                                   blk_maps[j])
#            image = {image, "\n", img}
#         end
#      end
#   end
#`endif
#   return image
#endfunction: convert2string
#
#
#

import unittest


class TestUVMRegBlock(unittest.TestCase):

    def test_add_reg(self):
        rb = UVMRegBlock("rb_blk")
        rb.create_map("", 0, 1, UVM_BIG_ENDIAN)
        reg1 = UVMReg("xx", 32, rb.get_full_name())
        reg1.configure(rb, None, "acp")
        # reg1.build()
        rb.default_map.add_reg(reg1, 0x0000,  "RW")
        print("len is now " + str(len(rb.regs)))
        rr = rb.get_reg_by_name('xx')
        self.assertEqual(rr.get_name(), 'xx')

        r_none = rb.get_reg_by_name('y_reg')
        self.assertEqual(r_none, None)


if __name__ == '__main__':
    unittest.main()
