#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2013 NVIDIA Corporation
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//------------------------------------------------------------------------------

from .uvm_object_globals import *
from .uvm_scope_stack import UVMScopeStack
from .sv import sv
from ..macros.uvm_message_defines import uvm_error, uvm_warning
from typing import List


SIZEOF_INT = 32
MASK_INT = 0xFFFFFFFF


class UVMPacker(object):
    """
    The UVMPacker class provides a policy object for packing and unpacking
    uvm_objects. The policies determine how packing and unpacking should be done.
    Packing an object causes the object to be placed into a bit (byte or int)
    array. If the `uvm_field_* macro are used to implement pack and unpack,
    by default no metadata information is stored for the packing of dynamic
    objects (strings, arrays, class objects).
    """


    bitstream = []  # local bits for (un)pack_bytes
    fabitstream = []  # field automation bits for (un)pack_bytes

    #  //----------------//
    #  // Group: Packing //
    #  //----------------//

    def __init__(self):
        #  //------------------//
        #  // Group: Variables //
        #  //------------------//

        #  // Variable: physical
        #  //
        #  // This bit provides a filtering mechanism for fields.
        #  //
        #  // The <abstract> and physical settings allow an object to distinguish between
        #  // two different classes of fields. It is up to you, in the
        #  // `UVMObject.do_pack` and `UVMObject.do_unpack` methods, to test the
        #  // setting of this field if you want to use it as a filter.
        #  bit physical = 1
        self.physical = 1


        #  // Variable: abstract
        #  //
        #  // This bit provides a filtering mechanism for fields.
        #  //
        #  // The abstract and physical settings allow an object to distinguish between
        #  // two different classes of fields. It is up to you, in the
        #  // `UVMObject.do_pack` and `UVMObject.do_unpack` routines, to test the
        #  // setting of this field if you want to use it as a filter.
        #  bit abstract
        self.abstract = 0


        #  // Variable: use_metadata
        #  //
        #  // This flag indicates whether to encode metadata when packing dynamic data,
        #  // or to decode metadata when unpacking.  Implementations of `UVMObject.do_pack`
        #  // and `UVMObject.do_unpack` should regard this bit when performing their
        #  // respective operation. When set, metadata should be encoded as follows:
        #  //
        #  // - For strings, pack an additional ~null~ byte after the string is packed.
        #  //
        #  // - For objects, pack 4 bits prior to packing the object itself. Use 4'b0000
        #  //   to indicate the object being packed is ~null~, otherwise pack 4'b0001 (the
        #  //   remaining 3 bits are reserved).
        #  //
        #  // - For queues, dynamic arrays, and associative arrays, pack 32 bits
        #  //   indicating the size of the array prior to packing individual elements.
        #  bit use_metadata
        self.use_metadata = 0


        #  // Variable: big_endian
        #  //
        #  // This bit determines the order that integral data is packed (using
        #  // <pack_field>, <pack_field_int>, <pack_time>, or <pack_real>) and how the
        #  // data is unpacked from the pack array (using <unpack_field>,
        #  // <unpack_field_int>, <unpack_time>, or <unpack_real>). When the bit is set,
        #  // data is associated msb to lsb; otherwise, it is associated lsb to msb.
        #  //
        #  // The following code illustrates how data can be associated msb to lsb and
        #  // lsb to msb:
        #  //
        #  //|  class mydata extends uvm_object;
        #  //|
        #  //|    logic[15:0] value = 'h1234;
        #  //|
        #  //|    function void do_pack (UVMPacker packer);
        #  //|      packer.pack_field_int(value, 16);
        #  //|    endfunction
        #  //|
        #  //|    function void do_unpack (UVMPacker packer);
        #  //|      value = packer.unpack_field_int(16);
        #  //|    endfunction
        #  //|  endclass
        #  //|
        #  //|  mydata d = new;
        #  //|  bit bits[];
        #  //|
        #  //|  initial begin
        #  //|    d.pack(bits);  // 'b0001001000110100
        #  //|    uvm_default_packer.big_endian = 0;
        #  //|    d.pack(bits);  // 'b0010110001001000
        #  //|  end
        #  bit big_endian = 1
        self.big_endian = 1

        # variables and methods primarily for internal use
        self.count = 0                # used to count the number of packed bits
        self.scope = UVMScopeStack()
        self.reverse_order = 0      # flip the bit order around
        self.byte_size     = 8   # set up bytesize for endianess
        self.word_size     = 16  # set up worksize for endianess
        self.nopack = 0          # only count packable bits
        self.policy = UVM_DEFAULT_POLICY
        self.m_bits = 0x0  # uvm_pack_bitstream_t
        self.m_packed_size = 0


    #  // Function: pack_field
    #  //
    #  // Packs an integral value (less than or equal to 4096 bits) into the
    #  // packed array. ~size~ is the number of bits of ~value~ to pack.
    #
    #  extern def pack_field(self,uvm_bitstream_t value, int size):
    def pack_field(self, value, size) -> None:
        #  for (int i=0; i<size; i++)
        if self.big_endian == 1:
            flipped = self.flip_bit_order(value, size)
            self.m_bits |= flipped << self.count
            # self.m_bits[count+i] = value[size-1-i]
        else:
            self.m_bits |= value << self.count
        self.count += size


    #  // Function: pack_field_int
    #  //
    #  // Packs the integral value (less than or equal to 64 bits) into the
    #  // pack array.  The ~size~ is the number of bits to pack, usually obtained by
    #  // ~$bits~. This optimized version of <pack_field> is useful for sizes up
    #  // to 64 bits.
    def pack_field_int(self, value: int, size: int) -> None:
        if self.big_endian == 1:
            flipped = self.flip_bit_order(value, size)
            self.m_bits |= flipped << self.count
            #self.m_bits[self.count+i] = value[size-1-i]
        else:
            self.m_bits |= value << self.count
            #self.m_bits[self.count+i] = value[i]
        self.count += size


    #  // Function: pack_bits
    #  //
    #  // Packs bits from upacked array of bits into the pack array.
    #  //
    #  // See <pack_ints> for additional information.
    #  extern def pack_bits(self,ref bit value[], input int size = -1):


    #  // Function: pack_bytes
    #  //
    #  // Packs bits from an upacked array of bytes into the pack array.
    #  //
    #  // See <pack_ints> for additional information.
    #  extern def pack_bytes(self,ref byte value[], input int size = -1):
    def pack_bytes(self, value, size=-1) -> None:
        max_size = len(value) * 8

        if size < 0:
            size = max_size

        if size > max_size:
            uvm_error("UVM/BASE/PACKER/BAD_SIZE",
            sv.sformatf("pack_bytes called with size '%0d', which exceeds value size of '%0d'",
                size, max_size))
            return
        else:
            for i in range(len(value)):
                byte = value[i]
                if self.big_endian == 1:
                    byte = self.flip_bit_order(value[len(value)-1-i], 8)
                self.m_bits |= byte << self.count
                self.count += 8


    #  // Function: pack_ints
    #  //
    #  // Packs bits from an unpacked array of ints into the pack array.
    #  //
    #  // The bits are appended to the internal pack array.
    #  // This method allows for fields of arbitrary length to be
    #  // passed in, using the SystemVerilog ~stream~ operator.
    #  //
    #  // For example
    #  // | bit[511:0] my_field;
    #  // | begin
    #  // |   int my_stream[];
    #  // |   { << int {my_stream}} = my_field;
    #  // |   packer.pack_ints(my_stream);
    #  // | end
    #  //
    #  // When appending the stream to the internal pack array, the packer will obey
    #  // the value of <big_endian> (appending the array from MSB to LSB if set).
    #  //
    #  // An optional ~size~ parameter is provided, which defaults to '-1'.  If set
    #  // to any value greater than '-1' (including 0), then the packer will use
    #  // the size as the number of bits to pack, otherwise the packer will simply
    #  // pack the entire stream.
    #  //
    #  // An error will be asserted if the ~size~ has been specified, and exceeds the
    #  // size of the source array.
    #  //
    #  extern def pack_ints(self,ref int value[], input int size = -1):
    def pack_ints(self, value, size=-1) -> None:
        max_size = len(value) * SIZEOF_INT

        if size < 0:
            size = max_size

        if size > max_size:
            uvm_error("UVM/BASE/PACKER/BAD_SIZE",
                sv.sformatf("pack_ints called with size '%0d', which exceeds value size of '%0d'",
                    size, max_size))
            return
        else:
            for i in range(len(value)):
                int_num = value[i]
                if self.big_endian == 1:
                    int_num = self.flip_bit_order(value[len(value)-1-i],
                        SIZEOF_INT)
                self.m_bits |= int_num << self.count
                self.count += SIZEOF_INT


    #  // Function: pack_string
    #  //
    #  // Packs a string value into the pack array.
    #  //
    #  // When the metadata flag is set, the packed string is terminated by a ~null~
    #  // character to mark the end of the string.
    #  //
    #  // This is useful for mixed language communication where unpacking may occur
    #  // outside of SystemVerilog UVM.
    #
    #  extern def pack_string(self,string value):
    def pack_string(self, value) -> None:
        bytearr = value.encode()

        size = 8 * len(bytearr)
        bits = int(bytearr.hex(), 16)
        if self.big_endian == 1:
            bits = self.flip_bit_order(bits, -1)
        self.m_bits |= bits << self.count
        self.count += size
        if self.use_metadata == 1:
            pass
            # TODO self.m_bits |= 0 << self.count
        #  byte b
        #  foreach (value[index]):
        #    if(self.big_endian == 0)
        #      self.m_bits[count +: 8] = value[index]
        #    else begin
        #      b = value[index]
        #      for(int i=0; i<8; ++i)
        #        self.m_bits[count+i] = b[7-i]
        #    end
        #    count += 8
        #  end
        #  if(use_metadata == 1):
        #    self.m_bits[count +: 8] = 0
        #    count += 8
        #  end
        #endfunction


    #  // Function: pack_time
    #  //
    #  // Packs a time ~value~ as 64 bits into the pack array.
    #
    #  extern def pack_time(self,time value):;


    #  // Function: pack_real
    #  //
    #  // Packs a real ~value~ as 64 bits into the pack array.
    #  //
    #  // The real ~value~ is converted to a 6-bit scalar value using the function
    #  // $real2bits before it is packed into the array.
    #
    #  extern def pack_real(self,real value):


    #  // Function: pack_object
    #  //
    #  // Packs an object value into the pack array.
    #  //
    #  // A 4-bit header is inserted ahead of the string to indicate the number of
    #  // bits that was packed. If a ~null~ object was packed, then this header will
    #  // be 0.
    #  //
    #  // This is useful for mixed-language communication where unpacking may occur
    #  // outside of UVM.
    #
    #  extern def pack_object(self,uvm_object value):
    def pack_object(self, value) -> None:
        if value in value._m_uvm_status_container.cycle_check:
            uvm_warning("CYCFND", sv.sformatf("Cycle detected for object @%0d during pack",
                value.get_inst_id()))
            return

        value._m_uvm_status_container.cycle_check[value] = 1

        if((self.policy != UVM_REFERENCE) and value is not None):
            if self.use_metadata == 1:
                pass
                #self.m_bits[count +: 4] = 1
                #count += 4; // to better debug when display packed bits in hexadecimal

            self.scope.down(value.get_name())
            value._m_uvm_field_automation(None, UVM_PACK,"")
            value.do_pack(self)
            self.scope.up()
        elif self.use_metadata == 1:
            pass
            #self.m_bits[count +: 4] = 0
            #count += 4
        del value._m_uvm_status_container.cycle_check[value]


    #  //------------------//
    #  // Group: Unpacking //
    #  //------------------//

    #  // Function: is_null
    #  //
    #  // This method is used during unpack operations to peek at the next 4-bit
    #  // chunk of the pack data and determine if it is 0.
    #  //
    #  // If the next four bits are all 0, then the return value is a 1; otherwise
    #  // it is 0.
    #  //
    #  // This is useful when unpacking objects, to decide whether a new object
    #  // needs to be allocated or not.
    #
    #  extern def is_null(self):


    #  // Function: unpack_field
    #  //
    #  // Unpacks bits from the pack array and returns the bit-stream that was
    #  // unpacked. ~size~ is the number of bits to unpack; the maximum is 4096 bits.
    #
    #  extern def unpack_field(self,int size):
    def unpack_field(self, size):
        return self.unpack_field_int(size)
        #  unpack_field =  0b0
        #  if (self.enough_bits(size,"integral")):
        #    count += size
        #    for (int i=0; i<size; i++)
        #      if(self.big_endian == 1)
        #        unpack_field[i] = self.m_bits[count-i-1]
        #      else
        #        unpack_field[i] = self.m_bits[count-size+i]
        #  end
        #endfunction


    #  // Function: unpack_field_int
    #  //
    #  // Unpacks bits from the pack array and returns the bit-stream that was
    #  // unpacked.
    #  //
    #  // ~size~ is the number of bits to unpack; the maximum is 64 bits.
    #  // This is a more efficient variant than unpack_field when unpacking into
    #  // smaller vectors.
    #
    #  extern def unpack_field_int(self,int size):
    def unpack_field_int(self, size) -> int:
        unpack_field_int = 0x0
        count_before = self.count
        if self.enough_bits(size,"integral"):
            self.count += size
            for i in range(size):
                if self.big_endian:
                    bit_sel = self.count-i-1
                    bit_sel = (1 << bit_sel)
                    unpack_field_int |= self.m_bits & bit_sel
                else:
                    bit_sel = self.count-size+i
                    bit_sel = (1 << bit_sel)
                    unpack_field_int |= self.m_bits & bit_sel
        unpack_field_int >>= count_before
        if self.big_endian:
            unpack_field_int = self.flip_bit_order(unpack_field_int, size)
        return unpack_field_int


    #  // Function: unpack_bits
    #  //
    #  // Unpacks bits from the pack array into an unpacked array of bits.
    #  //
    #  extern def unpack_bits(self,ref bit value[], input int size = -1):
    #

    #  // Function: unpack_bytes
    #  //
    #  // Unpacks bits from the pack array into an unpacked array of bytes.
    #  //
    #  extern def unpack_bytes(self,ref byte value[], input int size = -1):
    def unpack_bytes(self, value, size=-1):
        max_size = len(value) * 8
        if size < 0:
            size = max_size

        if size > max_size:
            uvm_error("UVM/BASE/PACKER/BAD_SIZE",
                sv.sformatf("unpack_bytes called with size '%0d', which exceeds value size of '%0d'",
                    size, len(value)))
            return []
        else:
            if self.enough_bits(size, "integral"):
                self.count += size
                for b in range(len(value)):
                    byte = (self.m_bits >> b * 8) & 0xFF
                    if self.big_endian == 1:
                        byte = self.flip_bit_order(byte, 8)
                        value[len(value)-1-b] = byte
                    else:
                        value[b] = byte
            return value


    #  // Function: unpack_ints
    #  //
    #  // Unpacks bits from the pack array into an unpacked array of ints.
    #  //
    #  // The unpacked array is unpacked from the internal pack array.
    #  // This method allows for fields of arbitrary length to be
    #  // passed in without expanding into a pre-defined integral type first.
    #  //
    #  // For example
    #  // | bit[511:0] my_field;
    #  // | begin
    #  // |   int my_stream[] = new[16]; // 512/32 = 16
    #  // |   packer.unpack_ints(my_stream);
    #  // |   my_field = {<<{my_stream}};
    #  // | end
    #  //
    #  // When unpacking the stream from the internal pack array, the packer will obey
    #  // the value of <big_endian> (unpacking the array from MSB to LSB if set).
    #  //
    #  // An optional ~size~ parameter is provided, which defaults to '-1'.  If set
    #  // to any value greater than '-1' (including 0), then the packer will use
    #  // the size as the number of bits to unpack, otherwise the packer will simply
    #  // unpack the entire stream.
    #  //
    #  // An error will be asserted if the ~size~ has been specified, and
    #  // exceeds the size of the target array.
    #  //
    #  extern def unpack_ints(self,ref int value[], input int size = -1):
    def unpack_ints(self, value, size=-1):
        max_size = len(value) * SIZEOF_INT
        if size < 0:
            size = max_size

        if size > max_size:
            uvm_error("UVM/BASE/PACKER/BAD_SIZE",
                sv.sformatf("unpack_ints called with size '%0d', which exceeds value size of '%0d'",
                   size, len(value)))
            return
        else:
            if self.enough_bits(size, "integral"):
                self.count += size
                for i in range(len(value)):
                    int_num = (self.m_bits >> i * SIZEOF_INT) & 0xFFFFFFFF
                    if self.big_endian == 1:
                        int_num = self.flip_bit_order(int_num, SIZEOF_INT)
                        value[len(value)-1-i] = int_num
                    else:
                        value[i] = int_num
            return value


    #  // Function: unpack_string
    #  //
    #  // Unpacks a string.
    #  //
    #  // num_chars bytes are unpacked into a string. If num_chars is -1 then
    #  // unpacking stops on at the first ~null~ character that is encountered.
    #// If num_chars is not -1, then the user only wants to unpack a
    #// specific number of bytes into the string.
    def unpack_string(self, num_chars=-1):
        #  byte b
        i = 0
        is_null_term = 0  # Assumes a ~None~ terminated string
        #  int i; i=0
        if num_chars == -1:
            is_null_term = 1

        #val_to_decode = 0x0
        # We'll use bytearray to decode this, so need to find the num of bytes

        byte_arr = bytearray()
        #unpack_string = 0
        curr_byte = (self.m_bits >> self.count) & 0xFF
        while (self.enough_bits(8,"string", is_error=False) and
              ((curr_byte != 0) or (is_null_term == 0)) and
              ((i < num_chars) or (is_null_term == 1))):
            # silly, because cannot append byte/char to string
            #unpack_string = unpack_string + " "
            #if self.big_endian == 0:
            #    unpack_string[i] = self.m_bits[count +: 8]
            #else:
            #    for(int j=0; j<8; ++j)
            #        b[7-j] = self.m_bits[count+j]
            #  unpack_string[i] = b
            i += 1
            byte_arr.insert(0, curr_byte)
            self.count += 8
            curr_byte = (self.m_bits >> self.count) & 0xFF
        if self.enough_bits(8,"string", is_error=False):
            self.count += 8
        return byte_arr.decode()
        #return unpack_string


    #  // Function: unpack_time
    #  //
    #  // Unpacks the next 64 bits of the pack array and places them into a
    #  // time variable.
    #
    #  extern def unpack_time(self):;



    #  // Function: unpack_real
    #  //
    #  // Unpacks the next 64 bits of the pack array and places them into a
    #  // real variable.
    #  //
    #  // The 64 bits of packed data are converted to a real using the $bits2real
    #  // system function.
    #
    #  extern def unpack_real(self):



    #  // Function: unpack_object
    #  //
    #  // Unpacks an object and stores the result into ~value~.
    #  //
    #  // ~value~ must be an allocated object that has enough space for the data
    #  // being unpacked. The first four bits of packed data are used to determine
    #  // if a ~null~ object was packed into the array.
    #  //
    #  // The <is_null> function can be used to peek at the next four bits in
    #  // the pack array before calling this method.
    #
    #  extern def unpack_object(self,uvm_object value):
    def unpack_object(self, value):
        is_non_null = 1

        if value in value._m_uvm_status_container.cycle_check:
            uvm_warning("CYCFND", sv.sformatf(
                "Cycle detected for object @%0d during unpack", value.get_inst_id()))
            return
        value._m_uvm_status_container.cycle_check[value] = 1

        if self.use_metadata == 1:
            is_non_null = get_bits(self.m_bits, self.count, 4) != 0  # [count +: 4]
            self.count += 4

        # NOTE- policy is a ~pack~ policy, not unpack policy;
        #       and you can't pack an object by REFERENCE
        if value is not None:
            if is_non_null > 0:
                self.scope.down(value.get_name())
                value._m_uvm_field_automation(None, UVM_UNPACK,"")
                value.do_unpack(self)
                self.scope.up()
            else:
                pass
                # TODO: help do_unpack know whether unpacked result would be null
                #       to avoid new'ing unnecessarily;
                #       this does not nullify argument; need to pass obj by ref
        elif ((is_non_null != 0) and (value is None)):
             uvm_error("UNPOBJ","cannot unpack into None object")
        del value._m_uvm_status_container.cycle_check[value]


    #  // Function: get_packed_size
    #  //
    #  // Returns the number of bits that were packed.
    def get_packed_size(self) -> int:
        return self.m_packed_size


    #  extern def unpack_object_ext(self,inout uvm_object value):


    #  extern def get_packed_bits(self):
    def get_packed_bits(self) -> int:
        return self.m_bits


    #  extern def bit  unsigned get_bit  (self,int unsigned index):
    def get_bit(self, index) -> int:
        if index >= self.m_packed_size:
            self.index_error(index, "bit",1)
        return (self.m_bits >> index) & 0x1


    #  extern def byte unsigned get_byte (self,int unsigned index):
    #  extern def int  unsigned get_int  (self,int unsigned index):

    #  extern def get_bits(self,ref bit unsigned bits[]):
    def get_bits(self) -> int:
        return self.m_bits

    #  extern def get_bytes(self,ref byte unsigned bytes[]):
    def get_bytes(self) -> List[int]:
        sz = 0
        v = 0x00
        sz = int((self.m_packed_size+7) / 8)
        bytes = [0] * sz
        for i in range(sz):
            if (i != sz-1 or (self.m_packed_size % 8) == 0):
                v = (self.m_bits >> (i * 8)) & 0xFF
            else:
                sel = (0xFF >> (8-(self.m_packed_size % 8)))
                v = (self.m_bits >> (i * 8)) & sel
            if self.big_endian:
                v = self.flip_bit_order(v, 8)
            bytes[i] = v
        return bytes


    #  extern def get_ints(self):
    def get_ints(self) -> List[int]:
        sz = 0
        v = 0
        sz = int((self.m_packed_size+31) / SIZEOF_INT)
        ints = [0] * sz
        for i in range(sz):
            if i != sz-1 or (self.m_packed_size % 32) == 0:
                v = (self.m_bits >> (i * SIZEOF_INT)) & 0xFFFFFFFF
            else:
                sel = (0xFFFFFFFF >> (32-(self.m_packed_size % 32)))
                v = (self.m_bits >> (i * SIZEOF_INT)) & sel
            if self.big_endian:
                v = self.flip_bit_order(v, SIZEOF_INT)
            ints[i] = v
        return ints


    #  extern def put_bits(self,ref bit unsigned bitstream[]):
    def put_bits(self, bitstream):
        #  int bit_size
        #  bit_size = bitstream.size()
        #
        #  if(self.big_endian)
        #    for (int i=bit_size-1;i>=0;i--)
        #      self.m_bits[i] = bitstream[i]
        #  else
        #    for (int i=0;i<bit_size;i++)
        #      self.m_bits[i] = bitstream[i]
        #
        self.m_bits = bitstream
        self.m_packed_size = len(bin(self.m_bits)) - 2
        self.count = 0

    #  extern def put_bytes(self,ref byte unsigned bytestream[]):
    #  extern def put_ints(self,ref int unsigned intstream[]):


    def set_packed_size(self):
        self.m_packed_size = self.count
        self.count = 0

    #  extern def index_error(self,int index, string id, int sz):
    def index_error(self, index, id, sz):
        uvm_error("PCKIDX",
            sv.sformatf("index %0d for get_%0s too large; valid index range is 0-%0d.",
                index,id,((self.m_packed_size+sz-1)/sz)-1))

    #  extern def enough_bits(self,int needed, string id):
    def enough_bits(self, needed, id, is_error=True):
        if ((self.m_packed_size - self.count) < needed):
            if is_error is True:
                uvm_error("PCKSZ",
                    sv.sformatf("%0d bits needed to unpack %0s, yet only %0d available.",
                    needed, id, (self.m_packed_size - self.count)))
            return 0
        return 1


    def reset(self):
        self.count = 0
        self.m_bits = 0
        self.m_packed_size = 0

    def flip_bit_order(self, value, size: int) -> int:
        flipped = 0x0
        num_bits = len(bin(value)) - 2
        while value:
            flipped = (flipped << 1) + (value & 0x1)  # Choose LSB
            value = value >> 1
        # For packing, need to add some right-padding
        if size != -1:
            rem_bits = size - num_bits
            if rem_bits >= 0:
                flipped <<= rem_bits
            else:
                raise Exception("rem_bits negative. size: {}, value: {}".format(
                    size, hex(value)))
        return flipped


