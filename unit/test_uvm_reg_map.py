
import unittest
from uvm.reg import (UVMRegMap, UVMRegBlock, UVMReg)


class TestUVMRegMap(unittest.TestCase):


    def test_map_base(self):
        reg_map = UVMRegMap()
        reg_blk = UVMRegBlock('my_blk')
        reg_map.configure(reg_blk, base_addr=0, n_bytes=32, endian=0,
                byte_addressing=1)
        reg_blk.add_map(reg_map)
        r1 = UVMReg('r1', 32, False)
        r1.configure(reg_blk)
        reg_map.add_reg(r1, 4)
        reg_blk.lock_model()
        self.assertEqual(r1.get_offset(), 4)
        r1.set_offset(reg_map, 16)
        self.assertEqual(r1.get_offset(), 16)

    def test_add_parent_map(self):
        pass
