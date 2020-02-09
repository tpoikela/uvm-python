
import unittest

from uvm.base.uvm_domain import UVMDomain
from uvm.base.uvm_common_phases import UVMBuildPhase
from uvm.base.uvm_phase import UVMPhase


class TestUVMDomain(unittest.TestCase):


    def test_common(self):
        common = UVMDomain.get_common_domain()
        self.assertNotEqual(common, None)
        bld = common.find(UVMBuildPhase.get())
        self.assertNotEqual(bld, None)


    def test_add_and_find(self):
        my_ph = UVMPhase('my_ph')
        dm = UVMDomain('my domain')
        dm.add(my_ph)
        my_ph2 = dm.find(my_ph)
        self.assertNotEqual(my_ph2, None)
        self.assertEqual(my_ph2.get_name(), 'my_ph')


if __name__ == '__main__':
    unittest.main()
