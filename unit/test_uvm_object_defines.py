
import unittest

from uvm.macros import uvm_component_utils, uvm_object_utils
from uvm.base.uvm_debug import UVMDebug
from uvm.base.uvm_object import UVMObject

class TestUVMObjectDefines(unittest.TestCase):

    def test_comp_utils(self):
        # Class for testing
        class Dummy:
            def __init__(self, name, parent):
                self.name = name
                self.parent = parent
        uvm_component_utils(Dummy)
        self.assertEqual(Dummy.type_name, 'Dummy')
        print('Dummy.type_name: ' + Dummy.type_name)
        obj = Dummy.type_id.create('comp', None)
        self.assertEqual(obj.get_type_name(), 'Dummy')
        #dum = Dummy()
        #tname = dum.get_type_name()
        #self.assertEqual(tname, 'Dummy')

    def test_object_utils(self):
        class Obj(UVMObject):
            def __init__(self, name):
                UVMObject.__init__(self, name)
                self.misc = 'misc field'
        self.assertEqual(hasattr(Obj, 'type_name'), False)
        uvm_object_utils(Obj)
        self.assertEqual(Obj.type_name, 'Obj')

        o = Obj("my_obj")
        type_obj = o.get_type()
        self.assertEqual(type_obj is not None, True)

if __name__ == '__main__':
    unittest.main()
