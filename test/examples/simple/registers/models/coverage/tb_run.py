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
from uvm import (UVMTest, sv, uvm_fatal, uvm_top,
    UVMRegBitBashSeq, UVMMemWalkSeq,
    UVM_CVR_ALL, UVM_FINISHED, uvm_info, UVM_LOW,
    UVMReg, UVMCoreService, run_test)

from tb_env import tb_env


class tb_test(UVMTest):

    def __init__(self, name="tb_test", parent=None):
        super().__init__(name, parent)

    def build_phase(self, phase):
        super().build_phase(phase)
        self.env = tb_env("env")

    @cocotb.coroutine
    def run_phase(self, phase):
        env = self.env
        phase.raise_objection(self)

        env.regmodel.reset()
        env.regmodel.set_coverage(UVM_CVR_ALL)  # cast to 'void' removed

        seq = UVMRegBitBashSeq.type_id.create("seq")
        seq.model = env.regmodel
        yield seq.start(env.bus.sqr)
        yield seq.wait_for_sequence_state(UVM_FINISHED)

        seq = UVMMemWalkSeq.type_id.create("seq")
        seq.model = env.regmodel
        yield seq.start(env.bus.sqr)
        yield seq.wait_for_sequence_state(UVM_FINISHED)


        uvm_info("Test", "Generating and uploading 100 configurations...", UVM_LOW)

        for _ in range(100):
            status = 0
            #env.regmodel.randomize_with({Ra.F2.value == Rb.F2.value}) # TODO
            env.regmodel.randomize()
            env.regmodel.update(status)
            env.regmodel.sample_values()

        phase.drop_objection(self)


@cocotb.test()
def initial_begin(dut):
    cs_ = UVMCoreService.get()

    #   tb_env env
    #   tb_test test
    #   uvm_report_server svr

    UVMReg.include_coverage("*", UVM_CVR_ALL)

    test = tb_test("test")

    svr = cs_.get_report_server()
    svr.set_max_quit_count(10)

    yield run_test()
