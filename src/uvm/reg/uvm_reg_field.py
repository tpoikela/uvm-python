#
#-------------------------------------------------------------
#   Copyright 2004-2009 Synopsys, Inc.
#   Copyright 2010-2011 Mentor Graphics Corporation
#   Copyright 2010-2011 Cadence Design Systems, Inc.
#   Copyright 2013 Semifore, Inc.
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
#    TODO add modifications
#-------------------------------------------------------------

from typing import Dict

from ..base.uvm_object import UVMObject
from ..base.uvm_globals import uvm_report_error, uvm_report_warning
from ..base.uvm_resource_db import UVMResourceDb
from ..macros.uvm_object_defines import uvm_object_utils
from ..macros.uvm_message_defines import uvm_error
from .uvm_reg_model import (UVM_CHECK, UVM_FRONTDOOR, UVM_IS_OK, UVM_NOT_OK, UVM_NO_CHECK,
                            UVM_NO_COVERAGE, UVM_PREDICT, UVM_PREDICT_DIRECT, UVM_PREDICT_READ,
                            UVM_PREDICT_WRITE, uvm_fatal)
from .uvm_reg_item import UVMRegItem
from .uvm_reg_cbs import UVMRegFieldCbIter

NO_RAND_SET = {"RO", "RC", "RS", "WC", "WS",
        "W1C", "W1S", "W1T", "W0C", "W0S", "W0T",
        "W1SRC", "W1CRS", "W0SRC", "W0CRS", "WSRC", "WCRS",
        "WOC", "WOS"}

KNOWN_ACCESSES = ["RO", "RW", "RC", "RS", "WC", "WS", "W1C", "W1S", "W1T",
        "W0C", "W0S", "W0T", "WRC", "WRS", "W1SRC", "W1CRS", "W0SRC", "W0CRS",
        "WSRC", "WCRS", "WO", "WOC", "WOS", "W1", "WO1"]

#constraint uvm_reg_field_valid {
#   if (`UVM_REG_DATA_WIDTH > self.m_size) {
#      value < (`UVM_REG_DATA_WIDTH'h1 << self.m_size)
#   }
#}


