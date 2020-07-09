#------------------------------------------------------------------------------
#   Copyright 2007-2010 Mentor Graphics Corporation
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
#   the License for the specific language governing
#   permissions and limitations under the License.
#------------------------------------------------------------------------------

from .uvm_object import UVMObject
from .uvm_object_globals import (UVM_DISPLAY, UVM_HEX, UVM_INFO, UVM_LOG,
    UVM_RM_RECORD, UVM_UNSIGNED)

#------------------------------------------------------------------------------
#
# CLASS: uvm_report_message_element_base
#
# Base class for report message element. Defines common interface.
#
#------------------------------------------------------------------------------


class UVMReportMessageElementBase(UVMObject):

    def __init__(self, name=""):
        UVMObject.__init__(self, name)
        self._action = UVM_DISPLAY
        self._name = ""
        self._val = None

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def set_action(self, action):
        self._action = action

    def get_action(self):
        return self._action

    def set_val(self, val):
        self._val = val

    def get_val(self):
        return self._val

    def pprint(self, printer):
        if self._action & (UVM_LOG | UVM_DISPLAY):
            self.do_print(printer)

    def record(self, recorder):
        if self._action & UVM_RM_RECORD:
            self.do_record(recorder)

    def copy(self, rhs):
        self.do_copy(rhs)

    def clone(self):
        return self.do_clone()

    def do_print(self, printer):
        pass

    def do_record(self, recorder):
        pass

    def do_copy(self, rhs):
        pass

    def do_clone(self):
        pass

#------------------------------------------------------------------------------
#
# CLASS: uvm_report_message_int_element
#
# Message element class for integral type
#
#------------------------------------------------------------------------------
class UVMReportMessageIntElement(UVMReportMessageElementBase):
    pass

class UVMReportMessageStringElement(UVMReportMessageElementBase):
    pass

class UVMReportMessageObjectElement(UVMReportMessageElementBase):
    pass

#------------------------------------------------------------------------------
#
# CLASS: uvm_report_message_element_container
#
# A container used by report message to contain the dynamically added elements,
# with APIs to add and delete the elements.
#
#------------------------------------------------------------------------------


class UVMReportMessageElementContainer(UVMObject):

    def __init__(self, name="element_container"):
        UVMObject.__init__(self, name)
        self.elements = []

    def size(self):
        return len(self.elements)

    def delete(self, index):
        elements = []
        for i in range(0, self.size()):
            if i != index:
                elements.append(self.elements[i])
        self.elements = elements

    def delete_elements(self):
        self.elements = []

    def get_elements(self):
        return self.elements

    def add(self, name, val, action=UVM_LOG | UVM_RM_RECORD):
        elem = UVMReportMessageElementBase()
        elem.set_name(name)
        elem.set_val(val)
        elem.set_action(action)
        self.elements.append(elem)

    def do_print(self, printer):
        UVMObject.do_print(self, printer)
        for i in range(0, self.size()):
            self.elements[i].pprint(printer)

    def do_record(self, recorder):
        UVMObject.do_record(self, recorder)
        for i in range(0, self.size()):
            self.elements[i].record(recorder)

    def do_copy(self, rhs):
        super().do_copy(rhs)
        #uvm_report_message_element_container urme_container
        #if(!$cast(urme_container, rhs) || (rhs==null))
        #    return
        urme_container = rhs
        if rhs is None:
            return

        self.delete_elements()
        for i in range(len(urme_container.elements)):
            self.elements.append(urme_container.elements[i].clone())


#------------------------------------------------------------------------------
#
# CLASS: uvm_report_message
#
# The uvm_report_message is the basic UVM object message class.  It provides
# the fields that are common to all messages.  It also has a message element
# container and provides the APIs necessary to add integral types, strings and
# uvm_objects to the container. The report message object can be initialized
# with the common fields, and passes through the whole reporting system (i.e.
# report object, report handler, report server, report catcher, etc) as an
# object. The additional elements can be added/deleted to/from the message
# object anywhere in the reporting system, and can be printed or recorded
# along with the common fields.
#
#------------------------------------------------------------------------------


