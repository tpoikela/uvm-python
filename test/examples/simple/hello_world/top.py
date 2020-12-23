#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela (tpoikela)
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

import cocotb
from cocotb.triggers import Timer
from uvm.base import UVMComponent, UVMPhase, uvm_top
#from uvm.base.uvm_root import uvm_top
from uvm.tlm1.uvm_tlm_fifos import UVMTLMFIFO
from uvm.macros import *
from producer import producer
from consumer import consumer

class top(UVMComponent):
    #  producer #(packet) p1
    #  producer #(packet) p2
    #  uvm_tlm_fifo #(packet) f
    #  consumer #(packet) c

    def __init__(self, name, parent=None):
        UVMComponent.__init__(self, name, parent)
        UVMPhase.m_phase_trace = True
        self.p1 = producer("producer1", self)
        self.p2 = producer("producer2", self)
        self.f = UVMTLMFIFO("fifo", self)
        self.c = consumer("consumer", self)

        # Create connections between components
        self.p1.out.connect(self.c.input)
        self.p2.out.connect(self.f.blocking_put_export)
        self.c.out.connect(self.f.get_export)
        self.error = False

    def end_of_elaboration_phase(self, phase):
        uvm_top.print_topology()

    
    async def run_phase(self, phase):
        print("top run_Phase started XYZ")
        phase.raise_objection(self)
        await Timer(1000, "NS")
        phase.drop_objection(self)

    def check_phase(self, phase):
        if self.c.count == 0:
            self.error = True
            self.uvm_report_error("COUNT_ERR", "Count was 0")

uvm_component_utils(top)

class top2(UVMComponent):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.prods = []
        self.prods2 = []
        self.cons = []
        self.fifos = []
        self.n = 128

        for i in range(self.n):
            self.prods.append(producer("producer" + str(i), self))
            self.prods2.append(producer("producer2_" + str(i), self))
            self.cons.append(consumer("consumer" + str(i), self))
            self.fifos.append(UVMTLMFIFO("fifo" + str(i), self))
        for i in range(self.n):
            self.prods[i].out.connect(self.cons[i].input)
            self.prods2[i].out.connect(self.fifos[i].blocking_put_export)
            self.cons[i].out.connect(self.fifos[i].get_export)

    async def run_phase(self, phase):
        print("top2 run_Phase started XYZ")
        phase.raise_objection(self)
        await Timer(1000, "NS")
        phase.drop_objection(self)

    def check_phase(self, phase):
        for i in range(self.n):
            if self.cons[i].count == 0:
                self.error = True
                self.uvm_report_error("COUNT_ERR", "Count was 0")

uvm_component_utils(top2)
