import unittest

from uvm.base.uvm_coreservice import UVMCoreService


class TestUVMCoreService(unittest.TestCase):

    def test_name(self):
        cs = UVMCoreService()
        root = cs.get_root()
        self.assertEqual(root.get_full_name(), "__top__")


if __name__ == '__main__':
    unittest.main()
