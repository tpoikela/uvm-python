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
from ..uvm_reg_model import (UVM_FRONTDOOR, UVM_IS_OK, UVM_NO_HIER,
    UVM_STATUS_NAMES)
from ...macros import (uvm_info, uvm_error, uvm_object_utils)
from ...base.uvm_resource_db import UVMResourceDb
from ...base.sv import sv
from ...base.uvm_object_globals import UVM_LOW
from ...base.uvm_globals import uvm_zero_delay

#//------------------------------------------------------------------------------
#// Title: Memory Walking-Ones Test Sequences
#//
#// This section defines sequences for applying a "walking-ones"
#// algorithm on one or more memories.
#//------------------------------------------------------------------------------


#//------------------------------------------------------------------------------
#// Class: UVMMemSingleWalkSeq
#//
#// Runs the walking-ones algorithm on the memory given by the <mem> property,
#// which must be assigned prior to starting this sequence.
#//
#// If bit-type resource named
#// "NO_REG_TESTS", "NO_MEM_TESTS", or "NO_MEM_WALK_TEST"
#// in the "REG::" namespace
#// matches the full name of the memory,
#// the memory is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.mem0.get_full_name()},
#//|                            "NO_MEM_TESTS", 1, this);
#//
#// The walking ones algorithm is performed for each map in which the memory
#// is defined.
#//
#//| for (k = 0 thru memsize-1)
#//|   write addr=k data=~k
#//|   if (k > 0) {
#//|     read addr=k-1, expect data=~(k-1)
#//|     write addr=k-1 data=k-1
#//|   if (k == last addr)
#//|     read addr=k, expect data=~k
#//
#//------------------------------------------------------------------------------


class UVMMemSingleWalkSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))

    #   // Function: new
    #   //
    #   // Creates a new instance of the class with the given name.
    #
    def __init__(self, name="UVMMemWalkSeq"):
        super().__init__(name)
        #   // Variable: mem
        #   //
        #   // The memory to test; must be assigned prior to starting sequence.
        self.mem = None
    #   endfunction


    #   // Task: body
    #   //
    #   // Performs the walking-ones algorithm on each map of the memory
    #   // specified in <mem>.
    
    async def body(self):
        maps = []  # uvm_reg_map [$]
        n_bits = 0
        mem = self.mem

        if mem is None:
            uvm_error("UVMMemWalkSeq", "No memory specified to run sequence on")
            return

        # Memories with some attributes are not to be tested
        if (UVMResourceDb.get_by_name("REG::" + mem.get_full_name(),
            "NO_REG_TESTS", 0) is not None or
            UVMResourceDb.get_by_name("REG::" + mem.get_full_name(),
                "NO_MEM_TESTS", 0) is not None or
            UVMResourceDb.get_by_name("REG::" + mem.get_full_name(),
                "NO_MEM_WALK_TEST", 0) is not None):
            return

        n_bits = mem.get_n_bits()

        # Memories may be accessible from multiple physical interfaces (maps)
        mem.get_maps(maps)

        # Walk the memory via each map
        for j in range(len(maps)):
            status = 0
            val = 0
            exp = 0
            # v = 0

            # Only deal with RW memories
            if mem.get_access(maps[j]) != "RW":
                continue

            uvm_info("UVMMemWalkSeq", sv.sformatf("Walking memory %s (n_bits: %d) in map \"%s\"...",
                mem.get_full_name(), n_bits, maps[j].get_full_name()), UVM_LOW)

            # The walking process is, for address k:
            # - Write ~k
            # - Read k-1 and expect ~(k-1) if k > 0
            # - Write k-1 at k-1
            # - Read k and expect ~k if k == last address
            for k in range(mem.get_size()):
                status = []
                await mem.write(status, k, ~k, UVM_FRONTDOOR, maps[j], self)
                status = status[0]

                if status != UVM_IS_OK:
                    uvm_error("UVMMemWalkSeq", sv.sformatf(
                        "Status was %s when writing \"%s[%0d]\" through map \"%s\".",
                        status.name(), mem.get_full_name(), k, maps[j].get_full_name()))

                if k > 0:
                    status = []
                    val = []
                    await mem.read(status, k-1, val, UVM_FRONTDOOR, maps[j], self)
                    status = status[0]
                    if status != UVM_IS_OK:
                       uvm_error("UVMMemWalkSeq", sv.sformatf(
                           "Status was %s when reading \"%s[%0d]\" through map \"%s\".",
                           UVM_STATUS_NAMES[status], mem.get_full_name(), k, maps[j].get_full_name()))
                    else:
                        exp = ~(k-1) & ((1 << n_bits)-1)
                        val = val[0]
                        if val != exp:
                            uvm_error("UVMMemWalkSeq",
                                sv.sformatf("\"%s[%0d-1]\" read back as 'h%h instead of 'h%h.",
                                mem.get_full_name(), k, val, exp))

                    status = []
                    await mem.write(status, k-1, k-1, UVM_FRONTDOOR, maps[j], self)
                    status = status[0]
                    if status != UVM_IS_OK:
                        uvm_error("UVMMemWalkSeq", sv.sformatf(
                            "Status was %s when writing \"%s[%0d-1]\" through map \"%s\".",
                            UVM_STATUS_NAMES[status], mem.get_full_name(), k, maps[j].get_full_name()))

                if k == mem.get_size() - 1:
                    status = []
                    val = []
                    await mem.read(status, k, val, UVM_FRONTDOOR, maps[j], self)
                    status = status[0]
                    if status != UVM_IS_OK:
                        uvm_error("UVMMemWalkSeq", sv.sformatf(
                            "Status was %s when reading \"%s[%0d]\" through map \"%s\".",
                            UVM_STATUS_NAMES[status], mem.get_full_name(), k, maps[j].get_full_name()))
                    else:
                        exp = ~(k) & ((1<<n_bits)-1)
                        val = val[0]
                        if val != exp:
                            uvm_error("UVMMemWalkSeq", sv.sformatf("\"%s[%0d]\" read back as 'h%h instead of 'h%h.",
                                mem.get_full_name(), k, val, exp))


