
import unittest

from uvm.base.uvm_cmdline_processor import UVMCmdlineProcessor
from uvm.base.uvm_debug import UVMDebug


class TestUVMCmdLineProc(unittest.TestCase):
    """ Unit tests for UVMCmdLineProcessor"""

    def test_get_arg(self):
        UVMCmdlineProcessor.m_test_mode = True
        UVMCmdlineProcessor.m_test_plusargs = {"ABC": "123"}
        clp = UVMCmdlineProcessor()
        arr = []
        count = clp.get_arg_values("+MY_TEST", arr)
        self.assertEqual(count, 0)
        count = clp.get_arg_values("+ABC=", arr)
        self.assertEqual(count, 1)
        self.assertEqual(arr[0], "123")
        UVMCmdlineProcessor.m_test_mode = False

    def test_get_arg_matches(self):
        UVMCmdlineProcessor.m_test_mode = True
        UVMCmdlineProcessor.m_test_plusargs = {"ABC": "123", "WW": "XX",
                "TRACE": "123"}
        UVMDebug.DEBUG = True
        clp = UVMCmdlineProcessor()
        args = []
        num = clp.get_arg_matches("XYZ", args)
        self.assertEqual(num, 0)
        num = clp.get_arg_matches("+TRACE=", args)
        self.assertEqual(num, 1)
        num = clp.get_arg_matches("+TRACE", args)
        self.assertEqual(num, 1)
        UVMCmdlineProcessor.m_test_mode = False



if __name__ == '__main__':
    unittest.main()
