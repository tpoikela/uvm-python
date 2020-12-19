#
#-----------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2013 NVIDIA Corporation
#   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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
#-----------------------------------------------------------------------------

from typing import Dict, Any

from .sv import sv, sv_obj
from .uvm_misc import UVMStatusContainer
from .uvm_object_globals import (UVM_PRINT, UVM_NONE, UVM_COPY, UVM_COMPARE,
        UVM_RECORD, UVM_SETINT, UVM_SETOBJ, UVM_SETSTR, UVM_PACK, UVM_UNPACK)
from .uvm_globals import uvm_report_error, uvm_report_warning, uvm_report_info
from typing import Tuple


class UVMObject(sv_obj):
    """
    The `UVMObject` class is the base class for all UVM data and hierarchical classes.
    Its primary role is to define a set of methods for such common operations as `create`,
    `copy`, `compare`, `print`, and `record`.
    Classes deriving from `UVMObject` must implement methods such as
    `create` and `get_type_name`.

    :ivar str name: Name of the object
    :ivar int inst_id: Unique instance ID for this object

    Group: Seeding

    :cvar bool use_uvm_seeding: This bit enables or disables the UVM seeding
    mechanism. It globally affects the operation of the `reseed` method.

    When enabled, UVM-based objects are seeded based on their type and full
    hierarchical name rather than allocation order. This improves random
    stability for objects whose instance names are unique across each type.
    The `UVMComponent` class is an example of a type that has a unique
    instance name.
    """

    # Should be set by uvm_*_utils macro
    type_id = None  # type: Any

    depth = 0
    m_inst_count = 0

    m_inst_count = 0
    use_uvm_seeding = True
    uvm_global_copy_map = {}  # type: Dict['UVMObject', 'UVMObject']
    _m_uvm_status_container = UVMStatusContainer()

    def __init__(self, name: str):
        """ Creates a new uvm_object with the given instance `name`. If `name` is not
        supplied, the object is unnamed.
        """
        sv_obj.__init__(self)
        self.name = name
        self.inst_id = UVMObject.m_inst_count
        UVMObject.m_inst_count += 1
        self.leaf_name = name


    def reseed(self) -> None:
        """
        Calls `srandom` on the object to reseed the object using the UVM seeding
        mechanism, which sets the seed based on type name and instance name instead
        of based on instance position in a thread.

        If the `use_uvm_seeding` static variable is set to 0, then reseed() does
        not perform any function.
        """
        if (UVMObject.use_uvm_seeding):
            pass

    def set_name(self, name: str):
        """
        Group: Identification

        Sets the instance name of this object, overwriting any previously
        given name.
        Args:
            name:
        """
        self.leaf_name = name

    def get_name(self) -> str:
        """
        Returns the name of the object, as provided by the `name` argument in the
        `new` constructor or `set_name` method.

        Returns:
            str: Name of the object.
        """
        return self.leaf_name

    def get_full_name(self) -> str:
        """
        Objects possessing hierarchy, such as <uvm_components>, override the default
        implementation. Other objects might be associated with component hierarchy
        but are not themselves components. For example, <uvm_sequence #(REQ,RSP)>
        classes are typically associated with a <uvm_sequencer #(REQ,RSP)>. In this
        case, it is useful to override get_full_name to return the sequencer's
        full name concatenated with the sequence's name. This provides the sequence
        a full context, which is useful when debugging.

        Returns:
            str: The full hierarchical name of this object. The default
            implementation is the same as <get_name>, as uvm_objects do not inherently
            possess hierarchy.
        """
        return self.get_name()

    def get_inst_id(self) -> int:
        """
        Returns:
            int: The object's unique, numeric instance identifier.
        """
        return self.inst_id


    @classmethod
    def get_inst_count(self) -> int:
        """
        Returns:
            int: The current value of the instance counter, which represents the
            total number of uvm_object-based objects that have been allocated in
            simulation. The instance counter is used to form a unique numeric instance
            identifier.
        """
        return UVMObject.m_inst_count

    def get_type(self) -> None:
        """
        Returns the type-proxy (wrapper) for this object. The `UVMFactory`'s
        type-based override and creation methods take arguments of
        `uvm_object_wrapper`. This method, if implemented, can be used as convenient
        means of supplying those arguments.

        The default implementation of this method produces an error and returns
        `None`. To enable use of this method, a user's subtype must implement a
        version that returns the subtype's wrapper.

        For example:

        .. code-block:: python

          class cmd(UVMObject):
            type_id = None

            @classmethod
            def get_type(cls):
              return cls.type_id.get()

        Then, to use:

        .. code-block:: python

            factory.set_type_override(cmd.get_type(), subcmd.get_type())

        This function is implemented by the uvm_*_utils functions, if employed.

        Returns:
        """
        uvm_report_error("NOTYPID", "get_type not implemented in derived class: "
                + str(self), UVM_NONE)
        return None

    def get_object_type(self) -> Any:
        """
        Function: get_object_type

        Returns the type-proxy (wrapper) for this object. The `uvm_factory`'s
        type-based override and creation methods take arguments of
        `uvm_object_wrapper`. This method, if implemented, can be used as convenient
        means of supplying those arguments. This method is the same as the static
        `get_type` method, but uses an already allocated object to determine
        the type-proxy to access (instead of using the static object).

        The default implementation of this method does a factory lookup of the
        proxy using the return value from `get_type_name`. If the type returned
        by `get_type_name` is not registered with the factory, then a `None`
        handle is returned.

        For example:

        .. code-block:: python

          class cmd (UVMObject):
            type_id = UVMObjectRegistry()
            @classmethod
            def type_id get_type(cls):
              return type_id.get()
            def get_object_type(self):
              return cmd.type_id.get()


        This function is implemented by the `uvm_*_utils macros, if employed.

        Returns:
        """
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        factory = cs.get_factory()
        if self.get_type_name() == "<unknown>":
            return None
        return factory.find_wrapper_by_name(self.get_type_name())

    def get_type_name(self) -> str:
        """
        This function returns the type name of the object, which is typically the
        type identifier enclosed in quotes. It is used for various debugging
        functions in the library, and it is used by the factory for creating
        objects.

        This function must be defined in every derived class.

        A typical implementation is as follows:

        .. code-block:: python
          class mytype (UVMObject):
            ...
            type_name = "mytype"

            def get_type_name(self):
              return my_type.type_name


          We define the `type_name` static variable to enable access to the type name
          without need of an object of the class, i.e., to enable access via the
          scope operator, ~mytype::type_name~.
        Returns:
            str: Type name of the object.
        """
        return "<unknown>"

    def create(self, name="") -> 'UVMObject':
        """
        Group: Creation

        The `create` method allocates a new object of the same type as this object
        and returns it via a base uvm_object handle. Every class deriving from
        uvm_object, directly or indirectly, must implement the create method.

        A typical implementation is as follows:

        .. code-block:: python

          class mytype (UVMObject):
            ...
            def create(self, name=""):
              mytype t = mytype(name)
              return t

        Args:
            name (str): Name of the created object.
        Returns:
            obj: New object.
        """
        return UVMObject(name)

    def clone(self) -> 'UVMObject':
        """
        The `clone` method creates and returns an exact copy of this object.

        The default implementation calls `create` followed by `copy`. As clone is
        virtual, derived classes may override this implementation if desired.

        Returns:
            UVMObject: Clone of the object.
        """
        tmp = self.create(self.get_name())
        if tmp is None:
            uvm_report_warning("CRFLD", sv.sformatf(
                "The create method failed for %s,  object cannot be cloned",
                self.get_name()), UVM_NONE)
        else:
            tmp.copy(self)
        return tmp

    def print_obj(self, printer=None) -> None:
        """
        Group: Printing

        Function: print

        The `print` method deep-prints this object's properties in a format and
        manner governed by the given `printer` argument; if the `printer` argument
        is not provided, the global `uvm_default_printer` is used. See
        `uvm_printer` for more information on printer output formatting. See also
        `uvm_line_printer`, `uvm_tree_printer`, and `uvm_table_printer` for details
        on the pre-defined printer "policies," or formatters, provided by the UVM.

        The `print` method is not virtual and must not be overloaded. To include
        custom information in the `print` and `sprint` operations, derived classes
        must override the `do_print` method and use the provided printer policy
        class to format the output.

        Args:
            printer (UVMPrinter): Printer that is used in printing.
        """
        if printer is None:
            from .uvm_global_vars import uvm_default_printer
            printer = uvm_default_printer
        if printer is None:
            uvm_report_error("NonePRINTER", "uvm_default_printer is None")
        sv.fwrite(printer.knobs.mcd, self.sprint(printer))

    def sprint(self, printer=None) -> str:
        """
        The `sprint` method works just like the `print` method, except the output
        is returned in a string rather than displayed.

        The `sprint` method is not virtual and must not be overloaded. To include
        additional fields in the `print` and `sprint` operation, derived classes
        must override the `do_print` method and use the provided printer policy
        class to format the output. The printer policy will manage all string
        concatenations and provide the string to `sprint` to return to the caller.

        Args:
            printer (UVMPrinter): Printer that is used in printing.
        Returns:
            str: String representation of the object.
        """
        if printer is None:
            from .uvm_global_vars import uvm_default_printer
            printer = uvm_default_printer
        if not printer.istop():
            UVMObject._m_uvm_status_container.printer = printer
            self._m_uvm_field_automation(None, UVM_PRINT, "")
            self.do_print(printer)
            return ""
        self._m_uvm_status_container = UVMObject._m_uvm_status_container
        printer.print_object(self.get_name(), self)
        if printer.m_string != "":
            return printer.m_string
        return printer.emit()

    def do_print(self, printer) -> None:
        """
        The `do_print` method is the user-definable hook called by `print` and
        `sprint` that allows users to customize what gets printed or sprinted
        beyond the field information provided by the `uvm_field_* macros,
        <Utility and Field Macros for Components and Objects>.

        The `printer` argument is the policy object that governs the format and
        content of the output. To ensure correct `print` and `sprint` operation,
        and to ensure a consistent output format, the `printer` must be used
        by all `do_print` implementations. That is, instead of using ~$display~ or
        string concatenations directly, a `do_print` implementation must call
        through the ~printer's~ API to add information to be printed or sprinted.

        An example implementation of `do_print` is as follows::

          class mytype (UVMObject):
            data_obj data
            int f1
            virtual function void do_print (uvm_printer printer)
              super.do_print(printer)
              printer.print_field_int("f1", f1, $bits(f1), UVM_DEC)
              printer.print_object("data", data)
            endfunction

        Then, to print and sprint the object, you could write::

          t = mytype()
          t.print()
          uvm_report_info("Received",t.sprint())

        See `UVMPrinter` for information about the printer API.

        Args:
            printer (UVMPrinter): Printer that is used in printing.
        """
        return

    def convert2string(self) -> str:
        """
        This virtual function is a user-definable hook, called directly by the
        user, that allows users to provide object information in the form of
        a string. Unlike `sprint`, there is no requirement to use a `uvm_printer`
        policy object. As such, the format and content of the output is fully
        customizable, which may be suitable for applications not requiring the
        consistent formatting offered by the `print`/`sprint`/`do_print`
        API.

        Fields declared in <Utility Macros> macros (`uvm_field_*), if used, will
        not automatically appear in calls to convert2string.

        An example implementation of convert2string follows.

        .. code-block:: python

          class Base(UVMObject):
            field = "foo"
            def convert2string(self):
              return "base_field=" + self.field

          class Obj2(UVMObject):
            field = "bar"
            def convert2string()
              convert2string = "child_field=" + self.field

          class Obj(Base):
            addr = 0x123
            data = 0x456
            write = 1
            child = Obj2()
            def convert2string(self):
               convert2string = super().convert2string() +
                 sv.sformatf(" write=%0d addr=%8h data=%8h ",write,addr,data) +
                 child.convert2string()

         Then, to display an object, you could write:

         .. code-block:: python

           o = Obj()
           uvm_report_info("BusMaster", "Sending:\n " + o.convert2string())

        The output will look similar to::

          UVM_INFO @ 0: reporter [BusMaster] Sending:
            base_field=foo write=1 addr=00000123 data=00000456 child_field=bar

        Returns:
            str: Object converted into string.
        """
        return ""

    def _m_uvm_field_automation(self, tmp_data__, what__, str__) -> None:
        pass

    def record(self, recorder=None) -> None:
        """
        Group: Recording

        The `record` method deep-records this object's properties according to an
        optional `recorder` policy. The method is not virtual and must not be
        overloaded. To include additional fields in the record operation, derived
        classes should override the `do_record` method.

        The optional `recorder` argument specifies the recording policy, which
        governs how recording takes place. See
        `uvm_recorder` for information.

        A simulator's recording mechanism is vendor-specific. By providing access
        via a common interface, the uvm_recorder policy provides vendor-independent
        access to a simulator's recording capabilities.

        Args:
            recorder (UVMRecorder):
        """
        if recorder is None:
            return
        UVMObject._m_uvm_status_container.recorder = recorder
        recorder.recording_depth += 1
        self._m_uvm_field_automation(None, UVM_RECORD, "")
        self.do_record(recorder)
        recorder.recording_depth -= 1


    def do_record(self, recorder) -> None:
        """
        The `do_record` method is the user-definable hook called by the `record`
        method. A derived class should override this method to include its fields
        in a record operation.

        The `recorder` argument is policy object for recording this object. A
        do_record implementation should call the appropriate recorder methods for
        each of its fields. Vendor-specific recording implementations are
        encapsulated in the `recorder` policy, thereby insulating user-code from
        vendor-specific behavior. See `uvm_recorder` for more information.

        A typical implementation is as follows:

        .. code-block:: python

          class mytype (UVMObject):
            data_obj data
            int f1
            def do_record (self, recorder):
              recorder.record_field("f1", f1, sv.bits(f1), UVM_DEC)
              recorder.record_object("data", data)

        Args:
            recorder (UVMRecorder): Recorder policy object.
        """
        return

    def copy(self, rhs: 'UVMObject'):
        """
        The copy makes this object a copy of the specified object.

        The `copy` method is not virtual and should not be overloaded in derived
        classes. To copy the fields of a derived class, that class should override
        the `do_copy` method.

        Args:
            rhs (UVMObject): An object to be copied.
        """
        # For cycle checking
        UVMObject.depth = 0
        if (rhs is not None) and rhs in UVMObject.uvm_global_copy_map:
            return

        if rhs is None:
            uvm_report_warning("NoneCP",
                "A None object was supplied to copy; copy is ignored", UVM_NONE)
            return

        UVMObject.uvm_global_copy_map[rhs] = self
        UVMObject.depth += 1
        self._m_uvm_field_automation(rhs, UVM_COPY, "")
        self.do_copy(rhs)

        UVMObject.depth -= 1
        if UVMObject.depth == 0:
            UVMObject.uvm_global_copy_map = {}

    def do_copy(self, rhs) -> None:
        """
        The `do_copy` method is the user-definable hook called by the `copy` method.
        A derived class should override this method to include its fields in a `copy`
        operation.

        A typical implementation is as follows:

        .. code-block:: python

          class mytype (UVMObject):
            ...
            field_1 = 0
            def do_copy(self, rhs):
              super.do_copy(rhs)
              # Optionanl type checking
              field_1 = rhs.field_1

        The implementation must call `super().do_copy`, and can optionally do
        type checking before copying.

        Args:
            rhs (UVMObject): Object to be copied.
        """
        return

    def compare(self, rhs, comparer=None) -> bool:
        """
        Deep compares members of this data object with those of the object provided
        in the `rhs` (right-hand side) argument, returning 1 on a match, 0 otherwise.

        The `compare` method is not virtual and should not be overloaded in derived
        classes. To compare the fields of a derived class, that class should
        override the `do_compare` method.

        The optional `comparer` argument specifies the comparison policy. It allows
        you to control some aspects of the comparison operation. It also stores the
        results of the comparison, such as field-by-field miscompare information
        and the total number of miscompares. If a compare policy is not provided,
        then the global `uvm_default_comparer` policy is used. See `uvm_comparer`
        for more information.

        Args:
            rhs (UVMObject): Object to be compared against.
            comparer (UVMComparer): Comparer policy object.
        Returns:
            bool: True if objects match, False otherwise.
        """
        # t = 0
        dc = 0
        #static int style
        # style = 0
        done = 0
        cls = UVMObject
        if comparer is not None:
            cls._m_uvm_status_container.comparer = comparer
        else:
            from .uvm_global_vars import uvm_default_comparer
            cls._m_uvm_status_container.comparer = uvm_default_comparer
        comparer = cls._m_uvm_status_container.comparer

        if(not cls._m_uvm_status_container.scope.depth()):
            comparer.compare_map.delete()
            comparer.result = 0
            comparer.miscompares = ""
            comparer.scope = cls._m_uvm_status_container.scope
            if self.get_name() == "":
                cls._m_uvm_status_container.scope.down("<object>")
            else:
                cls._m_uvm_status_container.scope.down(self.get_name())

        if(not done and (rhs is None)):
            if(cls._m_uvm_status_container.scope.depth()):
                comparer.print_msg_object(self, rhs)
            else:
                comparer.print_msg_object(self, rhs)
                uvm_report_info("MISCMP",
                     sv.sformatf("%0d Miscompare(s) for object %s@%0d vs. None",
                     comparer.result,
                     cls._m_uvm_status_container.scope.get(),
                      self.get_inst_id()),
                      cls._m_uvm_status_container.comparer.verbosity)
                done = 1

        if(not done and comparer.compare_map.exists(rhs)):
            if(comparer.compare_map[rhs] != self):
                comparer.print_msg_object(self, comparer.compare_map[rhs])
            done = 1  # don't do any more work after this case, but do cleanup

        if(not done and comparer.check_type and (rhs is not None) and
                (self.get_type_name() != rhs.get_type_name())):
            cls._m_uvm_status_container.stringv = ("lhs type = \"" + self.get_type_name()
                + "' : rhs type = '" + rhs.get_type_name() + "'")
            comparer.print_msg(cls._m_uvm_status_container.stringv)

        if not done:
            comparer.compare_map[rhs] = self
            self._m_uvm_field_automation(rhs, UVM_COMPARE, "")
            dc = self.do_compare(rhs, comparer)

        if cls._m_uvm_status_container.scope.depth() == 1:
            cls._m_uvm_status_container.scope.up()

        if rhs is not None:
            comparer.print_rollup(self, rhs)
        return (comparer.result == 0 and dc == 1)


    def do_compare(self, rhs, comparer) -> bool:
        """
        The `do_compare` method is the user-definable hook called by the `compare`
        method. A derived class should override this method to include its fields
        in a compare operation. It should return 1 if the comparison succeeds, 0
        otherwise.

        A typical implementation is as follows:

        .. code-block:: python

          class mytype (UVMObject):
            ...
            f1 = 0
            def do_compare(self, rhs, comparer):
              do_compare = super.do_compare(rhs,comparer)
              # Optional type checking
              do_compare &= comparer.compare_field_int("f1", f1, rhs.f1)
              return do_compare

        A derived class implementation must call `super().do_compare` to ensure its
        base class' properties, if any, are included in the comparison. If type
        matching is required instead of duck-typing, the user can also
        implemented this checking.

        The actual comparison should be implemented using the `UVMComparer` object
        rather than direct field-by-field comparison. This enables users of your
        class to customize how comparisons are performed and how much miscompare
        information is collected. See `UVMComparer` for more details.

        Args:
            rhs (UVMObject):
            comparer (UVMComparer):
        Returns:
            bool: True if objects match, False otherwise.
        """
        return True


    #  // Group: Packing

    #  // Function: pack
    #
    #  extern function int pack (ref bit bitstream[],
    #                            input uvm_packer packer=None)
    def pack(self, packer=None) -> Tuple[Any, Any]:
        packer = self.m_pack(packer)
        return packer.get_packed_size(), packer.get_bits()


    #  // Function: pack_bytes
    #
    #  extern function int pack_bytes (ref byte unsigned bytestream[],
    #                                  input uvm_packer packer=None)
    def pack_bytes(self, bytestream, packer=None) -> Any:
        packer = self.m_pack(packer)
        packed_bytes = packer.get_bytes()
        for b in packed_bytes:
            bytestream.append(b)
        return packer.get_packed_size()


    #  // Function: pack_ints
    #  //
    #  // The pack methods bitwise-concatenate this object's properties into an array
    #  // of bits, bytes, or ints. The methods are not virtual and must not be
    #  // overloaded. To include additional fields in the pack operation, derived
    #  // classes should override the <do_pack> method.
    #  //
    #  // The optional `packer` argument specifies the packing policy, which governs
    #  // the packing operation. If a packer policy is not provided, the global
    #  // <uvm_default_packer> policy is used. See <uvm_packer> for more information.
    #  //
    #  // The return value is the total number of bits packed into the given array.
    #  // Use the array's built-in `size` method to get the number of bytes or ints
    #  // consumed during the packing process.
    #
    #  extern function int pack_ints (ref int unsigned intstream[],
    #                                 input uvm_packer packer=None)
    def pack_ints(self, intstream, packer=None) -> Any:
        packer = self.m_pack(packer)
        ints = packer.get_ints()
        for i in ints:
            intstream.append(i)
        return packer.get_packed_size()


    #  // Function: do_pack
    #  //
    #  // The `do_pack` method is the user-definable hook called by the <pack> methods.
    #  // A derived class should override this method to include its fields in a pack
    #  // operation.
    #  //
    #  // The `packer` argument is the policy object for packing. The policy object
    #  // should be used to pack objects.
    #  //
    #  // A typical example of an object packing itself is as follows
    #  //
    #  //|  class mysubtype extends mysupertype
    #  //|    ...
    #  //|    shortint myshort
    #  //|    obj_type myobj
    #  //|    byte myarray[]
    #  //|    ...
    #  //|    function void do_pack (uvm_packer packer)
    #  //|      super.do_pack(packer); // pack mysupertype properties
    #  //|      packer.pack_field_int(myarray.size(), 32)
    #  //|      foreach (myarray)
    #  //|        packer.pack_field_int(myarray[index], 8)
    #  //|      packer.pack_field_int(myshort, $bits(myshort))
    #  //|      packer.pack_object(myobj)
    #  //|    endfunction
    #  //
    #  // The implementation must call ~super.do_pack~ so that base class properties
    #  // are packed as well.
    #  //
    #  // If your object contains dynamic data (object, string, queue, dynamic array,
    #  // or associative array), and you intend to unpack into an equivalent data
    #  // structure when unpacking, you must include meta-information about the
    #  // dynamic data when packing as follows.
    #  //
    #  //  - For queues, dynamic arrays, or associative arrays, pack the number of
    #  //    elements in the array in the 32 bits immediately before packing
    #  //    individual elements, as shown above.
    #  //
    #  //  - For string data types, append a zero byte after packing the string
    #  //    contents.
    #  //
    #  //  - For objects, pack 4 bits immediately before packing the object. For `None`
    #  //    objects, pack 4'b0000. For non-`None` objects, pack 4'b0001.
    #  //
    #  // When the `uvm_field_* macros are used,
    #  // <Utility and Field Macros for Components and Objects>,
    #  // the above meta information is included provided the <uvm_packer::use_metadata>
    #  // variable is set for the packer.
    #  //
    #  // Packing order does not need to match declaration order. However, unpacking
    #  // order must match packing order.
    def do_pack(self, packer) -> None:
        return


    #  // Group: Unpacking
    #
    #  // Function: unpack
    #
    #  extern function int unpack (ref   bit        bitstream[],
    #                              input uvm_packer packer=None)
    def unpack(self, bitstream, packer=None) -> Any:
        packer = self.m_unpack_pre(packer)
        packer.put_bits(bitstream)
        self.m_unpack_post(packer)
        packer.set_packed_size()
        return packer.get_packed_size()


    #  // Function: unpack_bytes
    #
    #  extern function int unpack_bytes (ref byte unsigned bytestream[],
    #                                    input uvm_packer packer=None)
    def unpack_bytes(self, bytestream, packer=None) -> Any:
        packer = self.m_unpack_pre(packer)
        packer.put_bytes(bytestream)
        self.m_unpack_post(packer)
        packer.set_packed_size()
        return packer.get_packed_size()


    #  // Function: unpack_ints
    #  //
    #  // The unpack methods extract property values from an array of bits, bytes, or
    #  // ints. The method of unpacking `must` exactly correspond to the method of
    #  // packing. This is assured if (a) the same `packer` policy is used to pack
    #  // and unpack, and (b) the order of unpacking is the same as the order of
    #  // packing used to create the input array.
    #  //
    #  // The unpack methods are fixed (non-virtual) entry points that are directly
    #  // callable by the user. To include additional fields in the <unpack>
    #  // operation, derived classes should override the <do_unpack> method.
    #  //
    #  // The optional `packer` argument specifies the packing policy, which governs
    #  // both the pack and unpack operation. If a packer policy is not provided,
    #  // then the global `uvm_default_packer` policy is used. See uvm_packer for
    #  // more information.
    #  //
    #  // The return value is the actual number of bits unpacked from the given array.
    #
    #  extern function int unpack_ints (ref   int unsigned intstream[],
    #                                   input uvm_packer packer=None)
    def unpack_ints(self, intstream, packer=None) -> Any:
        packer = self.m_unpack_pre(packer)
        packer.put_ints(intstream)
        self.m_unpack_post(packer)
        packer.set_packed_size()
        return packer.get_packed_size()


    #  // Function: do_unpack
    #  //
    #  // The `do_unpack` method is the user-definable hook called by the <unpack>
    #  // method. A derived class should override this method to include its fields
    #  // in an unpack operation.
    #  //
    #  // The `packer` argument is the policy object for both packing and unpacking.
    #  // It must be the same packer used to pack the object into bits. Also,
    #  // do_unpack must unpack fields in the same order in which they were packed.
    #  // See <uvm_packer> for more information.
    #  //
    #  // The following implementation corresponds to the example given in do_pack.
    #  //
    #  //|  function void do_unpack (uvm_packer packer)
    #  //|   int sz
    #  //|    super.do_unpack(packer); // unpack super's properties
    #  //|    sz = packer.unpack_field_int(myarray.size(), 32)
    #  //|    myarray.delete()
    #  //|    for(int index=0; index<sz; index++)
    #  //|      myarray[index] = packer.unpack_field_int(8)
    #  //|    myshort = packer.unpack_field_int($bits(myshort))
    #  //|    packer.unpack_object(myobj)
    #  //|  endfunction
    #  //
    #  // If your object contains dynamic data (object, string, queue, dynamic array,
    #  // or associative array), and you intend to <unpack> into an equivalent data
    #  // structure, you must have included meta-information about the dynamic data
    #  // when it was packed.
    #  //
    #  // - For queues, dynamic arrays, or associative arrays, unpack the number of
    #  //   elements in the array from the 32 bits immediately before unpacking
    #  //   individual elements, as shown above.
    #  //
    #  // - For string data types, unpack into the new string until a `None` byte is
    #  //   encountered.
    #  //
    #  // - For objects, unpack 4 bits into a byte or int variable. If the value
    #  //   is 0, the target object should be set to `None` and unpacking continues to
    #  //   the next property, if any. If the least significant bit is 1, then the
    #  //   target object should be allocated and its properties unpacked.
    def do_unpack(self, packer) -> None:
        return

    def set_int_local(self, field_name: str, value: int, recurse=True):
        """
        Group: Configuration

        Args:
            field_name (str): Variable to set
            value: Value for the variable
            recurse (bool):
        """
        UVMObject._m_uvm_status_container.cycle_check.clear()
        UVMObject._m_uvm_status_container.m_uvm_cycle_scopes.clear()

        UVMObject._m_uvm_status_container.status = False
        UVMObject._m_uvm_status_container.bitstream = value

        self._m_uvm_field_automation(None, UVM_SETINT, field_name)

        if UVMObject._m_uvm_status_container.warning and not self._m_uvm_status_container.status:
            uvm_report_error("NOMTC", sv.sformatf("did not find a match for field %s", field_name),UVM_NONE)
        UVMObject._m_uvm_status_container.cycle_check.clear()


    def set_string_local(self, field_name: str, value: str, recurse=True):
        """
        Function: set_string_local

        Args:
            field_name (str): Variable to set
            value: Value for the variable
            recurse (bool): If True, recurse into sub-objects.
        """
        UVMObject._m_uvm_status_container.cycle_check.clear()
        UVMObject._m_uvm_status_container.m_uvm_cycle_scopes.clear()

        UVMObject._m_uvm_status_container.status = False
        UVMObject._m_uvm_status_container.stringv = value
        self._m_uvm_field_automation(None, UVM_SETSTR, field_name)

        if UVMObject._m_uvm_status_container.warning and not UVMObject._m_uvm_status_container.status:
            uvm_report_error("NOMTC", sv.sformatf("did not find a match for field %s (@%0d)",
                field_name, self.get_inst_id()), UVM_NONE)

        UVMObject._m_uvm_status_container.cycle_check.clear()


    def set_object_local(self, field_name: str, value: 'UVMObject', clone=1, recurse=1):
        """
        These methods provide write access to integral, string, and
        uvm_object-based properties indexed by a `field_name` string. The object
        designer choose which, if any, properties will be accessible, and overrides
        the appropriate methods depending on the properties' types. For objects,
        the optional `clone` argument specifies whether to clone the `value`
        argument before assignment.

        The global `uvm_is_match` function is used to match the field names, so
        `field_name` may contain wildcards.

        An example implementation of all three methods is as follows.

        .. code-block:: python

          class mytype(UVMObject):

            def __init__(self, name):
              super().__init__(name)
              self.myint = 0
              self.mybyte = 0
              self.myshort = 0
              self.mystring = ""
              self.myobj = None

            # provide access to integral properties
            def set_int_local(self, field_name, value):
              if (uvm_is_match (field_name, "myint")):
                self.myint = value
              elif (uvm_is_match (field_name, "mybyte")):
                selef.mybyte = value

            # provide access to string properties
            def set_string_local(self, field_name, value):
              if (uvm_is_match (field_name, "mystring")):
                self.mystring = value

            # provide access to sub-objects
            def set_object_local(self, field_name, value,clone=1):
              if (uvm_is_match (field_name, "myobj")):
                if (value is not None):
                  tmp = None
                  # if provided value is not correct type, produce error
                  if (!$cast(tmp, value)):
                    # error
                  else:
                    if(clone)
                      self.myobj = tmp.clone()
                    else
                      self.myobj = tmp
                else:
                  myobj = None  # value is None, so simply assign None to myobj
              end
            ...

        Although the object designer implements these methods to provide outside
        access to one or more properties, they are intended for internal use (e.g.,
        for command-line debugging and auto-configuration) and should not be called
        directly by the user.

        Args:
            field_name (str): Variable to set
            value: Value for the variable
            clone (bool):
            recurse (bool):
        """
        # cc = None  # uvm_object cc
        UVMObject._m_uvm_status_container.cycle_check.clear()
        UVMObject._m_uvm_status_container.m_uvm_cycle_scopes.clear()

        if clone and (value is not None):
            cc = value.clone()
            if cc is not None:
                cc.set_name(field_name)
            value = cc

        UVMObject._m_uvm_status_container.status = False
        UVMObject._m_uvm_status_container.object = value
        UVMObject._m_uvm_status_container.clone = clone

        self._m_uvm_field_automation(None, UVM_SETOBJ, field_name)

        if UVMObject._m_uvm_status_container.warning and not UVMObject._m_uvm_status_container.status:
            uvm_report_error("NOMTC", sv.sformatf("did not find a match for field %s", field_name), UVM_NONE)

        UVMObject._m_uvm_status_container.cycle_check.clear()


    #  //---------------------------------------------------------------------------
    #  //                 **** Internal Methods and Properties ***
    #  //                           Do not use directly
    #  //---------------------------------------------------------------------------
    #

    #  extern local function void m_pack        (inout uvm_packer packer)
    def m_pack(self, packer) -> Any:
        if packer is not None:
            UVMObject._m_uvm_status_container.packer = packer
        else:
            from .uvm_global_vars import uvm_default_packer
            UVMObject._m_uvm_status_container.packer = uvm_default_packer
        packer = UVMObject._m_uvm_status_container.packer

        packer.reset()
        packer.scope.down(self.get_name())

        self._m_uvm_field_automation(None, UVM_PACK, "")
        self.do_pack(packer)
        packer.set_packed_size()
        packer.scope.up()
        return packer


    #  extern local function void m_unpack_pre  (inout uvm_packer packer)
    def m_unpack_pre(self, packer) -> Any:
        if packer is not None:
            UVMObject._m_uvm_status_container.packer = packer
        else:
            from .uvm_global_vars import uvm_default_packer
            UVMObject._m_uvm_status_container.packer = uvm_default_packer
        packer = UVMObject._m_uvm_status_container.packer
        packer.reset()
        return packer

    #  extern local function void m_unpack_post (uvm_packer packer)
    def m_unpack_post(self, packer) -> None:
        provided_size = packer.get_packed_size()
        # Put this object into the hierarchy
        packer.scope.down(self.get_name())

        self._m_uvm_field_automation(None, UVM_UNPACK, "")
        self.do_unpack(packer)
        # Scope back up before leaving
        packer.scope.up()

        if packer.get_packed_size() != provided_size:
            uvm_report_warning("BDUNPK", sv.sformatf(
                "Unpack operation unsuccessful: unpacked %0d bits from a total of %0d bits",
                packer.get_packed_size(), provided_size), UVM_NONE)
