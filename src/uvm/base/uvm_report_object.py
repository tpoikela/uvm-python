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
from .uvm_object_globals import (UVM_WARNING, UVM_INFO, UVM_ERROR, UVM_FATAL, UVM_LOW, UVM_NONE,
        UVM_MEDIUM)
from .uvm_report_message import UVMReportMessage


def get_verbosity(severity):
    if severity == UVM_ERROR:
        return UVM_LOW
    elif severity == UVM_FATAL:
        return UVM_NONE
    else:
        return UVM_MEDIUM



#------------------------------------------------------------------------------
#
# CLASS: uvm_report_object
#
#------------------------------------------------------------------------------
#
# The uvm_report_object provides an interface to the UVM reporting facility.
# Through this interface, components issue the various messages that occur
# during simulation. Users can configure what actions are taken and what
# file(s) are output for individual messages from a particular component
# or for all messages from all components in the environment. Defaults are
# applied where there is no explicit configuration.
#
# Most methods in uvm_report_object are delegated to an internal instance of a
# <uvm_report_handler>, which stores the reporting configuration and determines
# whether an issued message should be displayed based on that configuration.
# Then, to display a message, the report handler delegates the actual
# formatting and production of messages to a central <uvm_report_server>.
#
# A report consists of an id string, severity, verbosity level, and the textual
# message itself. They may optionally include the filename and line number from
# which the message came. If the verbosity level of a report is greater than the
# configured maximum verbosity level of its report object, it is ignored.
# If a report passes the verbosity filter in effect, the report's action is
# determined. If the action includes output to a file, the configured file
# descriptor(s) are determined.
#
# Actions - can be set for (in increasing priority) severity, id, and
# (severity,id) pair. They include output to the screen <UVM_DISPLAY>,
# whether the message counters should be incremented <UVM_COUNT>, and
# whether a $finish should occur <UVM_EXIT>.
#
# Default Actions - The following provides the default actions assigned to
# each severity. These can be overridden by any of the ~set_*_action~ methods.
#|    UVM_INFO -       UVM_DISPLAY
#|    UVM_WARNING -    UVM_DISPLAY
#|    UVM_ERROR -      UVM_DISPLAY | UVM_COUNT
#|    UVM_FATAL -      UVM_DISPLAY | UVM_EXIT
#
# File descriptors - These can be set by (in increasing priority) default,
# severity level, an id, or (severity,id) pair.  File descriptors are
# standard SystemVerilog file descriptors; they may refer to more than one file.
# It is the user's responsibility to open and close them.
#
# Default file handle - The default file handle is 0, which means that reports
# are not sent to a file even if a UVM_LOG attribute is set in the action
# associated with the report. This can be overridden by any of the ~set_*_file~
# methods.
#
#------------------------------------------------------------------------------


