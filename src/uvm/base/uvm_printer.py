#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
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
#   the License or the specific language governing
#   permissions and limitations under the License.
#------------------------------------------------------------------------------


from .uvm_scope_stack import UVMScopeStack
from .uvm_object_globals import (UVM_BIN, UVM_DEC, UVM_HEX, UVM_NORADIX, UVM_OCT, UVM_STRING,
                                 UVM_TIME, UVM_UNSIGNED)
from .uvm_misc import (uvm_leaf_scope, uvm_integral_to_string,
        uvm_bitstream_to_string, uvm_object_value_str)
from .uvm_globals import uvm_report_error

UVM_STDOUT = 1  # Writes to standard out and logfile


class UVMPrinterRowInfo:
    def __init__(self):
        self.level = 0
        self.name = ""
        self.type_name = ""
        self.size = ""
        self.val = ""

    def __str__(self):
        return "L: {} Name: {} Type: {} Size: {} Val: {}".format(
            self.level, self.name, self.type_name, self.size, self.val)


class UVMPrinter():
    """
    Class: UVMPrinter

    The UVMPrinter class provides an interface for printing <uvm_objects> in
    various formats. Subtypes of UVMPrinter implement different print formats,
    or policies.

    A user-defined printer format can be created, or one of the following four
    built-in printers can be used:

    - `UVMPrinter` - provides base printer functionality; must be overridden.

    - `UVMTablePrinter` - prints the object in a tabular form.

    - `UVMTreePrinter` - prints the object in a tree form.

    - `UVMLinePrinter` - prints the information on a single line, but uses the
      same object separators as the tree printer.

    Printers have knobs that you use to control what and how information is printed.
    These knobs are contained in a separate knob class:

    - <uvm_printer_knobs> - common printer settings

    For convenience, global instances of each printer type are available for
    direct reference in your testbenches.

     -  <uvm_default_tree_printer>
     -  <uvm_default_line_printer>
     -  <uvm_default_table_printer>
     -  <uvm_default_printer> (set to default_table_printer by default)

    When <uvm_object::print> and <uvm_object::sprint> are called without
    specifying a printer, the <uvm_default_printer> is used.
    """


    def __init__(self, name=""):
        self.knobs = UVMPrinterKnobs()
        self.m_array_stack = []
        self.m_scope = UVMScopeStack()
        self.m_string = ""
        self.m_rows = []

    def emit(self):
        """
        emit
        ----
        Returns:
        """
        uvm_report_error("NO_OVERRIDE","emit() method not overridden in printer subtype")
        return ""

    def format_row(self, row):
        """
        format_row
        ----------
        Args:
            row:
        Returns:
        """
        return ""

    def format_header(self):
        """
        format_header
        ----------
        Returns:
        """
        return ""

    def format_footer(self):
        """
        format_footer
        ----------
        Returns:
        """
        return ""

    # print_array_header
    # ------------------

    def print_array_header(self, name, size, arraytype="array",
          scope_separator="."):
        row_info = UVMPrinterRowInfo()
        if name != "":
            self.m_scope.set_arg(name)

        row_info.level = self.m_scope.depth()
        row_info.name = self.adjust_name(self.m_scope.get(),scope_separator)
        row_info.type_name = arraytype
        row_info.size = "{}".format(size)
        row_info.val = "-"

        self.m_rows.append(row_info)

        self.m_scope.down(name)
        self.m_array_stack.append(1)


    # print_array_footer
    # ------------------

    def print_array_footer(self, size=0):
        if len(self.m_array_stack) > 0:
            self.m_scope.up()
            self.m_array_stack.pop()


    def print_array_range(self, min_val, max_val):
        """
        print_array_range
        -----------------
        Args:
            min_val:
            max_val:
        """
        tmpstr = ""
        if min_val == -1 and max_val == -1:
            return
        if min_val == -1:
            min_val = max_val
        if max_val == -1:
            max_val = min_val
        if max_val < min_val:
            return
        self.print_generic("...", "...", -2, "...")

    def print_object_header(self, name, value, scope_separator="."):
        """
        print_object_header
        -------------------
        Args:
            name:
            value:
            scope_separator:
        """
        row_info = UVMPrinterRowInfo()
        comp = None
        if name == "":
            if value is not None:
                if self.m_scope.depth() == 0:
                    comp = value
                    name = comp.get_full_name()
                else:
                    name = value.get_name()

        if name == "":
            name = "<unnamed>"

        self.m_scope.set_arg(name)
        row_info.level = self.m_scope.depth()

        if row_info.level == 0 and self.knobs.show_root is True:
            row_info.name = value.get_full_name()
        else:
            row_info.name = self.adjust_name(self.m_scope.get(),scope_separator)

        if value is None:
            row_info.type_name = "object"
        else:
            row_info.type_name = value.get_type_name()
        row_info.size = "-"

        if self.knobs.reference is True:
            row_info.val = uvm_object_value_str(value)
        else:
            row_info.val = "-"


        self.m_rows.append(row_info)

    def print_object(self, name, value, scope_separator="."):
        """
        print_object
        ------------
        Args:
            name:
            value:
            scope_separator:
        """
        comp = None
        child_comp = None
        self.print_object_header(name,value,scope_separator)

        if value is not None:
            knobs_ok = self.knobs.depth == -1 or self.knobs.depth > self.m_scope.depth()
            if knobs_ok and not (value in value._m_uvm_status_container.cycle_check):
                value._m_uvm_status_container.cycle_check[value] = 1
                if name == "" and value is not None:
                    self.m_scope.down(value.get_name())
                else:
                    self.m_scope.down(name)

                # Handle children of the comp
                #if($cast(comp, value)) begin
                comp = value
                name = ""
                if hasattr(comp, "has_first_child"):
                    if comp.has_first_child():
                        child_comp = comp.get_first_child()
                        ok = True
                        while ok is True:
                            if child_comp.print_enabled:
                                self.print_object("", child_comp)
                            ok = comp.has_next_child()
                            if ok is True:
                                child_comp = comp.get_next_child()

                # print members of object
                value.sprint(self)

                if name != "" and name[0] == "[":
                    self.m_scope.up("[")
                else:
                    self.m_scope.up(".")
                del value._m_uvm_status_container.cycle_check[value]

    def istop(self):
        """
        istop
        -----
        Returns:
        """
        return self.m_scope.depth() == 0

    def adjust_name(self, id, scope_separator="."):
        """
        #self.adjust_name
        -----------
        Args:
            id:
            scope_separator:
        Returns:
        """
        knobs_ok = self.knobs.show_root and self.m_scope.depth() == 0
        if knobs_ok or self.knobs.full_name or id == "...":
            return id
        return uvm_leaf_scope(id, scope_separator)

    # print_generic
    # -------------

    def print_generic(self, name, type_name, size, value, scope_separator="."):
        row_info = UVMPrinterRowInfo()

        if name != "" and name != "...":
            self.m_scope.set_arg(name)
            name = self.m_scope.get()

        row_info.level = self.m_scope.depth()
        row_info.name = self.adjust_name(name,scope_separator)
        row_info.type_name = type_name
        if size == -2:
            row_info.size = "..."
        else:
            row_info.size = "{}".format(size)

        if value == "":
            row_info.val = '""'
        else:
            row_info.val = value

        self.m_rows.append(row_info)

    def print_int(self, name, value, size, radix=UVM_NORADIX,
            scope_separator=".", type_name=""):
        self.print_field(name, value, size, radix, scope_separator, type_name)

    def print_field(self, name, value, size, radix=UVM_NORADIX,
            scope_separator=".", type_name=""):
        """
        print_field
        ---------
        Args:
            name:
            value:
            size:
            radix:
            UVM_NORADIX:
            scope_separator:
            type_name:
        """
        row_info = UVMPrinterRowInfo()
        sz_str = ""
        val_str = ""

        if name != "":
            self.m_scope.set_arg(name)
            name = self.m_scope.get()

        if type_name == "":
            if radix == UVM_TIME:
                type_name = "time"
            elif radix == UVM_STRING:
                type_name = "string"
            else:
                type_name = "integral"

        sz_str = "{}".format(size)

        if radix == UVM_NORADIX:
            radix = self.knobs.default_radix

        val_str = uvm_bitstream_to_string(value, size, radix,
                                       self.knobs.get_radix_str(radix))

        row_info.level = self.m_scope.depth()
        row_info.name = self.adjust_name(name,scope_separator)
        row_info.type_name = type_name
        row_info.size = sz_str
        row_info.val = val_str
        self.m_rows.append(row_info)


    # print_field_int
    # ---------

    def print_field_int(self, name, value, size, radix=UVM_NORADIX,
            scope_separator=".", type_name=""):

        row_info = UVMPrinterRowInfo()
        sz_str = ""
        val_str = ""

        if name != "":
            self.m_scope.set_arg(name)
            name = self.m_scope.get()

        if type_name == "":
            if radix == UVM_TIME:
                type_name = "time"
            elif radix == UVM_STRING:
                type_name = "string"
            else:
                type_name = "integral"

        sz_str = "{}".format(size)
        if radix == UVM_NORADIX:
            radix = self.knobs.default_radix

        val_str = uvm_integral_to_string(value, size, radix,
                                          self.knobs.get_radix_str(radix))

        row_info.level = self.m_scope.depth()
        row_info.name = self.adjust_name(name,scope_separator)
        row_info.type_name = type_name
        row_info.size = sz_str
        row_info.val = val_str

        self.m_rows.append(row_info)

    def print_time(self, name, value, scope_separator="."):
        """
        print_time
        ----------
        Args:
            name:
            value:
            scope_separator:
        """
        self.print_field_int(name, value, 64, UVM_TIME, scope_separator)

    # print_string
    # ------------

    def print_string(self, name, value, scope_separator="."):

        row_info = UVMPrinterRowInfo()
        if name != "":
            self.m_scope.set_arg(name)

        row_info.level = self.m_scope.depth()
        row_info.name = self.adjust_name(self.m_scope.get(),scope_separator)
        row_info.type_name = "string"
        row_info.size = "{}".format(len(value))
        if value == "":
            row_info.val = '""'
        else:
            row_info.val = value
        self.m_rows.append(row_info)

    # print_real
    # ----------

    def print_real(self, name, value, scope_separator="."):
        row_info = UVMPrinterRowInfo()
        if name != "" and name != "...":
            self.m_scope.set_arg(name)
            name = self.m_scope.get()

        row_info.level = self.m_scope.depth()
        row_info.name = self.adjust_name(self.m_scope.get(),scope_separator)
        row_info.type_name = "real"
        row_info.size = "64"
        row_info.val = "{}".format(value)
        self.m_rows.append(row_info)

    def index_string(self, index, name=""):
        """
        index_string
        ------------
        Args:
            index:
            name:
        """
        res = "{}".index
        res = name + "[" + res + "]"

