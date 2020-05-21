#
#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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
#//----------------------------------------------------------------------

# About: UVM Reporting methods
# This example will illustrate the usage of UVM reporting functions,
# and mainly focusing on the fine-tuning of reporting

# To get more details about the reporting related methods, check the file:
#   - uvm/src/base/uvm_report_object.py
#   - uvm/src/base/uvm_component.py  - Hierarchical reporting methods

import cocotb
from cocotb.triggers import Timer

from uvm.macros import uvm_component_utils, uvm_info
from uvm import (UVMCoreService, UVMComponent, UVM_MEDIUM, sv, UVMTest,
    run_test, UVM_LOW, UVM_LOG, UVM_DISPLAY, UVM_INFO, UVMReportCatcher)


class my_child(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.tag = "MY_CHILD"

    async def main_phase(self, phase):
        uvm_info(self.tag, 'main_phase started in child', UVM_MEDIUM)

    def get_packet(self):
        uvm_info("PKTGEN", sv.sformatf("Getting a packet from %s (%s)",
            self.get_full_name(), self.get_type_name()), UVM_MEDIUM)
        return super().get_packet()


# Use the macro in a class to implement factory registration along with other
# utilities (create, get_type_name). To just do factory registration, use the
# macro `uvm_object_registry(mygen,"mygen")
uvm_component_utils(my_child)


class my_top_test(UVMTest):

    def __init__(self, name="my_top_test", parent=None):
        super().__init__(name, parent)
        self.tag = 'MY_TOP_TEST'

    def build_phase(self, phase):
        super().build_phase(phase)
        self.child = my_child.type_id.create('my_child', self)

    def connect_phase(self, phase):
        self.def_file = open('uvm_master_log.log', 'w')
        self.set_report_default_file_hier(self.def_file)
        self.set_report_severity_action_hier(UVM_INFO, UVM_LOG | UVM_DISPLAY)

    async def main_phase(self, phase):
        phase.raise_objection(self, 'main_phase_started')
        uvm_info(self.tag, 'main_phase started', UVM_MEDIUM)
        await Timer(10, 'NS')
        phase.drop_objection(self, 'main_phase_ending')

    def final_phase(self, phase):
        #uvm_info(self.tag, "Closing the file handle now", UVM_LOW)
        self.def_file.close()
        uvm_info(self.tag, "Closing the file handle now", UVM_LOW)


# Use the macro in after the class to implement factory registration along with other
# utilities (create, get_type_name).
uvm_component_utils(my_top_test)


@cocotb.test()
async def module_top(dut):
    # cs_ = UVMCoreService.get()  # type: UVMCoreService
    # uvm_root = cs_.get_root()
    # factory = cs_.get_factory()
    # factory.print_factory(1)

    # If a string is used to run_test, run_test will used the string based factory
    # create method to create an object of the desired type.
    await run_test("my_top_test")
