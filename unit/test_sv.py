
import unittest
from uvm.base.sv import (sv, sv_obj, uvm_glob_to_re)


class Packet(sv_obj):
    def __init__(self, name):
        sv_obj.__init__(self)
        # self.rand("addr")
        self.addr = 0
        self.b_addr = 0
        self.tx_id = 0
        self.rand("addr", list(range(1, 4)))
        self.rand("b_addr", list(range(0, 256)))
        #self.constraint("addr", [1, 2, 3])
        #self.constraint("b_addr", range(0, 256))
        self.data = 0
        self.rand("data", [0, 1, 2, 4, 8, 16, 32])

        self.free_var = 0x0

        c1 = lambda addr, b_addr: b_addr == 3 * addr
        self.constraint(c1)


class TestSV(unittest.TestCase):

    def test_sv_obj(self):
        """ Test that basic object randomization works """
        pp = Packet("ethss")
        pp.tx_id = 888
        pp.data = 1234
        ok = pp.randomize()
        self.assertEqual(ok, True)

        self.assertTrue(pp.addr in [1, 2, 3])
        self.assertNotEqual(pp.data, 1234)
        self.assertEqual(pp.tx_id, 888)
        self.assertEqual(3 * pp.addr, pp.b_addr)

        #ok = pp.randomize_with(lambda addr: addr in [5, 6, 7])
        #self.assertEqual(ok, True)
        #self.assertEqual(pp.addr, 3 * pp.b_addr)

    def test_randomize_with(self):
        pp = Packet("ethss")
        ok = pp.randomize_with(lambda addr: addr in [1, 2])
        self.assertTrue(ok)
        self.assertTrue(pp.addr in [1, 2])

        # Check that previous constraint does nothing
        ok = pp.randomize_with(lambda addr: addr in [3, 4])
        self.assertTrue(ok)
        self.assertTrue(pp.addr in [3, 4])
        # Add extra constraint outside class
        #p2 = Packet('pkt_dfess')
        #p2.rand('free_var', range(0, (1 << 32) - 1))
        #ok = p2.randomize_with(lambda free_var, addr, b_addr: free_var == (addr + b_addr))
        #self.assertTrue(ok)
        #self.assertEqual(p2.free_var, p2.addr + p2.b_addr)


    def test_uvm_glob_to_re(self):
        str1 = "uvm_*"
        res1 = uvm_glob_to_re(str1)
        self.assertEqual(res1, 'uvm_.*')
        str2 = "uvm_*xxx*yyy"
        res2 = uvm_glob_to_re(str2)
        self.assertEqual(res2, 'uvm_.*xxx.*yyy')
        str3 = "my_top.xxx*"
        res3 = uvm_glob_to_re(str3)
        self.assertEqual(res3, 'my_top\\.xxx.*')

        str4 = "__top__.master[0].slave*"
        res4 = uvm_glob_to_re(str4)
        self.assertEqual(res4, '__top__\\.master\\[0\\]\\.slave.*')

    def test_cast(self):
        my_int = 6
        arr = []
        ok = sv.cast(arr, my_int, int)
        self.assertEqual(ok, True)
        self.assertEqual(arr[0], 6)
        arr = []
        ok = sv.cast(arr, my_int, str)
        self.assertEqual(ok, False)
        self.assertEqual(len(arr), 0)

    def test_sformatf(self):
        str1 = sv.sformatf("Number: %0d, String: %s", 555, "xxx")
        self.assertRegex(str1, "Number: 555")
        self.assertRegex(str1, "String: xxx")
        test_str = [
            ["Hexadecimal: %5h", 123],
            ["Time value: %0t", 55555]
        ]
        for pair in test_str:
            str1 = sv.sformatf(pair[0], pair[1])



    def test_clog2(self):
        self.assertEqual(sv.clog2(0), 0)
        self.assertEqual(sv.clog2(3), 2)
        self.assertEqual(sv.clog2(5), 3)
        self.assertEqual(sv.clog2(16), 4)
        for i in range(0, 64):
            self.assertEqual(sv.clog2(1 << i), i)


    def test_sscanf(self):
        str_in = "ab12 23cd s"
        format_in = "%d %s"
        misc = 0
        num, my_str = sv.sscanf(str_in, format_in, misc)
        self.assertEqual(num, 12)
        self.assertEqual(my_str, "23cd")

        str_fails = "abc abc"
        format_in = "%d %d"
        res = sv.sscanf(str_fails, format_in, misc)
        self.assertEqual(res, [])

        num_str = "0x1234 5678 10104 -345.124"
        format_in = "%h %d %b %f"
        res = sv.sscanf(num_str, format_in, misc)
        num_hex, num_dec, num_bin, num_float = res
        self.assertEqual(num_hex, 0x1234)
        self.assertEqual(num_dec, 5678)
        self.assertEqual(num_bin, 0b1010)
        self.assertEqual(num_float, -345.124)


if __name__ == '__main__':
    unittest.main()
