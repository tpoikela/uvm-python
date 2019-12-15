
import unittest
from ..base.uvm_registry import *


def uvm_object_utils(T):
    Ts = T.__name__
    m_uvm_object_registry_internal(T,Ts)
    m_uvm_object_create_func(T, Ts)
    m_uvm_get_type_name_func(T, Ts)


def uvm_component_utils(T):
    #if not __name__ in T:
    #    raise Exception("No __name__ found in {}".format(T))
    Ts = T.__name__
    m_uvm_component_registry_internal(T, Ts)
    m_uvm_get_type_name_func(T, Ts)


def m_uvm_get_type_name_func(T, Ts):
    setattr(T, 'type_name', Ts)

    def get_type_name(self):
        return Ts
    setattr(T, 'get_type_name', get_type_name)


def m_uvm_component_registry_internal(T,S):
    setattr(T, 'type_id', UVMComponentRegistry(T, S))

    def type_id():
        return T.type_id

    def get_type():
        return T.type_id.get(S)

    def get_object_type():
        return T.type_id.get(S)


def m_uvm_object_registry_internal(T,S):
    setattr(T, 'type_id', UVMObjectRegistry(T, S))

    def type_id():
        return T.type_id

    def get_type():
        return T.type_id.get(S)

    def get_object_type():
        return T.type_id.get(S)


def m_uvm_object_create_func(T,S):
    # pass
    def create(self, name=""):
        return T(name)
    setattr(T, 'create', create)


class TestUVMGlobals(unittest.TestCase):

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
        self.assertEqual(Obj.type_name, None)
        class Obj(UVMObject):
            def __init__(self, name):
                UVMObject.__init__(name)
                self.misc = 'misc field'
        uvm_object_utils(UVMObject)
        self.assertEqual(Obj.type_name, 'Obj')

if __name__ == '__main__':
    unittest.main()
