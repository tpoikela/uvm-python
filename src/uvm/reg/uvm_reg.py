#
#-------------------------------------------------------------
#   Copyright 2004-2009 Synopsys, Inc.
#   Copyright 2010-2011 Mentor Graphics Corporation
#   Copyright 2010-2011 Cadence Design Systems, Inc.
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#-------------------------------------------------------------

from ..macros import uvm_error, uvm_info
from ..base.sv import sv
from ..base.uvm_mailbox import UVMMailbox
from ..base.uvm_object import UVMObject
from ..base.uvm_pool import UVMObjectStringPool, UVMPool
from ..base.uvm_queue import UVMQueue
from ..base.uvm_globals import (UVM_NONE, uvm_check_output_args, uvm_report_enabled,
                                uvm_report_error, uvm_report_fatal, uvm_report_info,
                                uvm_report_warning, uvm_zero_delay)
from ..base.uvm_object_globals import UVM_INFO, UVM_DEBUG, UVM_HIGH
from ..macros.uvm_message_defines import uvm_warning

from .uvm_reg_field import UVMRegField
from .uvm_reg_model import (UVM_BACKDOOR, UVM_CHECK, UVM_DEFAULT_PATH, UVM_FIELD, UVM_FRONTDOOR,
                            UVM_IS_OK, UVM_NOT_OK, UVM_NO_CHECK, UVM_NO_COVERAGE, UVM_NO_HIER,
                            UVM_PREDICT_DIRECT, UVM_PREDICT_READ, UVM_PREDICT_WRITE, UVM_READ,
                            UVM_REG, UVM_WRITE, uvm_hdl_concat2string, uvm_hdl_path_concat,
                            uvm_reg_cvr_rsrc_db)
from .uvm_reg_item import UVMRegItem
from .uvm_reg_cbs import UVMRegFieldCbIter, UVMRegCbIter
from .uvm_reg_map import UVMRegMap
from ..dpi.uvm_hdl import uvm_hdl

ERR_BD_READ = ("Backdoor read of register %s with multiple HDL copies: "
    + "values are not the same: %0h at path '%s', and %0h at path '%s'. "
    + "Returning first value.")



