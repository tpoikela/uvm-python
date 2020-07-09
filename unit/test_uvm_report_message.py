
import unittest

from uvm.base.uvm_report_message import UVMReportMessage
from uvm.base.uvm_object_globals import UVM_LOG


class TestUVMReportMessage(unittest.TestCase):

    def test_message(self):
        msg = UVMReportMessage()
        cont = msg.get_element_container()
        self.assertEqual(cont.size(), 0)
        msg.add("msg", {1: 2}, UVM_LOG)
        self.assertEqual(cont.size(), 1)

    def test_msg_copy(self):
        msg = UVMReportMessage.new_report_message()
        msg.set_message("My message is this")
        msg.set_verbosity(111)
        msg.set_filename('log.txt')
        msg_copy = msg.clone()

        self.assertEqual(msg_copy.get_name(), msg.get_name())
        self.assertEqual(msg_copy.get_verbosity(), msg.get_verbosity())
        self.assertEqual(msg_copy.get_filename(), msg.get_filename())

        msg_copy = UVMReportMessage()
        msg_copy.copy(msg)
        self.assertEqual(msg_copy.get_message(), msg.get_message())


if __name__ == '__main__':
    unittest.main()
