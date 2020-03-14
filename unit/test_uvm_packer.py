
import unittest
# import re
from uvm.base.uvm_packer import (UVMPacker)
from uvm.base.uvm_object import UVMObject


class TestUVMPacker(unittest.TestCase):

    def test_pack_int(self):
        packer = UVMPacker()
        packer.big_endian = 0
        myshort = 0x1234
        mybyte = 0x67
        packer.pack_field_int(myshort, 16)
        packer.pack_field_int(mybyte, 8)

        packer.set_packed_size()
        packed_size = packer.get_packed_size()
        self.assertEqual(packed_size, 24)

        bits = packer.get_packed_bits()
        self.assertEqual(bits, (0x67 << 16 | 0x1234))
        bit0 = packer.get_bit(0)
        self.assertEqual(bit0, 0x4 & 0x1)
        self.assertEqual(packer.get_bit(2), (0x4 >> 2)  & 0x1)

    def test_pack_unpack_bytes(self):
        packer = UVMPacker()
        packer.big_endian = 0
        arr_bytes = [0x01, 0x03, 0x07, 0xAB]
        packer.pack_bytes(arr_bytes, 32)
        packer.set_packed_size()
        bits = packer.get_packed_bits()
        self.assertEqual(bits, 0xAB070301)
        arr = [0] * 4
        new_bytes = packer.unpack_bytes(arr)
        self.assertEqual(new_bytes, arr_bytes)
        my_bytes = packer.get_bytes()
        self.assertEqual(my_bytes, arr_bytes)


    def test_pack_unpack_ints(self):
        packer = UVMPacker()
        packer.big_endian = 0
        arr_int = [0x0123, 0x4567, 0x0089, 0x00AB]
        packer.pack_ints(arr_int, 4 * 32)
        packer.set_packed_size()
        bits = packer.get_packed_bits()
        self.assertEqual(bits, 0x000000AB000000890000456700000123)
        arr = [0] * 4
        new_ints = packer.unpack_ints(arr)
        self.assertEqual(new_ints, arr_int)

        my_ints = packer.get_ints()
        self.assertEqual(my_ints, arr_int)

        packer.reset()
        packer.pack_ints(arr_int, 4 * 32)
        packer.set_packed_size()
        self.assertEqual(packer.unpack_field_int(128), 0x000000AB000000890000456700000123)

        packer.reset()
        packer.pack_ints(arr_int, 4 * 32)
        packer.set_packed_size()
        self.assertEqual(packer.unpack_field_int(64), 0x0000456700000123)

        packer.reset()
        packer.pack_ints(arr_int, 4 * 32)
        packer.set_packed_size()
        self.assertEqual(packer.unpack_field_int(32), 0x00000123)


if __name__ == '__main__':
    unittest.main()
