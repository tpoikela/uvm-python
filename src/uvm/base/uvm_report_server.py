
# from cocotb.utils import get_sim_time

from .uvm_object import UVMObject
from .uvm_object_globals import (UVM_BIN, UVM_COUNT, UVM_DEC, UVM_DISPLAY, UVM_ERROR, UVM_EXIT,
                                 UVM_FATAL, UVM_INFO, UVM_LOG, UVM_LOW, UVM_MEDIUM, UVM_NONE,
                                 UVM_NO_ACTION, UVM_RM_RECORD, UVM_SEVERITY_LEVELS, UVM_STOP,
                                 UVM_WARNING)
from .uvm_globals import uvm_report_info, uvm_sim_time
from .uvm_pool import UVMPool
from .uvm_global_vars import uvm_default_printer
from .sv import sv
from ..macros.uvm_message_defines import uvm_info
from .uvm_tr_database import UVMTrDatabase, UVMTextTrDatabase
from typing import List, Any, Callable



def ename(sever) -> str:
    """
    Converts given severity level into string.

    Args:
        sever (int): Severity level.
    Returns:
        str: Severity as string.
    Raises:
        Exception
    """
    if isinstance(sever, str):
        raise ValueError("str was given to ename(). Expected int. Got: " + sever)
    if sever == UVM_INFO:
        return "UVM_INFO"
    if sever == UVM_ERROR:
        return "UVM_ERROR"
    if sever == UVM_FATAL:
        return "UVM_FATAL"
    if sever == UVM_WARNING:
        return "UVM_WARNING"
    return "UNKNOWN_SEVERITY: {}".format(sever)



