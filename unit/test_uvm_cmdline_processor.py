
import unittest

from uvm.base.uvm_cmdline_processor import UVMCmdlineProcessor
from uvm.base.uvm_debug import UVMDebug

UVMDebug.DEBUG = False

class TestUVMCmdLineProc(unittest.TestCase):
    """ Unit tests for UVMCmdLineProcessor"""

    def test_get_arg(self):
        UVMCmdlineProcessor.m_test_mode = False
        #UVMCmdlineProcessor.m_test_plusargs = {"ABC": "123"}
        argv = ["+ABC=123"]
        clp = UVMCmdlineProcessor()
        clp.extract_args(argv)
        arr = []
        count = clp.get_arg_values("+MY_TEST", arr)
        self.assertEqual(count, 0)
        count = clp.get_arg_values("+ABC=", arr)
        self.assertEqual(count, 1)
        self.assertEqual(arr[0], "123")
        UVMCmdlineProcessor.m_test_mode = False

    def test_get_arg_matches(self):
        UVMCmdlineProcessor.m_test_mode = False
        plusargs = {"ABC": "123", "WW": "XX", "TRACE": "123"}
        argv = []
        for i, (key,val) in enumerate(plusargs.items()):
            argv.append("+" + key + "=" + str(val))
        #UVMDebug.DEBUG = True
        clp = UVMCmdlineProcessor()
        clp.extract_args(argv)
        args = []
        num = clp.get_arg_matches("XYZ", args)
        self.assertEqual(num, 0)
        num = clp.get_arg_matches("+TRACE=", args)
        self.assertEqual(num, 1)
        num = clp.get_arg_matches("+TRACE", args)
        self.assertEqual(num, 1)
        UVMCmdlineProcessor.m_test_mode = False

    def test_multiple_args(self):
        UVMCmdlineProcessor.m_test_mode = False
        UVMCmdlineProcessor.m_test_plusargs = {}
        argv = ["+ABC=123", "+ABC=567"]
        UVMCmdlineProcessor.m_test_argv = argv
        clp = UVMCmdlineProcessor()
        clp.extract_args(argv)
        args = []
        num = clp.get_arg_matches("+ABC=", args)
        self.assertEqual(num, 2)
        print('2 matches are' + str(args))

    def test_regex_in_arg_matches(self):
        UVMCmdlineProcessor.m_test_mode = False
        plusargs = {"ABC": "123", "WW": "XX", "TRACE": "123", "COMPLEX_MATCH": "555"}
        argv = []
        for i, (key,val) in enumerate(plusargs.items()):
            argv.append("+" + key + "=" + str(val))
        clp = UVMCmdlineProcessor()
        clp.extract_args(argv)
        args = []
        num = clp.get_arg_matches("/^XYZ$/", args)
        self.assertEqual(num, 0)

        args = []
        num = clp.get_arg_matches("/^\\+COMPLEX_MATCH=$/", args)
        self.assertEqual(num, 1)
        UVMCmdlineProcessor.m_test_mode = False




if __name__ == '__main__':
    unittest.main()
