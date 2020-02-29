#//
#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
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

from uvm.comps.uvm_test import UVMTest
from uvm.macros import *
from uvm import (run_test, uvm_debug, UVMDebug, UVMPhase, UVMReportCatcher,
    THROW, UVM_FATAL, UVM_INFO, UVMReportCb, UVMCallbacksBase)

from tb_timer import *
from tb_env import tb_env

UVMDebug.DEBUG = False
UVMPhase.m_phase_trace = False
UVMCallbacksBase.m_tracing = True


class timeout_catcher(UVMReportCatcher):
    def __init__(self, name="timeout_catcher"):
        super().__init__(name)
        self.num_fatals = 0

    def catch(self):
        uvm_info("CATCHER_ACTIVE", "Catcher was activated", UVM_LOW)
        if self.get_severity() == UVM_FATAL and self.get_id() == "TIMEOUT":
            self.set_severity(UVM_INFO)
            self.num_fatals += 1
        return THROW


class test_comp(UVMTest):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.timer = tb_timer("global_timer", None)
        self.catcher = timeout_catcher()
        UVMReportCb.add(None, self.catcher)

    
    async def pre_main_phase(self, phase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        phase.drop_objection(self)

    
    async def main_phase(self, phase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        # Will cause a time-out
        # because we forgot to drop the objection
        phase.drop_objection(self)


    
    async def shutdown_phase(self, phase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        phase.drop_objection(self)


uvm_component_utils(test_comp)


@cocotb.test()
async def initial_begin(dut):
    env = tb_env("env")
    await run_test("test_comp")
