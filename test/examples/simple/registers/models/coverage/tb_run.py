#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
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
from cocotb.triggers import FallingEdge
from cocotb.clock import Clock

from uvm import (UVMTest, uvm_top,
    UVMRegBitBashSeq, UVMMemWalkSeq,
    UVM_CVR_ALL, UVM_FINISHED, uvm_info, UVM_LOW,
    UVMReg, UVMCoreService, run_test, UVMConfigDb)

from tb_env import tb_env
from cocotb_coverage.coverage import coverage_db


class tb_test(UVMTest):

    def __init__(self, name="tb_test", parent=None):
        super().__init__(name, parent)
        self.dut = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.env = tb_env("env")

    
    async def run_phase(self, phase):
        env = self.env
        phase.raise_objection(self)

        env.regmodel.reset()
        env.regmodel.set_coverage(UVM_CVR_ALL)  # cast to 'void' removed

        self.dut.rst <= 0
        for _ in range(3):
            await FallingEdge(self.dut.clk)
        self.dut.rst <= 1
        await FallingEdge(self.dut.clk)

        seq = UVMRegBitBashSeq.type_id.create("reg_test_seq")
        seq.model = env.regmodel
        await seq.start(env.bus.sqr)
        await seq.wait_for_sequence_state(UVM_FINISHED)

        seq = UVMMemWalkSeq.type_id.create("memory_test_seq")
        seq.model = env.regmodel
        await seq.start(env.bus.sqr)
        await seq.wait_for_sequence_state(UVM_FINISHED)


        uvm_info("Test", "Generating and uploading 5 configurations...", UVM_LOW)

        for _ in range(5):
            status = 0
            #env.regmodel.randomize_with({Ra.F2.value == Rb.F2.value}) # TODO
            env.regmodel.randomize()
            status = []
            await env.regmodel.update(status)
            env.regmodel.sample_values()

        phase.drop_objection(self)


@cocotb.test()
async def initial_begin(dut):
    cs_ = UVMCoreService.get()

    UVMReg.include_coverage("*", UVM_CVR_ALL)
    c = Clock(dut.clk, 10, 'ns')

    test = tb_test("test")
    test.dut = dut

    svr = cs_.get_report_server()
    svr.set_max_quit_count(10)
    UVMConfigDb.set(None, "", "dut", dut)

    cocotb.fork(c.start())

    await run_test()

    def my_log(msg):
        uvm_info("COV_RPT", msg, UVM_LOW)

    coverage_db.report_coverage(my_log, bins=False)
    coverage_db.export_to_xml("results_coverage.xml")