class UVMReportMessage(UVMObject):

    def __init__(self, name=""):
        UVMObject.__init__(self, name)

        self._report_object = None
        self._report_handler = None
        self._report_server = None

        self._severity = UVM_INFO
        self._id = ""
        self._message = ""
        self._verbosity = 0
        self._filename = ""
        self._line = ""
        self._context_name = ""
        self._action = UVM_LOG | UVM_DISPLAY
        self._file = 0
        self._report_message_element_container = UVMReportMessageElementContainer()

    @classmethod
    def new_report_message(cls, name="uvm_report_message") -> 'UVMReportMessage':
        """
        Creates a new uvm_report_message object.
        This function is the same as new(), but keeps the random stability.

        Args:
            name (str): Name of the message
        Returns:
            UVMReportMessage: Created report message
        """
        p = None
        # rand_state = ""
        #p = process::self()

        if p is not None:
            pass
            #rand_state = p.get_randstate()
        new_report_message = UVMReportMessage(name)
        # if (p != null):
        #   p.set_randstate(rand_state)
        return new_report_message

    def do_print(self, printer):
        """
        The uvm_report_message implements `UVMObject.do_print()` such that
        `print` method provides UVM printer formatted output
        of the message.  A snippet of example output is shown here:

        Args:
            printer (UVMPrinter): Printer used for printing the msg
        """
        l_verbosity = 0
        UVMObject.do_print(self, printer)
        printer.print_generic("severity", "uvm_severity",
                          32, str(self._severity))
        printer.print_string("id", self._id)
        printer.print_string("message", self._message)
        printer.print_int("verbosity", self._verbosity, 32, UVM_HEX)
        printer.print_string("filename", self._filename)
        printer.print_int("line", self._line, 32, UVM_UNSIGNED)
        printer.print_string("context_name", self._context_name)
        if self._report_message_element_container.size() != 0:
            self._report_message_element_container.print(printer)

    def do_copy(self, rhs):
        report_message = rhs
        UVMObject.do_copy(self, rhs)
        if rhs is None:
            return
        self._report_object = report_message.get_report_object()
        self._report_handler = report_message.get_report_handler()
        self._report_server = report_message.get_report_server()
        self._context_name = report_message.get_context()
        self._file = report_message.get_file()
        self._filename = report_message.get_filename()
        self._line = report_message.get_line()
        self._action = report_message.get_action()
        self._severity = report_message.get_severity()
        self._id = report_message.get_id()
        self._message = report_message.get_message()
        self._verbosity = report_message.get_verbosity()
        self._report_message_element_container.copy(report_message._report_message_element_container)

    def create(self, name="") -> 'UVMReportMessage':
        return UVMReportMessage(name)

    #----------------------------------------------------------------------------
    # Group:  Infrastructure References
    #----------------------------------------------------------------------------

    def get_report_object(self):
        """
        Function: get_report_object

        Returns:
            UVMReportObject: Report object for this msg.
        """
        return self._report_object

    def set_report_object(self, ro):
        """
        Get or set the uvm_report_object that originated the message.

        Args:
            ro (UVMReportObject):
        """
        self._report_object = ro

    def get_report_handler(self):
        """
        Get the UVMReportHandler that is responsible for checking
        whether the message is enabled, should be upgraded/downgraded, etc.

        Returns:
            UVMReportHandler: Report handler for this msg.
        """
        return self._report_handler

    def set_report_handler(self, rh):
        """
        Set the UVMReportHandler that is responsible for checking
        whether the message is enabled, should be upgraded/downgraded, etc.

        Args:
            rh:
        """
        self._report_handler = rh

    def get_report_server(self):
        """
        Get the `UVMReportServer` that is responsible for servicing
        the message's actions.

        Returns:
            UVMReportServer: Report server for this object
        """
        return self._report_server

    def set_report_server(self, rs):
        """
        Set the `UVMReportServer` that is responsible for servicing
        the message's actions.

        Args:
            rs (UVMReportServer): Report server for this object.
        """
        self._report_server = rs

    #----------------------------------------------------------------------------
    # Group:  Message Fields
    #----------------------------------------------------------------------------

    def get_severity(self):
        """
        Function: get_severity
        Returns:
        """
        return self._severity

    def set_severity(self, sev):
        """
        Function: set_severity

        Get or set the severity (UVM_INFO, UVM_WARNING, UVM_ERROR or
        UVM_FATAL) of the message.  The value of this field is determined via
        the API used (`uvm_info(), `uvm_waring(), etc.) and populated for the user.
        Args:
            sev:
        """
        self._severity = sev

    def get_id(self):
        """
        Function: get_id
        Returns:
        """
        return self._id

    def set_id(self, id):
        """
        Function: set_id

        Get or set the id of the message.  The value of this field is
        completely under user discretion.  Users are recommended to follow a
        consistent convention.  Settings in the uvm_report_handler allow various
        messaging controls based on this field.  See `uvm_report_handler`.
        Args:
            id:
        """
        self._id = id

    def get_message(self):
        """
        Function: get_message
        Returns:
        """
        return self._message

    def set_message(self, msg):
        """
        Function: set_message

        Get or set the user message content string.
        Args:
            msg:
        """
        self._message = msg

    def get_verbosity(self):
        """
        Function: get_verbosity
        Returns:
        """
        return self._verbosity

    def set_verbosity(self, ver):
        """
        Function: set_verbosity

        Get or set the message threshold value.  This value is compared
        against settings in the `uvm_report_handler` to determine whether this
        message should be executed.
        Args:
            ver:
        """
        self._verbosity = ver

    def get_filename(self):
        """
        Function: get_filename
        Returns:
        """
        return self._filename

    def set_filename(self, fname):
        """
        Function: set_filename

        Get or set the file from which the message originates.  This value
        is automatically populated by the messaging macros.
        Args:
            fname:
        """
        self._filename = fname

    def get_line(self):
        """
        Function: get_line
        Returns:
        """
        return self._line

    def set_line(self, ln):
        """
        Function: set_line

        Get or set the line in the `file` from which the message originates.
        This value is automatically populate by the messaging macros.
        Args:
            ln:
        """
        self._line = ln

    def get_context(self):
        """
        Get the optional user-supplied string that is meant to convey
        the context of the message.  It can be useful in scopes that are not
        inherently UVM like modules, interfaces, etc.

        Returns:
            str: Context for the msg.
        """
        return self._context_name

    def set_context(self, cn):
        """
        Set the optional user-supplied string that is meant to convey
        the context of the message.  It can be useful in scopes that are not
        inherently UVM like modules, interfaces, etc.

        Args:
            cn (str): Context for the msg.
        """
        self._context_name = cn

    def get_action(self):
        """
        Get the action(s) that the `UVMReportServer` should perform
        for this message.  This field is populated by the `UVMReportHandler` during
        message execution flow.

        Returns:
        """
        return self._action

    def set_action(self, act):
        """
        Set the action(s) that the `UVMReportServer` should perform
        for this message.  This field is populated by the `UVMReportHandler` during
        message execution flow.

        Args:
            act:
        """
        self._action = act

    def get_file(self):
        """
        Get or set the file that the message is to be written to when the
        message's action is UVM_LOG.  This field is populated by the
        `UVMReportHandler` during message execution flow.

        Returns:
            str: Filename associated with this msg.
        """
        return self._file

    def set_file(self, fl):
        """
        Set the file that the message is to be written to when the
        message's action is UVM_LOG.  This field is populated by the
        `UVMReportHandler` during message execution flow.

        Args:
            fl (str): Filename associated with this msg.
        """
        self._file = fl

    def get_element_container(self):
        """
        Get the element_container of the message

        Returns:
            UVMReportMessageElementContainer: Element_container of the message
        """
        return self._report_message_element_container

    def set_report_message(self, severity, id, message, verbosity, filename,
            line, context_name):
        """
        Set all the common fields of the report message in one shot.

        Args:
            severity:
            id:
            message:
            verbosity:
            filename:
            line:
            context_name:
        """
        self._context_name = context_name
        self._filename = filename
        self._line = line
        self._severity = severity
        self._id = id
        self._message = message
        self._verbosity = verbosity

    #----------------------------------------------------------------------------
    # Group-  Message Recording
    #----------------------------------------------------------------------------
    # TODO

    def add(self, name, value, action=UVM_LOG | UVM_RM_RECORD):
        """
        #----------------------------------------------------------------------------
        Group:  Message Element APIs
        #----------------------------------------------------------------------------
        Args:
            name:
            value:
            action:
        """
        self._report_message_element_container.add(name, value, action)
