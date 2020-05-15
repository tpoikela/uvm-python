
import unittest
from uvm.base import (UVMComponent, UVM_LOW, UVM_HIGH)
from uvm.base.uvm_cmdline_processor import UVMCmdlineProcessor

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
        comp = UVMComponent("parent1", None)
        child = UVMComponent("child", comp)
        sub_child = UVMComponent("sub_child", child)

        c1 = comp.lookup('child')
        sc = comp.lookup('child.sub_child')
        self.assertEqual(c1, child)
        self.assertEqual(sub_child, sc)

    def test_errors(self):
        comp = UVMComponent("parent12345", None)
        child = comp.get_first_child()
        self.assertIsNone(child)
        child = comp.get_next_child()
        self.assertIsNone(child)

    #def test_clp_args(self):
    #    # "+uvm_set_verbosity=<comp>,<id>,<verbosity>,<phase|time>,<offset>"
    #    UVMCmdlineProcessor.m_test_mode = True
    #    UVMCmdlineProcessor.m_test_plusargs = {
    #        "uvm_set_verbosity": "*child1,_ALL_,UVM_LOW,,0",
    #        "uvm_set_verbosity": "parent1,_ALL_,UVM_HIGH,,0",
    #        "ABC": "123"
    #    }
    #    comp = UVMComponent("parent2", None)
    #    child = UVMComponent("child1", comp)
    #    child2 = UVMComponent("child2", comp)
    #    self.assertEqual(child.get_report_verbosity_level(), UVM_LOW)
    #    self.assertEqual(comp.get_report_verbosity_level(), UVM_HIGH)

    #    UVMCmdlineProcessor.m_test_mode = False


if __name__ == '__main__':
    unittest.main()
