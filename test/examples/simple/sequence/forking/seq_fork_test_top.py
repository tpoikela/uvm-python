#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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
from cocotb.triggers import Timer, Combine
from cocotb.utils import get_sim_time

from uvm.base.uvm_debug import UVMDebug
from uvm.base.sv import sv
from uvm.base.uvm_globals import run_test, uvm_sim_time
from uvm.base.uvm_object_globals import UVM_MEDIUM, UVM_HIGH
from uvm.base.uvm_phase import UVMPhase
from uvm.seq import UVMSequence, UVMSequenceItem, UVMSequencer
from uvm.macros import *
from uvm.comps import UVMDriver, UVMEnv

NUM_SEQS = 16
NUM_LOOPS = 1

start_times = {}
finish_times = {}


class MyReq(UVMSequenceItem):

    def __init__(self, name="my_seq_item"):
        super().__init__(name)


uvm_object_utils(MyReq)


class my_driver(UVMDriver):

    def __init__(self, name, parent):
        UVMDriver.__init__(self, name, parent)
        self.data_array = [0] * 512  # int data_array[511:0]
        self.nitems = 0
        self.recording_detail = UVM_HIGH

    
    async def main_phase(self, phase):
        # req = None
        # rsp = None

        while True:
            uvm_info("DRIVER", "my_driver getting the req now..",
                UVM_MEDIUM)
            qreq = []
            await self.seq_item_port.get_next_item(qreq)
            async def fork_task():
                await Timer(100, "NS")
            cocotb.fork(fork_task())
            self.nitems += 1
            self.seq_item_port.item_done()
            #self.end_tr(req)

uvm_component_utils(my_driver)


class sequenceA(UVMSequence):

    g_my_id = 1

    def __init__(self, name=""):
        UVMSequence.__init__(self, name)
        self.my_id = sequenceA.g_my_id
        sequenceA.g_my_id += 1
        self.id = -1

    async def body(self):
        uvm_info("sequenceA", "Starting sequence with ID {}".format(self.id), UVM_MEDIUM)
        req = MyReq()
        start_times[self.id] = uvm_sim_time()
        await self.start_item(req)
        await self.finish_item(req)
        finish_times[self.id] = uvm_sim_time()

uvm_object_utils(sequenceA)


class env(UVMEnv):


    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.drv = None
        self.sqr = None
        self.error = False

    def build_phase(self, phase):
        super().build_phase(phase)
        self.sqr = UVMSequencer("sequencer", self)

        # create and connect driver
        self.drv = my_driver("my_driver", self)
        uvm_info("ENV", "Connecting ports now here", UVM_MEDIUM)
        self.drv.seq_item_port.connect(self.sqr.seq_item_export)

    
    async def main_phase(self, phase):
        phase.raise_objection(self)
        uvm_info("ENV", 'Before 1000 x await Timer(0)', UVM_LOW)
        for _ in range(1000):
            await Timer(0)
        uvm_info("ENV", 'main_phase logic starting', UVM_LOW)
        fork_procs = []
        for i in range(NUM_SEQS):
            the_sequence = sequenceA("sequence_" + str(i))
            the_sequence.id = i
            fork_procs.append(cocotb.fork(the_sequence.start(self.sqr, None)))
        sv.fork_join(fork_procs)
        # join_list = list(map(lambda t: t.join(), fork_procs))
        await Timer(100, "NS")
        phase.drop_objection(self)

    def check_phase(self, phase):
        if self.drv.nitems != (NUM_SEQS * NUM_LOOPS):
            self.error = True
            self.uvm_report_error('env', sv.sformatf("nitems: Exp %0d, Got %0d",
                NUM_SEQS * NUM_LOOPS, self.drv.nitems))

    def report_phase(self, phase):
        rpt = "Start times:\n" + str(start_times)
        rpt += "\nFinish times:\n" + str(finish_times)
        uvm_info("ENV", rpt, UVM_LOW)


uvm_component_utils(env)


@cocotb.test()
async def seq_fork_module_top(dut):
    print("Using simulator " + cocotb.SIM_NAME)
    UVMPhase.m_phase_trace = True
    e = env("env_name", parent=None)
    uvm_info("top","In top initial block", UVM_MEDIUM)
    await run_test()
    sim_time = sim_time = get_sim_time('ns')

    if sim_time == 0:
        raise Exception('Sim time has not progressed')
    else:
        if sim_time < 50.0:
            msg = "Exp: > 50, got: " + str(sim_time)
            raise Exception('Wrong sim time at the end: ' + msg)
    if e.error is True:
        raise Exception('Env had errors')
