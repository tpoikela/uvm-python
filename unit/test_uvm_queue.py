import unittest

from uvm.base.uvm_queue import UVMQueue


class TestUVMQueue(unittest.TestCase):

    def test_size(self):
        q = UVMQueue("q")
        self.assertEqual(q.size(), 0)
        q.push_back(1234)
        self.assertEqual(q.size(), 1)

    def test_insert_delete(self):
        q = UVMQueue("q")
        q.insert(1, 123)
        q.push_back(1)
        q.push_back(2)
        q.insert(1, 123)
        val = q.pop_back()
        val = q.pop_back()
        self.assertEqual(val, 123)

    def test_push_pop(self):
        q = UVMQueue("q")
        q.push_back("b1")
        q.push_front("f1")
        self.assertEqual(q.size(), 2)
        q.insert(1, "i1")
        self.assertEqual(q.size(), 3)
        self.assertEqual(q.pop_front(), 'f1')
        self.assertEqual(q.size(), 2)
        self.assertEqual(q.pop_back(), 'b1')
        self.assertEqual(q.size(), 1)

    def test_conv_string(self):
        q = UVMQueue("q")
        q.push_back("b1")
        qs = q.convert2string()
        self.assertRegex(qs, 'b1')

    def test_find_func(self):
        q = UVMQueue('master')

        def my_func(elem):
            return True
        qq = q.find_with(my_func)
        self.assertEqual(qq.size(), 0)
        q.push_back(1234)
        qq = q.find_with(my_func)
        self.assertEqual(qq.size(), 1)

        aa = {'a': 1, 'b': 3}
        bb = {'a': 5, 'b': 8}
        q_obj = UVMQueue()
        q_obj.push_back(aa)
        q_obj.push_back(bb)

        def find_func1(obj):
            return obj['a'] == 5
        idx = q_obj.find_first_index(find_func1)
        self.assertEqual(idx, 1)

    def test_for_loop(self):
        q = UVMQueue('loop_queue')
        for i in q:
            self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
