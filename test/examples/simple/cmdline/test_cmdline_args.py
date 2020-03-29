#----------------------------------------------------------------------
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
from cocotb.triggers import Timer

from uvm import run_test, UVMTest, UVMComponent
from uvm.base.uvm_root import UVMRoot
from uvm.base.uvm_object_globals import *
from uvm.base.uvm_debug import uvm_debug, UVMDebug
from uvm.macros import (uvm_component_utils, uvm_fatal, uvm_error,
    uvm_info, uvm_component_utils_begin, uvm_component_utils_end,
    uvm_field_string, uvm_field_int)



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
        self.check_phase_ran = False

    def build_phase(self, phase):
        super().build_phase(phase)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(10000, 'ns')
        phase.drop_objection(self)


    def check_phase(self, phase):
        self.check_phase_ran = True
        if self.comp.verb_checked_build_phase is False:
            uvm_fatal("CmdLineTest", "No verb checked in my_comp")


uvm_component_utils(CmdLineTest)


class TestMaxQuitCount(CmdLineTest):

    def __init__(self, name="CmdLineTest", parent=None):
        super().__init__(name, parent)
        self.caught = False

    async def run_phase(self, phase):
        self.comp.set_config_int_test = True
        phase.raise_objection(self)
        await Timer(100, 'ns')
        for i in range(10):
            if i < 9:
                uvm_error("TestMaxQuitCountInfo", "Error " + str(i))
            else:
                # Need to catch this because max_quit_count reached
                try:
                    uvm_error("TestMaxQuitCountInfo", "Last Error " + str(i))
                except Exception as e:
                    uvm_info("TestMaxQuitCount_CAUGHT", "Exception: " + str(e),
                        UVM_NONE)
                    self.caught = True
        await Timer(100, 'ns')
        phase.drop_objection(self)


    def check_phase(self, phase):
        self.check_phase_ran = True
        if self.caught is False:
            uvm_fatal("TestMaxQuitCount TEST FAILED",
                "Did not catch the exception correctly")
        if self.comp.tag != 'matched_correctly':
            uvm_fatal("TestMaxQuitCount TEST FAILED",
                "+uvm_set_config_string did not match correctly")

uvm_component_utils(TestMaxQuitCount)


#------------------------------
# Sub-components for the tests
#------------------------------


class MyComponent(UVMComponent):
    """
    Sub-component created by the tests.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.verb_checked_build_phase = False
        self.old_rh = self.m_rh
        self.tag = "<not set>"
        self.hex_to_match = 0
        self.oct_to_match = 0
        self.dec_to_match = 0
        self.str_with_ws = "<not set>"
        self.set_config_int_test = False


    def build_phase(self, phase):
        # Need to be called, in order to trigger auto-config
        super().build_phase(phase)
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
        if self.set_config_int_test:
            if self.hex_to_match != 0x789:
                uvm_fatal("HEX_NUM_CONFIG_INT_FATAL",
                    "hex_to_match not auto-configured correctly")
            if self.oct_to_match != int('456', 8):
                uvm_fatal("OCT_NUM_CONFIG_INT_FATAL",
                    "oct_to_match not auto-configured correctly")
            if self.dec_to_match < 1000000000:
                uvm_fatal("DEC_NUM_CONFIG_INT_FATAL",
                    "dec_to_match not auto-configured correctly")

uvm_component_utils_begin(MyComponent)
uvm_field_string('tag')
uvm_field_string('str_with_ws')
uvm_field_int('hex_to_match')
uvm_field_int('oct_to_match')
uvm_field_int('dec_to_match')
uvm_component_utils_end(MyComponent)


@cocotb.test()
async def test_cmdline_args(dut):
    await run_test()
    await Timer(1001, 'ns')

    uvm_root = UVMRoot.get()
    test_top = uvm_root.find('uvm_test_top$')
    if test_top.check_phase_ran is False:
        raise Exception('*** TEST FAILED ***\nCheck phase did not run in test_top')
