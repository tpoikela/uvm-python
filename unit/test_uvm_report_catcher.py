
import unittest
from uvm.base.uvm_report_catcher import UVMReportCatcher


class MyReportCatcher(UVMReportCatcher):

    def __init__(self, name='catcher'):
        super().__init__(name)

    def catch(self):
        self.sev = self.get_severity()
        self._id = self.get_id()


class TestUVMReportCatcher(unittest.TestCase):

    def test_catcher(self):
        rpt_catcher = MyReportCatcher('catcher')


if __name__ == '__main__':
    unittest.main()