#------------------------------------------------------------------------------
#
# Class: UVMPrinterKnobs
#
# The ~uvm_printer_knobs~ class defines the printer settings available to all
# printer subtypes.
#
#------------------------------------------------------------------------------
class UVMPrinterKnobs:

    def __init__(self):
        # Variable: header
        #
        # Indicates whether the <UVMPrinter::format_header> function should be called when
        # printing an object.
        self.header = True

        # Variable: footer
        #
        # Indicates whether the <UVMPrinter::format_footer> function should be called when
        # printing an object.
        self.footer = True

        # Variable: full_name
        #
        # Indicates whether <UVMPrinter::adjust_name> should print the full name of an identifier
        # or just the leaf name.
        self.full_name = False

        # Variable: identifier
        #
        # Indicates whether <UVMPrinter::adjust_name> should print the identifier. This is useful
        # in cases where you just want the values of an object, but no identifiers.
        self.identifier = True

        # Variable: type_name
        #
        # Controls whether to print a field's type name.
        self.type_name = True

        # Variable: size
        #
        # Controls whether to print a field's size.
        self.size = True

        # Variable: depth
        #
        # Indicates how deep to recurse when printing objects.
        # A depth of -1 means to print everything.
        self.depth = -1

        # Variable: reference
        #
        # Controls whether to print a unique reference ID for object handles.
        # The behavior of this knob is simulator-dependent.
        self.reference = True

        # Variable: begin_elements
        #
        # Defines the number of elements at the head of a list to print.
        # Use -1 for no max.
        self.begin_elements = 5

        # Variable: end_elements
        #
        # This defines the number of elements at the end of a list that
        # should be printed.
        self.end_elements = 5

        # Variable: prefix
        #
        # Specifies the string prepended to each output line
        self.prefix = ""

        # Variable: indent
        #
        # This knob specifies the number of spaces to use for level indentation.
        # The default level indentation is two spaces.
        self.indent = 2

        # Variable: show_root
        #
        # This setting indicates whether or not the initial object that is printed
        # (when current depth is 0) prints the full path name. By default, the first
        # object is treated like all other objects and only the leaf name is printed.
        self.show_root = False

        # Variable: mcd
        #
        # This is a file descriptor, or multi-channel descriptor, that specifies
        # where the print output should be directed.
        #
        # By default, the output goes to the standard output of the simulator.
        self.mcd = UVM_STDOUT

        # Variable: separator
        #
        # For tree printers only, determines the opening and closing
        # separators used for nested objects.
        self.separator = "{}"

        # Variable: show_radix
        #
        # Indicates whether the radix string ('h, and so on) should be prepended to
        # an integral value when one is printed.
        self.show_radix = True

        # Variable: default_radix
        #
        # This knob sets the default radix to use for integral values when no radix
        # enum is explicitly supplied to the <UVMPrinter::print_field> or
        # <UVMPrinter::print_field_int> methods.
        self.default_radix = UVM_HEX

        # Variable: dec_radix
        #
        # This string should be prepended to the value of an integral type when a
        # radix of <UVM_DEC> is used for the radix of the integral object.
        #
        # When a negative number is printed, the radix is not printed since only
        # signed decimal values can print as negative.
        self.dec_radix = "'d"

        # Variable: bin_radix
        #
        # This string should be prepended to the value of an integral type when a
        # radix of <UVM_BIN> is used for the radix of the integral object.
        self.bin_radix = "'b"

        # Variable: oct_radix
        #
        # This string should be prepended to the value of an integral type when a
        # radix of <UVM_OCT> is used for the radix of the integral object.
        self.oct_radix = "'o"

        # Variable: unsigned_radix
        #
        # This is the string which should be prepended to the value of an integral
        # type when a radix of <UVM_UNSIGNED> is used for the radix of the integral
        # object.
        self.unsigned_radix = "'d"

        # Variable: hex_radix
        #
        # This string should be prepended to the value of an integral type when a
        # radix of <UVM_HEX> is used for the radix of the integral object.
        self.hex_radix = "'h"

    def get_radix_str(self, radix):
        if self.show_radix is False:
            return ""
        if radix == UVM_NORADIX:
            radix = self.default_radix
        if radix == UVM_BIN:
            return self.bin_radix
        if radix == UVM_OCT:
            return self.oct_radix
        if radix == UVM_DEC:
            return self.dec_radix
        if radix == UVM_HEX:
            return self.hex_radix
        if radix == UVM_UNSIGNED:
            return self.unsigned_radix
        return ""



