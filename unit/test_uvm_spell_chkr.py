
import unittest

from uvm.base.uvm_spell_chkr import UVMSpellChkr


class TestUVMSpellChkr(unittest.TestCase):

    def test_check_exact_match(self):
        strtab = {'xxx': 1, 'yyy': 2}
        self.assertTrue(UVMSpellChkr.check(strtab, 'xxx'))
        self.assertFalse(UVMSpellChkr.check(strtab, 'vvv'))


if __name__ == '__main__':
    unittest.main()
