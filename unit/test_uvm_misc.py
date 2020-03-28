
import unittest
from uvm.base.uvm_object_globals import (
    UVM_DEC, UVM_BIN, UVM_HEX, UVM_OCT)
from uvm.base.uvm_misc import (
    uvm_leaf_scope,
    uvm_bitstream_to_string)


class TestUVMMisc(unittest.TestCase):

    def test_uvm_leaf_scope(self):
        scope = uvm_leaf_scope("[ab]", "[")
        self.assertEqual(scope, "ab")
        scope = uvm_leaf_scope("[xx][ee][ab][cd]", "[")
        self.assertEqual(scope, "cd")
        #scope = uvm_leaf_scope("ab")
        scope = uvm_leaf_scope("a.b.leaf")
        self.assertEqual(scope, "leaf")
        scope = uvm_leaf_scope("leaf")
        self.assertEqual(scope, "leaf")
        #scope = uvm_leaf_scope("a#b#leaf", "#")
        #self.assertEqual(scope, "leaf")

    def test_uvm_bitstream_to_string(self):
        radix = [UVM_DEC, UVM_BIN, UVM_HEX, UVM_OCT]
        for rr in radix:
            num_str = uvm_bitstream_to_string(255, 8, rr)
            if rr == UVM_DEC:
                self.assertEqual(num_str, "{}".format(255))
            elif rr == UVM_HEX:
                self.assertEqual(num_str, "{:X}".format(255))
            elif rr == UVM_BIN:
                self.assertEqual(num_str, "{:b}".format(255))

        num_str = uvm_bitstream_to_string(-245, 8, UVM_DEC)
        self.assertEqual(num_str, "-245")


if __name__ == '__main__':
    unittest.main()
