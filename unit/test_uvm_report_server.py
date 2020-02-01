
import unittest
from uvm.base.uvm_report_server import UVMReportServer
from uvm.base.uvm_object_globals import *


class TestUVMReportServer(unittest.TestCase):

    def test_server(self):
        srv = UVMReportServer()

    def test_quit_count(self):
        srv = UVMReportServer()
        self.assertEqual(srv.get_quit_count(), 0)
        self.assertEqual(srv.is_quit_count_reached(), True)
        srv.set_max_quit_count(10, True)
        self.assertEqual(srv.is_quit_count_reached(), False)
        srv.set_quit_count(11)
        self.assertEqual(srv.is_quit_count_reached(), True)

    def test_severity_count(self):
        srv = UVMReportServer()
        self.assertEqual(srv.get_severity_count(UVM_ERROR), 0)
        srv.set_severity_count(UVM_FATAL, 10)
        self.assertEqual(srv.get_severity_count(UVM_FATAL), 10)
        srv.incr_severity_count(UVM_FATAL)
        self.assertEqual(srv.get_severity_count(UVM_FATAL), 11)
        srv.incr_severity_count(UVM_ERROR)
        self.assertEqual(srv.get_severity_count(UVM_ERROR), 1)

    def test_id_count(self):
        srv = UVMReportServer()
        self.assertEqual(srv.get_id_count("a"), 0)
        srv.incr_id_count("a")
        self.assertEqual(srv.get_id_count("a"), 1)
        srv.set_id_count("b", 10)
        self.assertEqual(srv.get_id_count("b"), 10)

    def test_do_print(self):
        srv = UVMReportServer()
        from uvm.base.uvm_printer import UVMTablePrinter
        printer = UVMTablePrinter()
        srv.do_print(printer)
        srv_as_str = printer.emit()
        self.assertRegex(srv_as_str, r'quit_count')
        self.assertRegex(srv_as_str, r'UVM_INFO')
        self.assertRegex(srv_as_str, r'UVM_ERROR')
        self.assertRegex(srv_as_str, r'UVM_FATAL')
        self.assertRegex(srv_as_str, r'UVM_WARNING')


    def test_process_report_message(self):
        srv = UVMReportServer()
        from uvm.base.uvm_report_message import UVMReportMessage
        rpt_msg = UVMReportMessage()
        rpt_msg.set_action(UVM_LOG | UVM_DISPLAY)
        srv.process_report_message(rpt_msg)

    def test_execute_report_message(self):
        srv = UVMReportServer()

    def test_compose_report_message(self):
        srv = UVMReportServer()

    def test_report_summarize(self):
        srv = UVMReportServer()
        from uvm.base.uvm_report_message import UVMReportMessage
        rpt_msg = UVMReportMessage()
        rpt_msg.set_action(UVM_LOG | UVM_DISPLAY)
        srv.process_report_message(rpt_msg)
        srv.report_summarize()

if __name__ == '__main__':
    unittest.main()
