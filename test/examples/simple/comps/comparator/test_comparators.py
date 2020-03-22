
#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
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
#----------------------------------------------------------------------

#
# About: 'ep' event poll
# This test is a simple test that will cover the creation of two uvm_events using the uvm_event_pool.
# Then use the uvm_event_pool methods to print those objects.
#
# For a full documentation of the uvm_event and uvm_event_pool, check the files:
#	- uvm/src/base/uvm_event.svh
#	- uvm/src/base/uvm_event.sv
#

import cocotb
from cocotb.triggers import Timer

from uvm import (run_test, UVMTest, UVMSequenceItem, UVMAnalysisPort,
    UVMCoreService, UVM_ERROR, UVMClassComp)
from uvm.comps.uvm_algorithmic_comparator import UVMAlgorithmicComparator

from uvm.macros import (uvm_error, uvm_component_utils, uvm_object_utils,
    uvm_object_utils_begin, uvm_object_utils_end, uvm_field_int)

class Packet(UVMSequenceItem):

    def __init__(self, name):
        super().__init__(name)
        self.addr = 0x0
        self.data = 0x0

uvm_object_utils_begin(Packet)
uvm_field_int('addr')
uvm_field_int('data')
uvm_object_utils_end(Packet)


class PacketTransformer():

    def transform(self, pkt):
        return pkt


class ComparatorTest(UVMTest):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)

    def build_phase(self, phase):
        super().build_phase(phase)
        trans = PacketTransformer()
        self.compar = UVMAlgorithmicComparator("comparator", self, trans)
        self.compar.comp.CompType = UVMClassComp

        self.ap_before = UVMAnalysisPort("ap_before", self)
        self.ap_after = UVMAnalysisPort("ap_after", self)

    def connect_phase(self, phase):
        self.ap_before.connect(self.compar.before_export)
        self.ap_after.connect(self.compar.after_export)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(10, "NS")
        self.ap_before.write(Packet('p_in'))
        self.ap_after.write(Packet('p_out'))

        await Timer(10, "NS")
        pkt_err = Packet('p_err')
        pkt_err.data = 0x1234
        self.ap_before.write(Packet('p_in2'))
        self.ap_after.write(pkt_err)
        await Timer(100, "NS")
        phase.drop_objection(self)


uvm_component_utils(ComparatorTest)


@cocotb.test()
async def test_comparators(dut):
    cs = UVMCoreService.get()
    svr = cs.get_report_server()
    await run_test()

    num_errors = svr.get_severity_count(UVM_ERROR)
    if num_errors != 1:
        raise Exception("There were {} uvm_errors, exp 1".format(num_errors))
