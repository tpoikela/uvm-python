

import unittest

from uvm.base.uvm_report_handler import UVMReportHandler
from uvm.base.uvm_object_globals import *


class TestUVMReportHandler(unittest.TestCase):

    def test_handler(self):
        rh = UVMReportHandler("handler")
        fhandle = rh.get_severity_id_file(UVM_ERROR, "")
        self.assertEqual(fhandle, rh.default_file_handle)
        verb = rh.get_verbosity_level()
        self.assertEqual(verb, rh.m_max_verbosity_level)
        rh.report(UVM_ERROR, "xxx", "id0", "Message")


    def test_action_overrides(self):
        rh = UVMReportHandler("handler")
        rh.set_severity_action(UVM_ERROR, UVM_LOG)
        rh.set_severity_id_action(UVM_ERROR, "XYZ", UVM_COUNT)

        verb = rh.get_action(UVM_ERROR, "ABC")
        self.assertEqual(verb, UVM_LOG)
        verb = rh.get_action(UVM_ERROR, "XYZ")
        self.assertEqual(verb, UVM_COUNT)


if __name__ == '__main__':
    unittest.main()