uvm_object_utils(UVMMemSingleWalkSeq)


#//------------------------------------------------------------------------------
#// Class: UVMMemWalkSeq
#//
#// Verifies the all memories in a block
#// by executing the <UVMMemSingleWalkSeq> sequence on
#// every memory within it.
#//
#// If bit-type resource named
#// "NO_REG_TESTS", "NO_MEM_TESTS", or "NO_MEM_WALK_TEST"
#// in the "REG::" namespace
#// matches the full name of the block,
#// the block is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.get_full_name(),".*"},
#//|                            "NO_MEM_TESTS", 1, this);
#//
#//------------------------------------------------------------------------------


class UVMMemWalkSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))


    def __init__(self, name="UVMMemWalkSeq"):
        super().__init__(name)
        #   // Variable: model
        #   //
        #   // The block to be tested. Declared in the base class.
        #   //
        #   //| uvm_reg_block model;
        self.model = None
        #   // Variable: mem_seq
        #   //
        #   // The sequence used to test one memory
        #   //
        self.mem_seq = None


    #
    #   // Task: body
    #   //
    #   // Executes the mem walk sequence, one block at a time.
    #   // Do not call directly. Use seq.start() instead.
    #   //
    
    async def body(self):
        if self.model is None:
            uvm_error("UVMMemWalkSeq", "No register model specified to run sequence on")
            return

        uvm_info("STARTING_SEQ","\n\nStarting " + self.get_name() + " sequence...\n",UVM_LOW)

        self.mem_seq = UVMMemSingleWalkSeq.type_id.create("single_mem_walk_seq")

        await self.reset_blk(self.model)
        self.model.reset()
        await self.do_block(self.model)


    #   // Task: do_block
    #   //
    #   // Test all of the memories in a given ~block~
    #   //
    
    async def do_block(self, blk):
        mems = []  # uvm_mem[$]

        if (UVMResourceDb.get_by_name("REG::" + blk.get_full_name(),
            "NO_REG_TESTS", 0) is not None or
            UVMResourceDb.get_by_name("REG::" + blk.get_full_name(),
                "NO_MEM_TESTS", 0) is not None or
            UVMResourceDb.get_by_name("REG::" + blk.get_full_name(),
                "NO_MEM_ACCESS_TEST", 0) is not None):
            return

        # Iterate over all memories, checking accesses
        blk.get_memories(mems, UVM_NO_HIER)
        for i in range(len(mems)):
            # Memories with some attributes are not to be tested
            if (UVMResourceDb.get_by_name("REG::" + mems[i].get_full_name(),
                "NO_REG_TESTS", 0) is not None or
                UVMResourceDb.get_by_name("REG::" + mems[i].get_full_name(),
                    "NO_MEM_TESTS", 0) is not None or
                UVMResourceDb.get_by_name("REG::" + mems[i].get_full_name(),
                    "NO_MEM_WALK_TEST", 0) is not None):
                continue
            self.mem_seq.mem = mems[i]
            await self.mem_seq.start(None, self)

        blks = []  # uvm_reg_block [$]
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
        await uvm_zero_delay()


uvm_object_utils(UVMMemWalkSeq)
