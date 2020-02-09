

import unittest

from uvm.reg.uvm_reg_field import UVMRegField
from uvm.reg.uvm_reg import UVMReg


class TestUVMRegField(unittest.TestCase):

    def create_field(self, name, reg):
        field = UVMRegField(name)
        field.configure(parent=reg, size=16, lsb_pos=0, access='RW',
            volatile=False, reset=0xABCD, has_reset=True, is_rand=False,
            individually_accessible=False)
        return field

    def test_configure(self):
        reg = UVMReg('my_reg', 16, False)
        field = self.create_field('f1', reg)
        self.assertEqual(field.get_reset(), 0xABCD)

    def test_string_conv(self):
        reg = UVMReg('r0_test', 16, False)
        field = self.create_field('f1', reg)
        ss = field.convert2string()
        self.assertRegex(ss, r'\[15:0\]={}'.format(16))

    def test_XupdateX(self):
        reg = UVMReg('update_reg', 16, False)
        field = self.create_field('field2', reg)
        field.set_access("RW")
        field.set(0x2345)
        value = field.XupdateX()
        self.assertEqual(value, 0x2345)
        # Clear on write
        field.set_access("WC")
        field.set(0x5555)
        value = field.XupdateX()
        self.assertEqual(value, 0x0)
        # Set on Write
        field.set_access("WS")
        field.set(0x5555)
        value = field.XupdateX()
        self.assertEqual(value, 0xFFFF)


if __name__ == '__main__':
    unittest.main()
