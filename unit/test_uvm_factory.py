import unittest

from uvm.base.uvm_object import UVMObject
from uvm.base.uvm_factory import (
    UVMFactory, UVMDefaultFactory)
from uvm.comps.uvm_test import UVMTest
#from uvm.macros.uvm_factory import UVMFactory, UVMDefaultFactory
from uvm.macros import uvm_component_utils, uvm_object_utils
from uvm.base.uvm_coreservice import UVMCoreService


class TestUVMDefaultFactory(unittest.TestCase):

    def test_override(self):
        cs = UVMCoreService.get()
        fact = UVMDefaultFactory()
        cs.set_factory(fact)

        class XXX(UVMObject):
            pass
        uvm_object_utils(XXX)

        class YYY(UVMObject):
            pass
        uvm_object_utils(YYY)

        fact.set_type_override_by_name('XXX', 'YYY')
        ovrd = fact.find_override_by_type(requested_type=XXX.get_type(), full_inst_path='')
        self.assertIsNotNone(ovrd, 'Override XXX->YYY should exist')
        self.assertEqual(ovrd.get_type_name(), 'YYY')


    def test_create_component_by_name(self):
        cs = UVMCoreService.get()
        factory = UVMFactory.get()
        cs.set_factory(factory)

        class MyTest123(UVMTest):
            def __init__(self, name, parent):
                UVMTest.__init__(self, name, parent)

        uvm_component_utils(MyTest123)
        test_name = 'MyTest123'
        uvm_test_top = factory.create_component_by_name(test_name,
            "", "uvm_test_top", None)
        self.assertEqual(uvm_test_top.get_full_name(), "uvm_test_top")


    def test_create_object_by_name(self):
        factory = UVMFactory.get()

        class MyObj(UVMObject):
            def __init__(self, name):
                UVMObject.__init__(self, name)

        uvm_object_utils(MyObj)

        new_obj = factory.create_object_by_name('MyObj', "", "my_obj_name")
        self.assertEqual(new_obj.get_name(), 'my_obj_name')


if __name__ == '__main__':
    unittest.main()
