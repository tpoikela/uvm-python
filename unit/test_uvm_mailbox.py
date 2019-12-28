
import unittest
from uvm.base.uvm_mailbox import UVMMailbox


class TestUVMMailbox(unittest.TestCase):

    def test_try_put(self):
        fifo = UVMMailbox(2)
        self.assertEqual(fifo.can_put(), True)
        self.assertEqual(fifo.can_get(), False)

    def test_try_get(self):
        fifo = UVMMailbox(2)
        self.assertEqual(fifo.can_get(), False)
        itemq = []
        self.assertEqual(fifo.try_get(itemq), False)
        self.assertEqual(fifo.try_put(234), True)
        self.assertEqual(fifo.try_get(itemq), True)
        self.assertEqual(len(itemq), 1)
        self.assertEqual(itemq[0], 234)

    def test_unbounded(self):
        fifo = UVMMailbox()
        self.assertEqual(fifo.can_put(), True)
        for i in range(0, 10):
            self.assertEqual(fifo.try_put(i), True)
            arr = []
            self.assertEqual(fifo.try_peek(arr), True)
            self.assertEqual(arr[0], 0)

        for i in range(0, 10):
            arr = []
            self.assertEqual(fifo.try_get(arr), True)
            self.assertEqual(arr[0], i)



if __name__ == '__main__':
    unittest.main()
