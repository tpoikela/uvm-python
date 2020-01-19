
import unittest
from uvm.reg.uvm_reg_model import *


class TestUVMRegModel(unittest.TestCase):


    def test_concat2string(self):
        concat = uvm_hdl_path_concat()
        path_sli = uvm_hdl_path_slice()
        path_sli.path = "dut"
        concat.add_path(path_sli.path)
        str_path = uvm_hdl_concat2string(concat)
        self.assertEqual(str_path, "dut")
        concat.add_path("test_reg")
        str_path = uvm_hdl_concat2string(concat)
        self.assertEqual(str_path, "{dut, test_reg}")


if __name__ == '__main__':
    unittest.main()