class UVMTablePrinter(UVMPrinter):
    """
    Class: UVMTablePrinter

    The table printer prints output in a tabular format.

    The following shows sample output from the table printer::

        ---------------------------------------------------
        Name        Type            Size        Value
        ---------------------------------------------------
        c1          container       -           @1013
        d1          mydata          -           @1022
        v1          integral        32          'hcb8f1c97
        e1          enum            32          THREE
        str         string          2           hi
        value       integral        12          'h2d
        ---------------------------------------------------

    """

    def __init__(self):
        UVMPrinter.__init__(self)
        self.m_max_name = 0
        self.m_max_type = 0
        self.m_max_size = 0
        self.m_max_value = 0

    def calculate_max_widths(self):
        self.m_max_name = 4
        self.m_max_type = 4
        self.m_max_size = 4
        self.m_max_value = 5
        for j in range(0, len(self.m_rows)):
            name_len = 0
            row = self.m_rows[j]
            name_len = self.knobs.indent*row.level + len(row.name)
            if name_len > self.m_max_name:
                self.m_max_name = name_len
            if len(row.type_name) > self.m_max_type:
                self.m_max_type = len(row.type_name)
            if len(row.size) > self.m_max_size:
                self.m_max_size = len(row.size)
            if len(row.val) > self.m_max_value:
                self.m_max_value = len(row.val)

    def emit(self):
        """
        Function: emit

        Formats the collected information from prior calls to ~print_*~
        into table format.

        Returns:
        """
        s = ""
        user_format = ""
        dash = ""
        space = ""
        dashes = ""
        linefeed = "\n" + self.knobs.prefix
        self.calculate_max_widths()

        q = [self. m_max_name, self.m_max_type,self.m_max_size,self.m_max_value,100]
        m = max(q)
        if len(dash) < m:
            dash = "-" * m
            space = " " * m

        if self.knobs.header is True:
            header = ""
            user_format = self.format_header()
            if user_format == "":
                dash_id = ""
                dash_typ = ""
                dash_sz = ""
                head_id = ""
                head_typ = ""
                head_sz = ""
                if self.knobs.identifier:
                    dashes = dash[1:self.m_max_name+2]
                    header = "Name" + space[1:self.m_max_name-2]
                if self.knobs.type_name is True:
                    dashes = dashes + dash[1:self.m_max_type+2]
                    header = header + "Type" + space[1:self.m_max_type-2]
                if self.knobs.size:
                    dashes = dashes + dash[1:self.m_max_size+2]
                    header = header + "Size" + space[1:self.m_max_size-2]
                dashes = dashes + dash[1:self.m_max_value] + linefeed
                header = header + "Value" + space[1:self.m_max_value-5] + linefeed

                s = s + dashes + header + dashes
            else:
                s = s + user_format + linefeed

        for i in range(0, len(self.m_rows)):
            row = self.m_rows[i]
            user_format = self.format_row(row)
            if user_format == "":
                row_str = ""
                if self.knobs.identifier:
                    row_str = (space[1:row.level * self.knobs.indent] + row.name
                        + space[1:self.m_max_name-len(row.name)-(row.level*self.knobs.indent)+2])
                if self.knobs.type_name:
                    row_str = (row_str + row.type_name
                        + space[1:(self.m_max_type-len(row.type_name)+2)])
                if self.knobs.size:
                    row_str = row_str + row.size + space[1:self.m_max_size-len(row.size)+2]
                s = s + row_str + row.val + space[1:self.m_max_value-len(row.val)] + linefeed
            else:
                s = s + user_format + linefeed

        if self.knobs.footer:
            user_format = self.format_footer()
            if user_format == "":
                s = s + dashes
            else:
                s = s + user_format + linefeed

        self.m_rows = []
        return self.knobs.prefix + s


