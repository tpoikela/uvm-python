
import unittest
from uvm.base.uvm_phase import UVMPhase


class TestUVMPhase(unittest.TestCase):

    def test_find(self):
        ph = UVMPhase()
        pred_ph = ph.find(ph)
        self.assertEqual(ph, pred_ph)
        ph1 = UVMPhase('unrelated')
        no_ph = ph.find(ph1)
        self.assertEqual(no_ph, None)


if __name__ == '__main__':
    unittest.main()
