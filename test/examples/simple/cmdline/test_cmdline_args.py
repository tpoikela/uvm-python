#----------------------------------------------------------------------
#   Copyright 2007-2010 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010-2011 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
# ----------------------------------------------------------------------

import cocotb
from cocotb.utils import get_sim_time
from cocotb.triggers import Timer

from uvm import run_test, UVMTest, UVMComponent
from uvm.base.uvm_object_globals import *
from uvm.base.uvm_debug import uvm_debug, UVMDebug
from uvm.macros import uvm_component_utils, uvm_fatal


class DummyTest(UVMTest):
    def __init__(self, name="DummyTest", parent=None):
        super().__init__(name, parent)
        uvm_fatal("DUMM_TEST", "Tests fails if this test is created")


uvm_component_utils(DummyTest)


class CmdLineTest(UVMTest):

    def __init__(self, name="CmdLineTest", parent=None):
        super().__init__(name, parent)
        self.comp = None
        self.comp = MyComponent("my_comp", self)

    def build_phase(self, phase):
        super().build_phase(phase)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(10000, 'ns')
        phase.drop_objection(self)


    def check_phase(self, phase):
        if self.comp.verb_checked_build_phase is False:
            uvm_fatal("CmdLineTest", "No verb checked in my_comp")


uvm_component_utils(CmdLineTest)


class MyComponent(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.verb_checked_build_phase = False
        self.old_rh = self.m_rh


    def build_phase(self, phase):
        if self.uvm_report_enabled(UVM_DEBUG):
            uvm_fatal("MyComponent", "Verbosity UVM_DEBUG must not be enabled")

        if not self.uvm_report_enabled(UVM_HIGH):
            uvm_fatal("MyComponent", "Verbosity not UVM_HIGH in build_Phase")
        self.verb_checked_build_phase = True

    
    
    async def run_phase(self, phase):
        self.uvm_report_info("component", "before raising objection", UVM_MEDIUM)
        phase.raise_objection(self)

        if self.uvm_report_enabled(UVM_DEBUG):
            uvm_fatal("MyComponent", "Verbosity UVM_DEBUG must not be enabled")
        #UVMDebug.DEBUG = False
        self.uvm_report_info("component", "after raising objection", UVM_MEDIUM)
        await Timer(1, 'ns')
        uvm_debug(self, 'run_phase', "Objection raised run_phase " +
                self.get_name())
        await Timer(2, 'ns')
        self.uvm_report_info("component", "hello out there!", UVM_MEDIUM)
        await Timer(1005, 'ns')
        assert(self.m_rh is self.old_rh)
        self.uvm_report_info("component", "hello after 1005ns!", UVM_HIGH)
        # verb_level = self.get_report_verbosity_level()

        if not self.uvm_report_enabled(UVM_DEBUG):
            uvm_fatal("MyComponent", "Verbosity UVM_DEBUG must be enabled after 1000ns")
        self.uvm_report_info("component", "finishing up!", UVM_MEDIUM)
        self.uvm_report_fatal("SUPPRESS_FATAL",
            "Should not give FATAL due to cmdline arg +uvm_set_action")
        phase.drop_objection(self)

    def check_phase(self, phase):
        uvm_fatal("FAT2WARN", "Severity should change UVM_FATAL->UVM_WARN")
# uvm_component_utils(MyComponent)


@cocotb.test()
async def test_cmdline_args(dut):
    await run_test()
    await Timer(1001, 'ns')
