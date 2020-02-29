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

import cocotb
from cocotb.triggers import Timer

from ..uvm_reg_sequence import UVMRegSequence
from ..uvm_reg_model import *
from ...macros import uvm_error, uvm_object_utils, uvm_info, uvm_warning
from ...base import sv, UVM_LOW


#//
#// TITLE: Memory Access Test Sequence
#//


#//
#// class: UVMMemSingleAccessSeq
#//
#// Verify the accessibility of a memory
#// by writing through its default address map
#// then reading it via the backdoor, then reversing the process,
#// making sure that the resulting value matches the written value.
#//
#// If bit-type resource named
#// "NO_REG_TESTS", "NO_MEM_TESTS", or "NO_MEM_ACCESS_TEST"
#// in the "REG::" namespace
#// matches the full name of the memory,
#// the memory is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.mem0.get_full_name()},
#//|                            "NO_MEM_TESTS", 1, this);
#//
#// Memories without an available backdoor
#// cannot be tested.
#//
#// The DUT should be idle and not modify the memory during this test.
#//


class UVMMemSingleAccessSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))


    def __init__(self, name="uam_mem_single_access_seq"):
        super().__init__(name)
        #   // Variable: mem
        #   //
        #   // The memory to be tested
        #   //
        self.mem = None


    
    async def body(self):
        mem = self.mem
        mode = ""
        maps = []  # uvm_reg_map[$]
        n_bits = 0

        if mem is None:
            uvm_error("UVMMemAccessSeq", "No register specified to run sequence on")
            return

        # Memories with some attributes are not to be tested
        if reg_test_off(mem, ["NO_REG_TESTS", "NO_MEM_TESTS", "NO_MEM_ACCESS_TEST"]):
            return

        # Can only deal with memories with backdoor access
        if (mem.get_backdoor() is None and not mem.has_hdl_path()):
            uvm_error("UVMMemAccessSeq", "Memory '" + mem.get_full_name()
                + "' does not have a backdoor mechanism available")
            return

        n_bits = mem.get_n_bits()

        # Memories may be accessible from multiple physical interfaces (maps)
        mem.get_maps(maps)

        # Walk the memory via each map
        for j in range(len(maps)):
            status = 0
            val = 0
            exp = 0
            v = 0

            uvm_info("UVMMemAccessSeq", "Verifying access of memory '"
                + mem.get_full_name() + "' in map '" + maps[j].get_full_name()
                + "' ...", UVM_LOW)
            mode = mem.get_access(maps[j])

            # The access process is, for address k:
            # - Write random value via front door
            # - Read via backdoor and expect same random value if RW
            # - Write complement of random value via back door
            # - Read via front door and expect inverted random value
            for k in range(mem.get_size()):
                val = sv.random() & (1 << n_bits) - 1  # cast to 'uvm_reg_data_t' removed
                if n_bits > 32:
                    val = (val << 32) | sv.random()
                if mode == "RO":
                    status = []
                    await mem.peek(status, k, exp)
                    status = status[0]
                    if status != UVM_IS_OK:
                       uvm_error("UVMMemAccessSeq", sv.sformatf(
                           "Status was %s when reading \"%s[%0d]\" through backdoor.",
                           status.name(), mem.get_full_name(), k))
                else:
                    exp = val

                status = []
                await mem.write(status, k, val, UVM_FRONTDOOR, maps[j], self)
                status = status[0]
                if status != UVM_IS_OK:
                    uvm_error("UVMMemAccessSeq", sv.sformatf(
                        "Status was %s when writing '%s[%0d]' through map '%s'.",
                        status.name(), mem.get_full_name(), k, maps[j].get_full_name()))
                await Timer(1, "NS")

                val = []
                status = []
                #yield mem.peek(status, k, val)
                mem.peek(status, k, val)
                status = status[0]
                if status != UVM_IS_OK:
                    uvm_error("UVMMemAccessSeq", sv.sformatf(
                        "Status was %s when reading '%s[%0d]' through backdoor.",
                        str(status), mem.get_full_name(), k))

                else:
                    val = val[0]
                    if val != exp:
                       uvm_error("UVMMemAccessSeq", sv.sformatf(
                           "Backdoor '%s[%0d]' read back as 'h%h instead of 'h%h.",
                           mem.get_full_name(), k, val, exp))

                exp = ~exp & ((1 << n_bits)-1)
                status = []
                #yield mem.poke(status, k, exp)
                mem.poke(status, k, exp)
                status = status[0]
                if status != UVM_IS_OK:
                    uvm_error("UVMMemAccessSeq", sv.sformatf(
                        "Status was %s when writing '%s[%0d-1]' through backdoor.",
                        str(status), mem.get_full_name(), k))

                status = []
                val = []
                await mem.read(status, k, val, UVM_FRONTDOOR, maps[j], self)
                status = status[0]
                val = val[0]
                if status != UVM_IS_OK:
                    uvm_error("UVMMemAccessSeq", sv.sformatf(
                        "Status was %s when reading \"%s[%0d]\" through map \"%s\".",
                        status.name(), mem.get_full_name(), k, maps[j].get_full_name()))
                else:
                    if mode == "WO":
                        if val != 0:
                           uvm_error("UVMMemAccessSeq", sv.sformatf(
                               "Front door \"%s[%0d]\" read back as 'h%h instead of 'h%h.",
                               mem.get_full_name(), k, val, 0))
                    else:
                        if val != exp:
                            uvm_error("UVMMemAccessSeq", sv.sformatf(
                                "Front door \"%s[%0d]\" read back as 'h%h instead of 'h%h.",
                                mem.get_full_name(), k, val, exp))
    #endclass: UVMMemSingleAccessSeq


