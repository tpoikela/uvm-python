
import unittest
from uvm.reg.uvm_reg import UVMReg
from uvm.reg.uvm_reg_field import UVMRegField
from uvm.uvm_unit import create_reg_map


class TestUVMReg(unittest.TestCase):

    def setUp(self):
        pass

    def create_reg(self, name='reg', nbits=32):
        reg = UVMReg(name, nbits, False)
        for i in range(0, nbits):
            f1 = UVMRegField('my_field_' + str(i))
            f1.configure(reg, 1, i, 'RW', volatile=False, reset=i % 2, has_reset=True,
                    is_rand=False, individually_accessible=True)
        return reg

    def test_add_field(self):
        UVMRegField.define_access('RW')
        reg = UVMReg('my_reg', 32, False)
        f1 = UVMRegField('my_field_1')
        f1.configure(reg, 16, 0, 'RW', volatile=False, reset=0, has_reset=True,
                is_rand=False, individually_accessible=True)
        arr = []
        reg.get_fields(arr)
        print(str(reg.m_fields))
        self.assertEqual(len(arr), 1)

    def test_base_ops(self):
        UVMRegField.define_access('RW')
        reg32 = self.create_reg('reg_32', 32)
        arr = []
        reg32.get_fields(arr)
        self.assertEqual(len(arr), 32)
        self.assertEqual(reg32.predict(0), True)
        # Why does not fail self.assertEqual(reg32.predict(1234), False)
        self.assertEqual(reg32.get(), 0)
        reg32.set(0x12345678)
        val = reg32.get()
        self.assertEqual(val, 0x12345678)

    def test_reg_randomize(self):
        class RandReg(UVMReg):
            def __init__(self, name):
                super().__init__(name, 16)
                self.F1 = UVMRegField('my_field_1')
                self.F1.configure(self, 16, 0, 'RW', volatile=False, reset=0,
                        has_reset=True, is_rand=False, individually_accessible=True)
                self.rand('F1')

        new_reg = RandReg('rng_reg')
        ok = new_reg.randomize()
        self.assertTrue(ok, 'randomize OK')
        self.assertTrue(new_reg.F1.value > 0)

    def test_get_address(self):
        reg = self.create_reg('my_reg', 32)
        reg_map, rb = create_reg_map('test_map')
        reg.configure(rb)
        reg_map.add_reg(reg, 0x8)
        # TODO fix this addr = reg.get_address()
        # self.assertEqual(addr, 0x8)


if __name__ == '__main__':
    unittest.main()
