#//
#// -------------------------------------------------------------
#//    Copyright 2004-2008 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2013 Cadence Design Systems, Inc.
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

Title: Register Access Test Sequences

This section defines sequences that test DUT register access via the
available frontdoor and backdoor paths defined in the provided register
model.

"""

from cocotb.triggers import Timer

from .uvm_mem_access_seq import UVMMemAccessSeq
from ..uvm_reg_model import *
from ..uvm_reg_map import UVMRegMap
from ..uvm_reg_sequence import UVMRegSequence
from ...macros import uvm_object_utils, uvm_error, uvm_info, uvm_warning
from ...base import UVMResourceDb, UVM_LOW, uvm_zero_delay
from ...base.uvm_globals import uvm_report_info


#//------------------------------------------------------------------------------
#//
#// Class: UVMRegSingleAccessSeq
#//
#// Verify the accessibility of a register
#// by writing through its default address map
#// then reading it via the backdoor, then reversing the process,
#// making sure that the resulting value matches the mirrored value.
#//
#// If bit-type resource named
#// "NO_REG_TESTS" or "NO_REG_ACCESS_TEST"
#// in the "REG::" namespace
#// matches the full name of the register,
#// the register is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.r0.get_full_name()},
#//|                            "NO_REG_TESTS", 1, this);
#//
#// Registers without an available backdoor or
#// that contain read-only fields only,
#// or fields with unknown access policies
#// cannot be tested.
#//
#// The DUT should be idle and not modify any register during this test.
#//
#//------------------------------------------------------------------------------


class UVMRegSingleAccessSeq(UVMRegSequence):

    def __init__(self, name="UVMRegSingleAccessSeq"):
        super().__init__(name)
        #   // Variable: rg
        #   // The register to be tested
        self.reg = None



    async def body(self):
        maps = []  # uvm_reg_map[$]
        rg = self.rg

        if rg is None:
            uvm_error("UVMRegAccessSeq", "No register specified to run sequence on")
            return


        # Registers with some attributes are not to be tested
        if (UVMResourceDb.get_by_name("REG::" + rg.get_full_name(),
            "NO_REG_TESTS", 0) is not None or
            UVMResourceDb.get_by_name("REG::" + rg.get_full_name(),
                "NO_REG_ACCESS_TEST", 0) is not None):
            return

        # Can only deal with registers with backdoor access
        if (rg.get_backdoor() is None and not rg.has_hdl_path()):
            uvm_error("UVMRegAccessSeq", ("Register '" + rg.get_full_name()
                + "' does not have a backdoor mechanism available"))
            return


        # Registers may be accessible from multiple physical interfaces (maps)
        rg.get_maps(maps)

        # Cannot test access if register contains RO or OTHER fields

        fields = []  # uvm_reg_field[$]
        rg.get_fields(fields)
        for k in range(len(maps)):
            ro = 0
            for j in range(len(fields)):
                if fields[j].get_access(maps[k]) == "RO":
                    ro += 1

                if not fields[j].is_known_access(maps[k]):
                    uvm_warning("UVMRegAccessSeq", ("Register '" + rg.get_full_name()
                        + "' has field with unknown access type '"
                        + fields[j].get_access(maps[k]) + "', skipping"))
                    return

            if ro == len(fields):
                uvm_warning("UVMRegAccessSeq", ("Register '" + rg.get_full_name()
                    + "' has only RO fields in map " + maps[k].get_full_name() + ", skipping"))
                return



        # Access each register:
        # - Write complement of reset value via front door
        # - Read value via backdoor and compare against mirror
        # - Write reset value via backdoor
        # - Read via front door and compare against mirror

        for j in range(len(maps)):
            status = 0
            v = 0
            exp = 0

            uvm_info("UVMRegAccessSeq", ("Verifying access of register '"
                + rg.get_full_name() + "' in map '" +  maps[j].get_full_name()
                + "' ..."), UVM_LOW)

            v = rg.get()
            status = []
            await rg.write(status, ~v, UVM_FRONTDOOR, maps[j], self)
            status = status[0]

            if status != UVM_IS_OK:
                uvm_error("UVMRegAccessSeq", ("Status was '" + status.name()
                   + "' when writing '" + rg.get_full_name()
                   + "' through map '" + maps[j].get_full_name() + "'"))
            await Timer(1, "NS")  # tpoikela: Original UVM has #1

            status = []
            await rg.mirror(status, UVM_CHECK, UVM_BACKDOOR, UVMRegMap.backdoor(), self)
            status = status[0]
            if status != UVM_IS_OK:
                uvm_error("UVMRegAccessSeq", ("Status was '" + status.name()
                                    + "' when reading reset value of register '"
                                    + rg.get_full_name() +  "' through backdoor"))

            status = []
            await rg.write(status, v, UVM_BACKDOOR, maps[j], self)
            status = status[0]
            if status != UVM_IS_OK:
                uvm_error("UVMRegAccessSeq", ("Status was '" + status.name()
                   + "' when writing '" + rg.get_full_name()
                   + "' through backdoor"))

            status = []
            await rg.mirror(status, UVM_CHECK, UVM_FRONTDOOR, maps[j], self)
            status = status[0]
            if status != UVM_IS_OK:
                uvm_error("UVMRegAccessSeq", ("Status was '" + status.name()
                   + "' when reading reset value of register '"
                   + rg.get_full_name() + "' through map '"
                   + maps[j].get_full_name() + "'"))


uvm_object_utils(UVMRegSingleAccessSeq)


#//------------------------------------------------------------------------------
#//
#// Class: UVMRegAccessSeq
#//
#// Verify the accessibility of all registers in a block
#// by executing the <UVMRegSingleAccessSeq> sequence on
#// every register within it.
#//
#// If bit-type resource named
#// "NO_REG_TESTS" or "NO_REG_ACCESS_TEST"
#// in the "REG::" namespace
#// matches the full name of the block,
#// the block is not tested.
#//
#//| uvm_resource_db#(bit)::set({"REG::",regmodel.blk.get_full_name(),".*"},
#//|                            "NO_REG_TESTS", 1, this);
#//
#//------------------------------------------------------------------------------


class UVMRegAccessSeq(UVMRegSequence):


    def __init__(self, name="UVMRegAccessSeq"):
        super().__init__(name)
        #   // Variable: model
        #   //
        #   // The block to be tested. Declared in the base class.
        #   //
        #   //| uvm_reg_block model;

        #   // Variable: reg_seq
        #   //
        #   // The sequence used to test one register
        #   //
        self.reg_seq = None



    #   // Task: body
    #   //
    #   // Executes the Register Access sequence.
    #   // Do not call directly. Use seq.start() instead.
    #   //
    async def body(self):
        model = self.model

        if model is None:
            uvm_error("UVMRegAccessSeq", "No register model specified to run sequence on")
            return


        uvm_info("STARTING_SEQ","\n\nStarting " + self.get_name() + " sequence...\n", UVM_LOW)
        self.reg_seq = UVMRegSingleAccessSeq.type_id.create("single_reg_access_seq")
        await self.reset_blk(model)
        model.reset()
        await self.do_block(model)


    #   // Task: do_block
    #   //
    #   // Test all of the registers in a block
    #   //
    async def do_block(self, blk):
        #      uvm_reg regs[$]
        regs = []

        if reg_test_off(blk, "NO_REG_TESTS") or reg_test_off(blk,
                "NO_REG_ACCESS_TEST"):
            return

        # Iterate over all registers, checking accesses
        blk.get_registers(regs, UVM_NO_HIER)
        for i in range(len(regs)):
            # Registers with some attributes are not to be tested
            if reg_test_off(regs[i], "NO_REG_TESTS") or reg_test_off(regs[i],
                    "NO_REG_ACCESS_TEST"):
                continue

            # Can only deal with registers with backdoor access
            if (regs[i].get_backdoor() is None and not regs[i].has_hdl_path()):
                uvm_warning("UVMRegAccessSeq", "Register '" + regs[i].get_full_name()
                       + "' does not have a backdoor mechanism available")
                continue

            self.reg_seq.rg = regs[i]
            await self.reg_seq.start(None,self)

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
        await uvm_zero_delay()


uvm_object_utils(UVMRegAccessSeq)



class UVMRegMemAccessSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))
    """
    Class: UVMRegMemAccessSeq

    Verify the accessibility of all registers and memories in a block
    by executing the `UVMRegAccessSeq` and
    `UVMMemAccessSeq` sequence respectively on every register
    and memory within it.

    Blocks and registers with the NO_REG_TESTS or
    the NO_REG_ACCESS_TEST attribute are not verified.
    """


    def __init__(self, name="UVMRegMemAccessSeq"):
        super().__init__(name)



    async def body(self):
        model = self.model

        if model is None:
            uvm_error("UVMRegMemAccessSeq", "Register model handle is None")
            return

        uvm_report_info("STARTING_SEQ",
            "\n\nStarting " + self.get_name() + " sequence...\n", UVM_LOW)

        if reg_test_on(model, "NO_REG_TESTS") and reg_test_on(model,
                "NO_REG_ACCESS_TEST"):
            sub_seq = UVMRegAccessSeq("reg_access_seq")
            await self.reset_blk(model)
            model.reset()
            sub_seq.model = model
            await sub_seq.start(None,self)

        if reg_test_on(model, "NO_MEM_ACCESS_TEST"):
            sub_seq = UVMMemAccessSeq("mem_access_seq")
            await self.reset_blk(model)
            model.reset()
            sub_seq.model = model
            await sub_seq.start(None,self)


    #   // Any additional steps required to reset the block
    #   // and make it accessibl
    async def reset_blk(self, blk):
        await uvm_zero_delay()


uvm_object_utils(UVMRegMemAccessSeq)
