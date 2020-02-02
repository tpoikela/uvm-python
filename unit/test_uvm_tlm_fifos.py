
import unittest
from uvm.tlm1.uvm_tlm_fifos import (UVMTLMAnalysisFIFO, UVMTLMFIFO)


class TestUVMTLMFIFO(unittest.TestCase):

    def test_flush(self):
        fifo = UVMTLMFIFO('tlm_fifo', None)
        fifo.flush()
        self.assertEqual(fifo.used(), 0)
        self.assertTrue(fifo.is_empty())


class TestUVMTLMAnalysisFIFO(unittest.TestCase):

    def test_write_and_get(self):
        fifo = UVMTLMAnalysisFIFO('fifo', None)
        fifo.write(12345)
        arr = []
        self.assertEqual(fifo.try_get(arr), True)
        self.assertEqual(arr[0], 12345)
        self.assertEqual(fifo.can_get(), False)
        self.assertEqual(fifo.try_put('xxx'), True)
        self.assertEqual(fifo.can_get(), True)
        arr = []
        self.assertEqual(fifo.try_get(arr), True)
        self.assertEqual(arr[0], 'xxx')

    def test_try_put(self):
        fifo = UVMTLMAnalysisFIFO('fifo2', None)
        for i in range(10):
            ok = fifo.try_put(i * 2 + 1)
            self.assertTrue(ok)
        for i in range(10):
            arr = []
            ok = fifo.try_get(arr)
            self.assertEqual(arr[0], i * 2 + 1)