class UVMReportServer(UVMObject):
    """
    UVMReportServer is a global server that processes all of the reports
    generated by a uvm_report_handler.

    The `UVMReportServer` is an abstract class which declares many of its methods
    as ~pure virtual~.  The UVM uses the <uvm_default_report_server> class
    as its default report server implementation.
    """

    def __init__(self, name="base"):
        UVMObject.__init__(self, name)
        self.m_quit_count = 0
        self.m_max_quit_count = 0
        self.max_quit_overridable = True
        self.m_severity_count = UVMPool()
        self.m_id_count = UVMPool()

        self.enable_report_id_count_summary = True
        self.record_all_messages = False
        self.show_verbosity = False
        self.show_terminator = False

        self.m_message_db: UVMTrDatabase = UVMTextTrDatabase()  # uvm_tr_database
        self.m_streams = {}
        self.reset_quit_count()
        self.reset_severity_counts()
        self.set_max_quit_count(0)
        self.print_on_closed_file = True
        self.logger = print  # By default, use print to emit the messages

    def get_type_name(self) -> str:
        return "uvm_report_server"

    @classmethod
    def set_server(cls, server):
        cs = get_cs()
        #server.copy(cs.get_report_server())
        cs.set_report_server(server)

    @classmethod
    def get_server(cls) -> 'UVMReportServer':
        cs = get_cs()
        return cs.get_report_server()

    def set_logger(self, logger: Callable):
        """
        Sets the logger function used to print the messages. Default is python
        built-in print.

        logger (func): Logging function to use.
        """
        self.logger = logger

    # Function: print
    #
    # The uvm_report_server implements the `UVMObject.do_print()` such that
    # ~print~ method provides UVM printer formatted output
    # of the current configuration. A snippet of example output is shown here::
    #
    #  uvm_report_server                 uvm_report_server  -     @13
    #    quit_count                      int                32    'd0
    #    max_quit_count                  int                32    'd5
    #    max_quit_overridable            bit                1     'b1
    #    severity_count                  severity counts    4     -
    #      [UVM_INFO]                    integral           32    'd4
    #      [UVM_WARNING]                 integral           32    'd2
    #      [UVM_ERROR]                   integral           32    'd50
    #      [UVM_FATAL]                   integral           32    'd10
    #    id_count                        id counts          4     -
    #      [ID1]                         integral           32    'd1
    #      [ID2]                         integral           32    'd2
    #      [RNTST]                       integral           32    'd1
    #    enable_report_id_count_summary  bit                1     'b1
    #    record_all_messages             bit                1     `b0
    #    show_verbosity                  bit                1     `b0
    #    show_terminator                 bit                1     `b0

    def do_print(self, printer):
        """
        Print to show report server state

        Args:
            printer (UVMPrinter):
        """
        l_severity_count_index = 0
        l_id_count_index = ""

        printer.print_int("quit_count", self.m_quit_count, sv.bits(self.m_quit_count), UVM_DEC,
            ".", "int")
        printer.print_int("max_quit_count", self.m_max_quit_count,
            sv.bits(self.m_max_quit_count), UVM_DEC, ".", "int")
        printer.print_int("max_quit_overridable", self.max_quit_overridable,
            sv.bits(self.max_quit_overridable), UVM_BIN, ".", "bit")

        if self.m_severity_count.has_first():
            l_severity_count_index = self.m_severity_count.first()
            sev_count = self.m_severity_count.num()
            printer.print_array_header("severity_count",sev_count,"severity counts")
            ok = True
            while ok:
                printer.print_int("[{}]".format(ename(l_severity_count_index)),
                    self.m_severity_count[l_severity_count_index], 32, UVM_DEC)
                ok = self.m_severity_count.has_next()
                if ok:
                    l_severity_count_index = self.m_severity_count.next()
            printer.print_array_footer()

        if self.m_id_count.has_first():
            l_id_count_index = self.m_id_count.first()
            printer.print_array_header("id_count",self.m_id_count.num(),"id counts")
            ok = True
            while ok:
                printer.print_int("[{}]".format(l_id_count_index),
                    self.m_id_count[l_id_count_index], 32, UVM_DEC)
                ok = self.m_id_count.has_next()
                if ok:
                    l_id_count_index = self.m_id_count.next()
            printer.print_array_footer()

        printer.print_int("enable_report_id_count_summary", self.enable_report_id_count_summary,
            sv.bits(self.enable_report_id_count_summary), UVM_BIN, ".", "bit")
        printer.print_int("record_all_messages", self.record_all_messages,
            sv.bits(self.record_all_messages), UVM_BIN, ".", "bit")
        printer.print_int("show_verbosity", self.show_verbosity,
            sv.bits(self.show_verbosity), UVM_BIN, ".", "bit")
        printer.print_int("show_terminator", self.show_terminator,
            sv.bits(self.show_terminator), UVM_BIN, ".", "bit")

    #----------------------------------------------------------------------------
    # Group: Quit Count
    #----------------------------------------------------------------------------

    def get_max_quit_count(self):
        """
        Get the maximum number of COUNT actions that can be tolerated
        before a UVM_EXIT action is taken. The default is 0, which specifies
        no maximum.

        Returns:
            int: Max quit count allowed for the server.
        """
        return self.m_max_quit_count

    # Function: set_max_quit_count
    #
    # Get or set the maximum number of COUNT actions that can be tolerated
    # before a UVM_EXIT action is taken. The default is 0, which specifies
    # no maximum.
    def set_max_quit_count(self, count, overridable=True):
        if self.max_quit_overridable is False:
            uvm_report_info("NOMAXQUITOVR",
                "The max quit count setting of {} is not overridable to {} due to a previous setting."
                .format(self.m_max_quit_count, count), UVM_NONE)
            return
        self.max_quit_overridable = overridable
        if count < 0:
            self.m_max_quit_count = 0
        else:
            self.m_max_quit_count = count

    def get_quit_count(self):
        """
        Function: get_quit_count

        Returns:
            int: Quit count set for this report server.
        """
        return self.m_quit_count

    def set_quit_count(self, quit_count):
        """
        Args:
            quit_count (int): Desired quit count for this server.
        """
        if quit_count < 0:
            self.m_quit_count = 0
        else:
            self.m_quit_count = quit_count

    def incr_quit_count(self):
        """
        Increment quit count by one.
        """
        self.m_quit_count += 1

    def reset_quit_count(self):
        """
        Set, get, increment, or reset to 0 the quit count, i.e., the number of
        `UVM_COUNT` actions issued.
        """
        self.m_quit_count = 0

    def is_quit_count_reached(self):
        """
        If is_quit_count_reached returns 1, then the quit counter has reached
        the maximum.

        Returns:
            bool: True is maximum quit count reached, False otherwise.
        """
        return self.m_quit_count >= self.m_max_quit_count

    #----------------------------------------------------------------------------
    # Group: Severity Count
    #----------------------------------------------------------------------------


    def get_severity_count(self, severity):
        """
        Returns number of messages reported for given severity.

        Args:
            severity (int): Severity level
        Returns:
            int: Number of messages reported for given severity.
        """
        if self.m_severity_count.exists(severity):
            return self.m_severity_count.get(severity)
        return 0

    # Function: set_severity_count
    def set_severity_count(self, severity, count):
        val = count
        if count < 0:
            val = 0
        self.m_severity_count.add(severity, val)

    # Function: incr_severity_count
    def incr_severity_count(self, severity):
        if self.m_severity_count.exists(severity):
            new_count = self.m_severity_count.get(severity) + 1
            self.m_severity_count.add(severity, new_count)
        else:
            self.m_severity_count.add(severity, 1)

    def reset_severity_counts(self):
        """
        Function: reset_severity_counts

        Set, get, or increment the counter for the given severity, or reset
        all severity counters to 0.
        """
        for s in UVM_SEVERITY_LEVELS:
            self.m_severity_count.add(s, 0)

    #----------------------------------------------------------------------------
    # Group: id Count
    #----------------------------------------------------------------------------

    # Function: get_id_count
    def get_id_count(self, id):
        if self.m_id_count.exists(id):
            return self.m_id_count.get(id)
        return 0

    # Function: set_id_count
    def set_id_count(self, id, count):
        val = count
        if count < 0:
            val = 0
        self.m_id_count.add(id, val)

    # Function: incr_id_count
    #
    # Set, get, or increment the counter for reports with the given id.
    def incr_id_count(self, id):
        if self.m_id_count.exists(id):
            val = self.m_id_count.get(id)
            self.m_id_count.add(id, val + 1)
        else:
            self.m_id_count.add(id, 1)

    #----------------------------------------------------------------------------
    # Group: message recording
    #
    # The ~uvm_default_report_server~ will record messages into the message
    # database, using one transaction per message, and one stream per report
    # object/handler pair.
    #
    #----------------------------------------------------------------------------

    def set_message_database(self, database: UVMTrDatabase):
        """
        Function: set_message_database
        sets the `UVMTrDatabase` used for recording messages

        Args:
            database (UVMTrDatabase):
        """
        self.m_message_db = database

    def get_message_database(self) -> UVMTrDatabase:
        """
        Function: get_message_database
        returns the `uvm_tr_database` used for recording messages

        Returns:
            UVMTrDatabase: Message database.
        """
        return self.m_message_db

    def get_severity_set(self, q: List[Any]) -> None:
        while self.m_severity_count.has_next():
            q.append(self.m_severity_count.next())

    def get_id_set(self, q: List[Any]) -> None:
        while self.m_id_count.has_next():
            q.append(self.m_id_count.next())

    def f_display(self, file, _str) -> None:
        """
        This method sends string severity to the command line if file is 0 and to
        the file(s) specified by file if it is not 0.

        Args:
            file:
            _str:
        """
        if file == 0:
            self.logger(_str)
            # print(_str)
        else:
            if not file.closed:
                file.write(_str + "\n")
            else:
                if self.print_on_closed_file:
                    self.logger('UVM_WARNING. File already closed for msg ' + _str)

    def process_report_message(self, report_message) -> None:
        l_report_handler = report_message.get_report_handler()
        #process p = process::self()
        report_ok = True

        # Set the report server for this message
        report_message.set_report_server(self)

        if report_ok is True:
            from .uvm_report_catcher import UVMReportCatcher
            report_ok = UVMReportCatcher.process_all_report_catchers(report_message)

        if report_message.get_action() == UVM_NO_ACTION:
            report_ok = False

        if report_ok:
            m = ""
            cs = get_cs()
            # give the global server a chance to intercept the calls
            svr = cs.get_report_server()

            # no need to compose when neither UVM_DISPLAY nor UVM_LOG is set
            if report_message.get_action() & (UVM_LOG | UVM_DISPLAY):
                m = svr.compose_report_message(report_message)
            svr.execute_report_message(report_message, m)

    #----------------------------------------------------------------------------
    # Group: Message Processing
    #----------------------------------------------------------------------------


    def execute_report_message(self, report_message, composed_message) -> None:
        """
        Processes the provided message per the actions contained within.

        Expert users can overload this method to customize action processing.

        Args:
            report_message (UVMReportMessage):
            composed_message (str): Formatted message string
        """
        #process p = process::self()

        # Update counts
        self.incr_severity_count(report_message.get_severity())
        self.incr_id_count(report_message.get_id())

        if self.record_all_messages is True:
            report_message.set_action(report_message.get_action() | UVM_RM_RECORD)

        # UVM_RM_RECORD action
        if report_message.get_action() & UVM_RM_RECORD:
            stream = None  # uvm_tr_stream stream
            ro = report_message.get_report_object()
            rh = report_message.get_report_handler()

            # Check for pre-existing stream TODO
            #if (m_streams.exists(ro.get_name()) && (m_streams[ro.get_name()].exists(rh.get_name())))
            #stream = m_streams[ro.get_name()][rh.get_name()]

            # If no pre-existing stream (or for some reason pre-existing stream was ~null~)
            if stream is None:
                # Grab the database
                db = self.get_message_database()

                # If database is ~null~, use the default database
                if db is None:
                    cs = get_cs()
                    db = cs.get_default_tr_database()

                if db is not None:
                    # Open the stream.    Name=report object name, scope=report handler name, type=MESSAGES
                    stream = db.open_stream(ro.get_name(), rh.get_name(), "MESSAGES")
                    # Save off the openned stream
                    self.m_streams[ro.get_name()][rh.get_name()] = stream
            if stream is not None:
                recorder = stream.open_recorder(report_message.get_name(), None,report_message.get_type_name())
                if recorder is not None:
                    report_message.record(recorder)
                    recorder.free()

        # DISPLAY action
        if report_message.get_action() & UVM_DISPLAY:
            self.logger(composed_message)

        # LOG action
        # if log is set we need to send to the file but not resend to the
        # display. So, we need to mask off stdout for an mcd or we need
        # to ignore the stdout file handle for a file handle.
        if report_message.get_action() & UVM_LOG:
            if report_message.get_file() == 0 or report_message.get_file() != 0x80000001: #ignore stdout handle
                tmp_file = report_message.get_file()
                #if report_message.get_file() & 0x80000000 == 0: # is an mcd so mask off stdout
                #    tmp_file = report_message.get_file() & 0xfffffffe
                self.f_display(tmp_file, composed_message)

        # Process the UVM_COUNT action
        if report_message.get_action() & UVM_COUNT:
            if self.get_max_quit_count() != 0:
                self.incr_quit_count()
                # If quit count is reached, add the UVM_EXIT action.
                if self.is_quit_count_reached():
                    report_message.set_action(report_message.get_action() | UVM_EXIT)

        # Process the UVM_EXIT action
        if report_message.get_action() & UVM_EXIT:
            cs = get_cs()
            l_root = cs.get_root()
            l_root.die()

        # Process the UVM_STOP action
        if report_message.get_action() & UVM_STOP:
            raise Exception("$stop from uvm_report_server, msg: " +
                    report_message.sprint())

    def compose_report_message(self, report_message, report_object_name="") -> str:
        """
        Constructs the actual string sent to the file or command line
        from the severity, component name, report id, and the message itself.

        Expert users can overload this method to customize report formatting.

        Args:
            report_message (UVMReportMessage):
            report_object_name (UVMReportObject):
        Returns:
            str: Composed message as string.
        """
        sev_string = ""
        l_severity = UVM_INFO
        l_verbosity = UVM_MEDIUM
        filename_line_string = ""
        time_str = ""
        line_str = ""
        context_str = ""
        verbosity_str = ""
        terminator_str = ""
        msg_body_str = ""
        el_container = None
        prefix = ""
        l_report_handler = None

        l_severity = report_message.get_severity()
        sev_string = ename(l_severity)

        if report_message.get_filename() != "":
            line_str = str(report_message.get_line())
            filename_line_string = report_message.get_filename() + "(" + line_str + ") "

        # Make definable in terms of units.
        #$swrite(time_str, "%0t", $time)
        #time_str = get_sim_time('ns') TODO
        time_str = str(uvm_sim_time('NS')) + 'NS'

        if report_message.get_context() != "":
            context_str = "@@" + report_message.get_context()

        if self.show_verbosity is True:
            verb = report_message.get_verbosity()
            verbosity_str = "(" + verb + ")"

        if self.show_terminator is True:
            terminator_str = " -" + sev_string

        el_container = report_message.get_element_container()
        if el_container.size() == 0:
            msg_body_str = report_message.get_message()
        else:
            prefix = uvm_default_printer.knobs.prefix
            uvm_default_printer.knobs.prefix = " +"
            msg_body_str = report_message.get_message() + "\n" + el_container.sprint()
            uvm_default_printer.knobs.prefix = prefix

        if report_object_name == "":
            l_report_handler = report_message.get_report_handler()
            if l_report_handler is not None:
                report_object_name = l_report_handler.get_full_name()
            else:
                report_object_name = "NO_REPORT_OBJECT"

        result = (sev_string + verbosity_str + " " + filename_line_string
            + "@ " + time_str + ": " + report_object_name + context_str
            + " [" + report_message.get_id() + "] " + msg_body_str + terminator_str)
        return result


    def report_summarize(self, file=0) -> None:
        """
        Outputs statistical information on the reports issued by this central
        report server. This information will be sent to the command line if
        ~file~ is 0, or to the file descriptor ~file~ if it is not 0.

        The `UVMRoot.run_test` method in `UVMRoot` calls this method.
        """
        rpt = self.get_summary_string()
        uvm_info("UVM/REPORT/SERVER", rpt, UVM_LOW)

    def get_summary_string(self) -> str:
        """
        Returns the statistical information on the reports issued by this central report
        server as multi-line string.

        Returns:
            str: End of simulation summary.
        """
        id = ""
        q = []

        from .uvm_report_catcher import UVMReportCatcher
        UVMReportCatcher.summarize()
        q.append("\n--- UVM Report Summary ---\n\n")

        if self.m_max_quit_count != 0:
            if self.m_quit_count >= self.m_max_quit_count:
                q.append("Quit count reached!\n")
            q.append("Quit count : {} of {}\n".format(self.m_quit_count,
                self.m_max_quit_count))

        q.append("** Report counts by severity\n")
        for s in self.m_severity_count.keys():
            q.append("{} : {}\n".format(ename(s), self.m_severity_count.get(s)))

        if self.enable_report_id_count_summary is True:
            q.append("** Report counts by id\n")
            for id in self.m_id_count.keys():
                q.append("[{}] {}\n".format(id, self.m_id_count.get(id)))
        return "".join(q)


def get_cs():
    from .uvm_coreservice import UVMCoreService
    return UVMCoreService.get()
