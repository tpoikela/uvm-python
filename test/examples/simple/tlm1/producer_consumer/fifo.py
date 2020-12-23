#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
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


# About: producer_consumer
# This test is the basic simple to illustrates how to create a producer and
# consumer which are completely independent and connecting them using a uvm_tlm_fifo channel
#
# Walk through the test:
#
# Two processes *producer* and *consumer* will use uvm_blocking_put port and
# uvm_blocking_get port, to transfer an integer from the producer to the
# consumer through fifo exports at the connection function of an environment
# class
#
# Note that unlike in SystemVerilog, in Python we use arrays instead of ref
# parameters to obtain values from  blocking (coroutine) functions.


import cocotb
from cocotb.triggers import Timer

from uvm.tlm1 import *
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_globals import run_test
from uvm.base.uvm_object_globals import UVM_DEBUG, UVM_MEDIUM
from uvm.comps.uvm_env import UVMEnv
from uvm.macros import *

from uvm.base.uvm_debug import UVMDebug

# UVMDebug.full_debug()

#  //----------------------------------------------------------------------
#  // class producer
#  //----------------------------------------------------------------------
class producer(UVMComponent):

    def __init__(self, name, p=None):
        super().__init__(name,p)
        self.put_port = UVMBlockingPutPort("put_port", self)
        self.num_items = 0

    
    async def run_phase(self, phase):
        #
        randval = 0

        for i in range(10):
            randval = sv.random() % 100
            #10
            await Timer(10, "NS")
            uvm_info("producer", sv.sformatf("sending %d", randval), UVM_MEDIUM)
            await self.put_port.put(randval)
            self.num_items += 1
        uvm_info("PRODUCER", "Finished run_phase", UVM_LOW)


class consumer(UVMComponent):

    def __init__(self, name, p=None):
        super().__init__(name,p)
        self.get_port = UVMBlockingGetPort("get_port", self)
        self.num_items = 0

    
    async def run_phase(self, phase):
        val = 0
        while True:
            uvm_info("CONSUMER", "Started to get items..", UVM_MEDIUM)
            arr = []
            await self.get_port.get(arr)
            val = arr[0]
            uvm_info("consumer", sv.sformatf("receiving %d", val), UVM_MEDIUM)
            self.num_items += 1
        uvm_info("CONSUMER", "Finished run_phase", UVM_LOW)


#  //----------------------------------------------------------------------
#  // class env
#  //----------------------------------------------------------------------

class env(UVMEnv):

    def __init__(self, name="env"):
        super().__init__(name)
        self.p = producer("producer", self)
        self.c = consumer("consumer", self)
        self.f = UVMTLMFIFO("fifo", self)
        sv.display("fifo put_export: %s", self.f.m_name)


    def connect_phase(self, phase):
        self.p.put_port.connect(self.f.put_export)
        self.c.get_port.connect(self.f.get_export)
        self.f.set_report_verbosity_level_hier(UVM_DEBUG)

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(1000, "NS")
        phase.drop_objection(self)


    def check_phase(self, phase):
        super().check_phase(phase)
        if self.p.num_items != self.c.num_items:
            uvm_fatal("TEST_ERR", "Mismatch in number of items: producer " +
                    str(self.p.num_items) + ' cons: ' + str(self.c.num_items))

    # endclass


@cocotb.test()
async def module_top(dut):
    # Main body of module top:
    e = env("prod_cons_env")
    await run_test()