uvm_object_utils(UVMMemSingleAccessSeq)

#//
#// class: UVMMemAccessSeq
#//
#// Verify the accessibility of all memories in a block
#// by executing the <UVMMemSingleAccessSeq> sequence on
#// every memory within it.
#//
#// If bit-type resource named
#// "NO_REG_TESTS", "NO_MEM_TESTS", or "NO_MEM_ACCESS_TEST"
#// in the "REG::" namespace
#// matches the full name of the block,
#// the block is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.get_full_name(),".*"},
#//|                            "NO_MEM_TESTS", 1, this);
#//


class UVMMemAccessSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))

    def __init__(self, name="UVMMemAccessSeq"):
        super().__init__(name)
        #   // Variable: mem_seq
        #   //
        #   // The sequence used to test one memory
        #   //
        self.mem_seq = None


    #   // Task: body
    #   //
    #   // Execute the Memory Access sequence.
    #   // Do not call directly. Use seq.start() instead.
    #   //
    
    async def body(self):
        model = self.model
        if model is None:
            uvm_error("UVMMemAccessSeq", "No register model specified to run sequence on")
            return

        uvm_info("STARTING_SEQ", "\n\nStarting " + self.get_name()
                + " sequence...\n", UVM_LOW)

        self.mem_seq = UVMMemSingleAccessSeq.type_id.create("single_mem_access_seq")

        await self.reset_blk(model)
        model.reset()

        await self.do_block(model)


    #   // Task: do_block
    #   //
    #   // Test all of the memories in a given ~block~
    #   //
    
    async def do_block(self, blk):

        if reg_test_off(blk, ["NO_REG_TESTS", "NO_MEM_TESTS", "NO_MEM_ACCESS_TEST"]):
            return

        # Iterate over all memories, checking accesses
        mems = []  # uvm_mem[$]
        blk.get_memories(mems, UVM_NO_HIER)
        for i in range(len(mems)):
            # Registers with some attributes are not to be tested
            if reg_test_off(mems[i], ["NO_REG_TESTS", "NO_MEM_TESTS",
                "NO_MEM_ACCESS_TEST"]):
                continue

            # Can only deal with memories with backdoor access
            if (mems[i].get_backdoor() is None and
                    not mems[i].has_hdl_path()):
                uvm_warning("UVMMemAccessSeq", sv.sformatf(
                    "Memory \"%s\" does not have a backdoor mechanism available",
                    mems[i].get_full_name()))
                continue

            self.mem_seq.mem = mems[i]
            await self.mem_seq.start(None, self)

        blks = []  # uvm_reg_block[$]

        blk.get_blocks(blks)
        for i in range(len(blks)):
            await self.do_block(blks[i])


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
        await Timer(1, "NS")



    #endclass: UVMMemAccessSeq

uvm_object_utils(UVMMemAccessSeq)
