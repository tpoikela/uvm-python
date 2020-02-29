
# UNIT TESTS

import unittest
from uvm.base.uvm_root import UVMRoot


class TestUVMRoot(unittest.TestCase):

    def test_name(self):
        root = UVMRoot()
        self.assertEqual(root.get_name(), "")

    def test_singleton(self):
        root1 = UVMRoot.m_uvm_get_root()
        root2 = UVMRoot.m_uvm_get_root()
        self.assertEqual(root1, root2)

    async def test_run_phase(self):
        root = UVMRoot()
        await root.run_phase()


if __name__ == '__main__':
    unittest.main()
