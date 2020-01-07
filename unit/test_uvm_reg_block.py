
import unittest
from uvm.reg.uvm_reg import UVMReg
from uvm.reg.uvm_reg_block import UVMRegBlock
from uvm.reg.uvm_reg_model import *


class TestUVMRegBlock(unittest.TestCase):

    def test_add_reg(self):
        rb = UVMRegBlock("rb_blk")
        rb.create_map("", 0, 1, UVM_BIG_ENDIAN)
        reg1 = UVMReg("xx", 32, rb.get_full_name())
        reg1.configure(rb, None, "acp")
        # reg1.build()
        rb.default_map.add_reg(reg1, 0x0000, "RW")
        print("len is now " + str(len(rb.regs)))
        rr = rb.get_reg_by_name('xx')
        self.assertEqual(rr.get_name(), 'xx')

        r_none = rb.get_reg_by_name('y_reg')
        self.assertEqual(r_none, None)

    def test_add_block(self):
        top_b = UVMRegBlock("top_reg_block")
        top_b.create_map("custom_map", 0x100, 4, UVM_LITTLE_ENDIAN)
        custom_map = top_b.get_map_by_name("custom_map")
        top_b.set_default_map(custom_map)
        self.assertIsNotNone(custom_map)
        for i in range(10):
            base_addr = i * 0x100
            sub_b = UVMRegBlock("sub_blk_" + str(i))
            top_b.add_block(sub_b)
        top_b.configure(parent=None, hdl_path="")
        top_b.lock_model()


if __name__ == '__main__':
    unittest.main()
