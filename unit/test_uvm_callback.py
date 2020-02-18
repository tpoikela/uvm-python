
import unittest

from uvm.base.uvm_callback import (UVMCallback, UVMCallbacks,
    UVMCallbackIter, UVMTypedCallbacks, UVMCallbacksBase)

from uvm.base.uvm_component import UVMComponent

from uvm.uvm_unit import MockObj, MockCb
from uvm.macros import (uvm_register_cb, uvm_do_callbacks)

UVMCallbacksBase.m_tracing = True


class TestUVMCallback(unittest.TestCase):

    def test_typed_callbacks(self):
        typed_cb = UVMTypedCallbacks.m_initialize()
        self.assertEqual(isinstance(typed_cb, UVMTypedCallbacks), True)
        typed_cb2 = UVMTypedCallbacks.m_initialize()
        self.assertEqual(typed_cb, typed_cb2)

    def test_callback_mode(self):
        cb = UVMCallback('my_cb')
        cb.callback_mode(1)
        self.assertEqual(cb.is_enabled(), True)

    def test_type_name(self):
        cb = UVMCallback('my_cb')
        self.assertEqual(cb.get_type_name(), 'uvm_callback')

    def test_callback_iter(self):
        obj = MockObj("parent", None)
        my_iter = UVMCallbackIter(obj)
        cb = my_iter.first()
        self.assertEqual(cb, None)
        cb = my_iter.last()
        self.assertEqual(cb, None)
        cb_obj = MockCb("cb_obj")
        UVMCallbacks.add(obj, cb_obj)
        cb = my_iter.first()
        self.assertEqual(cb, cb_obj)
        cb = my_iter.last()
        self.assertEqual(cb, cb_obj)

    def test_uvm_callbacks(self):
        parent_obj = MockObj("parent", None)
        cb_obj = MockCb("cb_obj")
        my_iter = UVMCallbackIter(parent_obj)
        UVMCallbacks.add(parent_obj, cb_obj)

        cb = UVMCallbacks.get_first(my_iter, parent_obj)
        self.assertEqual(cb, cb_obj)

        cb2 = my_iter.first()
        self.assertEqual(cb2, cb_obj)

        class MyCallback(UVMCallback):
            def get_name(self):
                return "my_cb"
            def do_it(self):
                self.called = True
            def get_type_name(self):
                return "MyCallback"

        class MyCallbackWrong(UVMCallback):
            def do_it(self):
                raise Exception('Dont call this')
            def get_type_name(self):
                return "MyCallbackWrong"

        class MyClass(UVMComponent):
            def do_it(self):
                uvm_do_callbacks(self, MyCallback, 'do_it')
        uvm_register_cb(MyClass, MyCallback)
        uvm_register_cb(MyClass, MyCallbackWrong)

        my_class = MyClass('my_class_obj', None)
        my_cb = MyCallback()
        UVMCallbacks.add(my_class, my_cb)
        UVMCallbacks.add(my_class, MyCallbackWrong())
        my_class.do_it()
        self.assertTrue(my_cb.called)




if __name__ == '__main__':
    unittest.main()
