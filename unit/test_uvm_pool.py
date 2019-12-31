
import unittest
from uvm.base.uvm_pool import UVMPool, UVMEventPool


class TestUVMPool(unittest.TestCase):

    def test_global_pool(self):
        gpool = UVMPool.get_global_pool()
        gpool.add('abc', 879)
        g_val = UVMPool.get_global('abc')
        self.assertEqual(g_val, 879)

    def test_pool(self):
        pool = UVMPool()
        pool.add('xxx', 123)
        self.assertEqual(pool.num(), 1)
        self.assertEqual(pool.get('xxx'), 123)
        first_key = pool.first()
        last_key = pool.last()
        self.assertEqual(first_key, 'xxx')
        self.assertEqual(first_key, last_key)

    def test_pool_iter(self):
        pool = UVMPool()
        pool.add('a', 1)
        pool.add('b', 2)
        pool.add('c', 3)
        self.assertEqual(pool.num(), 3)
        self.assertEqual(pool.has_prev(), False)
        self.assertEqual(pool.has_next(), True)
        self.assertEqual(pool.last(), 'c')
        self.assertEqual(pool.first(), 'a')
        self.assertEqual(pool.last(), 'c')
        self.assertEqual(pool.prev(), 'b')
        self.assertEqual(pool.prev(), 'a')
        self.assertEqual(pool.next(), 'b')
        self.assertEqual(pool.next(), 'c')

    def test_len_and_in(self):
        pool = UVMPool()
        self.assertEqual('xxx' in pool, False)
        self.assertEqual(len(pool), 0)
        pool.add('xxx', 1234)
        self.assertEqual('xxx' in pool, True)
        self.assertEqual(len(pool), 1)
        empty = UVMPool()
        self.assertEqual('xxx' in empty, False)

    def test_while_has_next(self):
        pool = UVMPool()
        pool.add(1, 2)
        pool.add(4, 8)
        pool.add(8, 16)
        while (pool.has_next()):
            val = pool.next()

    def test_for_loop(self):
        pool = UVMPool()
        pool.add("z", 0)
        pool.add("a", 4)
        pool.add("b", 8)
        pool.add("c", 16)
        for key in pool:
            val = pool[key]
            self.assertEqual(val in [0, 4, 8, 16], True)
            self.assertEqual(key in ["z", "a", "b", "c"], True)


class TestUVMEventPool(unittest.TestCase):

    def test_event_pool(self):
        event_pool = UVMEventPool('event_pool')
        evt_start = event_pool.get('start')
        evt_end = event_pool.get('end')
        self.assertEqual(evt_start.get_name(), 'start')
        self.assertEqual(evt_end.get_name(), 'end')
        evt_end2 = event_pool.get('end')
        self.assertEqual(evt_end, evt_end2)
        self.assertNotEqual(evt_end, evt_start)


if __name__ == '__main__':
    unittest.main()
