
import unittest

from uvm.base.uvm_object import UVMObject
from uvm.macros.uvm_object_defines import *
from uvm.base.uvm_object_globals import *


class TestObj(UVMObject):

    def __init__(self, name):
        super().__init__(name)
        self.addr = 0
        self.data = 10

uvm_object_utils_begin(TestObj)
uvm_field_int("addr")
uvm_field_int("data", UVM_COMPARE)
uvm_object_utils_end(TestObj)


class TestUVMObject(unittest.TestCase):

    def test_name(self):
        comp = UVMObject("my_component")
        self.assertEqual(comp.get_name(), "my_component")

    def test_inst_count(self):
        UVMObject.inst_id_count = 0
        comp = UVMObject("my_component")
        self.assertEqual(comp.get_inst_count(), 1)

    def test_object_utils(self):
        o1 = TestObj("o1")
        o1.addr = 10
        o2 = o1.clone()
        self.assertEqual(o2.addr, 10)
        o1.data = 20
        o3 = o1.clone()
        self.assertFalse(o1.compare(o3))


if __name__ == '__main__':
    unittest.main()
