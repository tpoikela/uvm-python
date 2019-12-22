
import unittest

from uvm.base.uvm_cmdline_processor import UVMCmdlineProcessor


class TestUVMCmdLineProc(unittest.TestCase):

    def test_get_arg(self):
        clp = UVMCmdlineProcessor()
        arr = []
        count = clp.get_arg_values("+MY_TEST", arr)
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()