#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#// NOTE- max size limited to BITSTREAM bits parameter (default: 4096)
#
#
#// put_bytes
#// ---------
#
#def void UVMPacker::put_bytes (self,ref byte unsigned bytestream []):
#
#  int byte_size
#  int index
#  byte unsigned b
#
#  byte_size = bytestream.size()
#  index = 0
#  for (int i=0;i<byte_size;i++):
#    b = bytestream[i]
#    if(self.big_endian):
#      byte unsigned tb; tb = b
#      for(int j=0;j<8;++j) b[j] = tb[7-j]
#    end
#    self.m_bits[index +:8] = b
#    index += 8
#  end
#
#  m_packed_size = byte_size*8
#  count = 0
#endfunction
#
#
#// put_ints
#// --------
#
#def void UVMPacker::put_ints (self,ref int unsigned intstream []):
#
#  int int_size
#  int index
#  int unsigned v
#
#  int_size = intstream.size()
#
#  index = 0
#  for (int i=0;i<int_size;i++):
#    v = intstream[i]
#    if(self.big_endian):
#      v = self.flip_bit_order(v)
#    self.m_bits[index +:32] = v
#    index += 32
#  end
#
#  m_packed_size = int_size*32
#  count = 0
#endfunction
#
#
#
#
#
#
#// get_byte
#// --------
#
#def byte unsigned UVMPacker::get_byte(self,int unsigned index):
#  if (index >= (m_packed_size+7)/8)
#    index_error(index, "byte",8)
#  return self.m_bits[index*8 +: 8]
#endfunction
#
#
#// get_int
#// -------
#
#def int unsigned UVMPacker::get_int(self,int unsigned index):
#  if (index >= (m_packed_size+31)/32)
#    index_error(index, "int",32)
#  return self.m_bits[(index*32) +: 32]
#endfunction
#
#
#// PACK
#
#
#
#
#// pack_real
#// ---------
#
#def void UVMPacker::pack_real(self,real value):
#  pack_field_int($realtobits(value), 64)
#endfunction
#
#
#// pack_time
#// ---------
#
#def void UVMPacker::pack_time(self,time value):
#  pack_field_int(value, 64)
#  //m_bits[count +: 64] = value; this overwrites endian adjustments
#endfunction
#
#
#
#
#
#// pack_bits
#// -----------------
#
#def void UVMPacker::pack_bits(self,ref bit value[], input int size = -1):
#   if (size < 0)
#     size = len(value)
#
#   if (size > len(value)):
#      uvm_error("UVM/BASE/PACKER/BAD_SIZE",
#                 sv.sformatf("pack_bits called with size '%0d', which exceeds len(value) of '%0d'",
#                           size,
#                           len(value)))
#      return
#   end
#
#   for (int i=0; i<size; i++)
#     if (self.big_endian == 1)
#       self.m_bits[count+i] = value[size-1-i]
#     else
#       self.m_bits[count+i] = value[i]
#   count += size
#endfunction
#
#
#
#
#
#
#// UNPACK
#
#
#// is_null
#// -------
#
#def bit UVMPacker::is_null(self):
#  return (m_bits[count+:4]==0)
#endfunction
#
#// unpack_object
#// -------------
#
#def void UVMPacker::unpack_object_ext(self,inout uvm_object value):
#  unpack_object(value)
#endfunction
#
#
#
#// unpack_real
#// -----------
#
#def real UVMPacker::unpack_real(self):
#  if (self.enough_bits(64,"real")):
#    return $bitstoreal(unpack_field_int(64))
#  end
#endfunction
#
#
#// unpack_time
#// -----------
#
#def time UVMPacker::unpack_time(self):
#  if (self.enough_bits(64,"time")):
#    return unpack_field_int(64)
#  end
#endfunction
#
#
#
#
#
#// unpack_bits
#// -------------------
#
#def void UVMPacker::unpack_bits(self,ref bit value[], input int size = -1):
#   if (size < 0)
#     size = len(value)
#
#   if (size > len(value)):
#      uvm_error("UVM/BASE/PACKER/BAD_SIZE",
#                 sv.sformatf("unpack_bits called with size '%0d', which exceeds len(value) of '%0d'",
#                           size,
#                           len(value)))
#      return
#   end
#
#   if (self.enough_bits(size, "integral")):
#      count += size
#      for (int i=0; i<size; i++)
#        if (self.big_endian == 1)
#          value[i] = self.m_bits[count-i-1]
#        else
#          value[i] = self.m_bits[count-size+i]
#   end
#endfunction
#
#

def get_bits(bits, count, nbits):  # [count +: 4]
    val = 0x0
    idx = 0
    for i in range(count, count + nbits + 1):
        val |= (1 << (nbits - idx)) & (bits >> (i-idx))
        idx += 1
    return val
