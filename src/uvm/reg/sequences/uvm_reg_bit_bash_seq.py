#//
#// -------------------------------------------------------------
#//    Copyright 2004-2008 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//
"""
Title: Bit Bashing Test Sequences

This section defines classes that test individual bits of the registers
defined in a register model.
"""

import cocotb
from cocotb.triggers import Timer

from ..uvm_reg_sequence import UVMRegSequence
from ..uvm_reg_model import (UVM_NO_HIER, UVM_NO_CHECK,
        UVM_FRONTDOOR, UVM_IS_OK)
from ...macros import (uvm_object_utils, uvm_error, uvm_info, UVM_REG_DATA_WIDTH,
    uvm_warning)
from ...base import UVMResourceDb, sv, UVM_LOW, UVM_HIGH, uvm_zero_delay


#//----------------------------------------------------------------------------
#// Class: UVMRegSingleBitBashSeq
#//
#// Verify the implementation of a single register
#// by attempting to write 1's and 0's to every bit in it,
#// via every address map in which the register is mapped,
#// making sure that the resulting value matches the mirrored value.
#//
#// If bit-type resource named
#// "NO_REG_TESTS" or "NO_REG_BIT_BASH_TEST"
#// in the "REG::" namespace
#// matches the full name of the register,
#// the register is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.r0.get_full_name()},
#//|                            "NO_REG_TESTS", 1, this);
#//
#// Registers that contain fields with unknown access policies
#// cannot be tested.
#//
#// The DUT should be idle and not modify any register during this test.
#//
#//----------------------------------------------------------------------------


class UVMRegSingleBitBashSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))

    #   // Variable: rg
    #   // The register to be tested
    #   uvm_reg rg

    def __init__(self, name="UVMRegSingleBitBashSeq"):
        super().__init__(name)
        self.rg = None


    async def body(self):
        fields = []  # uvm_reg_field[$]
        mode = [""] * UVM_REG_DATA_WIDTH  # string [`UVM_REG_DATA_WIDTH]
        maps = []  # uvm_reg_map [$]
        dc_mask = [0] * UVM_REG_DATA_WIDTH
        reset_val = 0x0
        n_bits = 0
        field_access = ""
        rg = self.rg

        if self.rg is None:
            uvm_error("UVMRegBitBashSeq", "No register specified to run sequence on")
            return

        # Registers with some attributes are not to be tested
        if (UVMResourceDb.get_by_name("REG::" + rg.get_full_name(),
            "NO_REG_TESTS", 0) is not None or
                  UVMResourceDb.get_by_name("REG::" + rg.get_full_name(),
                      "NO_REG_BIT_BASH_TEST", 0) is not None):
            return

        n_bits = self.rg.get_n_bytes() * 8

        # Let's see what kind of bits we have...
        rg.get_fields(fields)

        # Registers may be accessible from multiple physical interfaces (maps)
        rg.get_maps(maps)

        # TODO Bash the bits in the register via each map
        for j in range(len(maps)):
            status = 0
            val = 0x0
            exp = 0x0
            v = 0x0
            next_lsb = 0
            dc_mask  = [0] * UVM_REG_DATA_WIDTH

            for k in range(len(fields)):

                field_access = fields[k].get_access(maps[j])
                dc = (fields[k].get_compare() == UVM_NO_CHECK)
                lsb = fields[k].get_lsb_pos()
                w   = fields[k].get_n_bits()

                # Ignore Write-only fields because
                # you are not supposed to read them
                if field_access in ["WO", "WOC", "WOS", "WO1", "NOACCESS"]:
                    dc = 1

                # Any unused bits on the right side of the LSB?
                while next_lsb < lsb:
                    mode[next_lsb] = "RO"
                    next_lsb += 1

                for _ in range(w):
                    mode[next_lsb] = field_access
                    dc_mask[next_lsb] = dc
                    next_lsb += 1
            # Any unused bits on the left side of the MSB?
            while next_lsb < UVM_REG_DATA_WIDTH:
                mode[next_lsb] = "RO"
                next_lsb += 1

            uvm_info("UVMRegBitBashSeq", sv.sformatf("Verifying bits in register %s in map \"%s\"...",
                rg.get_full_name(), maps[j].get_full_name()),UVM_LOW)

            bits_bashed = 0
            # Bash the kth bit
            for k in range(n_bits):
                # Cannot test unpredictable bit behavior
                if dc_mask[k] == 1:
                    continue
                dc_mask_int = 0x0
                for i in range(len(dc_mask)):
                    dc_mask_int |= (dc_mask[i] << i)

                await self.bash_kth_bit(rg, k, mode[k], maps[j], dc_mask_int)
                bits_bashed += 1

            if bits_bashed == 0:
                uvm_warning('UVMRegBitBashSeq', 'No bits bashed for ' +
                    rg.get_name())


    async def bash_kth_bit(self, rg, k, mode, _map, dc_mask):
        status = 0
        val = 0x0
        exp = 0x0
        v = 0x0
        bit_val = False
        uvm_info("UVMRegBitBashSeq", sv.sformatf("...Bashing %s bit #%0d", mode, k), UVM_HIGH)

        for _ in range(2):
            val = rg.get()
            v   = val
            exp = val
            mask = 1 << k
            #val[k] = ~val[k]
            #val = (val & ~mask) | (~val & mask)
            val ^= mask
            bit_val = (val >> k) & 0x1

            status = []
            await rg.write(status, val, UVM_FRONTDOOR, _map, self)
            status = status[0]
            if status != UVM_IS_OK:
                uvm_error("UVMRegBitBashSeq",
                        sv.sformatf("Status was %s when writing to register \"%s\" through map \"%s\".",
                            status.name(), rg.get_full_name(), _map.get_full_name()))

            exp = rg.get() & ~dc_mask
            status = []
            out_val = []
            await rg.read(status, out_val, UVM_FRONTDOOR, _map, self)
            status = status[0]
            val = out_val[0]
            if status != UVM_IS_OK:
               uvm_error("UVMRegBitBashSeq",
                       sv.sformatf("Status was %s when reading register \"%s\" through map \"%s\".",
                           status.name(), rg.get_full_name(), _map.get_full_name()))

            val &= ~dc_mask
            if val != exp:
                uvm_error("UVMRegBitBashSeq", sv.sformatf(
                    ("Writing a %b in bit #%0d of register \"%s\" with initial value "
                    + "'h%h yielded 'h%h instead of 'h%h"),
                    bit_val, k, rg.get_full_name(), v, val, exp))


