
import unittest
from uvm.base.uvm_report_object import UVMReportObject
from uvm.base.uvm_object_globals import (
    UVM_INFO, UVM_ERROR, UVM_LOG, UVM_DISPLAY, UVM_COUNT, UVM_MEDIUM, UVM_HIGH)


class TestUVMReportObject(unittest.TestCase):
    """ Unit tests for UVMReportObject """

    def test_verbosity(self):
        obj = UVMReportObject('rpt')
        rh = obj.get_report_handler()
        verb = rh.get_verbosity_level(UVM_INFO, "")
        self.assertEqual(verb, UVM_MEDIUM)
        self.assertEqual(obj.uvm_report_enabled(UVM_MEDIUM, UVM_INFO), True)

    def test_report_enabled(self):
        obj = UVMReportObject('rpt')
        is_en = obj.uvm_report_enabled(UVM_MEDIUM, UVM_INFO, id="")
        self.assertEqual(is_en, True)
        is_en = obj.uvm_report_enabled(UVM_HIGH, UVM_INFO, id="")
        self.assertEqual(is_en, False)

    def test_report_severity(self):
        obj = UVMReportObject('rpt')
        act = obj.get_report_action(UVM_ERROR, id="")
        self.assertEqual(act, UVM_DISPLAY | UVM_COUNT)
        act = obj.get_report_action(UVM_INFO, id="")
        self.assertEqual(act, UVM_DISPLAY)

        obj.set_report_severity_action(UVM_ERROR, UVM_LOG)
        act = obj.get_report_action(UVM_ERROR, id="")
        self.assertEqual(act, UVM_LOG)



if __name__ == '__main__':
    unittest.main()
