
import unittest

from uvm.base.uvm_registry import UVMComponentRegistry, UVMObjectRegistry
from uvm.macros.uvm_object_defines import uvm_component_utils, uvm_object_utils


class TestUVMRegistry(unittest.TestCase):


    def test_object_registry(self):
        class ABC:
            def __init__(self, name):
                self.name = name
                self.value = 5
        uvm_object_utils(ABC)
        reg = UVMObjectRegistry(ABC, 'ABC')
        abc_obj = reg.create('obj_name')
        self.assertEqual(abc_obj.name, 'obj_name')
        self.assertEqual(isinstance(abc_obj, ABC), True)


    def test_component_registry(self):
        class ABC:
            def __init__(self, name, parent):
                self.name = name
                self.parent = parent
        uvm_component_utils(ABC)
        reg = UVMComponentRegistry(ABC, 'ABC')
        abc_comp = reg.create('inst_name', None)
        self.assertEqual(abc_comp.name, 'inst_name')
        self.assertEqual(abc_comp.parent, None)


if __name__ == '__main__':
    unittest.main()