class UVMRegField(UVMObject):
    """
    Field abstraction class

    A field represents a set of bits that behave consistently
    as a single entity.

    A field is contained within a single register, but may
    have different access policies depending on the address map
    use the access the register (thus the field).
    """

    m_max_size = 0
    m_policy_names = {}  # type: Dict[str, int]
    m_predefined = False



    def __init__(self, name='uvm_reg_field'):
        """
        This method should not be used directly.
        The `UVMRegField.type_id.create()` factory method
        should be used instead.

        Args:
            name: (str): Name of the register field
        """
        UVMObject.__init__(self, name)
        self.value = 0  # Mirrored after randomize()
        self.m_mirrored = 0  # What we think is in the HW
        self.m_desired = 0  # Mirrored after set()
        self.m_access = ""
        self.m_parent = None  # uvm_reg
        self.m_lsb = 0
        self.m_size = 0
        self.m_volatile = False
        self.m_reset = {}  # string -> uvm_reg_data_t
        self.m_written = False
        self.m_read_in_progress = False
        self.m_write_in_progress = False
        self.m_fname = ""
        self.m_lineno = 0
        self.m_cover_on = 0
        self.m_individually_accessible = False
        self.m_check = UVM_CHECK  # uvm_check_e
        if UVMRegField.m_predefined is False:
            UVMRegField.m_predefined = UVMRegField.m_predefine_policies()


    def configure(self, parent, size, lsb_pos, access, volatile, reset, has_reset, is_rand,
            individually_accessible):
        """
        Instance-specific configuration

        Specify the `parent` register of this field, its
        `size` in bits, the position of its least-significant bit
        within the register relative to the least-significant bit
        of the register, its `access` policy, volatility,
        "HARD" `reset` value,
        whether the field value is actually reset
        (the `reset` value is ignored if `FALSE`),
        whether the field value may be randomized and
        whether the field is the only one to occupy a byte lane in the register.

        See `set_access` for a specification of the pre-defined
        field access policies.

        If the field access policy is a pre-defined policy and NOT one of
        "RW", "WRC", "WRS", "WO", "W1", or "WO1",
        the value of `is_rand` is ignored and the rand_mode() for the
        field instance is turned off since it cannot be written.

        Args:
            parent (UVMReg): Parent register.
            size (int): Size of the field in bits
            lsb_pos (int): LSB position of the field.
            access (str): Access of the fields (ie "RW" or "RO")
            volatile (bool):
            reset:
            has_reset (bool):
            is_rand (bool):
            individually_accessible (bool)
        """
        self.m_parent = parent
        if size == 0:
            uvm_report_error("RegModel",
               "Field \"{}\" cannot have 0 bits".format(self.get_full_name()))
            size = 1

        self.m_size      = size
        self.rand('value', range(1 << size))
        self.m_volatile  = volatile
        self.m_access    = access.upper()
        self.m_lsb       = lsb_pos
        self.m_cover_on  = UVM_NO_COVERAGE
        self.m_written   = False
        if volatile:
            self.m_check = UVM_NO_CHECK
        else:
            self.m_check = self.m_check
        self.m_individually_accessible = individually_accessible

        if has_reset:
            self.set_reset(reset)
        else:
            UVMResourceDb.set("REG::" + self.get_full_name(),
                   "NO_REG_HW_RESET_TEST", 1)

        self.m_parent.add_field(self)

        if not (self.m_access in UVMRegField.m_policy_names):
            uvm_report_error("RegModel", ("Access policy '" + access
             + "' for field '" + self.get_full_name() + "' is not defined.  Setting to RW"))
            self.m_access = "RW"

        if size > UVMRegField.m_max_size:
            UVMRegField.m_max_size = size

        # Ignore is_rand if the field is known not to be writeable
        # i.e. not "RW", "WRC", "WRS", "WO", "W1", "WO1"
        if access in NO_RAND_SET:
            self.is_rand = False
        #if not is_rand:
        #    self.value.rand_mode(0)

    #---------------------
    # Group: Introspection
    #---------------------

    def get_full_name(self):
        """
        Get the hierarchical name

        Return the hierarchal name of this field
        The base of the hierarchical name is the root block.

        Returns:
            str: Full hier name (including parent's name)
        """
        return self.m_parent.get_full_name() + "." + self.get_name()

    def get_parent(self):
        """
        Get the parent register

        Returns:
            UVMReg: Parent register of this field
        """
        return self.m_parent

    def get_register(self):
        """
        Get the parent register

        Returns:
            UVMReg: Parent register of this field
        """
        return self.m_parent

    def get_lsb_pos(self):
        """
        Return the position of the field

        Returns the index of the least significant bit of the field
        in the register that instantiates it.
        An offset of 0 indicates a field that is aligned with the
        least-significant bit of the register.

        Returns:
            int: LSB position of this field
        """
        return self.m_lsb

    def get_n_bits(self):
        """
           Returns the width, in number of bits, of the field.

        Returns:
            int: Width of the field in bits
        """
        return self.m_size

    @classmethod
    def get_max_size(cls):
        """
        Function: get_max_size
        Returns the width, in number of bits, of the largest field.

        Returns:
            int: Width of largest field
        """
        return UVMRegField.m_max_size


    def set_access(self, mode):
        """
        Modify the access policy of the field

        Modify the access policy of the field to the specified one and
        return the previous access policy.

        The pre-defined access policies are as follows.
        The effect of a read operation are applied after the current
        value of the field is sampled.
        The read operation will return the current value,
        not the value affected by the read operation (if any)::

            "RO"       - W: no effect, R: no effect
            "RW"       - W: as-is, R: no effect
            "RC"       - W: no effect, R: clears all bits
            "RS"       - W: no effect, R: sets all bits
            "WRC"      - W: as-is, R: clears all bits
            "WRS"      - W: as-is, R: sets all bits
            "WC"       - W: clears all bits, R: no effect
            "WS"       - W: sets all bits, R: no effect
            "WSRC"     - W: sets all bits, R: clears all bits
            "WCRS"     - W: clears all bits, R: sets all bits
            "W1C"      - W: 1/0 clears/no effect on matching bit, R: no effect
            "W1S"      - W: 1/0 sets/no effect on matching bit, R: no effect
            "W1T"      - W: 1/0 toggles/no effect on matching bit, R: no effect
            "W0C"      - W: 1/0 no effect on/clears matching bit, R: no effect
            "W0S"      - W: 1/0 no effect on/sets matching bit, R: no effect
            "W0T"      - W: 1/0 no effect on/toggles matching bit, R: no effect
            "W1SRC"    - W: 1/0 sets/no effect on matching bit, R: clears all bits
            "W1CRS"    - W: 1/0 clears/no effect on matching bit, R: sets all bits
            "W0SRC"    - W: 1/0 no effect on/sets matching bit, R: clears all bits
            "W0CRS"    - W: 1/0 no effect on/clears matching bit, R: sets all bits
            "WO"       - W: as-is, R: error
            "WOC"      - W: clears all bits, R: error
            "WOS"      - W: sets all bits, R: error
            "W1"       - W: 1st W after ``HARD`` reset is as-is, other W have no effects, R: no effect
            "WO1"      - W: 1st W after ``HARD`` reset is as-is, other W have no effects, R: error
            "NOACCESS" - W: no effect, R: no effect

        It is important to remember that modifying the access of a field
        will make the register model diverge from the specification
        that was used to create it.

        Args:
            mode (str): Mode from the list above.
        Returns:
        """
        set_access = self.m_access
        self.m_access = mode.upper()
        if self.m_access not in UVMRegField.m_policy_names:
            uvm_error("RegModel", "Access policy '" + self.m_access
                + "' is not a defined field access policy")
            self.m_access = set_access
        return set_access


    @classmethod
    def define_access(cls, name):
        """
        Define a new access policy value

        Because field access policies are specified using string values,
        there is no way for SystemVerilog to verify if a specific access
        value is valid or not.
        To help catch typing errors, user-defined access values
        must be defined using this method to avoid begin reported as an
        invalid access policy.

        The name of field access policies are always converted to all uppercase.

        Returns TRUE if the new access policy was not previously
        defined.
        Returns FALSE otherwise but does not issue an error message.

        Args:
            cls:
            name:
        Returns:
            bool: False if name already exists, True on success.
        """
        if not UVMRegField.m_predefined:
            UVMRegField.m_predefined = UVMRegField.m_predefine_policies()

        name = name.upper()
        if name in UVMRegField.m_policy_names:
            return False

        UVMRegField.m_policy_names[name] = 1
        return True

    @classmethod
    def m_predefine_policies(cls):
        """
        Internal function which creates the predefines policies.
        """
        if UVMRegField.m_predefined is True:
            return True
        UVMRegField.m_predefined = True
        UVMRegField.define_access("RO")
        UVMRegField.define_access("RW")
        UVMRegField.define_access("RC")
        UVMRegField.define_access("RS")
        UVMRegField.define_access("WRC")
        UVMRegField.define_access("WRS")
        UVMRegField.define_access("WC")
        UVMRegField.define_access("WS")
        UVMRegField.define_access("WSRC")
        UVMRegField.define_access("WCRS")
        UVMRegField.define_access("W1C")
        UVMRegField.define_access("W1S")
        UVMRegField.define_access("W1T")
        UVMRegField.define_access("W0C")
        UVMRegField.define_access("W0S")
        UVMRegField.define_access("W0T")
        UVMRegField.define_access("W1SRC")
        UVMRegField.define_access("W1CRS")
        UVMRegField.define_access("W0SRC")
        UVMRegField.define_access("W0CRS")
        UVMRegField.define_access("WO")
        UVMRegField.define_access("WOC")
        UVMRegField.define_access("WOS")
        UVMRegField.define_access("W1")
        UVMRegField.define_access("WO1")
        return True

    def get_access(self, reg_map=None):
        """
           Get the access policy of the field

           Returns the current access policy of the field
           when written and read through the specified address `map`.
           If the register containing the field is mapped in multiple
           address map, an address map must be specified.
           The access policy of a field from a specific
           address map may be restricted by the register's access policy in that
           address map.
           For example, a RW field may only be writable through one of
           the address maps and read-only through all of the other maps.
           If the field access contradicts the map's access value
           (field access of WO, and map access value of RO, etc), the
           method's return value is NOACCESS.
        Args:
            reg_map:
        Returns:
        """
        field_access = self.m_access
        from .uvm_reg_map import UVMRegMap
        if reg_map == UVMRegMap.backdoor():
            return field_access

        # Is the register restricted in this reg_map?
        rights = self.m_parent.get_rights(reg_map)
        if rights == "RW":
            # No restrictions
            return field_access
        elif rights == "RO":
            if field_access in ["RW", "RO", "WC", "WS",
                    "W1C", "W1S", "W1T", "W0C", "W0S", "W0T", "W1"]:
                field_access = "RO"
            elif field_access in ["RC", "WRC", "W1SRC", "W0SRC",
                    "WSRC"]:
                field_access = "RC"
            elif field_access in ["RS", "WRS", "W1CRS", "W0CRS", "WCRS"]:
                field_access = "RS"
            elif field_access in ["WO", "WOC", "WOS", "WO1"]:
                field_access = "NOACCESS"

        elif rights == "WO":
            field_access = "NOACCESS"
            if field_access == 'RW' or field_access == 'WO':
                field_access = "WO"
        else:
            field_access = "NOACCESS"
            fname = ""
            if reg_map is not None:
                fname = reg_map.get_full_name()
            uvm_report_warning("RegModel", ("Register '" + self.m_parent.get_full_name()
                + "' containing field '" + self.get_name() + "' is mapped in reg_map '"
                + fname + "' with unknown access right '"
                + self.m_parent.get_rights(reg_map) + "'"))
        return field_access

    def is_known_access(self, _map=None):
        """
           Check if access policy is a built-in one.

           Returns TRUE if the current access policy of the field,
           when written and read through the specified address `map`,
           is a built-in access policy.

        Args:
            _map:
        Returns:
        """
        acc = self.get_access(_map)
        if acc in KNOWN_ACCESSES:
            return 1
        return 0


    def set_volatility(self, volatile):
        """
           Function: set_volatility
           Modify the volatility of the field to the specified one.

           It is important to remember that modifying the volatility of a field
           will make the register model diverge from the specification
           that was used to create it.

        Args:
            volatile:
        """
        self.m_volatile = volatile


    def is_volatile(self):
        """
           Function: is_volatile
           Indicates if the field value is volatile

           UVM uses the IEEE 1685-2009 IP-XACT definition of "volatility".
           If TRUE, the value of the register is not predictable because it
           may change between consecutive accesses.
           This typically indicates a field whose value is updated by the DUT.
           The nature or cause of the change is not specified.
           If FALSE, the value of the register is not modified between
           consecutive accesses.

        Returns:
            bool: True if field volatile (see the definition above)
        """
        return self.m_volatile


    def set(self, value, fname="", lineno=0):
        """
          --------------
           Group: Access
          --------------


           Set the desired value for this field

           It sets the desired value of the field to the specified `value`
           modified by the field access policy.
           It does not actually set the value of the field in the design,
           only the desired value in the abstraction class.
           Use the `UVMReg.update` method to update the actual register
           with the desired value or the `UVMRegField.write` method
           to actually write the field and update its mirrored value.

           The final desired value in the mirror is a function of the field access
           policy and the set value, just like a normal physical write operation
           to the corresponding bits in the hardware.
           As such, this method (when eventually followed by a call to
           `UVMReg.update`)
           is a zero-time functional replacement for the `UVMRegField.write`
           method.
           For example, the desired value of a read-only field is not modified
           by this method and the desired value of a write-once field can only
           be set if the field has not yet been
           written to using a physical (for example, front-door) write operation.

           Use the `UVMRegField.predict` to modify the mirrored value of
           the field.
           Function: set

        Args:
            value:
            fname:
            lineno:
        """
        mask = (1 << self.m_size)-1
        self.m_fname = fname
        self.m_lineno = lineno
        if value >> self.m_size:
            uvm_report_warning("RegModel",
                "Specified value (0x{}) greater than field \"{}\" size ({} bits)".format(
                     value, self.get_name(), self.m_size))
            value = value & mask

        if self.m_parent.is_busy():
            uvm_report_warning("UVM/FLD/SET/BSY", ("Setting the value of field \"{}\" while containing"
                + "register \"{}\" is being accessed may result in loss of desired field value. "
                + "A race condition between threads concurrently accessing the register model is "
                + "the likely cause of the problem.").format(
                    self.get_name(), self.m_parent.get_full_name()))

        if self.m_access == "RO":
            self.m_desired = self.m_desired
        elif self.m_access == "RW":
            self.m_desired = value
        elif self.m_access == "RC":
            self.m_desired = self.m_desired
        elif self.m_access == "RS":
            self.m_desired = self.m_desired
        elif self.m_access == "WC":
            self.m_desired = 0
        elif self.m_access == "WS":
            self.m_desired = mask
        elif self.m_access == "WRC":
            self.m_desired = value
        elif self.m_access == "WRS":
            self.m_desired = value
        elif self.m_access == "WSRC":
            self.m_desired = mask
        elif self.m_access == "WCRS":
            self.m_desired = 0
        elif self.m_access == "W1C":
            self.m_desired = self.m_desired & (~value)
        elif self.m_access == "W1S":
            self.m_desired = self.m_desired | value
        elif self.m_access == "W1T":
            self.m_desired = self.m_desired ^ value
        elif self.m_access == "W0C":
            self.m_desired = self.m_desired & value
        elif self.m_access == "W0S":
            self.m_desired = self.m_desired | (~value & mask)
        elif self.m_access == "W0T":
            self.m_desired = self.m_desired ^ (~value & mask)
        elif self.m_access == "W1SRC":
            self.m_desired = self.m_desired | value
        elif self.m_access == "W1CRS":
            self.m_desired = self.m_desired & (~value)
        elif self.m_access == "W0SRC":
            self.m_desired = self.m_desired | (~value & mask)
        elif self.m_access == "W0CRS":
            self.m_desired = self.m_desired & value
        elif self.m_access == "WO":
            self.m_desired = value
        elif self.m_access == "WOC":
            self.m_desired = 0
        elif self.m_access == "WOS":
            self.m_desired = mask
        elif self.m_access == "W1":
            if self.m_written:
                self.m_desired = self.m_desired
            else:
                self.m_desired = value
        elif self.m_access == "WO1":
            if self.m_written:
                self.m_desired = self.m_desired
            else:
                self.m_desired = value
        else:
            self.m_desired = value
        self.value = self.m_desired


    def get(self, fname="", lineno=0):
        """
           Function: get

           Return the desired value of the field

           It does not actually read the value
           of the field in the design, only the desired value
           in the abstraction class. Unless set to a different value
           using the `UVMRegField.set`, the desired value
           and the mirrored value are identical.

           Use the `UVMRegField.read` or `UVMRegField.peek`
           method to get the actual field value.

           If the field is write-only, the desired/mirrored
           value is the value last written and assumed
           to reside in the bits implementing it.
           Although a physical read operation would something different,
           the returned value is the actual content.
        Args:
            fname:
            lineno:
        Returns:
        """
        self.m_fname = fname
        self.m_lineno = lineno
        return self.m_desired

    def get_mirrored_value(self, fname="", lineno=0):
        """

           Function: get_mirrored_value

           Return the mirrored value of the field

           It does not actually read the value of the field in the design, only the mirrored value
           in the abstraction class.

           If the field is write-only, the desired/mirrored
           value is the value last written and assumed
           to reside in the bits implementing it.
           Although a physical read operation would something different,
           the returned value is the actual content.

        Args:
            fname:
            lineno:
        Returns:
        """
        self.m_fname = fname
        self.m_lineno = lineno
        return self.m_mirrored

    def reset(self, kind = "HARD"):
        """
           Function: reset

           Reset the desired/mirrored value for this field.

           It sets the desired and mirror value of the field
           to the reset event specified by `kind`.
           If the field does not have a reset value specified for the
           specified reset `kind` the field is unchanged.

           It does not actually reset the value of the field in the design,
           only the value mirrored in the field abstraction class.

           Write-once fields can be modified after
           a "HARD" reset operation.

        Args:
            kind:
        """
        if not kind in self.m_reset:
            return
        self.m_mirrored = self.m_reset[kind]
        self.m_desired  = self.m_mirrored
        self.value      = self.m_mirrored
        if kind == "HARD":
            self.m_written  = False

    def get_reset(self, kind="HARD"):
        """

           Function: get_reset

           Get the specified reset value for this field

           Return the reset value for this field
           for the specified reset `kind`.
           Returns the current field value is no reset value has been
           specified for the specified reset event.

        Args:
            kind:
        Returns:
        """
        if not kind in self.m_reset:
            return self.m_desired
        return self.m_reset[kind]


    def has_reset(self, kind="HARD", delete=False):
        """
           Function: has_reset

           Check if the field has a reset value specified

           Return TRUE if this field has a reset value specified
           for the specified reset `kind`.
           If `delete` is TRUE, removes the reset value, if any.

        Args:
            kind:
            delete:
        Returns:
        """
        if kind not in self.m_reset:
            return False
        if delete:
            del self.m_reset[kind]
        return True

    def set_reset(self, value,kind="HARD"):
        """
           Function: set_reset

           Specify or modify the reset value for this field

           Specify or modify the reset value for this field corresponding
           to the cause specified by `kind`.

        Args:
            value:
            kind:
        """
        self.m_reset[kind] = value & ((1 << self.m_size) - 1)

    def needs_update(self):
        """
           Function: needs_update

           Check if the abstract model contains different desired and mirrored values.

           If a desired field value has been modified in the abstraction class
           without actually updating the field in the DUT,
           the state of the DUT (more specifically what the abstraction class
           `thinks` the state of the DUT is) is outdated.
           This method returns TRUE
           if the state of the field in the DUT needs to be updated
           to match the desired value.
           The mirror values or actual content of DUT field are not modified.
           Use the `UVMReg.update` to actually update the DUT field.

        Returns:
        """
        return (self.m_mirrored != self.m_desired) or self.m_volatile

    #
    #   // Task: write
    #   //
    #   // Write the specified value in this field
    #   //
    #   // Write ~value~ in the DUT field that corresponds to this
    #   // abstraction class instance using the specified access
    #   // ~path~.
    #   // If the register containing this field is mapped in more
    #   //  than one address map,
    #   // an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   // If a back-door access path is used, the effect of writing
    #   // the field through a physical access is mimicked. For
    #   // example, read-only bits in the field will not be written.
    #   //
    #   // The mirrored value will be updated using the `UVMRegField.predict`
    #   // method.
    #   //
    #   // If a front-door access is used, and
    #   // if the field is the only field in a byte lane and
    #   // if the physical interface corresponding to the address map used
    #   // to access the field support byte-enabling,
    #   // then only the field is written.
    #   // Otherwise, the entire register containing the field is written,
    #   // and the mirrored values of the other fields in the same register
    #   // are used in a best-effort not to modify their value.
    #   //
    #   // If a backdoor access is used, a peek-modify-poke process is used.
    #   // in a best-effort not to modify the value of the other fields in the
    #   // register.
    #   //
    #   extern virtual task write (output uvm_status_e       status,
    #                              input  uvm_reg_data_t     value,
    #                              input  uvm_path_e         path = UVM_DEFAULT_PATH,
    #                              input  uvm_reg_map        map = null,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)



    #   // Task: read
    #   //
    #   // Read the current value from this field
    #   //
    #   // Read and return ~value~ from the DUT field that corresponds to this
    #   // abstraction class instance using the specified access
    #   // ~path~.
    #   // If the register containing this field is mapped in more
    #   // than one address map, an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   // If a back-door access path is used, the effect of reading
    #   // the field through a physical access is mimicked. For
    #   // example, clear-on-read bits in the field will be set to zero.
    #   //
    #   // The mirrored value will be updated using the `UVMRegField.predict`
    #   // method.
    #   //
    #   // If a front-door access is used, and
    #   // if the field is the only field in a byte lane and
    #   // if the physical interface corresponding to the address map used
    #   // to access the field support byte-enabling,
    #   // then only the field is read.
    #   // Otherwise, the entire register containing the field is read,
    #   // and the mirrored values of the other fields in the same register
    #   // are updated.
    #   //
    #   // If a backdoor access is used, the entire containing register is peeked
    #   // and the mirrored value of the other fields in the register is updated.
    #   //
    #   extern virtual task read  (output uvm_status_e       status,
    #                              output uvm_reg_data_t     value,
    #                              input  uvm_path_e         path = UVM_DEFAULT_PATH,
    #                              input  uvm_reg_map        map = null,
    #                              input  uvm_sequence_base  parent = null,
    #                              input  int                prior = -1,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #

    #   // Task: poke
    #   //
    #   // Deposit the specified value in this field
    #   //
    #   // Deposit the value in the DUT field corresponding to this
    #   // abstraction class instance, as-is, using a back-door access.
    #   // A peek-modify-poke process is used
    #   // in a best-effort not to modify the value of the other fields in the
    #   // register.
    #   //
    #   // The mirrored value will be updated using the `UVMRegField.predict`
    #   // method.
    #   //
    #   extern virtual task poke  (output uvm_status_e       status,
    #                              input  uvm_reg_data_t     value,
    #                              input  string             kind = "",
    #                              input  uvm_sequence_base  parent = null,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #

    #   // Task: peek
    #   //
    #   // Read the current value from this field
    #   //
    #   // Sample the value in the DUT field corresponding to this
    #   // abstraction class instance using a back-door access.
    #   // The field value is sampled, not modified.
    #   //
    #   // Uses the HDL path for the design abstraction specified by ~kind~.
    #   //
    #   // The entire containing register is peeked
    #   // and the mirrored value of the other fields in the register
    #   // are updated using the `UVMRegField.predict` method.
    #   //
    #   //
    #   extern virtual task peek  (output uvm_status_e       status,
    #                              output uvm_reg_data_t     value,
    #                              input  string             kind = "",
    #                              input  uvm_sequence_base  parent = null,
    #                              input  uvm_object         extension = null,
    #                              input  string             fname = "",
    #                              input  int                lineno = 0)
    #
    #

    #   // Task: mirror
    #   //
    #   // Read the field and update/check its mirror value
    #   //
    #   // Read the field and optionally compared the readback value
    #   // with the current mirrored value if ~check~ is <UVself.m_check>.
    #   // The mirrored value will be updated using the <predict()>
    #   // method based on the readback value.
    #   //
    #   // The ~path~ argument specifies whether to mirror using
    #   // the  <UVM_FRONTDOOR> (<read>) or
    #   // <UVM_BACKDOOR> (<peek()>).
    #   //
    #   // If ~check~ is specified as <UVself.m_check>,
    #   // an error message is issued if the current mirrored value
    #   // does not match the readback value, unless <set_compare> was used
    #   // disable the check.
    #   //
    #   // If the containing register is mapped in multiple address maps and physical
    #   // access is used (front-door access), an address ~map~ must be specified.
    #   // For write-only fields, their content is mirrored and optionally
    #   // checked only if a UVM_BACKDOOR
    #   // access path is used to read the field.
    #   //
    #   extern virtual task mirror(output uvm_status_e      status,
    #                              input  uvm_check_e       check = UVM_NO_CHECK,
    #                              input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                              input  uvm_reg_map       map = null,
    #                              input  uvm_sequence_base parent = null,
    #                              input  int               prior = -1,
    #                              input  uvm_object        extension = null,
    #                              input  string            fname = "",
    #                              input  int               lineno = 0)
    #
    #

    def set_compare(self, check=UVM_CHECK):
        """
        Sets the compare policy during a mirror update.
        The field value is checked against its mirror only when both the
        `check` argument in `UVMRegBlock.mirror`, `UVMReg.mirror`,
        or `UVMRegField.mirror` and the compare policy for the
        field is `UVMRegField.m_check`.

        Args:
            check:
        """
        self.m_check = check



    def get_compare(self):
        """
        Returns the compare policy for this field.

        Returns:
        """
        return self.m_check

    #   // Function: is_indv_accessible
    #   //
    #   // Check if this field can be written individually, i.e. without
    #   // affecting other fields in the containing register.
    #   //
    #function bit uvm_reg_field::is_indv_accessible(uvm_path_e  path,
    #                                               uvm_reg_map local_map)
    #   if (path == UVM_BACKDOOR) begin
    #      `uvm_warning("RegModel",
    #         {"Individual BACKDOOR field access not available for field '",
    #         get_full_name(), "'. Accessing complete register instead."})
    #      return 0
    #   end
    #
    #   if (!self.m_individually_accessible) begin
    #         `uvm_warning("RegModel",
    #            {"Individual field access not available for field '",
    #            get_full_name(), "'. Accessing complete register instead."})
    #      return 0
    #   end
    #
    #   // Cannot access individual fields if the container register
    #   // has a user-defined front-door
    #   if (self.m_parent.get_frontdoor(local_map) != null) begin
    #      `uvm_warning("RegModel",
    #                   {"Individual field access not available for field '",
    #                    get_name(), "' because register '", self.m_parent.get_full_name(), "' has a user-defined front-door. Accessing complete register instead."})
    #      return 0
    #   end
    #
    #   begin
    #     uvm_reg_map system_map = local_map.get_root_map()
    #     uvm_reg_adapter adapter = system_map.get_adapter()
    #     if (adapter.supports_byte_enable)
    #       return 1
    #   end
    #
    #   begin
    #     int fld_idx
    #     int bus_width = local_map.get_n_bytes()
    #     uvm_reg_field fields[$]
    #     bit sole_field
    #
    #     self.m_parent.get_fields(fields)
    #
    #     if (fields.size() == 1) begin
    #        sole_field = 1
    #     end
    #     else begin
    #        int prev_lsb,this_lsb,next_lsb;
    #        int prev_sz,this_sz,next_sz;
    #        int bus_sz = bus_width*8
    #
    #        foreach (fields[i]) begin
    #           if (fields[i] == this) begin
    #              fld_idx = i
    #              break
    #           end
    #        end
    #
    #        this_lsb = fields[fld_idx].get_lsb_pos()
    #        this_sz  = fields[fld_idx].get_n_bits()
    #
    #        if (fld_idx>0) begin
    #          prev_lsb = fields[fld_idx-1].get_lsb_pos()
    #          prev_sz  = fields[fld_idx-1].get_n_bits()
    #        end
    #
    #        if (fld_idx < fields.size()-1) begin
    #          next_lsb = fields[fld_idx+1].get_lsb_pos()
    #          next_sz  = fields[fld_idx+1].get_n_bits()
    #        end
    #
    #        // if first field in register
    #        if (fld_idx == 0 &&
    #           ((next_lsb % bus_sz) == 0 ||
    #            (next_lsb - this_sz) > (next_lsb % bus_sz)))
    #           return 1
    #
    #        // if last field in register
    #        else if (fld_idx == (fields.size()-1) &&
    #            ((this_lsb % bus_sz) == 0 ||
    #             (this_lsb - (prev_lsb + prev_sz)) >= (this_lsb % bus_sz)))
    #           return 1
    #
    #        // if somewhere in between
    #        else begin
    #           if ((this_lsb % bus_sz) == 0) begin
    #              if ((next_lsb % bus_sz) == 0 ||
    #                  (next_lsb - (this_lsb + this_sz)) >= (next_lsb % bus_sz))
    #                 return 1
    #           end
    #           else begin
    #              if ( (next_lsb - (this_lsb + this_sz)) >= (next_lsb % bus_sz) &&
    #                  ((this_lsb - (prev_lsb + prev_sz)) >= (this_lsb % bus_sz)) )
    #                 return 1
    #           end
    #        end
    #     end
    #   end
    #
    #   `uvm_warning("RegModel",
    #       {"Target bus does not support byte enabling, and the field '",
    #       get_full_name(),"' is not the only field within the entire bus width. ",
    #       "Individual field access will not be available. ",
    #       "Accessing complete register instead."})
    #
    #   return 0
    #
    #endfunction


    def predict(self, value, be=-1, kind=UVM_PREDICT_DIRECT, path=UVM_FRONTDOOR,
            _map=None, fname="", lineno=0):
        """
        Update the mirrored and desired value for this field.

        Predict the mirror and desired value of the field based on the specified
        observed `value` on a bus using the specified address `map`.

        If `kind` is specified as `UVM_PREDICT_READ`, the value
        was observed in a read transaction on the specified address `map` or
        backdoor (if `path` is `UVM_BACKDOOR`).
        If `kind` is specified as `UVM_PREDICT_WRITE`, the value
        was observed in a write transaction on the specified address `map` or
        backdoor (if `path` is `UVM_BACKDOOR`).
        If `kind` is specified as `UVM_PREDICT_DIRECT`, the value
        was computed and is updated as-is, without regard to any access policy.
        For example, the mirrored value of a read-only field is modified
        by this method if `kind` is specified as `UVM_PREDICT_DIRECT`.

        This method does not allow an update of the mirror (or desired)
        when the register containing this field is busy executing
        a transaction because the results are unpredictable and
        indicative of a race condition in the testbench.

        Returns TRUE if the prediction was successful.

        #function bit uvm_reg_field::predict (uvm_reg_data_t    value,
                                            uvm_reg_byte_en_t be = -1,
                                            uvm_predict_e     kind = UVM_PREDICT_DIRECT,
                                            uvm_path_e        path = UVM_FRONTDOOR,
                                            uvm_reg_map       map = null,
                                            string            fname = "",
                                            int               lineno = 0)
        Args:
            value:
            be (int): Byte-enable
            kind:
            path: 
            _map (UVMRegMap):
            fname (str):
            lineno (int):
        Returns:
        """
        rw = UVMRegItem()
        rw.value[0] = value
        rw.path = path
        rw.map = _map
        rw.fname = fname
        rw.lineno = lineno
        self.do_predict(rw, kind, be)
        # predict = (rw.status == UVM_NOT_OK) ? 0 : 1
        if rw.status == UVM_NOT_OK:
            return 0
        return 1

    def _get_mask(self):
        return ((1 << self.m_size)-1)



    def XpredictX(self, cur_val, wr_val, _map):
        """
          /*local*/
          extern virtual function uvm_reg_data_t XpredictX (uvm_reg_data_t cur_val,
                                                            uvm_reg_data_t wr_val,
                                                            uvm_reg_map    map)
        Args:
            cur_val:
            wr_val:
            _map:
        Returns:
        """
        mask = self._get_mask()
        acc = self.get_access(_map)
        #   case (get_access(map))
        if acc == "RO":
            return cur_val
        elif acc == "RW":
            return wr_val
        elif acc == "RC":
            return cur_val
        elif acc == "RS":
            return cur_val
        elif acc == "WC":
            return 0
        elif acc == "WS":
            return mask
        elif acc == "WRC":
            return wr_val
        elif acc == "WRS":
            return wr_val
        elif acc == "WSRC":
            return mask
        elif acc == "WCRS":
            return 0
        elif acc == "W1C":
            return cur_val & (~wr_val)
        elif acc == "W1S":
            return cur_val | wr_val
        elif acc == "W1T":
            return cur_val ^ wr_val
        elif acc == "W0C":
            return cur_val & wr_val
        elif acc == "W0S":
            return cur_val | (~wr_val & mask)
        elif acc == "W0T":
            return cur_val ^ (~wr_val & mask)
        elif acc == "W1SRC":
            return cur_val | wr_val
        elif acc == "W1CRS":
            return cur_val & (~wr_val)
        elif acc == "W0SRC":
            return cur_val | (~wr_val & mask)
        elif acc == "W0CRS":
            return cur_val & wr_val
        elif acc == "WO":
            return wr_val
        elif acc == "WOC":
            return 0
        elif acc == "WOS":
            return mask
        elif acc == "W1":
            if (self.m_written):
                return cur_val
            else:
                return wr_val
        elif acc == "WO1":
            if (self.m_written):
                return cur_val
            else:
                return wr_val
        elif acc == "NOACCESS":
            return cur_val
        else:
            return wr_val

        uvm_fatal("RegModel", "uvm_reg_field::XpredictX(): Internal error")
        return 0
        #endfunction: XpredictX


    def XupdateX(self):
        """
        XupdateX
        Returns:
        """
        #   Figure out which value must be written to get the desired value
        #   given what we think is the current value in the hardware
        XupdateX = self.m_desired  # default action
        if self.m_access == "W1C":
            XupdateX = ~self.m_desired
        if self.m_access == "W1S":
            XupdateX = self.m_desired
        if self.m_access == "W1T":
            XupdateX = self.m_desired ^ self.m_mirrored
        if self.m_access == "W0C":
            XupdateX = self.m_desired
        if self.m_access == "W0S":
            XupdateX = ~self.m_desired
        if self.m_access == "W0T":
            XupdateX = ~(self.m_desired ^ self.m_mirrored)
        if self.m_access == "W1SRC":
            XupdateX = self.m_desired
        if self.m_access == "W1CRS":
            XupdateX = ~self.m_desired
        if self.m_access == "W0SRC":
            XupdateX = ~self.m_desired
        if self.m_access == "W0CRS":
            XupdateX = self.m_desired
        if self.m_access == "WO":
            XupdateX = self.m_desired
        if self.m_access == "WOC":
            XupdateX = self.m_desired
        if self.m_access == "WOS":
            XupdateX = self.m_desired
        if self.m_access == "W1":
            XupdateX = self.m_desired
        if self.m_access == "WO1":
            XupdateX = self.m_desired
        XupdateX = XupdateX & self._get_mask()
        return XupdateX


    #   /*local*/
    #   extern function bit Xcheck_accessX (input uvm_reg_item rw,
    #                                       output uvm_reg_map_info map_info,
    #                                       input string caller)

    #   extern virtual task do_write(uvm_reg_item rw)
    #   extern virtual task do_read(uvm_reg_item rw)

    def do_predict(self, rw, kind=UVM_PREDICT_DIRECT, be=-1):
        """
        do_predict
        Args:
            rw (UVMRegItem):
            kind:
            be (int): Byte-enable
        Raises:
        """
        field_val = rw.value[0] & self._get_mask()
        if rw.status != UVM_NOT_OK:
            rw.status = UVM_IS_OK

        # Assume that the entire field is enabled
        if (0x00000001 & be) == 0:
            raise Exception('DBG Early return field not enabled')

        self.m_fname = rw.fname
        self.m_lineno = rw.lineno
        #   case (kind)
        if kind == UVM_PREDICT_WRITE:
            #UVMRegFieldCbIter cbs = new(this)
            cbs = UVMRegFieldCbIter(self)
            if rw.path == UVM_FRONTDOOR or rw.path == UVM_PREDICT:
                field_val = self.XpredictX(self.m_mirrored, field_val, rw.map)
            self.m_written = True

            cb = cbs.first()
            while cb is not None:
                cb.post_predict(self, self.m_mirrored, field_val,
                        UVM_PREDICT_WRITE, rw.path, rw.map)
                cb = cbs.next()
            field_val &= self._get_mask()

        elif kind == UVM_PREDICT_READ:
            cbs = UVMRegFieldCbIter(self)
            if rw.path == UVM_FRONTDOOR or rw.path == UVM_PREDICT:
                acc = self.get_access(rw.map)
                if acc in ["RC", "WRC", "WSRC", "W1SRC", "W0SRC"]:
                    field_val = 0  # (clear)
                elif acc in ["RS", "WRS", "WCRS", "W1CRS", "W0CRS"]:
                    field_val = self._get_mask()  # all 1's (set)
                elif acc in ["WO", "WOC", "WOS", "WO1", "NOACCESS"]:
                    return
            # TODO callbacks

            cb = cbs.first()
            while cb is not None:
                cb.post_predict(self, self.m_mirrored, field_val,
                        UVM_PREDICT_READ, rw.path, rw.map)
                cb = cbs.next()
            field_val &= self._get_mask()

        elif UVM_PREDICT_DIRECT:
            if self.m_parent.is_busy():
                uvm_report_warning("RegModel", ("Trying to predict value of field '"
                   + self.get_name() + "' while register '" + self.m_parent.get_full_name()
                   + "' is being accessed"))
                rw.status = UVM_NOT_OK
        #   endcase

        # update the mirror with predicted value
        self.m_mirrored = field_val
        self.m_desired  = field_val
        self.value = field_val


    def pre_randomize(self):
        #   // Update the only publicly known property with the current
        #   // desired value so it can be used as a state variable should
        #   // the rand_mode of the field be turned off.
        self.value = self.m_desired


    def post_randomize(self):
        self.m_desired = self.value


    #   //-----------------
    #   // Group: Callbacks
    #   //-----------------
    #   `uvm_register_cb(uvm_reg_field, uvm_reg_cbs)

    async def pre_write(self, rw):
        """
           Called before field write.

           If the specified data value, access `path` or address `map` are modified,
           the updated data value, access path or address map will be used
           to perform the register operation.
           If the `status` is modified to anything other than `UVM_IS_OK`,
           the operation is aborted.

           The field callback methods are invoked after the callback methods
           on the containing register.
           The registered callback methods are invoked after the invocation
           of this method.

        Args:
            rw (UVMRegItem): Reg item associated with write.
        """
        #await uvm_zero_delay()
        pass

    async def post_write(self, rw):
        """
           Called after field write.

           If the specified `status` is modified,
           the updated status will be
           returned by the register operation.

           The field callback methods are invoked after the callback methods
           on the containing register.
           The registered callback methods are invoked before the invocation
           of this method.

        Args:
            rw (UVMRegItem): Reg item associated with write.
        """
        #await uvm_zero_delay()
        pass

    async def pre_read(self, rw):
        """
           Called before field read.

           If the access `path` or address `map` in the `rw` argument are modified,
           the updated access path or address map will be used to perform
           the register operation.
           If the `status` is modified to anything other than `UVM_IS_OK`,
           the operation is aborted.

           The field callback methods are invoked after the callback methods
           on the containing register.
           The registered callback methods are invoked after the invocation
           of this method.

        Args:
            rw (UVMRegItem): Reg item associated with read.
        """
        pass

    async def post_read(self, rw):
        """
           Task: post_read

           Called after field read.

           If the specified readback data or`status` in the `rw` argument is
           modified, the updated readback data or status will be
           returned by the register operation.

           The field callback methods are invoked after the callback methods
           on the containing register.
           The registered callback methods are invoked before the invocation
           of this method.

        Args:
            rw (UVMRegItem): Reg item associated with read.
        """
        pass

    #   extern virtual function void do_print (uvm_printer printer)

    def convert2string(self):
        """
        convert2string

        Returns:
            str:
        """
        fmt = ""
        res_str = ""
        t_str = ""
        with_debug_info = False
        prefix = ""
        reg_ = self.get_register()
        convert2string = ""

        fmt = "{}'h%{}h".format(self.get_n_bits(), (self.get_n_bits()-1)/4 + 1)

        mirrored = ""
        if self.m_desired != self.m_mirrored:
            mirrored = (" (Mirror: " + fmt + ")").format(self.m_mirrored)

        convert2string = ("{} {} {}[{}:{}]=" + fmt + "{}").format(prefix,
            self.get_access(),
            reg_.get_name(),
            self.get_lsb_pos() + self.get_n_bits() - 1,
            self.get_lsb_pos(), self.m_desired,
            mirrored)

        if self.m_read_in_progress == 1:
            if self.m_fname != "" and self.m_lineno != 0:
                res_str = " from {}:{}".format(self.m_fname, self.m_lineno)
            convert2string = convert2string + "\n" + "currently being read" + res_str
        if self.m_write_in_progress == 1:
            if self.m_fname != "" and self.m_lineno != 0:
                res_str += " from {}:{}".format(self.m_fname, self.m_lineno)
            convert2string = convert2string + "\n" + res_str + "currently being written"
        return convert2string


    #   extern virtual function uvm_object clone()
    #   extern virtual function void do_copy   (uvm_object rhs)
    #   extern virtual function bit  do_compare (uvm_object  rhs,
    #                                            uvm_comparer comparer)
    #   extern virtual function void do_pack (uvm_packer packer)
    #   extern virtual function void do_unpack (uvm_packer packer)


