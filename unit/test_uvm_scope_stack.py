
import unittest

from uvm.base.uvm_scope_stack import UVMScopeStack


class TestUVMScopeStack(unittest.TestCase):

    def test_depth(self):
        stack = UVMScopeStack()
        self.assertEqual(stack.depth(), 0)

    def test_down_and_up(self):
        stack = UVMScopeStack()
        stack.down('xxx')
        stack.down('yyy')
        stack.down('zzz')
        self.assertEqual(stack.get(), 'xxx.yyy.zzz')
        self.assertEqual(stack.depth(), 3)
        stack.up()
        self.assertEqual(stack.get(), 'xxx.yyy')

    def test_down_and_up_element(self):
        stack = UVMScopeStack()
        stack.down('uvm_top')
        stack.down_element(4)
        self.assertEqual(stack.get(), 'uvm_top[4]')
        self.assertEqual(stack.depth(), 2)
        stack.up_element()
        self.assertEqual(stack.get(), 'uvm_top')


if __name__ == '__main__':
    unittest.main()
