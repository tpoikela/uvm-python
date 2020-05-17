import unittest

from uvm.base.uvm_object import UVMObject
from uvm.base.uvm_factory import (
    UVMFactory, UVMDefaultFactory)
from uvm.comps.uvm_test import UVMTest
#from uvm.macros.uvm_factory import UVMFactory, UVMDefaultFactory
from uvm.macros import uvm_component_utils, uvm_object_utils
from uvm.base.uvm_coreservice import UVMCoreService


def createXXX():
    class XXX(UVMObject):
        pass
    uvm_object_utils(XXX)
    return XXX


def createYYY():
    class YYY(UVMObject):
        pass
    uvm_object_utils(YYY)
    return  YYY

def createLastOverride():
    class LastOverride(UVMObject):
        pass
    uvm_object_utils(LastOverride)
    return LastOverride


class TestUVMDefaultFactory(unittest.TestCase):

    def test_override(self):
        cs = UVMCoreService.get()
        fact = UVMDefaultFactory()
        cs.set_factory(fact)
        XXX = createXXX()
        YYY = createYYY()

        fact.set_type_override_by_name('XXX', 'YYY')
        ovrd = fact.find_override_by_type(requested_type=XXX.get_type(), full_inst_path='')
        self.assertIsNotNone(ovrd, 'Override XXX->YYY should exist')
        self.assertEqual(ovrd.get_type_name(), 'YYY')
        fact.debug_create_by_name('XXX')
        #fact.debug_create_by_type(XXX.get_type())


    def test_type_double_override(self):
        cs = UVMCoreService.get()
        fact = UVMDefaultFactory()
        cs.set_factory(fact)

        XXX = createXXX()
        YYY = createYYY()
        LastOverride = createLastOverride()

        fact.set_type_override_by_name('XXX', 'YYY')
        fact.set_type_override_by_name('XXX', 'LastOverride')
        self.assertFalse(fact.check_inst_override_exists(XXX.get_type(),
            LastOverride.get_type(), ''))
        ovrd = fact.find_override_by_type(requested_type=XXX.get_type(), full_inst_path='')
        self.assertIsNotNone(ovrd, 'Override XXX->LastOverride should exist')
        self.assertEqual(ovrd.get_type_name(), 'LastOverride')

        fact.set_type_override_by_name('YYY', 'LastOverride')
        ovrd = fact.find_override_by_type(requested_type=YYY.get_type(), full_inst_path='')
        self.assertIsNotNone(ovrd, 'Override YYY->LastOverride should exist')
        self.assertEqual(ovrd.get_type_name(), 'LastOverride')


    def test_inst_override(self):
        cs = UVMCoreService.get()
        fact = UVMDefaultFactory()
        cs.set_factory(fact)

        XXX = createXXX()
        LastOverride = createLastOverride()

        fact.set_inst_override_by_type(XXX.get_type(), LastOverride.get_type(),
                'top.my_inst.is_override')
        self.assertTrue(fact.check_inst_override_exists(XXX.get_type(),
            LastOverride.get_type(), 'top.my_inst.is_override'))
        self.assertFalse(fact.check_inst_override_exists(XXX.get_type(),
            LastOverride.get_type(), 'top.my_inst2'))

        obj = fact.create_object_by_type(XXX.get_type(), 'top.my_inst', 'is_override')
        obj2 = fact.create_object_by_type(XXX.get_type(), 'top.my_inst2', 'is_xxx')
        self.assertEqual(obj.get_name(), 'is_override')
        self.assertEqual(obj.get_type_name(), 'LastOverride')
        self.assertEqual(obj2.get_name(), 'is_xxx')
        self.assertEqual(obj2.get_type_name(), 'XXX')

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


    def test_register(self):
        fact = UVMDefaultFactory()
        class NotWorks(UVMObject):
            type_name = "xxx"

        obj = NotWorks('my_name')
        fact.register(obj)


if __name__ == '__main__':
    unittest.main()