class UVMTreePrinter(UVMPrinter):
    """
    Class: uvm_tree_printer

    By overriding various methods of the <UVMPrinter> super class,
    the tree printer prints output in a tree format.

    The following shows sample output from the tree printer::

      c1: (container@1013) {
        d1: (mydata@1022) {
             v1: 'hcb8f1c97
             e1: THREE
             str: hi
        }
        value: 'h2d
      }
    """


    def __init__(self):
        UVMPrinter.__init__(self)
        self.newline = "\n"
        self.knobs.size = 0
        self.knobs.type_name = 0
        self.knobs.header = 0
        self.knobs.footer = 0

    def emit(self):
        knobs = self.knobs
        s = knobs.prefix
        space = " " * 100
        user_format = ""
        newline = self.newline

        linefeed = newline + knobs.prefix
        if newline == "" or newline == " ":
            linefeed = newline

        # Header
        if knobs.header:
            user_format = self.format_header()
            if user_format != "":
                s = s + user_format + linefeed

        # Loops through all rows formatting them properly
        for i in range(len(self.m_rows)):
            row = self.m_rows[i]
            user_format = self.format_row(row)
            if user_format == "":
                indent_str = space[1:row.level * knobs.indent]

                # Name (id)
                if knobs.identifier:
                    s = s + indent_str + row.name
                    if row.name != "" and row.name != "...":
                        s = s + ": "

                # Type Name
                if row.val[0] == "@":  # is an object w/ knobs.reference on
                    s = s + "(" + row.type_name + row.val + ") "
                else:
                    if (knobs.type_name and
                         (row.type_name != "" or
                          row.type_name != "-" or
                          row.type_name != "...")):
                        s = s + "(" + row.type_name + ") "

                # Size
                if knobs.size:
                    if (row.size != "" or row.size != "-"):
                        s = s + "(" + row.size + ") "

                if i < (len(self.m_rows) - 1):
                    if self.m_rows[i+1].level > row.level:
                        sep = ""
                        if len(knobs.separator) > 0:
                            sep = str(knobs.separator[0])
                        s = s + sep + linefeed
                        continue

                # Value (unconditional)
                s = s + row.val + " " + linefeed

                # Scope handling...
                if i <= len(self.m_rows)-1:
                    end_level = 0
                    if (i == len(self.m_rows)-1):
                        end_level = 0
                    else:
                        end_level = self.m_rows[i+1].level
                    if (end_level < row.level):
                        indent_str = ""
                        for l in range(row.level-1, end_level-1, -1):
                            indent_str = space[1:l * knobs.indent+1]
                            sep = ""
                            if len(knobs.separator) > 1:
                                sep = str(knobs.separator[1])
                            s = s + indent_str + sep + linefeed
            else:
                s = s + user_format

        # Footer
        if knobs.footer:
            user_format = self.format_footer()
            if (user_format != ""):
                s = s + user_format + linefeed

        if (newline == "" or newline == " "):
            s = s + "\n"

        emit = s
        self.m_rows = []
        return emit

class UVMLinePrinter(UVMTreePrinter):
    """
    Class: UVMLinePrinter

    The line printer prints output in a line format.

    The following shows sample output from the line printer::
      c1: (container@1013) { d1: (mydata@1022) { v1: 'hcb8f1c97 e1: THREE str: hi } value: 'h2d }
    """

    def __init__(self):
        UVMTreePrinter.__init__(self)
        self.newline = " "
        self.knobs.indent = 0


# TODO: Print object info in JSON format
class UVMJSONPrinter(UVMPrinter):
    pass
