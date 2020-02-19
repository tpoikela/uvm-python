

import unittest

from uvm.reg.uvm_reg_field import UVMRegField, NO_RAND_SET
from uvm.reg.uvm_reg import UVMReg
from uvm.reg.uvm_reg_model import (UVM_READ, UVM_WRITE, UVM_PREDICT_WRITE,
    UVM_PREDICT_READ)


class TestUVMRegField(unittest.TestCase):

    def create_field(self, name, reg, acc='RW'):
        field = UVMRegField(name)
        field.configure(parent=reg, size=16, lsb_pos=0, access=acc,
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

    def test_set_get(self):
        for mode in NO_RAND_SET:
            reg = UVMReg('my_reg', 16, False)
            field = self.create_field('field_' + mode, reg, acc=mode)
            field.reset()
            access = field.get_access()
            field.set(0x1234)
            val = field.get()
            msg = 'Access ' + access + ' OK'
            predict_msg = 'Predict for ' + access + ' OK'
            if access in ['RW', 'WRS', 'WRC']:
                self.assertEqual(val, 0x1234, msg)
                self.assertTrue(field.predict(0x1234, -1, UVM_PREDICT_WRITE), predict_msg)
            elif access in ['RO', 'RC', 'RS']:
                self.assertEqual(val, field.get_reset(), msg)
                self.assertTrue(field.predict(field.get_reset(), -1, UVM_PREDICT_READ), predict_msg)
            else:
                self.assertTrue(field.predict(0x12), predict_msg)
                val = field.get()
                self.assertEqual(val, 0x12, 'Val OK after predict with ' + access)


if __name__ == '__main__':
    unittest.main()
