
from .uvm_object import UVMObject
from .uvm_pool import UVMPool
from .uvm_object_globals import *
from .uvm_globals import uvm_report_enabled

class UVMReportHandler(UVMObject):

    def __init__(self, name=""): 
        UVMObject.__init__(self, name)
        self.m_max_verbosity_level = 0
        self.id_verbosities = UVMPool()
        self.severity_id_verbosities = {}  # string -> UVMPool()
        self.id_actions = UVMPool()
        self.severity_actions = UVMPool()
        self.severity_id_actions = {}  # string -> UVMPool
        self.sev_overrides = UVMPool()
        self.sev_id_overrides = {}  # string -> UVMPool

        self.default_file_handle = 1
        self.id_file_handles = UVMPool()
        self.severity_file_handles = {}  # severity -> UVM_FILE
        self.severity_id_file_handles = {}  # severity -> UVMPool
        self.initialize()

    def do_print(self, printer):
        print("UVMReportHandler do_print() TODO")

    @classmethod
    def format_action(cls, action):
        s = ""
        if action == UVM_NO_ACTION:
            s = "UVM_NO_ACTION"
        else:
            if action & UVM_DISPLAY:
                s = s + "DISPLAY "
            if action & UVM_LOG:
                s = s + "LOG "
            if action & UVM_RM_RECORD:
                s = s + "RM_RECORD "
            if action & UVM_COUNT:
                s = s + "COUNT "
            if action & UVM_CALL_HOOK:
                s = s + "CALL_HOOK "
            if action & UVM_EXIT:
                s = s + "EXIT "
            if action & UVM_STOP:
                s = s + "STOP "
        return s

    def initialize(self):
        self.set_default_file(0)
        self.m_max_verbosity_level = UVM_MEDIUM
        self.set_severity_action(UVM_INFO,    UVM_DISPLAY)
        self.set_severity_action(UVM_WARNING, UVM_DISPLAY)
        self.set_severity_action(UVM_ERROR,   UVM_DISPLAY | UVM_COUNT)
        self.set_severity_action(UVM_FATAL,   UVM_DISPLAY | UVM_EXIT)

        self.set_severity_file(UVM_INFO, self.default_file_handle)
        self.set_severity_file(UVM_WARNING, self.default_file_handle)
        self.set_severity_file(UVM_ERROR,   self.default_file_handle)
        self.set_severity_file(UVM_FATAL,   self.default_file_handle)

    def get_severity_id_file(self, severity, id):
        """ Return the file id based on the severity and the id """
        if severity in self.severity_id_file_handles:
            array = self.severity_id_file_handles[severity]
            if array.exists(id):
                return array.get(id)

        if self.id_file_handles.exists(id):
            return self.id_file_handles.get(id)

        if severity in self.severity_file_handles:
            return self.severity_file_handles[severity]
        return self.default_file_handle

    def set_verbosity_level(self, verbosity_level):
        self.m_max_verbosity_level = verbosity_level

    # Function- get_verbosity_level
    #
    # Returns the verbosity associated with the given ~severity~ and ~id~.
    # 
    # First, if there is a verbosity associated with the ~(severity,id)~ pair,
    # return that.  Else, if there is a verbosity associated with the ~id~, return
    # that.  Else, return the max verbosity setting.
    def get_verbosity_level(self, severity=UVM_INFO, id=""):
        if severity in self.severity_id_verbosities:
            array = self.severity_id_verbosities[severity]
            if array.exists(id):
                return array.get(id)

        if self.id_verbosities.exists(id):
            return self.id_verbosities.get(id)

        return self.m_max_verbosity_level

    # Function- get_action
    #
    # Returns the action associated with the given ~severity~ and ~id~.
    # 
    # First, if there is an action associated with the ~(severity,id)~ pair,
    # return that.  Else, if there is an action associated with the ~id~, return
    # that.  Else, if there is an action associated with the ~severity~, return
    # that. Else, return the default action associated with the ~severity~.
    def get_action(self, severity, id):
        if severity in self.severity_id_actions:
            array = self.severity_id_actions[severity]
            if array.exists(id):
                return array.get(id)

        if self.id_actions.exists(id):
            return self.id_actions.get(id)
        return self.severity_actions.get(severity)

    # Function- get_file_handle
    #
    # Returns the file descriptor associated with the given ~severity~ and ~id~.
    #
    # First, if there is a file handle associated with the ~(severity,id)~ pair,
    # return that. Else, if there is a file handle associated with the ~id~, return
    # that. Else, if there is an file handle associated with the ~severity~, return
    # that. Else, return the default file handle.
    def get_file_handle(self, severity, id):
        _file = self.get_severity_id_file(severity, id)
        if _file != 0:
            return _file
        
        if self.id_file_handles.exists(id):
            _file = self.id_file_handles.get(id)
            if _file != 0:
                return _file
        
        if severity in self.severity_file_handles:
            _file = self.severity_file_handles[severity]
            if _file != 0:
                return _file
        return self.default_file_handle

    def process_report_message(self, report_message):
        from .uvm_report_server import UVMReportServer
        srvr = UVMReportServer.get_server()
        id = report_message.get_id()
        severity = report_message.get_severity()

        # Check for severity overrides and apply them before calling the server.
        # An id specific override has precedence over a generic severity override.
        if id in self.sev_id_overrides:
            if self.sev_id_overrides[id].exists(severity):
                severity = self.sev_id_overrides[id].get(severity)
                report_message.set_severity(severity)
        else:
            if self.sev_overrides.exists(severity):
                severity = self.sev_overrides.get(severity)
                report_message.set_severity(severity)
        report_message.set_file(self.get_file_handle(severity, id))
        report_message.set_report_handler(self)
        report_message.set_action(self.get_action(severity, id))
        srvr.process_report_message(report_message)

    def set_severity_action(self, severity, action):
        self.severity_actions.add(severity, action)

    def set_id_action(self, id, action):
        self.id_actions.add(id, action)

    def set_severity_id_action(self, severity, id, action):
        if severity not in self.severity_id_actions:
            self.severity_id_actions[severity] = UVMPool()
        self.severity_id_actions[severity].add(id, action)
  
    def set_id_verbosity(self, id, verbosity):
        self.id_verbosities.add(id, verbosity)

    def set_severity_id_verbosity(self, severity, id, verbosity):
        if severity not in self.severity_id_verbosities:
            self.severity_id_verbosities[severity] = UVMPool()
        self.severity_id_verbosities[severity].add(id,verbosity)

    def set_default_file(self, file):
        self.default_file_handle = file

    def set_severity_file(self, severity, file):
        self.severity_file_handles[severity] = file

    def set_id_file(self, id, file):
        self.id_file_handles.add(id, file)

    def set_severity_id_file(self, severity, id, file):
        if severity not in self.severity_id_file_handles:
            self.severity_id_file_handles[severity] = UVMPool()
        self.severity_id_file_handles[severity].add(id, file)

    def set_severity_override(self, cur_severity, new_severity):
        self.sev_overrides.add(cur_severity, new_severity)

    def set_severity_id_override(self, cur_severity, id, new_severity):
        # has precedence over set_severity_override
        # silently override previous setting
        if id not in self.sev_id_overrides:
            self.sev_id_overrides[id] = UVMPool()
        self.sev_id_overrides[id].add(cur_severity, new_severity)

    # Function- report
    #
    # This is the common handler method used by the four core reporting methods
    # (e.g., uvm_report_error) in <uvm_report_object>.

    def report(self, severity, name, id, message,
      verbosity_level=UVM_MEDIUM, filename="", line=0,
      client=None):

        l_report_enabled = False
        l_report_message = None
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        if not uvm_report_enabled(verbosity_level, UVM_INFO, id):
            return

        if client is None:
            client = cs.get_root()

        from .uvm_report_message import UVMReportMessage
        l_report_message = UVMReportMessage.new_report_message()
        l_report_message.set_report_message(severity, id, message, 
                                            verbosity_level, filename, line, name)
        l_report_message.set_report_object(client)
        l_report_message.set_action(self.get_action(severity,id))
        self.process_report_message(l_report_message)