class UVMReg(UVMObject):
    """
    Register abstraction base class

    A register represents a set of fields that are accessible
    as a single entity.

    A register may be mapped to one or more address maps,
    each with different access rights and policy.
    """

    m_max_size = 0

    def __init__(self, name, n_bits, has_coverage=UVM_NO_COVERAGE):
        """
        Create a new instance and type-specific configuration

        Creates an instance of a register abstraction class with the specified
        name.

        `n_bits` specifies the total number of bits in the register.
        Not all bits need to be implemented.
        This value is usually a multiple of 8.

        `has_coverage` specifies which functional coverage models are present in
        the extension of the register abstraction class.
        Multiple functional coverage models may be specified by adding their
        symbolic names, as defined by the `uvm_coverage_model_e` type.

        Args:
            name:
            n_bits:
            has_coverage:
        """
        super().__init__(name)
        self.m_fields = []   # Fields in LSB to MSB order
        self.m_parent = None  # uvm_reg_block
        if n_bits == 0:
            uvm_report_error("RegModel", "Register \"{}\" cannot have 0 bits".format(
                self.get_name()))
            n_bits = 1
        self.m_n_bits      = n_bits
        self.m_has_cover   = has_coverage
        self.m_cover_on    = False

        self.m_atomic_rw = None
        self.m_atomic  = UVMMailbox(1)
        self.m_atomic.try_put(1)

        #   self.m_process = None
        self.m_n_used_bits = 0
        self.m_locked      = False
        self.m_is_busy     = False
        self.m_is_locked_by_field = False
        self.m_hdl_paths_pool = UVMObjectStringPool()  # string -> UVMQueue of uvm_hdl_path_concat
        self.m_read_in_progress = False
        self.m_write_in_progress = False
        self.m_update_in_progress = False
        self.m_lineno = 0
        self.m_fname = ""
        self.m_maps = UVMPool()  # bit[uvm_reg_map]
        self.m_regfile_parent = None  # uvm_reg_file
        self.m_backdoor = None  # uvm_reg_backdoor

        if n_bits > UVMReg.m_max_size:
            UVMReg.m_max_size = n_bits


    def configure(self, blk_parent, regfile_parent=None, hdl_path=""):
        """
        Instance-specific configuration

        Specify the parent block of this register.
        May also set a parent register file for this register,

        If the register is implemented in a single HDL variable,
        its name is specified as the `hdl_path`.
        Otherwise, if the register is implemented as a concatenation
        of variables (usually one per field), then the HDL path
        must be specified using the <add_hdl_path()> or
        `add_hdl_path_slice` method.

        Args:
            blk_parent (UVMRegBlock):
            regfile_parent (UVMRegFile):
            hdl_path (str):
        """
        if blk_parent is None:
            uvm_report_error("UVM/REG/CFG/NOBLK", (
                "uvm_reg::configure() called without a parent block for instance \""
                + self.get_name() + "\" of register type \"" +
                self.get_type_name() + "\"."))
            return

        self.m_parent = blk_parent
        self.m_parent.add_reg(self)
        self.m_regfile_parent = regfile_parent
        if hdl_path != "":
            self.add_hdl_path_slice(hdl_path, -1, -1)


    def set_offset(self, reg_map, offset, unmapped=0):
        """
        Modify the offset of the register

        The offset of a register within an address map is set using the
        <uvm_reg_map::add_reg()> method.
        This method is used to modify that offset dynamically.

        Modifying the offset of a register will make the register model
        diverge from the specification that was used to create it.

        Args:
            reg_map:
            offset:
            unmapped:
        """
        orig_map = reg_map
        if self.m_maps.num() > 1 and reg_map is None:
            uvm_report_error("RegModel", ("set_offset requires a non-None reg_map when register '"
                       + self.get_full_name() + "' belongs to more than one reg_map."))
            return
        reg_map = self.get_local_map(reg_map,"set_offset()")

        if reg_map is None:
            return
        reg_map.m_set_reg_offset(self, offset, unmapped)

    def set_parent(self, blk_parent, regfile_parent):
        """
        Set parent(s) for this register.

        Args:
            blk_parent (UVMRegBlock): Parent register block.
            regfile_parent (UVMRegFile): Parent register file.
        """
        if self.m_parent is not None:
            pass
            # TODO: remove register from previous parent
        self.m_parent = blk_parent
        self.m_regfile_parent = regfile_parent

    def add_field(self, field):
        """
        Add a field into this register.
        Args:
            field (UVMRegField): Reg field to add into this register.
        """
        offset = 0
        idx = 0

        if self.m_locked:
            uvm_report_error("RegModel", "Cannot add field to locked register model")
            return

        if field is None:
            uvm_report_fatal("RegModel", "Attempting to register None field")

        # Store fields in LSB to MSB order
        offset = field.get_lsb_pos()
        idx = -1
        for i, f in enumerate(self.m_fields):
            if offset < f.get_lsb_pos():
                j = i
                self.m_fields.insert(j, field)
                idx = i
                break
        if idx < 0:
            self.m_fields.append(field)
            idx = len(self.m_fields)-1

        self.m_n_used_bits += field.get_n_bits()

        # Check if there are too many fields in the register
        if self.m_n_used_bits > self.m_n_bits:
            uvm_report_error("RegModel",
              "Fields use more bits ({}) than available in register \"{}\" ({})".format(
                 self.m_n_used_bits, self.get_name(), self.m_n_bits))

        # Check if there are overlapping fields
        if idx > 0:
            if (self.m_fields[idx-1].get_lsb_pos() +
                    self.m_fields[idx-1].get_n_bits() > offset):
                uvm_report_error("RegModel",
                    "Field {} overlaps field {} in register \"{}\"".format(
                        self.m_fields[idx-1].get_name(), field.get_name(), self.get_name()))

        if idx < len(self.m_fields)-1:
            if (offset + field.get_n_bits() >
                    self.m_fields[idx+1].get_lsb_pos()):
                uvm_report_error("RegModel", "Field {} overlaps field {} in register \"{}\"".format(
                    field.get_name(), self.m_fields[idx+1].get_name(), self.get_name()))


    def add_map(self, reg_map):
        """
        Args:
            reg_map (UVMRegMap): Add a register map for this register.
        """
        self.m_maps.add(reg_map, 1)

    def Xlock_modelX(self):
        """
          /*local*/ extern function void   Xlock_modelX
        """
        if self.m_locked is True:
            return
        self.m_locked = True

    #   //---------------------
    #   // Group: Introspection
    #   //---------------------

    #   // Function: get_name
    #   //
    #   // Get the simple name
    #   //
    #   // Return the simple object name of this register.

    def get_full_name(self):
        """
           Get the hierarchical name

           Return the hierarchal name of this register.
           The base of the hierarchical name is the root block.

        Returns:
            str: The hierarchical name of this register.
        """
        if (self.m_regfile_parent is not None):
            return self.m_regfile_parent.get_full_name() + "." + self.get_name()
        if (self.m_parent is not None):
            return self.m_parent.get_full_name() + "." + self.get_name()

        return self.get_name()


    def get_parent(self):
        """
        Get the parent block

        Returns:
            UVMRegBlock: Parent block of this register.
        """
        return self.get_block()

    def get_block(self):
        """
        Returns:
            UVMRegBlock: Parent block of this register.
        """
        return self.m_parent

    def get_regfile(self):
        """
        Get the parent register file
        Returns `None` if this register is instantiated in a block.

        Returns:
            UVMRegFile: Parent register file of this register.
        """
        return self.m_regfile_parent


    def get_n_maps(self):
        """
        Returns the number of address maps this register is mapped in

        Returns:
            int: Number of address map this registers is mapped in
        """
        return self.m_maps.num()

    def is_in_map(self, _map):
        """
        Returns 1 if this register is in the specified address `map`

        Args:
            _map (UVMRegMap):
        Returns:
        """
        if _map in self.m_maps:
            return True
        for key in self.m_maps.key_list():
            local_map = key  # uvm_reg_map
            parent_map = local_map.get_parent_map()

            while parent_map is not None:
                if (parent_map == _map):
                    return True
                parent_map = parent_map.get_parent_map()
        return False


    def get_maps(self, maps):
        """
        Returns all of the address `maps` where this register is mapped

        Args:
            maps (list): Appends found maps into this list.
        Returns:
        """
        for _map in self.m_maps.key_list():
            maps.append(_map)
        return maps


    def get_local_map(self, reg_map, caller=""):
        """
        get_local_map
        Args:
            reg_map:
            caller:
        Returns:
        """
        if reg_map is None:
            return self.get_default_map()
        if reg_map in self.m_maps:
            return reg_map
        for l in self.m_maps.keys():
            local_map = l
            parent_map = local_map.get_parent_map()

            while parent_map is not None:
                if parent_map == reg_map:
                    return local_map
                parent_map = parent_map.get_parent_map()
        cname = self._get_cname(caller)
        uvm_report_warning("RegModel", ("Register '" + self.get_full_name()
            + "' is not contained within reg_map '" + reg_map.get_full_name() + "'"
            + cname))
        return None

    def get_default_map(self, caller=""):
        """
        get_default_map
        Args:
            caller (str):
        Returns:
        """
        # if reg is not associated with any map, return ~None~
        if self.m_maps.num() == 0:
            cname = self._get_cname(caller)
            uvm_report_warning("RegModel", ("Register '" + self.get_full_name()
                + "' is not registered with any map" + cname))
            return None
        # if only one map, choose that
        if self.m_maps.num() == 1:
            return self.m_maps.first()

        # try to choose one based on default_map in parent blocks.
        for l in self.m_maps.keys():
            reg_map = l
            blk = reg_map.get_parent()
            default_map = blk.get_default_map()
            if default_map is not None:
                local_map = self.get_local_map(default_map,"get_default_map()")
                if local_map is not None:
                    return local_map

        # if that fails, choose the first in this reg's maps
        return self.m_maps.first()

    def _get_cname(self, caller):
        cname = ""
        if caller != "":
            cname = " (called from " + caller + ")"
        return cname

    def get_rights(self, reg_map=None):
        """
           Returns the accessibility ("RW, "RO", or "WO") of this register in the given `map`.

           If no address map is specified and the register is mapped in only one
           address map, that address map is used. If the register is mapped
           in more than one address map, the default address map of the
           parent block is used.

           Whether a register field can be read or written depends on both the field's
           configured access policy (refer to <uvm_reg_field::configure>) and the register's
           accessibility rights in the map being used to access the field.

           If an address map is specified and
           the register is not mapped in the specified
           address map, an error message is issued
           and "RW" is returned.

        Args:
            reg_map (UVMRegMap):
        Returns:
            str: Register access rights.
        """
        reg_map = self.get_local_map(reg_map,"get_rights()")
        if reg_map is None:
            return "RW"
        info = reg_map.get_reg_map_info(self)
        return info.rights

    def get_n_bits(self):
        """
        Returns the width, in bits, of this register.

        Returns:
        """
        return self.m_n_bits

    def get_n_bytes(self):
        """
        Returns the width, in bytes, of this register. Rounds up to
        next whole byte if register is not a multiple of 8.

        Returns:
        """
        return int((self.m_n_bits-1) / 8) + 1

    @classmethod
    def get_max_size(cls):
        """
        Returns the maximum width, in bits, of all registers.

        Returns:
        """
        return UVMReg.m_max_size

    def get_fields(self, fields):
        """
        Return the fields in this register

        Fills the specified array with the abstraction class
        for all of the fields contained in this register.
        Fields are ordered from least-significant position to most-significant
        position within the register.

        Args:
            fields (list):
        """
        for f in self.m_fields:
            fields.append(f)
        return fields

    def get_field_by_name(self, name):
        """
        Return the named field in this register

        Finds a field with the specified name in this register
        and returns its abstraction class.
        If no fields are found, returns `None`.

        Args:
            name (str): Name of the sought field.
        Returns:
            UVMRegField: Named field, or `None` if nothing found.
        """
        for f in self.m_fields:
            if f.get_name() == name:
                return f
        uvm_warning("RegModel", "Unable to locate field '" + name +
                "' in register '" + self.get_name() + "'")
        return None


    def Xget_fields_accessX(self, _map):
        """
        Returns "WO" if all of the fields in the registers are write-only
        Returns "RO" if all of the fields in the registers are read-only
        Returns "RW" otherwise.
        Args:
            _map (UVMRegMap):
        Returns:
        """
        is_R = False
        is_W = False

        for i in range(len(self.m_fields)):
            access = self.m_fields[i].get_access(_map)
            if access in ["RO", "RC", "RS"]:
                is_R = True
            elif access in ["WO", "WOC", "WOS", "WO1"]:
                is_W = True
            else:
                return "RW"
            if (is_R and is_W):
                return "RW"

        if is_R is False and is_W is True:  #2'b01:
            return "WO"
        elif is_R is True and is_W is False:  # 2'b10:
            return "RO"
        return "RW"


    def get_offset(self, reg_map=None):
        """
           Returns the offset of this register

           Returns the offset of this register in an address `map`.

           If no address map is specified and the register is mapped in only one
           address map, that address map is used. If the register is mapped
           in more than one address map, the default address map of the
           parent block is used.

           If an address map is specified and
           the register is not mapped in the specified
           address map, an error message is issued.

        Args:
            reg_map (UVMRegMap): Offset in this map.
        Returns:
            int: Offset of this register.
        """
        orig_map = reg_map
        reg_map = self.get_local_map(reg_map,"get_offset()")

        if reg_map is None:
            return -1
        map_info = reg_map.get_reg_map_info(self)

        if map_info.unmapped:
            map_name = reg_map.get_full_name()
            if orig_map is not None:
                map_name = orig_map.get_full_name()
            uvm_report_warning("RegModel", ("Register '" + self.get_name()
                         + "' is unmapped in reg_map '" + map_name + "'"))
            return -1
        return map_info.offset

    def get_address(self, reg_map=None):
        """
        Returns the base external physical address of this register

        Returns the base external physical address of this register
        if accessed through the specified address `map`.

        If no address map is specified and the register is mapped in only one
        address map, that address map is used. If the register is mapped
        in more than one address map, the default address map of the
        parent block is used.

        If an address map is specified and
        the register is not mapped in the specified
        address map, a warning message is issued.

        Args:
            reg_map:
        Returns:
            int: Base external physical address of this register
        """
        addr = []
        self.get_addresses(reg_map,addr)
        if len(addr) > 0:
            return addr[0]

    def get_addresses(self, reg_map, addr):
        """
        Identifies the external physical address(es) of this register

        Computes all of the external physical addresses that must be accessed
        to completely read or write this register. The addressed are specified in
        little endian order.
        Returns the number of bytes transferred on each access.

        If no address map is specified and the register is mapped in only one
        address map, that address map is used. If the register is mapped
        in more than one address map, the default address map of the
        parent block is used.

        If an address map is specified and
        the register is not mapped in the specified
        address map, an error message is issued.

        Args:
            reg_map (UVMRegMap):
            addr (int):
        Returns:
            int: Number of bytes transferred on each access.
        """
        map_info = None
        system_map = None
        orig_map = reg_map
        reg_map = self.get_local_map(reg_map,"get_addresses()")
        if reg_map is None:
            return -1

        map_info = reg_map.get_reg_map_info(self)
        if map_info.unmapped:
            map_name = reg_map.get_full_name()
            if orig_map is not None:
                map_name = orig_map.get_full_name()
            uvm_warning("RegModel", ("Register '" + self.get_name()
                 + "' is unmapped in reg_map '" + map_name + "'"))
            return -1
        addr.extend(map_info.addr)
        system_map = reg_map.get_root_map()
        return reg_map.get_n_bytes()

    #   //--------------
    #   // Group: Access
    #   //--------------

    def set(self, value, fname="", lineno=0):
        """
           Set the desired value for this register

           Sets the desired value of the fields in the register
           to the specified value. Does not actually
           set the value of the register in the design,
           only the desired value in its corresponding
           abstraction class in the RegModel model.
           Use the `UVMReg.update` method to update the
           actual register with the mirrored value or
           the `UVMReg.write` method to set
           the actual register and its mirrored value.

           Unless this method is used, the desired value is equal to
           the mirrored value.

           Refer <uvm_reg_field::set()> for more details on the effect
           of setting mirror values on fields with different
           access policies.

           To modify the mirrored field values to a specific value,
           and thus use the mirrored as a scoreboard for the register values
           in the DUT, use the `UVMReg.predict` method.

        Args:
            value:
            fname:
            lineno:
        """
        # Split the value into the individual fields
        self.m_fname = fname
        self.m_lineno = lineno

        for field in self.m_fields:
            field.set((value >> field.get_lsb_pos()) &
                    ((1 << field.get_n_bits()) - 1))

    def get(self, fname="", lineno=0):
        """
           Function: get

           Return the desired value of the fields in the register.

           Does not actually read the value
           of the register in the design, only the desired value
           in the abstraction class. Unless set to a different value
           using the `UVMReg.set`, the desired value
           and the mirrored value are identical.

           Use the `UVMReg.read` or `UVMReg.peek`
           method to get the actual register value.

           If the register contains write-only fields, the desired/mirrored
           value for those fields are the value last written and assumed
           to reside in the bits implementing these fields.
           Although a physical read operation would something different
           for these fields,
           the returned value is the actual content.

        Args:
            fname:
            lineno:
        Returns:
        """
        # Concatenate the value of the individual fields
        # to form the register value
        self.m_fname = fname
        self.m_lineno = lineno
        get = 0

        for field in self.m_fields:
            get |= field.get() << field.get_lsb_pos()
        return get


    def get_mirrored_value(self, fname="", lineno=0):
        """
        Return the mirrored value of the fields in the register.

        Does not actually read the value
        of the register in the design

        If the register contains write-only fields, the desired/mirrored
        value for those fields are the value last written and assumed
        to reside in the bits implementing these fields.
        Although a physical read operation would something different
        for these fields, the returned value is the actual content.

        Args:
            fname:
            lineno:
        Returns:
            int: Mirrored value in the register
        """
        # Concatenate the value of the individual fields
        # to form the register value
        self.m_fname = fname
        self.m_lineno = lineno
        #
        get_mirrored_value = 0
        #
        for i in range(len(self.m_fields)):
            lsb_pos = self.m_fields[i].get_lsb_pos()
            get_mirrored_value |= self.m_fields[i].get_mirrored_value() << lsb_pos
        return get_mirrored_value


    def needs_update(self):
        """
           Function: needs_update

           Returns 1 if any of the fields need updating

           See <uvm_reg_field::needs_update()> for details.
           Use the `UVMReg.update` to actually update the DUT register.

        Returns:
        """
        for i in range(len(self.m_fields)):
            if self.m_fields[i].needs_update():
                return True
        return False


    def reset(self, kind="HARD"):
        """
           Function: reset

           Reset the desired/mirrored value for this register.

           Sets the desired and mirror value of the fields in this register
           to the reset value for the specified reset `kind`.
           See <uvm_reg_field.reset()> for more details.

           Also resets the semaphore that prevents concurrent access
           to the register.
           This semaphore must be explicitly reset if a thread accessing
           this register array was killed in before the access
           was completed

        Args:
            kind:
        """
        for i in range(len(self.m_fields)):
            self.m_fields[i].reset(kind)
        # Put back a key in the semaphore if it is checked out
        # in case a thread was killed during an operation
        q = []
        self.m_atomic.try_get(q)
        self.m_atomic.try_put(1)
        self.m_process = None
        self.Xset_busyX(0)


    #   // Function: get_reset
    #   //
    #   // Get the specified reset value for this register
    #   //
    #   // Return the reset value for this register
    #   // for the specified reset ~kind~.
    #   //
    #   extern virtual function uvm_reg_data_t
    #                             get_reset(string kind = "HARD")
    #
    #
    #   // Function: has_reset
    #   //
    #   // Check if any field in the register has a reset value specified
    #   // for the specified reset ~kind~.
    #   // If ~delete~ is TRUE, removes the reset value, if any.
    #   //
    #   extern virtual function bit has_reset(string kind = "HARD",
    #                                         bit    delete = 0)
    #
    #
    #   // Function: set_reset
    #   //
    #   // Specify or modify the reset value for this register
    #   //
    #   // Specify or modify the reset value for all the fields in the register
    #   // corresponding to the cause specified by ~kind~.
    #   //
    #   extern virtual function void
    #                       set_reset(uvm_reg_data_t value,
    #                                 string         kind = "HARD")
    #
    #

    async def write(self, status, value, path=UVM_DEFAULT_PATH, _map=None, parent=None, prior=-1,
            extension=None, fname="", lineno=0):
        """
           Task: write

           Write the specified value in this register

           Write `value` in the DUT register that corresponds to this
           abstraction class instance using the specified access
           `path`.
           If the register is mapped in more than one address map,
           an address `map` must be
           specified if a physical access is used (front-door access).
           If a back-door access path is used, the effect of writing
           the register through a physical access is mimicked. For
           example, read-only bits in the registers will not be written.

           The mirrored value will be updated using the `UVMReg.predict`
           method.

          extern virtual task write(output uvm_status_e      status,
                                    input  uvm_reg_data_t    value,
                                    input  uvm_path_e        path = UVM_DEFAULT_PATH,
                                    input  uvm_reg_map       map = None,
                                    input  uvm_sequence_base parent = None,
                                    input  int               prior = -1,
                                    input  uvm_object        extension = None,
                                    input  string            fname = "",
                                    input  int               lineno = 0)
        Args:
            status:
            value:
            path:
            UVM_DEFAULT_PATH:
            _map:
            parent:
            prior:
            extension:
            fname:
            lineno:
        """

        uvm_check_output_args([status])
        # create an abstract transaction for this operation
        rw = UVMRegItem.type_id.create("write_item", None, self.get_full_name())
        await self.XatomicX(1, rw)
        self.set(value)

        rw.element      = self
        rw.element_kind = UVM_REG
        rw.kind         = UVM_WRITE
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
        await self.XatomicX(0)


    async def read(self, status, value, path=UVM_DEFAULT_PATH, _map=None,
            parent=None, prior=-1, extension=None, fname="", lineno=0):
        """
           Task: read

           Read the current value from this register

           Read and return `value` from the DUT register that corresponds to this
           abstraction class instance using the specified access
           `path`.
           If the register is mapped in more than one address map,
           an address `map` must be
           specified if a physical access is used (front-door access).
           If a back-door access path is used, the effect of reading
           the register through a physical access is mimicked. For
           example, clear-on-read bits in the registers will be set to zero.

           The mirrored value will be updated using the `UVMReg.predict`
           method.

          extern virtual task read(output uvm_status_e      status,
                                   output uvm_reg_data_t    value,
                                   input  uvm_path_e        path = UVM_DEFAULT_PATH,
                                   input  uvm_reg_map       map = None,
                                   input  uvm_sequence_base parent = None,
                                   input  int               prior = -1,
                                   input  uvm_object        extension = None,
                                   input  string            fname = "",
                                   input  int               lineno = 0)

        Args:
            status:
            value:
            path:
            UVM_DEFAULT_PATH:
            _map:
            parent:
            prior:
            extension:
            fname:
            lineno:
        """
        uvm_check_output_args([status, value])
        rw = UVMRegItem.type_id.create("pseudo-read_item", None, self.get_full_name())
        await self.XatomicX(1, rw)
        await self.XreadX(status, value, path, _map, parent, prior, extension, fname, lineno)
        await self.XatomicX(0)
        #endtask: read


    #   // Task: poke
    #   //
    #   // Deposit the specified value in this register
    #   //
    #   // Deposit the value in the DUT register corresponding to this
    #   // abstraction class instance, as-is, using a back-door access.
    #   //
    #   // Uses the HDL path for the design abstraction specified by ~kind~.
    #   //
    #   // The mirrored value will be updated using the `UVMReg.predict`
    #   // method.
    #   //
    #   extern virtual task poke(output uvm_status_e      status,
    #                            input  uvm_reg_data_t    value,
    #                            input  string            kind = "",
    #                            input  uvm_sequence_base parent = None,
    #                            input  uvm_object        extension = None,
    #                            input  string            fname = "",
    #                            input  int               lineno = 0)
    #
    #

    #   // Task: peek
    #   //
    #   // Read the current value from this register
    #   //
    #   // Sample the value in the DUT register corresponding to this
    #   // abstraction class instance using a back-door access.
    #   // The register value is sampled, not modified.
    #   //
    #   // Uses the HDL path for the design abstraction specified by ~kind~.
    #   //
    #   // The mirrored value will be updated using the `UVMReg.predict`
    #   // method.
    #   //
    #   extern virtual task peek(output uvm_status_e      status,
    #                            output uvm_reg_data_t    value,
    #                            input  string            kind = "",
    #                            input  uvm_sequence_base parent = None,
    #                            input  uvm_object        extension = None,
    #                            input  string            fname = "",
    #                            input  int               lineno = 0)

    async def update(self, status, path=UVM_DEFAULT_PATH, _map=None, parent=None, prior=-1, extension=None,
            fname="", lineno=0):
        """
           Task: update

           Updates the content of the register in the design to match the
           desired value

           This method performs the reverse
           operation of `UVMReg.mirror`.
           Write this register if the DUT register is out-of-date with the
           desired/mirrored value in the abstraction class, as determined by
           the `UVMReg.needs_update` method.

           The update can be performed using the using the physical interfaces
           (frontdoor) or `UVMReg.poke` (backdoor) access.
           If the register is mapped in multiple address maps and physical access
           is used (front-door), an address `map` must be specified.

          extern virtual task update(output uvm_status_e      status,
                                     input  uvm_path_e        path = UVM_DEFAULT_PATH,
                                     input  uvm_reg_map       map = None,
                                     input  uvm_sequence_base parent = None,
                                     input  int               prior = -1,
                                     input  uvm_object        extension = None,
                                     input  string            fname = "",
                                     input  int               lineno = 0)

        Args:
            status:
            path:
            UVM_DEFAULT_PATH:
            _map:
            parent:
            prior:
            extension:
            fname:
            lineno:
        """
        uvm_check_output_args([status])
        upd = 0x0
        # status = UVM_IS_OK

        if self.needs_update() is False:
            return

        # Concatenate the write-to-update values from each field
        # Fields are stored in LSB or MSB order
        for i in range(len(self.m_fields)):
            upd = upd | (self.m_fields[i].XupdateX() << self.m_fields[i].get_lsb_pos())

        await self.write(status, upd, path, _map, parent, prior, extension, fname, lineno)


    async def mirror(self, status, check=UVM_NO_CHECK, path=UVM_DEFAULT_PATH, _map=None,
            parent=None, prior=-1, extension=None, fname="", lineno=0):
        """
        Read the register and update/check its mirror value

        Read the register and optionally compared the readback value
        with the current mirrored value if `check` is `UVM_CHECK`.
        The mirrored value will be updated using the `UVMReg.predict`
        method based on the readback value.

        The mirroring can be performed using the physical interfaces (frontdoor)
        or `UVMReg.peek` (backdoor).

        If `check` is specified as UVM_CHECK,
        an error message is issued if the current mirrored value
        does not match the readback value. Any field whose check has been
        disabled with <uvm_reg_field::set_compare()> will not be considered
        in the comparison.

        If the register is mapped in multiple address maps and physical
        access is used (front-door access), an address `map` must be specified.
        If the register contains
        write-only fields, their content is mirrored and optionally
        checked only if a UVM_BACKDOOR
        access path is used to read the register.

          extern virtual task mirror(output uvm_status_e      status,
                                     input uvm_check_e        check  = UVM_NO_CHECK,
                                     input uvm_path_e         path = UVM_DEFAULT_PATH,
                                     input uvm_reg_map        map = None,
                                     input uvm_sequence_base  parent = None,
                                     input int                prior = -1,
                                     input  uvm_object        extension = None,
                                     input string             fname = "",
                                     input int                lineno = 0)
        Args:
            status:
            check:
            path:
            _map:
            parent:
            prior:
            extension:
            fname:
            lineno:
        """
        uvm_check_output_args([status])
        exp = 0  # uvm_reg_data_t  exp
        bkdr = self.get_backdoor()

        rw = UVMRegItem.type_id.create("mirror_pseudo_item", None, self.get_full_name())
        await self.XatomicX(1, rw)
        self.m_fname = fname
        self.m_lineno = lineno

        if path == UVM_DEFAULT_PATH:
            path = self.m_parent.get_default_path()

        if (path == UVM_BACKDOOR and (bkdr is not None or self.has_hdl_path())):
            _map = UVMRegMap.backdoor()
        else:
            _map = self.get_local_map(_map, "read()")

        if _map is None:
            return

        # Remember what we think the value is before it gets updated
        if check == UVM_CHECK:
            exp = self.get_mirrored_value()

        v = []
        await self.XreadX(status, v, path, _map, parent, prior, extension, fname, lineno)
        v = v[0]

        if status == UVM_NOT_OK:
            await self.XatomicX(0)
            return

        if check == UVM_CHECK:
            self.do_check(exp, v, _map)

        await self.XatomicX(0)


    def predict(self, value, be=-1, kind=UVM_PREDICT_DIRECT, path=UVM_FRONTDOOR,
            reg_map=None, fname="", lineno=0):
        """
           Function: predict

           Update the mirrored and desired value for this register.

           Predict the mirror (and desired) value of the fields in the register
           based on the specified observed `value` on a specified address `map`,
           or based on a calculated value.
           See <uvm_reg_field::predict()> for more details.

           Returns TRUE if the prediction was successful for each field in the
           register.

        Args:
            value:
            be:
            kind:
            UVM_PREDICT_DIRECT:
            path:
            UVM_FRONTDOOR:
            reg_map:
            fname:
            lineno:
        Returns:
        """
        rw = UVMRegItem()
        rw.value[0] = value
        rw.path = path
        rw.map = reg_map
        rw.fname = fname
        rw.lineno = lineno
        self.do_predict(rw, kind, be)
        predict = 1
        if rw.status == UVM_NOT_OK:
            predict = 0
        return predict

    def is_busy(self):
        """
           Function: is_busy

           Returns 1 if register is currently being read or written.

        Returns:
        """
        return self.m_is_busy

    def Xset_busyX(self, busy):
        """
          /*local*/ extern function void Xset_busyX(bit busy)
        Args:
            busy:
        """
        self.m_is_busy = busy


    async def XreadX(self, status, value, path, _map,
            parent=None, prior=-1,extension=None,fname="", lineno=0):
        """
          /*local*/ extern task XreadX (output uvm_status_e      status,
                                        output uvm_reg_data_t    value,
                                        input  uvm_path_e        path,
                                        input  uvm_reg_map       map,
                                        input  uvm_sequence_base parent = None,
                                        input  int               prior = -1,
                                        input  uvm_object        extension = None,
                                        input  string            fname = "",
                                        input  int               lineno = 0)
        Args:
            status:
            value:
            path:
            _map:
            parent:
            prior:
            extension:
            fname:
            lineno:
        """
        uvm_check_output_args([status, value])

        # create an abstract transaction for this operation
        rw = UVMRegItem.type_id.create("read_item", None, self.get_full_name())
        rw.element      = self
        rw.element_kind = UVM_REG
        rw.kind         = UVM_READ
        rw.value[0]     = 0
        rw.path         = path
        rw.map          = _map
        rw.parent       = parent
        rw.prior        = prior
        rw.extension    = extension
        rw.fname        = fname
        rw.lineno       = lineno

        await self.do_read(rw)
        # TODO change arg passing
        status.append(rw.status)
        value.append(rw.value[0])
        #endtask: XreadX

    async def XatomicX(self, on, rw=None):
        """
          /*local*/ extern task XatomicX(bit on)
        Args:
            on:
            rw:
        Raises:
        """
        #   process m_reg_process
        #   m_reg_process=process::self()
        if on == 1:
            if rw is None:
                raise Exception("rw must not be None for on=1")
            if (rw is not None) and rw == self.m_atomic_rw:
                await uvm_zero_delay()
                return
            q = []
            await self.m_atomic.get(q)
            self.m_atomic_rw = rw
        else:
            # Maybe a key was put back in by a spurious call to reset()
            q = []
            self.m_atomic.try_get(q)
            await self.m_atomic.put(1)
            self.m_atomic_rw = None



    def Xcheck_accessX(self, rw, map_info, caller):
        """
          /*local*/ extern virtual function bit Xcheck_accessX
                                       (input uvm_reg_item rw,
                                        output uvm_reg_map_info map_info,
                                        input string caller)
        Args:
            rw:
            map_info:
            caller:
        Returns:
        """
        uvm_check_output_args([map_info])
        if (rw.path == UVM_DEFAULT_PATH):
            rw.path = self.m_parent.get_default_path()

        if (rw.path == UVM_BACKDOOR):
            if (self.get_backdoor() is None and not self.has_hdl_path()):
                uvm_warning("RegModel",
                  "No backdoor access available for register '" + self.get_full_name()
                  + "' . Using frontdoor instead.")
                rw.path = UVM_FRONTDOOR
            else:
                rw.map = UVMRegMap.backdoor()

        if (rw.path != UVM_BACKDOOR):
            rw.local_map = self.get_local_map(rw.map,caller)

            if rw.local_map is None:
                uvm_error(self.get_type_name(),
                   "No transactor available to physically access register on map '" +
                    rw.map.get_full_name() + "'")
                rw.status = UVM_NOT_OK
                return False

            _map_info = rw.local_map.get_reg_map_info(self)
            map_info.append(_map_info)

            if (_map_info.frontdoor is None and _map_info.unmapped):
                name = rw.local_map.get_full_name()
                if (rw.map is not None):
                    name = rw.map.get_full_name()
                uvm_error("RegModel", "Register '" + self.get_full_name()
                   + "' unmapped in map '" + name
                   + "' and does not have a user-defined frontdoor")
                rw.status = UVM_NOT_OK
                return False

            if (rw.map is None):
                rw.map = rw.local_map
        return True
        #endfunction


    #
    #   /*local*/ extern function bit Xis_locked_by_fieldX()
    #
    #

    def do_check(self, expected, actual, _map):
        """
          extern virtual function bit do_check(uvm_reg_data_t expected,
                                               uvm_reg_data_t actual,
                                               uvm_reg_map    map)
        Args:
            expected:
            actual:
            _map:
        Returns:
        """
        dc = 0

        for i in range(len(self.m_fields)):
            acc = self.m_fields[i].get_access(_map)
            acc = acc[0:1]
            if (self.m_fields[i].get_compare() == UVM_NO_CHECK or
                    acc == "WO"):
                lsb_pos = self.m_fields[i].get_lsb_pos()
                dc |= ((1 << self.m_fields[i].get_n_bits())-1) << lsb_pos

        if ((actual | dc) == (expected | dc)):
            return True

        uvm_error("RegModel", sv.sformatf(
            "Register \"%s\" value read from DUT (0x%h) does not match mirrored value (0x%h)",
            self.get_full_name(), actual, (expected ^ dc)))

        #foreach(self.m_fields[i]):
        for i in range(len(self.m_fields)):
            acc = self.m_fields[i].get_access(_map)
            acc = acc[0:1]
            if (not(self.m_fields[i].get_compare() == UVM_NO_CHECK or
                   acc == "WO")):
                mask = ((1 << self.m_fields[i].get_n_bits())-1)
                val = actual   >> self.m_fields[i].get_lsb_pos() & mask
                exp = expected >> self.m_fields[i].get_lsb_pos() & mask

                if (val != exp):
                    uvm_info("RegModel",
                            sv.sformatf("Field %s (%s[%0d:%0d]) mismatch read=%0d'h%0h mirrored=%0d'h%0h ",
                                self.m_fields[i].get_name(), self.get_full_name(),
                                self.m_fields[i].get_lsb_pos() + self.m_fields[i].get_n_bits() - 1,
                                self.m_fields[i].get_lsb_pos(),
                                self.m_fields[i].get_n_bits(), val,
                                self.m_fields[i].get_n_bits(), exp), UVM_NONE)
        return False



    async def do_write(self, rw):
        """
          extern virtual task do_write(uvm_reg_item rw)

        Args:
            rw:
        """
        await uvm_zero_delay()
        # TODO finish this
        cbs = UVMRegCbIter(self)  # uvm_reg_cb_iter  cbs = new(this)
        arr_map_info = []  # uvm_reg_map_info
        value = 0  # uvm_reg_data_t   value

        self.m_fname  = rw.fname
        self.m_lineno = rw.lineno

        if self.Xcheck_accessX(rw, arr_map_info, "write()") is False:
            await uvm_zero_delay()
            return

        # map_info = None
        # May be not be set for BACKDOOR, so check len
        # if len(arr_map_info) > 0:
        # map_info = arr_map_info[0]
        self.m_write_in_progress = True

        rw.value[0] &= ((1 << self.m_n_bits)-1)
        value = rw.value[0]
        rw.status = UVM_IS_OK

        # PRE-WRITE CBS - FIELDS
        # pre_write_callbacks
        msk = 0
        lsb = 0

        for i in range(len(self.m_fields)):
            cbs = UVMRegFieldCbIter(self.m_fields[i])
            f = self.m_fields[i]  # uvm_reg_field
            lsb = f.get_lsb_pos()
            msk = ((1 << f.get_n_bits() )-1) << lsb
            rw.value[0] = (value & msk) >> lsb
            await f.pre_write(rw)  # TODO yield?
            cb = cbs.first()
            while cb is not None:
                rw.element = f
                rw.element_kind = UVM_FIELD
                await cb.pre_write(rw)
                cb = cbs.next()
            value = (value & ~msk) | (rw.value[0] << lsb)

        rw.element = self
        rw.element_kind = UVM_REG
        rw.value[0] = value

        # PRE-WRITE CBS - REG
        await self.pre_write(rw)
        cb = cbs.first()
        while cb is not None:
            await cb.pre_write(rw)
            cb = cbs.next()

        if rw.status != UVM_IS_OK:
            self.m_write_in_progress = False
            await self.XatomicX(0)
            return

        if rw.path == UVM_BACKDOOR:
            final_val = 0
            bkdr = self.get_backdoor()  # uvm_reg_backdoor
            value = rw.value[0]

            # Mimick the final value after a physical read
            rw.kind = UVM_READ
            if bkdr is not None:
                bkdr.read(rw)
            else:
                self.backdoor_read(rw)

            if rw.status == UVM_NOT_OK:
                self.m_write_in_progress = False
                return

            for i in range(len(self.m_fields)):
                field_val = 0
                lsb = self.m_fields[i].get_lsb_pos()
                sz  = self.m_fields[i].get_n_bits()
                field_val = self.m_fields[i].XpredictX((rw.value[0] >> lsb) & ((1 << sz)-1),
                        (value >> lsb) & ((1 << sz)-1),
                        rw.local_map)
                final_val |= field_val << lsb
            rw.kind = UVM_WRITE
            rw.value[0] = final_val

            if bkdr is not None:
                bkdr.write(rw)
            else:
                self.backdoor_write(rw)

            self.do_predict(rw, UVM_PREDICT_WRITE)
        elif rw.path == UVM_FRONTDOOR:
            system_map = rw.local_map.get_root_map()  # uvm_reg_map
            self.m_is_busy = True

            # This should be safe, but...
            map_info = arr_map_info[0]

            # ...VIA USER FRONTDOOR
            if map_info is not None and map_info.frontdoor is not None:
                fd = map_info.frontdoor  # uvm_reg_frontdoor
                fd.rw_info = rw
                if fd.sequencer is None:
                    fd.sequencer = system_map.get_sequencer()
                await fd.start(fd.sequencer, rw.parent)

            # ...VIA BUILT-IN FRONTDOOR
            else:  # built_in_frontdoor
                await rw.local_map.do_write(rw)

            self.m_is_busy = False

            if system_map.get_auto_predict():
                status = 0
                if rw.status != UVM_NOT_OK:
                    self.sample(value, -1, 0, rw.map)
                    self.m_parent.XsampleX(map_info.offset, 0, rw.map)

                status = rw.status  # do_predict will override rw.status, so we save it here
                self.do_predict(rw, UVM_PREDICT_WRITE)
                rw.status = status

        value = rw.value[0]

        # POST-WRITE CBS - REG
        cb = cbs.first()
        while cb is not None:
            await cb.post_write(rw)
            cb = cbs.next()
        await self.post_write(rw)

        # POST-WRITE CBS - FIELDS
        for i in range(len(self.m_fields)):
            cbs = UVMRegFieldCbIter(self.m_fields[i])
            f = self.m_fields[i]  # uvm_reg_field
            rw.element = f
            rw.element_kind = UVM_FIELD
            rw.value[0] = (value >> f.get_lsb_pos()) & ((1 << f.get_n_bits())-1)

            cb = cbs.first()
            while cb is not None:
                cb.post_write(rw)
                cb = cbs.next()
            await f.post_write(rw)

        rw.value[0] = value
        rw.element = self
        rw.element_kind = UVM_REG

        # REPORT

        map_info = None
        if len(arr_map_info) > 0:
            map_info = arr_map_info[0]
        self._report_op_with(rw, map_info)

        self.m_write_in_progress = False
        #yield self.XatomicX(0)
        #endtask: do_write


    def _report_op_with(self, rw, map_info):
        if (uvm_report_enabled(UVM_HIGH, UVM_INFO, "RegModel")):
            path_s = ""
            value_s = ""
            if (rw.path == UVM_FRONTDOOR):
                path_s = "map " + rw.map.get_full_name()
                if map_info.frontdoor is not None:
                    path_s = "user frontdoor"
            else:
                path_s = "DPI backdoor"
                if self.get_backdoor() is not None:
                    path_s = "user backdoor"

            op_s = "Wrote"
            if rw.kind == UVM_READ:
                op_s = "Read"
            value_s = sv.sformatf("=0x%0h",rw.value[0])
            uvm_report_info("RegModel", op_s + " register via " + path_s + ": "
                    + self.get_full_name() + value_s, UVM_HIGH)


    async def do_read(self, rw):
        """
          extern virtual task do_read(uvm_reg_item rw)
        Args:
            rw:
        """
        value = 0  # uvm_reg_data_t   value
        exp = 0  # uvm_reg_data_t   exp

        self.m_fname   = rw.fname
        self.m_lineno  = rw.lineno

        arr_map_info = []
        if not(self.Xcheck_accessX(rw, arr_map_info, "read()")):
            return
        # May be not be set for BACKDOOR, so check len
        # map_info = None
        # if len(arr_map_info) > 0:
        # map_info = arr_map_info[0]

        self.m_read_in_progress = 1
        rw.status = UVM_IS_OK

        #   // PRE-READ CBS - FIELDS
        for i in range(len(self.m_fields)):
            cbs = UVMRegFieldCbIter(self.m_fields[i])
            f = self.m_fields[i]  # uvm_reg_field
            rw.element = f
            rw.element_kind = UVM_FIELD
            await self.m_fields[i].pre_read(rw)
            cb = cbs.first()
            while cb is not None:
                await cb.pre_read(rw)
                cb = cbs.next()

        rw.element = self
        rw.element_kind = UVM_REG

        cbs = UVMRegCbIter(self)
        # PRE-READ CBS - REG
        # TODO yield?
        await self.pre_read(rw)
        cb = cbs.first()
        while cb is not None:
            cb.pre_read(rw)
            cb = cbs.next()

        if rw.status != UVM_IS_OK:
            self.m_read_in_progress = 0
            return

        # EXECUTE READ...
        if rw.path == UVM_BACKDOOR:

            #  ...VIA USER BACKDOOR
            bkdr = self.get_backdoor()
            _map = UVMRegMap.backdoor()
            if _map.get_check_on_read():
                exp = self.get()

            if (bkdr is not None):
                bkdr.read(rw)
            else:
                self.backdoor_read(rw)
            value = rw.value[0]

            # Need to clear RC fields, set RS fields and mask WO fields
            if (rw.status != UVM_NOT_OK):
                wo_mask = 0  # uvm_reg_data_t

                for i in range(len(self.m_fields)):
                    acc = self.m_fields[i].get_access(UVMRegMap.backdoor())
                    nbits = self.m_fields[i].get_n_bits()
                    lsb_pos = self.m_fields[i].get_lsb_pos()
                    if (acc == "RC" or
                            acc == "WRC" or
                            acc == "WSRC" or
                            acc == "W1SRC" or
                            acc == "W0SRC"):
                        value &= ~(((1 << nbits)-1) << lsb_pos)
                    elif (acc == "RS" or
                            acc == "WRS" or
                            acc == "WCRS" or
                            acc == "W1CRS" or
                            acc == "W0CRS"):
                        value |= ((1 << nbits)-1) << lsb_pos
                    elif (acc == "WO" or
                            acc == "WOC" or
                            acc == "WOS" or
                            acc == "WO1"):
                        wo_mask |= ((1 << nbits)-1) << lsb_pos

                if value != rw.value[0]:
                    #uvm_reg_data_t saved
                    saved = rw.value[0]
                    rw.value[0] = value
                    if bkdr is not None:
                        bkdr.write(rw)
                    else:
                        self.backdoor_write(rw)
                    rw.value[0] = saved

                rw.value[0] &= ~wo_mask

                if (_map.get_check_on_read() and
                        rw.status != UVM_NOT_OK):
                    self.do_check(exp, rw.value[0], _map)

                self.do_predict(rw, UVM_PREDICT_READ)
        elif rw.path == UVM_FRONTDOOR:
            #raise Exception('NO UVM_FRONTDOOR access yet')
            system_map = rw.local_map.get_root_map()

            self.m_is_busy = True

            if (rw.local_map.get_check_on_read()):
                exp = self.get()

            map_info = arr_map_info[0]
            #  ...VIA USER FRONTDOOR
            if map_info.frontdoor is not None:
                fd = map_info.frontdoor  # uvm_reg_frontdoor
                fd.rw_info = rw
                if fd.sequencer is None:
                    fd.sequencer = system_map.get_sequencer()
                await fd.start(fd.sequencer, rw.parent)
            # ...VIA BUILT-IN FRONTDOOR
            else:
                await rw.local_map.do_read(rw)

            self.m_is_busy = 0

            if system_map.get_auto_predict():
                status = 0
                if (rw.local_map.get_check_on_read() and
                        rw.status != UVM_NOT_OK):
                    self.do_check(exp, rw.value[0], system_map)

                if (rw.status != UVM_NOT_OK):
                    self.sample(rw.value[0], -1, 1, rw.map)
                    self.m_parent.XsampleX(map_info.offset, 1, rw.map)

                status = rw.status  # do_predict will override rw.status, so we save it here
                self.do_predict(rw, UVM_PREDICT_READ)
                rw.status = status
            #   endcase
        #
        value = rw.value[0]  # preserve

        # POST-READ CBS - REG
        cb = cbs.first()
        while (cb is not None):
            cb.post_read(rw)
            cb = cbs.next()
        await self.post_read(rw)

        # POST-READ CBS - FIELDS
        for i in range(len(self.m_fields)):
            cbs = UVMRegFieldCbIter(self.m_fields[i])
            f = self.m_fields[i]  # uvm_reg_field
            rw.element = f
            rw.element_kind = UVM_FIELD
            rw.value[0] = (value >> f.get_lsb_pos()) & ((1 << f.get_n_bits())-1)

            cb = cbs.first()
            while (cb is not None):
                cb.post_read(rw)
                cb = cbs.next()
            await f.post_read(rw)

        rw.value[0] = value  # restore
        rw.element = self
        rw.element_kind = UVM_REG

        # REPORT
        map_info = None
        if len(arr_map_info) > 0:
            map_info = arr_map_info[0]
        self._report_op_with(rw, map_info)
        self.m_read_in_progress = False
        #endtask: do_read


    def do_predict(self, rw, kind=UVM_PREDICT_DIRECT, be=-1):
        reg_value = rw.value[0]
        self.m_fname = rw.fname
        self.m_lineno = rw.lineno

        if rw.status == UVM_IS_OK:
            rw.status = UVM_IS_OK

        if self.m_is_busy and kind == UVM_PREDICT_DIRECT:
            uvm_report_warning("RegModel", ("Trying to predict value of register '"
                        + self.get_full_name() + "' while it is being accessed"))
            rw.status = UVM_NOT_OK
            return

        for field in self.m_fields:
            rw.value[0] = ((reg_value >> field.get_lsb_pos()) &
                ((1 << field.get_n_bits())-1))
            be_shift = int(field.get_lsb_pos() / 8)
            field.do_predict(rw, kind, be >> be_shift)
        rw.value[0] = reg_value


    #   //-----------------
    #   // Group: Frontdoor
    #   //-----------------
    #
    #   // Function: set_frontdoor
    #   //
    #   // Set a user-defined frontdoor for this register
    #   //
    #   // By default, registers are mapped linearly into the address space
    #   // of the address maps that instantiate them.
    #   // If registers are accessed using a different mechanism,
    #   // a user-defined access
    #   // mechanism must be defined and associated with
    #   // the corresponding register abstraction class
    #   //
    #   // If the register is mapped in multiple address maps, an address ~map~
    #   // must be specified.
    #   //
    #   extern function void set_frontdoor(uvm_reg_frontdoor ftdr,
    #                                      uvm_reg_map       map = None,
    #                                      string            fname = "",
    #                                      int               lineno = 0)

    #   // Function: get_frontdoor
    #   //
    #   // Returns the user-defined frontdoor for this register
    #   //
    #   // If ~None~, no user-defined frontdoor has been defined.
    #   // A user-defined frontdoor is defined
    #   // by using the `UVMReg.set_frontdoor` method.
    #   //
    #   // If the register is mapped in multiple address maps, an address ~map~
    #   // must be specified.
    #   //
    #   extern function uvm_reg_frontdoor get_frontdoor(uvm_reg_map map = None)

    #   //----------------
    #   // Group: Backdoor
    #   //----------------

    #   // Function: set_backdoor
    #   //
    #   // Set a user-defined backdoor for this register
    #   //
    #   // By default, registers are accessed via the built-in string-based
    #   // DPI routines if an HDL path has been specified using the
    #   // `UVMReg.configure` or `UVMReg.add_hdl_path` method.
    #   //
    #   // If this default mechanism is not suitable (e.g. because
    #   // the register is not implemented in pure SystemVerilog)
    #   // a user-defined access
    #   // mechanism must be defined and associated with
    #   // the corresponding register abstraction class
    #   //
    #   // A user-defined backdoor is required if active update of the
    #   // mirror of this register abstraction class, based on observed
    #   // changes of the corresponding DUT register, is used.
    #   //
    #   extern function void set_backdoor(uvm_reg_backdoor bkdr,
    #                                     string          fname = "",
    #                                     int             lineno = 0)

    def get_backdoor(self, inherited=True):
        """
           Function: get_backdoor

           Returns the user-defined backdoor for this register

           If `None`, no user-defined backdoor has been defined.
           A user-defined backdoor is defined
           by using the `UVMReg.set_backdoor` method.

           If `inherited` is TRUE, returns the backdoor of the parent block
           if none have been specified for this register.

        Args:
            inherited:
        Returns:
        """
        if (self.m_backdoor is None and inherited):
            blk = self.get_parent()
            bkdr = None  # uvm_reg_backdoor
            while (blk is not None):
                bkdr = blk.get_backdoor()
                if (bkdr is not None):
                    self.m_backdoor = bkdr
                    break
                blk = blk.get_parent()
        return self.m_backdoor


    #   // Function: clear_hdl_path
    #   //
    #   // Delete HDL paths
    #   //
    #   // Remove any previously specified HDL path to the register instance
    #   // for the specified design abstraction.
    #   //
    #   extern function void clear_hdl_path (string kind = "RTL")

    def add_hdl_path(self, slices, kind="RTL"):
        """
           Function: add_hdl_path

           Add an HDL path

           Add the specified HDL path to the register instance for the specified
           design abstraction. This method may be called more than once for the
           same design abstraction if the register is physically duplicated
           in the design abstraction

           For example, the following register

        .. code-block:: python

          |        1 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0
          | Bits:  5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          |       +-+---+-------------+---+-------+
          |       |A|xxx|      B      |xxx|   C   |
          |       +-+---+-------------+---+-------+

           would be specified using the following literal value:

        .. code-block:: python

          | add_hdl_path([ ["A_reg", 15, 1],
          |                 ["B_reg",  6, 7],
          |                 ['C_reg",  0, 4] ] )

           If the register is implemented using a single HDL variable,
           The array should specify a single slice with its `offset` and `size`
           specified as -1. For example:

        .. code-block:: python

          | r1.add_hdl_path('{ '{"r1", -1, -1} })

        Args:
            slices:
            kind:
        """
        if not (self.m_hdl_paths_pool.exists(kind)):
            self.m_hdl_paths_pool[kind] = UVMQueue()
        paths = self.m_hdl_paths_pool.get(kind)  # uvm_queue #(uvm_hdl_path_concat)
        concat = uvm_hdl_path_concat()
        concat.set(slices)
        paths.push_back(concat)

    def add_hdl_path_slice(self, name, offset, size, first=0, kind="RTL"):
        """
           Function: add_hdl_path_slice

           Append the specified HDL slice to the HDL path of the register instance
           for the specified design abstraction.
           If `first` is TRUE, starts the specification of a duplicate
           HDL implementation of the register.

        Args:
            name:
            offset:
            size:
            first:
            kind:
        """
        if not (self.m_hdl_paths_pool.exists(kind)):
            self.m_hdl_paths_pool[kind] = UVMQueue()
        paths = self.m_hdl_paths_pool.get(kind)  # uvm_queue #(uvm_hdl_path_concat)
        concat = None

        if first or paths.size() == 0:
            concat = uvm_hdl_path_concat()
            paths.push_back(concat)
        else:
            concat = paths[paths.size()-1]
        concat.add_path(name, offset, size)


    def has_hdl_path(self, kind=""):
        """
           Function: has_hdl_path

           Check if a HDL path is specified

           Returns TRUE if the register instance has a HDL path defined for the
           specified design abstraction. If no design abstraction is specified,
           uses the default design abstraction specified for the parent block.

        Args:
            kind:
        Returns:
        """
        if kind == "":
            if self.m_regfile_parent is not None:
                kind = self.m_regfile_parent.get_default_hdl_path()
            else:
                kind = self.m_parent.get_default_hdl_path()

        return self.m_hdl_paths_pool.exists(kind)


    #   // Function:  get_hdl_path
    #   //
    #   // Get the incremental HDL path(s)
    #   //
    #   // Returns the HDL path(s) defined for the specified design abstraction
    #   // in the register instance.
    #   // Returns only the component of the HDL paths that corresponds to
    #   // the register, not a full hierarchical path
    #   //
    #   // If no design abstraction is specified, the default design abstraction
    #   // for the parent block is used.
    #   //
    #   extern function void get_hdl_path (ref uvm_hdl_path_concat paths[$],
    #                                      input string kind = "")



    #   // Function:  get_hdl_path_kinds
    #   //
    #   // Get design abstractions for which HDL paths have been defined
    #   //
    #   extern function void get_hdl_path_kinds (ref string kinds[$])


    def get_full_hdl_path(self, paths, kind="", separator="."):
        """
           Function:  get_full_hdl_path

           Get the full hierarchical HDL path(s)

           Returns the full hierarchical HDL path(s) defined for the specified
           design abstraction in the register instance.
           There may be more than one path returned even
           if only one path was defined for the register instance, if any of the
           parent components have more than one path defined for the same design
           abstraction

           If no design abstraction is specified, the default design abstraction
           for each ancestor block is used to get each incremental path.

        Args:
            paths:
            kind:
            separator:
        """

        if kind == "":
            if self.m_regfile_parent is not None:
                kind = self.m_regfile_parent.get_default_hdl_path()
            else:
                kind = self.m_parent.get_default_hdl_path()


        if not self.has_hdl_path(kind):
            uvm_error("RegModel", "Register " + self.get_full_name()
                    + " does not have hdl path defined for abstraction '" + kind + "'")
            return

        hdl_paths = self.m_hdl_paths_pool.get(kind)  # uvm_queue #(uvm_hdl_path_concat)
        parent_paths = []

        if self.m_regfile_parent is not None:
            self.m_regfile_parent.get_full_hdl_path(parent_paths, kind, separator)
        else:
            self.m_parent.get_full_hdl_path(parent_paths, kind, separator)

        for i in range(len(hdl_paths)):
            hdl_concat = hdl_paths.get(i)

            for j in range(len(parent_paths)):
                t = uvm_hdl_path_concat()

                for k in range(len(hdl_concat.slices)):
                    if (hdl_concat.slices[k].path == ""):
                        t.add_path(parent_paths[j])
                    else:
                        t.add_path(parent_paths[j] + separator + hdl_concat.slices[k].path,
                                  hdl_concat.slices[k].offset,
                                  hdl_concat.slices[k].size)
                paths.append(t)
        #endfunction


    def backdoor_read(self, rw):
        """
           Function: backdoor_read

           User-define backdoor read access

           Override the default string-based DPI backdoor access read
           for this register type.
           By default calls `UVMReg.backdoor_read_func`.

        Args:
            rw:
        """
        rw.status = self.backdoor_read_func(rw)

    def backdoor_write(self, rw):
        """
           Function: backdoor_write

           User-defined backdoor read access

           Override the default string-based DPI backdoor access write
           for this register type.

        Args:
            rw:
        """
        paths = []  # uvm_hdl_path_concat [$]
        ok = 1
        self.get_full_hdl_path(paths,rw.bd_kind)
        for i in range(len(paths)):
            hdl_concat = paths[i]  # uvm_hdl_path_concat
            for j in range(len(hdl_concat.slices)):
                uvm_info("RegMem", "backdoor_write to "
                        + hdl_concat.slices[j].path, UVM_DEBUG)

                if hdl_concat.slices[j].offset < 0:
                    ok &= uvm_hdl.uvm_hdl_deposit(hdl_concat.slices[j].path,rw.value[0])
                    continue

                _slice = 0  # uvm_reg_data_t
                _slice = rw.value[0] >> hdl_concat.slices[j].offset
                _slice &= (1 << hdl_concat.slices[j].size)-1
                ok &= uvm_hdl.uvm_hdl_deposit(hdl_concat.slices[j].path, _slice)

        rw.status = UVM_NOT_OK
        if ok:
            rw.status = UVM_IS_OK
        #endtask


    def backdoor_read_func(self, rw):
        """
           Function: backdoor_read_func

           User-defined backdoor read access

           Override the default string-based DPI backdoor access read
           for this register type.

        Args:
            rw:
        Returns:
        """
        paths = []  # uvm_hdl_path_concat [$]
        val = 0x0
        ok = 1
        self.get_full_hdl_path(paths,rw.bd_kind)
        for i in range(len(paths)):
            hdl_concat = paths[i]  # uvm_hdl_path_concat
            val = 0
            for j in range(len(hdl_concat.slices)):
                uvm_info("RegMem", "backdoor_read from %s "
                    + hdl_concat.slices[j].path, UVM_DEBUG)

                if hdl_concat.slices[j].offset < 0:
                    arr = []
                    ok &= uvm_hdl.uvm_hdl_read(hdl_concat.slices[j].path, arr)
                    val = arr[0]
                    continue

                _slice = 0
                k = hdl_concat.slices[j].offset

                ok &= uvm_hdl.uvm_hdl_read(hdl_concat.slices[j].path, _slice)

                for _ in range(hdl_concat.slices[j].size):
                    bit_val = _slice & 0x1
                    val = sv.set_bit(val, k, bit_val)
                    k += 1
                    _slice >>= 1

            val &= (1 << self.m_n_bits)-1

            if i == 0:
                rw.value[0] = val

            if val != rw.value[0]:
                uvm_error("RegModel", sv.sformatf(ERR_BD_READ,
                      self. get_full_name(), rw.value[0], uvm_hdl_concat2string(paths[0]),
                      val, uvm_hdl_concat2string(paths[i])))
                return UVM_NOT_OK

            uvm_info("RegMem",
                sv.sformatf("returned backdoor value 0x%0x",rw.value[0]),UVM_DEBUG)

        rw.status = UVM_NOT_OK
        if ok:
            rw.status = UVM_IS_OK
        return rw.status


    @classmethod
    def include_coverage(cls, scope, models, accessor=None):
        """
           Function: backdoor_watch

           User-defined DUT register change monitor

           Watch the DUT register corresponding to this abstraction class
           instance for any change in value and return when a value-change occurs.
           This may be implemented a string-based DPI access if the simulation
           tool provide a value-change callback facility. Such a facility does
           not exists in the standard SystemVerilog DPI and thus no
           default implementation for this method can be provided.

          virtual task  backdoor_watch(); endtask


          ----------------
           Group: Coverage
          ----------------

           Function: include_coverage

           Specify which coverage model that must be included in
           various block, register or memory abstraction class instances.

           The coverage models are specified by OR'ing or adding the
           `uvm_coverage_model_e` coverage model identifiers corresponding to the
           coverage model to be included.

           The scope specifies a hierarchical name or pattern identifying
           a block, memory or register abstraction class instances.
           Any block, memory or register whose full hierarchical name
           matches the specified scope will have the specified functional
           coverage models included in them.

           The scope can be specified as a POSIX regular expression
           or simple pattern.
           See <uvm_resource_base::Scope Interface> for more details.

        .. code-block:: python

          | uvm_reg::include_coverage("*", UVM_CVR_ALL)

           The specification of which coverage model to include in
           which abstraction class is stored in a `uvm_reg_cvr_t` resource in the
           `uvm_resource_db` resource database,
           in the "uvm_reg::" scope namespace.

          extern static function void include_coverage(string scope,
                                                       uvm_reg_cvr_t models,
                                                       uvm_object accessor = None)
        Args:
            cls:
            scope:
            models:
            accessor:
        """
        uvm_reg_cvr_rsrc_db.set("uvm_reg::" + scope, "include_coverage",
            models, accessor)


    def build_coverage(self, models):
        """
           Function: build_coverage

           Check if all of the specified coverage models must be built.

           Check which of the specified coverage model must be built
           in this instance of the register abstraction class,
           as specified by calls to `UVMReg.include_coverage`.

           Models are specified by adding the symbolic value of individual
           coverage model as defined in `uvm_coverage_model_e`.
           Returns the sum of all coverage models to be built in the
           register model.

        Args:
            models:
        Returns:
        """
        build_coverage = UVM_NO_COVERAGE
        cov_arr = []
        uvm_reg_cvr_rsrc_db.read_by_name("uvm_reg::" + self.get_full_name(),
                "include_coverage", cov_arr, self)
        build_coverage = cov_arr[0]
        return build_coverage & models


    def add_coverage(self, models):
        """
           Function: add_coverage

           Specify that additional coverage models are available.

           Add the specified coverage model to the coverage models
           available in this class.
           Models are specified by adding the symbolic value of individual
           coverage model as defined in `uvm_coverage_model_e`.

           This method shall be called only in the constructor of
           subsequently derived classes.

          extern virtual protected function void add_coverage(uvm_reg_cvr_t models)
        Args:
            models:
        """
        self.m_has_cover |= models

    def has_coverage(self, models):
        """
           Function: has_coverage

           Check if register has coverage model(s)

           Returns TRUE if the register abstraction class contains a coverage model
           for all of the models specified.
           Models are specified by adding the symbolic value of individual
           coverage model as defined in `uvm_coverage_model_e`.

          extern virtual function bit has_coverage(uvm_reg_cvr_t models)
        Args:
            models:
        Returns:
        """
        return ((self.m_has_cover & models) == models)


    def set_coverage(self, is_on):
        """
           Function: set_coverage

           Turns on coverage measurement.

           Turns the collection of functional coverage measurements on or off
           for this register.
           The functional coverage measurement is turned on for every
           coverage model specified using `uvm_coverage_model_e` symbolic
           identifiers.
           Multiple functional coverage models can be specified by adding
           the functional coverage model identifiers.
           All other functional coverage models are turned off.
           Returns the sum of all functional
           coverage models whose measurements were previously on.

           This method can only control the measurement of functional
           coverage models that are present in the register abstraction classes,
           then enabled during construction.
           See the `UVMReg.has_coverage` method to identify
           the available functional coverage models.

        Args:
            is_on:
        Returns:
        """
        if is_on == UVM_NO_COVERAGE:
            self.m_cover_on = is_on
            return self.m_cover_on

        self.m_cover_on = self.m_has_cover & is_on
        return self.m_cover_on


    def get_coverage(self, is_on):
        """
           Function: get_coverage

           Check if coverage measurement is on.

           Returns TRUE if measurement for all of the specified functional
           coverage models are currently on.
           Multiple functional coverage models can be specified by adding the
           functional coverage model identifiers.

           See `UVMReg.set_coverage` for more details.

        Args:
            is_on:
        Returns:
        """
        if (self.has_coverage(is_on) == 0):
            return False
        return ((self.m_cover_on & is_on) == is_on)


    def sample(self, data, byte_en, is_read, _map):
        """
           Function: sample

           Functional coverage measurement method

           This method is invoked by the register abstraction class
           whenever it is read or written with the specified `data`
           via the specified address `map`.
           It is invoked after the read or write operation has completed
           but before the mirror has been updated.

           Empty by default, this method may be extended by the
           abstraction class generator to perform the required sampling
           in any provided functional coverage model.

          protected virtual function void sample(uvm_reg_data_t  data,
                                                 uvm_reg_data_t  byte_en,
                                                 bit             is_read,
                                                 uvm_reg_map     map)
        Args:
            data:
            byte_en:
            is_read:
            _map:
        """
        pass


    def sample_values(self):
        """
           Function: sample_values

           Functional coverage measurement method for field values

           This method is invoked by the user
           or by the <uvm_reg_block::sample_values()> method of the parent block
           to trigger the sampling
           of the current field values in the
           register-level functional coverage model.

           This method may be extended by the
           abstraction class generator to perform the required sampling
           in any provided field-value functional coverage model.

        """
        pass


    def XsampleX(self, data, byte_en, is_read, _map):
        """
          /*local*/ function void XsampleX(uvm_reg_data_t  data,
                                           uvm_reg_data_t  byte_en,
                                           bit             is_read,
                                           uvm_reg_map     map)
        Args:
            data:
            byte_en:
            is_read:
            _map:
        """
        self.sample(data, byte_en, is_read, _map)


    #   //-----------------
    #   // Group: Callbacks
    #   //-----------------
    #   TODO `uvm_register_cb(uvm_reg, uvm_reg_cbs)


    #   // Task: pre_write
    #   //
    #   // Called before register write.
    #   //
    #   // If the specified data value, access ~path~ or address ~map~ are modified,
    #   // the updated data value, access path or address map will be used
    #   // to perform the register operation.
    #   // If the ~status~ is modified to anything other than <UVM_IS_OK>,
    #   // the operation is aborted.
    #   //
    #   // The registered callback methods are invoked after the invocation
    #   // of this method.
    #   // All register callbacks are executed before the corresponding
    #   // field callbacks
    #   //
    async def pre_write(self, rw):
        pass


    async def post_write(self, rw):
        """
           Task: post_write

           Called after register write.

           If the specified `status` is modified,
           the updated status will be
           returned by the register operation.

           The registered callback methods are invoked before the invocation
           of this method.
           All register callbacks are executed before the corresponding
           field callbacks

        Args:
            rw:
        """
        pass


    async def pre_read(self, rw):
        """
           Task: pre_read

           Called before register read.

           If the specified access `path` or address `map` are modified,
           the updated access path or address map will be used to perform
           the register operation.
           If the `status` is modified to anything other than `UVM_IS_OK`,
           the operation is aborted.

           The registered callback methods are invoked after the invocation
           of this method.
           All register callbacks are executed before the corresponding
           field callbacks

        Args:
            rw:
        """
        pass

    async def post_read(self, rw):
        """
        Called after register read.

        If the specified readback data or `status` is modified,
        the updated readback data or status will be
        returned by the register operation.

        The registered callback methods are invoked before the invocation
        of this method.
        All register callbacks are executed before the corresponding
        field callbacks

        Args:
            rw:
        """
        pass


    #   extern virtual function void            do_print (uvm_printer printer)

    def convert2string(self):
        """
        Converts this register into string.

        Returns:
            str: String representation of this register.
        """
        prefix = ""
        convert2string = sv.sformatf("Register %s -- %0d bytes, mirror value:'h%h",
            self.get_full_name(), self.get_n_bytes(),self.get())

        if self.m_maps.num() == 0:
            convert2string = convert2string + "  (unmapped)\n"
        else:
            convert2string = convert2string + "\n"
        for key in self.m_maps.key_list():
            parent_map = key  # uvm_reg_map
            offset = 0
            while parent_map is not None:
                this_map = parent_map  # uvm_reg_map
                parent_map = this_map.get_parent_map()
                offset = this_map.get_base_addr(UVM_NO_HIER)
                if parent_map is not None:
                    offset = parent_map.get_submap_offset(this_map)
                prefix += "  "
                e = this_map.get_endian()  # uvm_endianness_e
                convert2string += sv.sformatf("%sMapped in '%s' -- %d bytes, %s, offset 'h%0h\n",
                    prefix, this_map.get_full_name(), this_map.get_n_bytes(),
                    str(e), offset)

        prefix = "  "
        for i in range(len(self.m_fields)):
            convert2string += sv.sformatf("\n%s", self.m_fields[i].convert2string())

        if self.m_read_in_progress is True:
            res_str = ""
            if self.m_fname != "" and self.m_lineno != 0:
                res_str  = sv.sformatf("%s:%0d ",self.m_fname, self.m_lineno)
            convert2string += "\n" + res_str + "currently executing read method"

        if self.m_write_in_progress is True:
            res_str = ""
            if self.m_fname != "" and self.m_lineno != 0:
                res_str  = sv.sformatf("%s:%0d ",self.m_fname, self.m_lineno)
            convert2string += "\n" + res_str + "currently executing write method"
        return convert2string


    #   extern virtual function uvm_object      clone      ()
    #   extern virtual function void            do_copy    (uvm_object rhs)
    #   extern virtual function bit             do_compare (uvm_object  rhs,
    #                                                       uvm_comparer comparer)
    #   extern virtual function void            do_pack    (uvm_packer packer)
    #   extern virtual function void            do_unpack  (uvm_packer packer)
    #
    #endclass: uvm_reg