class UVMReportObject(UVMObject):

    def __init__(self, name=""):
        UVMObject.__init__(self, name)
        from .uvm_report_handler import UVMReportHandler
        self.m_rh = UVMReportHandler(name)

    #----------------------------------------------------------------------------
    # Group: Reporting
    #----------------------------------------------------------------------------

    # Function: uvm_get_report_object
    #
    # Returns the nearest uvm_report_object when called.  From inside a
    # uvm_component, the method simply returns ~this~.
    #
    # See also the global version of <uvm_get_report_object>.
    def uvm_get_report_object(self):
        return self

    # Function: uvm_report_enabled
    #
    # Returns 1 if the configured verbosity for this severity/id is greater than
    # or equal to ~verbosity~ else returns 0.
    #
    # See also <get_report_verbosity_level> and the global version of
    # <uvm_report_enabled>.
    def uvm_report_enabled(self, verbosity, severity=UVM_INFO, id=""):
        if self.get_report_verbosity_level(severity, id) >= verbosity:
            return True
        return False

    def uvm_report(self, severity, id, message,
            verbosity=-1,
            filename="",
            line=0,
            context_name="",
            report_enabled_checked=False):

        if verbosity == -1:
            verbosity = get_verbosity(severity)
        l_report_message = None
        if report_enabled_checked is False:
            if not self.uvm_report_enabled(verbosity, severity, id):
                return
        l_report_message = UVMReportMessage.new_report_message()
        l_report_message.set_report_message(severity, id, message,
                                            verbosity, filename, line, context_name)
        self.uvm_process_report_message(l_report_message)

    # Function: uvm_report_info
    def uvm_report_info(self, id, message, verbosity=UVM_MEDIUM, filename="",
            line=0, context_name="", report_enabled_checked=False):
        self.uvm_report(UVM_INFO, id, message, verbosity,
                  filename, line, context_name, report_enabled_checked)

    # Function: uvm_report_warning
    def uvm_report_warning(self, id, message, verbosity=UVM_MEDIUM, filename="",
            line=0, context_name="", report_enabled_checked=False):
        self.uvm_report(UVM_WARNING, id, message, verbosity,
                filename, line, context_name, report_enabled_checked)

    # Function: uvm_report_error
    def uvm_report_error(self, id, message, verbosity = UVM_LOW, filename = "",
            line = 0, context_name = "", report_enabled_checked = False):
        self.uvm_report (UVM_ERROR, id, message, verbosity,
                filename, line, context_name, report_enabled_checked)

    # Function: uvm_report_fatal
    def uvm_report_fatal(self, id, message, verbosity = UVM_NONE, filename = "",
            line = 0, context_name = "", report_enabled_checked = False):
        self.uvm_report (UVM_FATAL, id, message, verbosity,
                filename, line, context_name, report_enabled_checked)

    # Function: uvm_process_report_message
    #
    # This method takes a preformed uvm_report_message, populates it with
    # the report object and passes it to the report handler for processing.
    # It is expected to be checked for verbosity and populated.
    def uvm_process_report_message(self, report_message):
        report_message.set_report_object(self)
        self.m_rh.process_report_message(report_message)

    #----------------------------------------------------------------------------
    # Group: Verbosity Configuration
    #----------------------------------------------------------------------------

    # Function: get_report_verbosity_level
    #
    # Gets the verbosity level in effect for this object. Reports issued
    # with verbosity greater than this will be filtered out. The severity
    # and tag arguments check if the verbosity level has been modified for
    # specific severity/tag combinations.
    def get_report_verbosity_level(self, severity=UVM_INFO, id=""):
        return self.m_rh.get_verbosity_level(severity, id)

    # Function: get_report_max_verbosity_level
    #
    # Gets the maximum verbosity level in effect for this report object.
    # Any report from this component whose verbosity exceeds this maximum will
    # be ignored.
    def get_report_max_verbosity_level(self):
        return self.m_rh.m_max_verbosity_level

    # Function: set_report_verbosity_level
    #
    # This method sets the maximum verbosity level for reports for this component.
    # Any report from this component whose verbosity exceeds this maximum will
    # be ignored.
    def set_report_verbosity_level(self, verbosity_level):
        self.m_rh.set_verbosity_level(verbosity_level)

    # Function: set_report_id_verbosity
    #
    def set_report_id_verbosity(self, id, verbosity):
        self.m_rh.set_id_verbosity(id, verbosity)

    # Function: set_report_severity_id_verbosity
    #
    # These methods associate the specified verbosity threshold with reports of the
    # given ~severity~, ~id~, or ~severity-id~ pair. This threshold is compared with
    # the verbosity originally assigned to the report to decide whether it gets
    # processed.    A verbosity threshold associated with a particular ~severity-id~
    # pair takes precedence over a verbosity threshold associated with ~id~, which
    # takes precedence over a verbosity threshold associated with a ~severity~.
    #
    # The ~verbosity~ argument can be any integer, but is most commonly a
    # predefined <uvm_verbosity> value, <UVM_NONE>, <UVM_LOW>, <UVM_MEDIUM>,
    # <UVM_HIGH>, <UVM_FULL>.

    def set_report_severity_id_verbosity(self, severity, id, verbosity):
        self.m_rh.set_severity_id_verbosity(severity, id, verbosity)

    #----------------------------------------------------------------------------
    # Group: Action Configuration
    #----------------------------------------------------------------------------

    # Function: get_report_action
    #
    # Gets the action associated with reports having the given ~severity~
    # and ~id~.

    def get_report_action(self, severity, id):
        return self.m_rh.get_action(severity,id)

    # Function: set_report_severity_action
    #
    def set_report_severity_action(self, severity, action):
        self.m_rh.set_severity_action(severity, action)

    # Function: set_report_id_action
    #
    def set_report_id_action(self, id, action):
        self.m_rh.set_id_action(id, action)

    # Function: set_report_severity_id_action
    #
    # These methods associate the specified action or actions with reports of the
    # given ~severity~, ~id~, or ~severity-id~ pair. An action associated with a
    # particular ~severity-id~ pair takes precedence over an action associated with
    # ~id~, which takes precedence over an action associated with a ~severity~.
    #
    # The ~action~ argument can take the value <UVM_NO_ACTION>, or it can be a
    # bitwise OR of any combination of <UVM_DISPLAY>, <UVM_LOG>, <UVM_COUNT>,
    # <UVM_STOP>, <UVM_EXIT>, and <UVM_CALL_HOOK>.
    def set_report_severity_id_action(self, severity, id, action):
        self.m_rh.set_severity_id_action(severity, id, action)

    #----------------------------------------------------------------------------
    # Group: File Configuration
    #----------------------------------------------------------------------------

    # Function: get_report_file_handle
    #
    # Gets the file descriptor associated with reports having the given
    # ~severity~ and ~id~.
    def get_report_file_handle(self, severity, id):
        return self.m_rh.get_file_handle(severity,id)

    # Function: set_report_default_file
    def set_report_default_file(self, file):
        self.m_rh.set_default_file(file)

    # Function: set_report_id_file
    def set_report_id_file(self, id, file):
        self.m_rh.set_id_file(id, file)

    # Function: set_report_severity_file
    #
    def set_report_severity_file(self, severity, file):
        self.m_rh.set_severity_file(severity, file)

    # Function: set_report_severity_id_file
    #
    # These methods configure the report handler to direct some or all of its
    # output to the given file descriptor. The ~file~ argument must be a
    # multi-channel descriptor (mcd) or file id compatible with $fdisplay.
    #
    # A FILE descriptor can be associated with reports of
    # the given ~severity~, ~id~, or ~severity-id~ pair.    A FILE associated with
    # a particular ~severity-id~ pair takes precedence over a FILE associated
    # with ~id~, which take precedence over an a FILE associated with a
    # ~severity~, which takes precedence over the default FILE descriptor.
    #
    # When a report is issued and its associated action has the UVM_LOG bit
    # set, the report will be sent to its associated FILE descriptor.
    # The user is responsible for opening and closing these files.

    def set_report_severity_id_file (self, severity, id, file):
        self.m_rh.set_severity_id_file(severity, id, file)

    #----------------------------------------------------------------------------
    # Group: Override Configuration
    #----------------------------------------------------------------------------

    # Function: set_report_severity_override
    #
    def set_report_severity_override(self, cur_severity, new_severity):
        self.m_rh.set_severity_override(cur_severity, new_severity)

    # Function: set_report_severity_id_override
    #
    # These methods provide the ability to upgrade or downgrade a message in
    # terms of severity given ~severity~ and ~id~.    An upgrade or downgrade for
    # a specific ~id~ takes precedence over an upgrade or downgrade associated
    # with a ~severity~.
    def set_report_severity_id_override(self, cur_severity, id, new_severity):
        self. m_rh.set_severity_id_override(cur_severity, id, new_severity)

    #----------------------------------------------------------------------------
    # Group: Report Handler Configuration
    #----------------------------------------------------------------------------

    # Function: set_report_handler
    #
    # Sets the report handler, overwriting the default instance. This allows
    # more than one component to share the same report handler.
    def set_report_handler(self, handler):
        self.m_rh = handler

    # Function: get_report_handler
    #
    # Returns the underlying report handler to which most reporting tasks
    # are delegated.
    def get_report_handler(self):
        return self.m_rh

    # Function: reset_report_handler
    #
    # Resets the underlying report handler to its default settings. This clears
    # any settings made with the ~set_report_*~ methods (see below).
    def reset_report_handler(self):
        self.m_rh.initialize()


