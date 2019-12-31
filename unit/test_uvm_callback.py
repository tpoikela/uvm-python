
import unittest

from uvm.base.uvm_callback import (UVMCallback, UVMCallbacks,
    UVMCallbackIter, UVMTypedCallbacks)

from uvm.base.uvm_unit import MockObj, MockCb


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

    def test_uvm_callbacks(self):
        parent_obj = MockObj("parent", None)
        cb_obj = MockCb("cb_obj")
        my_iter = UVMCallbackIter(parent_obj)
        UVMCallbacks.add(parent_obj, cb_obj)
        # cbs = UVMCallbacks.get()
        #self.assertEqual(cbs.m_inst.m_typeid.typename, 'UVMCallbacks')
        cb = UVMCallbacks.get_first(my_iter, parent_obj)
        self.assertEqual(cb, cb_obj)

        cb2 = my_iter.first()
        self.assertEqual(cb2, cb_obj)


if __name__ == '__main__':
    unittest.main()