#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#//----------------------
#// Group- User Frontdoor
#//----------------------
#
#// set_frontdoor
#
#function void uvm_reg::set_frontdoor(uvm_reg_frontdoor ftdr,
#                                     uvm_reg_map       map = None,
#                                     string            fname = "",
#                                     int               lineno = 0)
#   uvm_reg_map_info map_info
#   ftdr.fname = self.m_fname
#   ftdr.lineno = self.m_lineno
#   map = get_local_map(map, "set_frontdoor()")
#   if (map is None)
#     return
#   map_info = map.get_reg_map_info(this)
#   if (map_info is None)
#      map.add_reg(this, -1, "RW", 1, ftdr)
#   else begin
#      map_info.frontdoor = ftdr
#   end
#endfunction: set_frontdoor
#
#
#// get_frontdoor
#
#function uvm_reg_frontdoor uvm_reg::get_frontdoor(uvm_reg_map map = None)
#   uvm_reg_map_info map_info
#   map = get_local_map(map, "get_frontdoor()")
#   if (map is None)
#     return None
#   map_info = map.get_reg_map_info(this)
#   return map_info.frontdoor
#endfunction: get_frontdoor
#
#
#// set_backdoor
#
#function void uvm_reg::set_backdoor(uvm_reg_backdoor bkdr,
#                                    string           fname = "",
#                                    int              lineno = 0)
#   bkdr.fname = fname
#   bkdr.lineno = lineno
#   if (self.m_backdoor is not None &&
#       self.m_backdoor.has_update_threads()):
#      `uvm_warning("RegModel", "Previous register backdoor still has update threads running. Backdoors with active mirroring should only be set before simulation starts.")
#   end
#   self.m_backdoor = bkdr
#endfunction: set_backdoor
#
#
#
#
#
#// clear_hdl_path
#
#function void uvm_reg::clear_hdl_path(string kind = "RTL")
#  if (kind == "ALL"):
#    self.m_hdl_paths_pool = new("hdl_paths")
#    return
#  end
#
#  if (kind == ""):
#     if (self.m_regfile_parent is not None)
#        kind = self.m_regfile_parent.get_default_hdl_path()
#     else
#        kind = self.m_parent.get_default_hdl_path()
#  end
#
#  if (!self.m_hdl_paths_pool.exists(kind)):
#    `uvm_warning("RegModel",{"Unknown HDL Abstraction '",kind,"'"})
#    return
#  end
#
#  self.m_hdl_paths_pool.delete(kind)
#endfunction
#
#
#
#
#// get_hdl_path_kinds
#
#function void uvm_reg::get_hdl_path_kinds (ref string kinds[$])
#  string kind
#  kinds.delete()
#  if (!self.m_hdl_paths_pool.first(kind))
#    return
#  do
#    kinds.append(kind)
#  while (self.m_hdl_paths_pool.next(kind))
#endfunction
#
#
#// get_hdl_path
#
#function void uvm_reg::get_hdl_path(ref uvm_hdl_path_concat paths[$],
#                                        input string kind = "")
#
#  uvm_queue #(uvm_hdl_path_concat) hdl_paths
#
#  if (kind == ""):
#     if (self.m_regfile_parent is not None)
#        kind = self.m_regfile_parent.get_default_hdl_path()
#     else
#        kind = self.m_parent.get_default_hdl_path()
#  end
#
#  if (!has_hdl_path(kind)):
#    `uvm_error("RegModel",
#       {"Register does not have hdl path defined for abstraction '",kind,"'"})
#    return
#  end
#
#  hdl_paths = self.m_hdl_paths_pool.get(kind)
#
#  for (int i=0; i<hdl_paths.size();i++):
#     paths.append(hdl_paths.get(i))
#  end
#
#endfunction
#
#
#// get_reset
#
#function uvm_reg_data_t uvm_reg::get_reset(string kind = "HARD")
#   // Concatenate the value of the individual fields
#   // to form the register value
#   get_reset = 0
#
#   foreach (self.m_fields[i])
#      get_reset |= self.m_fields[i].get_reset(kind) << self.m_fields[i].get_lsb_pos()
#endfunction: get_reset
#
#
#// has_reset
#
#function bit uvm_reg::has_reset(string kind = "HARD",
#                                bit    delete = 0)
#
#   has_reset = 0
#   foreach (self.m_fields[i]):
#      has_reset |= self.m_fields[i].has_reset(kind, delete)
#      if (!delete && has_reset)
#        return True
#   end
#endfunction: has_reset
#
#
#// set_reset
#
#function void uvm_reg::set_reset(uvm_reg_data_t value,
#                                 string         kind = "HARD")
#   foreach (self.m_fields[i]):
#      self.m_fields[i].set_reset(value >> self.m_fields[i].get_lsb_pos(), kind)
#   end
#endfunction: set_reset
#
#
#
#// Xis_loacked_by_fieldX
#
#function bit uvm_reg::Xis_locked_by_fieldX()
#  return self.m_is_locked_by_field
#endfunction
#
#
#
#
#
#
#
#
#// poke
#
#task uvm_reg::poke(output uvm_status_e      status,
#                   input  uvm_reg_data_t    value,
#                   input  string            kind = "",
#                   input  uvm_sequence_base parent = None,
#                   input  uvm_object        extension = None,
#                   input  string            fname = "",
#                   input  int               lineno = 0)
#
#   uvm_reg_backdoor bkdr = get_backdoor()
#   uvm_reg_item rw
#
#   self.m_fname = fname
#   self.m_lineno = lineno
#
#
#   if (bkdr is None && !has_hdl_path(kind)):
#      `uvm_error("RegModel",
#        {"No backdoor access available to poke register '",get_full_name(),"'"})
#      status = UVM_NOT_OK
#      return
#   end
#
#   rw = uvm_reg_item::type_id::create("reg_poke_item",,get_full_name())
#   if (!self.m_is_locked_by_field)
#     yield self.XatomicX(1, rw)
#
#   // create an abstract transaction for this operation
#   rw.element      = this
#   rw.path         = UVM_BACKDOOR
#   rw.element_kind = UVM_REG
#   rw.kind         = UVM_WRITE
#   rw.bd_kind      = kind
#   rw.value[0]     = value & ((1 << self.m_n_bits)-1)
#   rw.parent       = parent
#   rw.extension    = extension
#   rw.fname        = fname
#   rw.lineno       = lineno
#
#   if (bkdr is not None)
#     bkdr.write(rw)
#   else
#     backdoor_write(rw)
#
#   status = rw.status
#
#   `uvm_info("RegModel", $sformatf("Poked register \"%s\": 'h%h",
#                              get_full_name(), value),UVM_HIGH)
#
#   do_predict(rw, UVM_PREDICT_WRITE)
#
#   if (!self.m_is_locked_by_field)
#     yield self.XatomicX(0)
#endtask: poke
#
#
#// peek
#
#task uvm_reg::peek(output uvm_status_e      status,
#                   output uvm_reg_data_t    value,
#                   input  string            kind = "",
#                   input  uvm_sequence_base parent = None,
#                   input  uvm_object        extension = None,
#                   input  string            fname = "",
#                   input  int               lineno = 0)
#
#   uvm_reg_backdoor bkdr = get_backdoor()
#   uvm_reg_item rw
#
#   self.m_fname = fname
#   self.m_lineno = lineno
#
#   if (bkdr is None && !has_hdl_path(kind)):
#      `uvm_error("RegModel",
#        $sformatf("No backdoor access available to peek register \"%s\"",
#                  get_full_name()))
#      status = UVM_NOT_OK
#      return
#   end
#
#   rw = uvm_reg_item::type_id::create("mem_peek_item",,get_full_name())
#   if(!self.m_is_locked_by_field)
#      yield self.XatomicX(1, rw)
#
#   // create an abstract transaction for this operation
#   rw.element      = this
#   rw.path         = UVM_BACKDOOR
#   rw.element_kind = UVM_REG
#   rw.kind         = UVM_READ
#   rw.bd_kind      = kind
#   rw.parent       = parent
#   rw.extension    = extension
#   rw.fname        = fname
#   rw.lineno       = lineno
#
#   if (bkdr is not None)
#     bkdr.read(rw)
#   else
#     backdoor_read(rw)
#
#   status = rw.status
#   value = rw.value[0]
#
#   `uvm_info("RegModel", $sformatf("Peeked register \"%s\": 'h%h",
#                          get_full_name(), value),UVM_HIGH)
#
#   do_predict(rw, UVM_PREDICT_READ)
#
#   if (!self.m_is_locked_by_field)
#      yield self.XatomicX(0)
#endtask: peek
#
#
#
#
#//-------------
#// STANDARD OPS
#//-------------
#
#
#// do_print
#
#function void uvm_reg::do_print (uvm_printer printer)
#  uvm_reg_field f[$]
#  super.do_print(printer)
#  get_fields(f)
#  foreach(f[i]) printer.print_generic(f[i].get_name(),f[i].get_type_name(),-2,f[i].convert2string())
#endfunction
#
#
#
#// clone
#
#function uvm_object uvm_reg::clone()
#  `uvm_fatal("RegModel","RegModel registers cannot be cloned")
#  return None
#endfunction
#
#// do_copy
#
#function void uvm_reg::do_copy(uvm_object rhs)
#  `uvm_fatal("RegModel","RegModel registers cannot be copied")
#endfunction
#
#
#// do_compare
#
#function bit uvm_reg::do_compare (uvm_object  rhs,
#                                        uvm_comparer comparer)
#  `uvm_warning("RegModel","RegModel registers cannot be compared")
#  return False
#endfunction
#
#
#// do_pack
#
#function void uvm_reg::do_pack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel registers cannot be packed")
#endfunction
#
#
#// do_unpack
#
#function void uvm_reg::do_unpack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel registers cannot be unpacked")
#endfunction
