
import unittest
from uvm.base.uvm_misc import *


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


if __name__ == '__main__':
    unittest.main()