uvm_object_utils(UVMRegSingleBitBashSeq)


#//------------------------------------------------------------------------------
#// Class: UVMRegBitBashSeq
#//
#//
#// Verify the implementation of all registers in a block
#// by executing the <UVMRegSingleBitBashSeq> sequence on it.
#//
#// If bit-type resource named
#// "NO_REG_TESTS" or "NO_REG_BIT_BASH_TEST"
#// in the "REG::" namespace
#// matches the full name of the block,
#// the block is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.get_full_name(),".*"},
#//|                            "NO_REG_TESTS", 1, this);
#//
#//------------------------------------------------------------------------------


class UVMRegBitBashSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))

    def __init__(self, name="UVMRegBitBashSeq"):
        super().__init__(name)
        #   // Variable: reg_seq
        #   //
        #   // The sequence used to test one register
        #   //
        self.reg_seq = None
        #   // Variable: model
        #   //
        #   // The block to be tested. Declared in the base class.
        #   //
        self.model = None

    #   // Task: body
    #   //
    #   // Executes the Register Bit Bash sequence.
    #   // Do not call directly. Use seq.start() instead.
    #   //
    async def body(self):

        if self.model is None:
            uvm_error("UVMRegBitBashSeq", "No register model specified to run sequence on")
            return

        uvm_info("STARTING_SEQ","\n\nStarting " + self.get_name() + " sequence...\n",UVM_LOW)
        self.reg_seq = UVMRegSingleBitBashSeq.type_id.create("reg_single_bit_bash_seq")

        await self.reset_blk(self.model)
        self.model.reset()
        await self.do_block(self.model)


    #   // Task: do_block
    #   //
    #   // Test all of the registers in a given ~block~
    async def do_block(self, blk):
        regs = []

        if (UVMResourceDb.get_by_name("REG::" + blk.get_full_name(),
            "NO_REG_TESTS", 0) is not None or
            UVMResourceDb.get_by_name("REG::" + blk.get_full_name(),
                "NO_REG_BIT_BASH_TEST", 0) is not None):
            return

        # Iterate over all registers, checking accesses
        blk.get_registers(regs, UVM_NO_HIER)
        for i in range(len(regs)):
            # Registers with some attributes are not to be tested
            if (UVMResourceDb.get_by_name("REG::" + regs[i].get_full_name(),
                "NO_REG_TESTS", 0) is not None or
                UVMResourceDb.get_by_name("REG::" + regs[i].get_full_name(),
                    "NO_REG_BIT_BASH_TEST", 0) is not None):
                continue

            self.reg_seq.rg = regs[i]
            await self.reg_seq.start(None,self)

        blks = []
        blk.get_blocks(blks)
        for blk in blks:
            await self.do_block(blk)


    #   // Task: reset_blk
    #   //
    #   // Reset the DUT that corresponds to the specified block abstraction class.
    #   //
    #   // Currently empty.
    #   // Will rollback the environment's phase to the ~reset~
    #   // phase once the new phasing is available.
    #   //
    #   // In the meantime, the DUT should be reset before executing this
    #   // test sequence or this method should be implemented
    #   // in an extension to reset the DUT.
    #   //
    async def reset_blk(self, blk):
        await uvm_zero_delay()


uvm_object_utils(UVMRegBitBashSeq)
