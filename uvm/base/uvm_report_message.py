#
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
from .uvm_object_globals import *

#------------------------------------------------------------------------------
#
# CLASS: uvm_report_message_element_base
#
# Base class for report message element. Defines common interface.
#
#------------------------------------------------------------------------------


class UVMReportMessageElementBase(UVMObject):

    def __init__(self, name = ""):
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
        self.do_copy(rhs);

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

    def __init__(self, name = "element_container"):
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

    def delete_elements(self, index):
        self.elements = []

    def get_elements(self):
        return self.elements

    def add(self, name, val, action = UVM_LOG|UVM_RM_RECORD):
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
        raise Exception("Not implemented")

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

    def __init__(self, name = ""):
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

    # Function: new_report_message
    # 
    # Creates a new uvm_report_message object.
    # This function is the same as new(), but keeps the random stability.
    #
    @classmethod
    def new_report_message(cls, name = "uvm_report_message"):
        p = None
        rand_state = ""
        #p = process::self();

        if not p is None:
            pass
            #rand_state = p.get_randstate();
        new_report_message = UVMReportMessage(name)
        #if (p != null):
            #p.set_randstate(rand_state);
        return new_report_message

    # Function: print
    #
    # The uvm_report_message implements <uvm_object::do_print()> such that
    # ~print~ method provides UVM printer formatted output
    # of the message.  A snippet of example output is shown here:
    #
    def do_print(self, printer):
        l_verbosity = 0
        UVMObject.do_print(self, printer)
        printer.print_generic("severity", "uvm_severity", 
                          32, _severity.name());
        printer.print_string("id", _id);
        printer.print_string("message",_message);
        printer.print_int("verbosity", _verbosity, 32, UVM_HEX);
        printer.print_string("filename", _filename);
        printer.print_int("line", _line, 32, UVM_UNSIGNED);
        printer.print_string("context_name", _context_name);
        if self._report_message_element_container.size() != 0:
            self._report_message_element_container.pprint(printer);

    def do_copy (self, rhs):
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

    #----------------------------------------------------------------------------
    # Group:  Infrastructure References
    #----------------------------------------------------------------------------

    # Function: get_report_object
    def get_report_object(self):
        return self._report_object

    # Function: set_report_object
    #
    # Get or set the uvm_report_object that originated the message.
    def set_report_object(self, ro):
        self._report_object = ro;

    # Function: get_report_handler
    def get_report_handler(self):
        return self._report_handler

    # Function: set_report_handler
    #
    # Get or set the uvm_report_handler that is responsible for checking
    # whether the message is enabled, should be upgraded/downgraded, etc.
    def set_report_handler(self, rh):
        self._report_handler = rh
  
    # Function: get_report_server
    def get_report_server(self):
        return self._report_server

    # Function: set_report_server
    #
    # Get or set the uvm_report_server that is responsible for servicing
    # the message's actions.  
    def set_report_server(self, rs):
        self._report_server = rs;

    #----------------------------------------------------------------------------
    # Group:  Message Fields
    #----------------------------------------------------------------------------

    # Function: get_severity
    def get_severity(self):
        return self._severity

    # Function: set_severity
    #
    # Get or set the severity (UVM_INFO, UVM_WARNING, UVM_ERROR or 
    # UVM_FATAL) of the message.  The value of this field is determined via
    # the API used (`uvm_info(), `uvm_waring(), etc.) and populated for the user.
    def set_severity(self, sev):
        self._severity = sev;

    # Function: get_id
    def get_id(self):
        return self._id

    # Function: set_id
    #
    # Get or set the id of the message.  The value of this field is 
    # completely under user discretion.  Users are recommended to follow a
    # consistent convention.  Settings in the uvm_report_handler allow various
    # messaging controls based on this field.  See <uvm_report_handler>.
    def set_id(self, id):
        self._id = id;

    # Function: get_message
    def get_message(self):
        return self._message

    # Function: set_message
    #
    # Get or set the user message content string.
    def set_message(self, msg):
        self._message = msg;

    # Function: get_verbosity
    def get_verbosity(self):
        return self._verbosity

    # Function: set_verbosity
    #
    # Get or set the message threshold value.  This value is compared
    # against settings in the <uvm_report_handler> to determine whether this
    # message should be executed.
    def set_verbosity(self, ver):
        self._verbosity = ver;

    # Function: get_filename
    def get_filename(self):
        return self._filename

    # Function: set_filename
    #
    # Get or set the file from which the message originates.  This value
    # is automatically populated by the messaging macros.
    def set_filename(self, fname):
        self._filename = fname;

    # Function: get_line
    def get_line(self):
        return self._line

    # Function: set_line
    #
    # Get or set the line in the ~file~ from which the message originates.
    # This value is automatically populate by the messaging macros.
    def set_line(self, ln):
        self._line = ln;

    # Function: get_context
    def get_context(self):
        return self._context_name

    # Function: set_context
    #
    # Get or set the optional user-supplied string that is meant to convey
    # the context of the message.  It can be useful in scopes that are not
    # inherently UVM like modules, interfaces, etc.
    def set_context(self, cn):
        self._context_name = cn;

    # Function: get_action
    def get_action(self):
        return self._action

    # Function: set_action
    #
    # Get or set the action(s) that the uvm_report_server should perform
    # for this message.  This field is populated by the uvm_report_handler during
    # message execution flow.
    def set_action(self, act):
        self._action = act

    # Function: get_file
    def get_file(self):
        return self._file

    # Function: set_file
    #
    # Get or set the file that the message is to be written to when the 
    # message's action is UVM_LOG.  This field is populated by the 
    # uvm_report_handler during message execution flow.
    def set_file(self, fl):
        self._file = fl

    # Function: get_element_container
    #
    # Get the element_container of the message
    def get_element_container(self):
        return self._report_message_element_container

    # Function: set_report_message
    #
    # Set all the common fields of the report message in one shot.
    #
    def set_report_message(self, severity, id, message, verbosity, filename,
            line, context_name):
        self._context_name = context_name;
        self._filename = filename;
        self._line = line;
        self._severity = severity;
        self._id = id;
        self._message = message;
        self._verbosity = verbosity;

    #----------------------------------------------------------------------------
    # Group-  Message Recording
    #----------------------------------------------------------------------------
    # TODO

    #----------------------------------------------------------------------------
    # Group:  Message Element APIs
    #----------------------------------------------------------------------------
    def add(self, name, value, action = UVM_LOG|UVM_RM_RECORD):
         self._report_message_element_container.add(name, value, action)

import unittest

class TestUVMReportMessage(unittest.TestCase):

    def test_message(self):
        msg = UVMReportMessage()
        cont = msg.get_element_container()
        self.assertEqual(cont.size(), 0)
        msg.add("msg", {1: 2}, UVM_LOG)
        self.assertEqual(cont.size(), 1)

if __name__ == '__main__':
    unittest.main()