uvm_object_utils(UVMRegField)

#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#// m_predefined_policies
#
#typedef class uvm_reg_map_info
#
#// Xcheck_accessX
#
#function bit uvm_reg_field::Xcheck_accessX(input uvm_reg_item rw,
#                                           output uvm_reg_map_info map_info,
#                                           input string caller)
#
#
#   if (rw.path == UVM_DEFAULT_PATH) begin
#     uvm_reg_block blk = self.m_parent.get_block()
#     rw.path = blk.get_default_path()
#   end
#
#   if (rw.path == UVM_BACKDOOR) begin
#      if (self.m_parent.get_backdoor() == null && !self.m_parent.has_hdl_path()) begin
#         `uvm_warning("RegModel",
#            {"No backdoor access available for field '",get_full_name(),
#            "' . Using frontdoor instead."})
#         rw.path = UVM_FRONTDOOR
#      end
#      else
#        rw.map = uvm_reg_map::backdoor()
#   end
#
#   if (rw.path != UVM_BACKDOOR) begin
#
#     rw.local_map = self.m_parent.get_local_map(rw.map,caller)
#
#     if (rw.local_map == null) begin
#        `uvm_error(get_type_name(),
#           {"No transactor available to physically access memory from map '",
#            rw.map.get_full_name(),"'"})
#        rw.status = UVM_NOT_OK
#        return 0
#     end
#
#     map_info = rw.local_map.get_reg_map_info(self.m_parent)
#
#     if (map_info.frontdoor == null && map_info.unmapped) begin
#        `uvm_error("RegModel", {"Field '",get_full_name(),
#                   "' in register that is unmapped in map '",
#                   rw.map.get_full_name(),
#                   "' and does not have a user-defined frontdoor"})
#        rw.status = UVM_NOT_OK
#        return 0
#     end
#
#     if (rw.map == null)
#       rw.map = rw.local_map
#   end
#
#   return 1
#endfunction
#
#
#// write
#
#task uvm_reg_field::write(output uvm_status_e       status,
#                          input  uvm_reg_data_t     value,
#                          input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                          input  uvm_reg_map        map = null,
#                          input  uvm_sequence_base  parent = null,
#                          input  int                prior = -1,
#                          input  uvm_object         extension = null,
#                          input  string             fname = "",
#                          input  int                lineno = 0)
#
#   uvm_reg_item rw
#   rw = uvm_reg_item::type_id::create("field_write_item",,get_full_name())
#   rw.element      = this
#   rw.element_kind = UVM_FIELD
#   rw.kind         = UVM_WRITE
#   rw.value[0]     = value
#   rw.path         = path
#   rw.map          = map
#   rw.parent       = parent
#   rw.prior        = prior
#   rw.extension    = extension
#   rw.fname        = fname
#   rw.lineno       = lineno
#
#   do_write(rw)
#
#   status = rw.status
#
#endtask
#
#
#// do_write
#
#task uvm_reg_field::do_write(uvm_reg_item rw)
#
#   uvm_reg_data_t   value_adjust
#   uvm_reg_map_info map_info
#   uvm_reg_field    fields[$]
#   bit bad_side_effect
#
#   self.m_parent.XatomicX(1)
#   self.m_fname  = rw.fname
#   self.m_lineno = rw.lineno
#
#   if (!Xcheck_accessX(rw,map_info,"write()"))
#     return
#
#   self.m_write_in_progress = 1'b1
#
#   if (rw.value[0] >> self.m_size) begin
#      `uvm_warning("RegModel", {"uvm_reg_field::write(): Value greater than field '",
#                          get_full_name(),"'"})
#      rw.value[0] &= ((1<<self.m_size)-1)
#   end
#
#   // Get values to write to the other fields in register
#   self.m_parent.get_fields(fields)
#   foreach (fields[i]) begin
#
#      if (fields[i] == this) begin
#         value_adjust |= rw.value[0] << self.m_lsb
#         continue
#      end
#
#      // It depends on what kind of bits they are made of...
#      case (fields[i].get_access(rw.local_map))
#        // These...
#        "RO", "RC", "RS", "W1C", "W1S", "W1T", "W1SRC", "W1CRC":
#          // Use all 0's
#          value_adjust |= 0
#
#        // These...
#        "W0C", "W0S", "W0T", "W0SRC", "W0CRS":
#          // Use all 1's
#          value_adjust |= ((1<<fields[i].get_n_bits())-1) << fields[i].get_lsb_pos()
#
#        // These might have side effects! Bad!
#        "WC", "WS", "WCRS", "WSRC", "WOC", "WOS":
#           bad_side_effect = 1
#
#        default:
#           value_adjust |= fields[i].m_mirrored << fields[i].get_lsb_pos()
#
#      endcase
#   end
#
#`ifdef UVM_REG_NO_INDIVIDUAL_FIELD_ACCESS
#   rw.element_kind = UVM_REG
#   rw.element = self.m_parent
#   rw.value[0] = value_adjust
#   self.m_parent.do_write(rw);
#`else
#
#   if (!is_indv_accessible(rw.path,rw.local_map)) begin
#      rw.element_kind = UVM_REG
#      rw.element = self.m_parent
#      rw.value[0] = value_adjust
#      self.m_parent.do_write(rw)
#
#      if (bad_side_effect) begin
#         `uvm_warning("RegModel", $sformatf("Writing field \"%s\" will cause unintended side effects in adjoining Write-to-Clear or Write-to-Set fields in the same register", this.get_full_name()))
#      end
#   end
#   else begin
#
#     uvm_reg_map system_map = rw.local_map.get_root_map()
#     UVMRegFieldCbIter cbs = new(this)
#
#     self.m_parent.Xset_busyX(1)
#
#     rw.status = UVM_IS_OK
#
#     pre_write(rw)
#     for (uvm_reg_cbs cb=cbs.first(); cb!=null; cb=cbs.next())
#        cb.pre_write(rw)
#
#     if (rw.status != UVM_IS_OK) begin
#        self.m_write_in_progress = 1'b0
#        self.m_parent.Xset_busyX(0)
#        self.m_parent.XatomicX(0)
#
#        return
#     end
#
#     rw.local_map.do_write(rw)
#
#     if (system_map.get_auto_predict())
#        // ToDo: Call parent.XsampleX()
#        do_predict(rw, UVM_PREDICT_WRITE)
#
#     post_write(rw)
#     for (uvm_reg_cbs cb=cbs.first(); cb!=null; cb=cbs.next())
#        cb.post_write(rw)
#
#     self.m_parent.Xset_busyX(0)
#
#   end
#
#`endif
#
#   self.m_write_in_progress = 1'b0
#   self.m_parent.XatomicX(0)
#
#endtask: do_write
#
#
#// read
#
#task uvm_reg_field::read(output uvm_status_e       status,
#                         output uvm_reg_data_t     value,
#                         input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                         input  uvm_reg_map        map = null,
#                         input  uvm_sequence_base  parent = null,
#                         input  int                prior = -1,
#                         input  uvm_object         extension = null,
#                         input  string             fname = "",
#                         input  int                lineno = 0)
#
#   uvm_reg_item rw
#   rw = uvm_reg_item::type_id::create("field_read_item",,get_full_name())
#   rw.element      = this
#   rw.element_kind = UVM_FIELD
#   rw.kind         = UVM_READ
#   rw.value[0]     = 0
#   rw.path         = path
#   rw.map          = map
#   rw.parent       = parent
#   rw.prior        = prior
#   rw.extension    = extension
#   rw.fname        = fname
#   rw.lineno       = lineno
#
#   do_read(rw)
#
#   value = rw.value[0]
#   status = rw.status
#
#endtask: read
#
#
#// do_read
#
#task uvm_reg_field::do_read(uvm_reg_item rw)
#
#   uvm_reg_map_info map_info
#   bit bad_side_effect
#
#   self.m_parent.XatomicX(1)
#   self.m_fname  = rw.fname
#   self.m_lineno = rw.lineno
#   self.m_read_in_progress = 1'b1
#
#   if (!Xcheck_accessX(rw,map_info,"read()"))
#     return
#
#`ifdef UVM_REG_NO_INDIVIDUAL_FIELD_ACCESS
#   rw.element_kind = UVM_REG
#   rw.element = self.m_parent
#   self.m_parent.do_read(rw)
#   rw.value[0] = (rw.value[0] >> self.m_lsb) & ((1<<self.m_size))-1
#   bad_side_effect = 1
#`else
#
#   if (!is_indv_accessible(rw.path,rw.local_map)) begin
#      rw.element_kind = UVM_REG
#      rw.element = self.m_parent
#      bad_side_effect = 1
#      self.m_parent.do_read(rw)
#      rw.value[0] = (rw.value[0] >> self.m_lsb) & ((1<<self.m_size))-1
#   end
#   else begin
#
#     uvm_reg_map system_map = rw.local_map.get_root_map()
#     UVMRegFieldCbIter cbs = new(this)
#
#     self.m_parent.Xset_busyX(1)
#
#     rw.status = UVM_IS_OK
#
#     pre_read(rw)
#     for (uvm_reg_cbs cb = cbs.first(); cb != null; cb = cbs.next())
#        cb.pre_read(rw)
#
#     if (rw.status != UVM_IS_OK) begin
#        self.m_read_in_progress = 1'b0
#        self.m_parent.Xset_busyX(0)
#        self.m_parent.XatomicX(0)
#
#        return
#     end
#
#     rw.local_map.do_read(rw)
#
#
#     if (system_map.get_auto_predict())
#        // ToDo: Call parent.XsampleX()
#        do_predict(rw, UVM_PREDICT_READ)
#
#     post_read(rw)
#     for (uvm_reg_cbs cb=cbs.first(); cb!=null; cb=cbs.next())
#        cb.post_read(rw)
#
#     self.m_parent.Xset_busyX(0)
#
#   end
#
#`endif
#
#   self.m_read_in_progress = 1'b0
#   self.m_parent.XatomicX(0)
#
#   if (bad_side_effect) begin
#      uvm_reg_field fields[$]
#      self.m_parent.get_fields(fields)
#      foreach (fields[i]) begin
#         string mode
#         if (fields[i] == this)
#            continue
#         mode = fields[i].get_access()
#         if (mode == "RC" ||
#             mode == "RS" ||
#             mode == "WRC" ||
#             mode == "WRS" ||
#             mode == "WSRC" ||
#             mode == "WCRS" ||
#             mode == "W1SRC" ||
#             mode == "W1CRS" ||
#             mode == "W0SRC" ||
#             mode == "W0CRS") begin
#            `uvm_warning("RegModel", {"Reading field '",get_full_name(),
#                "' will cause unintended side effects in adjoining ",
#                "Read-to-Clear or Read-to-Set fields in the same register"})
#         end
#      end
#   end
#
#endtask: do_read
#
#
#// is_indv_accessible
#
#
#
#// poke
#
#task uvm_reg_field::poke(output uvm_status_e      status,
#                         input  uvm_reg_data_t    value,
#                         input  string            kind = "",
#                         input  uvm_sequence_base parent = null,
#                         input  uvm_object        extension = null,
#                         input  string            fname = "",
#                         input  int               lineno = 0)
#   uvm_reg_data_t  tmp
#
#   self.m_fname = fname
#   self.m_lineno = lineno
#
#   if (value >> self.m_size) begin
#      `uvm_warning("RegModel",
#         {"uvm_reg_field::poke(): Value exceeds size of field '",
#          get_name(),"'"})
#      value &= value & ((1<<self.m_size)-1)
#   end
#
#
#   self.m_parent.XatomicX(1)
#   self.m_parent.m_is_locked_by_field = 1'b1
#
#   tmp = 0
#
#   // What is the current values of the other fields???
#   self.m_parent.peek(status, tmp, kind, parent, extension, fname, lineno)
#
#   if (status == UVM_NOT_OK) begin
#      `uvm_error("RegModel", {"uvm_reg_field::poke(): Peek of register '",
#         self.m_parent.get_full_name(),"' returned status ",status.name()})
#      self.m_parent.XatomicX(0)
#      self.m_parent.m_is_locked_by_field = 1'b0
#      return
#   end
#
#   // Force the value for this field then poke the resulting value
#   tmp &= ~(((1<<self.m_size)-1) << self.m_lsb)
#   tmp |= value << self.m_lsb
#   self.m_parent.poke(status, tmp, kind, parent, extension, fname, lineno)
#
#   self.m_parent.XatomicX(0)
#   self.m_parent.m_is_locked_by_field = 1'b0
#endtask: poke
#
#
#// peek
#
#task uvm_reg_field::peek(output uvm_status_e      status,
#                         output uvm_reg_data_t    value,
#                         input  string            kind = "",
#                         input  uvm_sequence_base parent = null,
#                         input  uvm_object        extension = null,
#                         input  string            fname = "",
#                         input  int               lineno = 0)
#   uvm_reg_data_t  reg_value
#
#   self.m_fname = fname
#   self.m_lineno = lineno
#
#   self.m_parent.peek(status, reg_value, kind, parent, extension, fname, lineno)
#   value = (reg_value >> self.m_lsb) & ((1<<self.m_size))-1
#
#endtask: peek
#
#
#// mirror
#
#task uvm_reg_field::mirror(output uvm_status_e      status,
#                           input  uvm_check_e       check = UVM_NO_CHECK,
#                           input  uvm_path_e        path = UVM_DEFAULT_PATH,
#                           input  uvm_reg_map       map = null,
#                           input  uvm_sequence_base parent = null,
#                           input  int               prior = -1,
#                           input  uvm_object        extension = null,
#                           input  string            fname = "",
#                           input  int               lineno = 0)
#   self.m_fname = fname
#   self.m_lineno = lineno
#   self.m_parent.mirror(status, check, path, map, parent, prior, extension,
#                      fname, lineno)
#endtask: mirror
#
#
#
#// do_print
#
#function void uvm_reg_field::do_print (uvm_printer printer)
#  printer.print_generic(get_name(), get_type_name(), -1, convert2string())
#endfunction
#
#
#
#
#// clone
#
#function uvm_object uvm_reg_field::clone()
#  `uvm_fatal("RegModel","RegModel field cannot be cloned")
#  return null
#endfunction
#
#// do_copy
#
#function void uvm_reg_field::do_copy(uvm_object rhs)
#  `uvm_warning("RegModel","RegModel field copy not yet implemented")
#  // just a set(rhs.get()) ?
#endfunction
#
#
#// do_compare
#
#function bit uvm_reg_field::do_compare (uvm_object  rhs,
#                                        uvm_comparer comparer)
#  `uvm_warning("RegModel","RegModel field compare not yet implemented")
#  // just a return (get() == rhs.get()) ?
#  return 0
#endfunction
#
#
#// do_pack
#
#function void uvm_reg_field::do_pack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel field cannot be packed")
#endfunction
#
#
#// do_unpack
#
#function void uvm_reg_field::do_unpack (uvm_packer packer)
#  `uvm_warning("RegModel","RegModel field cannot be unpacked")
#endfunction
#
