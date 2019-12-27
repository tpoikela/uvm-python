
import unittest
from uvm.base import (UVMComponent)

#------------------------------------------------------------------------------
# UNIT TESTS
#------------------------------------------------------------------------------


class TestUVMComponent(unittest.TestCase):

    def test_name(self):
        from uvm.base.uvm_root import UVMRoot
        uvm_top = UVMRoot.get()
        comp = UVMComponent("my_component", uvm_top)
        self.assertEqual(comp.get_full_name(), "my_component")
        comp_child = UVMComponent("my_child", comp)
        self.assertEqual(comp_child.get_full_name(), "my_component.my_child")

    def test_children(self):
        comp = UVMComponent("parent", None)
        child = UVMComponent("child", comp)
        self.assertEqual(child.get_parent(), comp)
        self.assertEqual(comp.get_first_child(), child)
        self.assertEqual(comp.get_num_children(), 1)
        self.assertEqual(comp.get_child("child"), child)
        self.assertEqual(comp.has_child("child"), True)
        self.assertEqual(comp.has_child("xchild"), False)
        children = []
        comp.get_children(children)
        self.assertEqual(children[0], child)

    def test_lookup(self):
        comp = UVMComponent("parent", None)
        child = UVMComponent("child", comp)
        sub_child = UVMComponent("sub_child", child)

        c1 = comp.lookup('child')
        sc = comp.lookup('child.sub_child')
        self.assertEqual(c1, child)
        self.assertEqual(sub_child, sc)



if __name__ == '__main__':
    unittest.main()
