
import unittest

from uvm.tlm1 import UVMSeqItemPullExport


class TestUVMSeqItemPullExport(unittest.TestCase):

    def test_new(self):
        pull_exp = UVMSeqItemPullExport('pull_export', None)
        self.assertEqual(pull_exp.get_name(), 'pull_export')


if __name__ == '__main__':
    unittest.main()
