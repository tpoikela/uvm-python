
import unittest
from uvm.seq.uvm_sequencer_base import UVMSequencerBase

from uvm.uvm_unit import MockObj

class MockSeq(MockObj):

    def __init__(self, name='mock_seq', parent=None):
        super().__init__(name, parent)
        self.parent = parent

    def get_parent_sequence(self):
        return self.parent


class TestUVMReg(unittest.TestCase):

    def test_init(self):
        sqr = UVMSequencerBase('new_sqr_123', None)
        self.assertFalse(sqr.is_grabbed())
        seq1 = MockSeq('seq1')
        seq2 = MockSeq('seq2')
        self.assertFalse(sqr.is_child(seq1, seq2))
        par_seq3 = MockSeq('par_seq3')
        seq4 = MockSeq('seq2', par_seq3)
        self.assertTrue(sqr.is_child(par_seq3, seq4))


if __name__ == '__main__':
    unittest.main()
