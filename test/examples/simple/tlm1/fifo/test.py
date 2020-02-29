#
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

#
#About: uvm_tlm_fifo
#
# This test case supposed to test a producer consumer connection through a uvm_tlm_fifo of 10 levels.
#
# Walk through the test:
# Inside a module, there will be two threads established, the first one the *producer*
# will put a packet of an integer to put port, the second one *consumer* will get self
# packet through a get port. The put and get ports will be connected to the uvm_tlm_fifo exports. 
#
# the method *fifo.used* will be used here to display which fifo level is used.

import cocotb
from cocotb.triggers import Timer

# You can also do 'from uvm import *' but this gives lint errors for undefined names
from uvm import (sv, UVMComponent, UVMTest, uvm_component_utils, run_test)
from uvm.tlm1 import *


class packet():
    def __init__(self, v):
        self.i = v


class producer(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.data_out = UVMPutPort("data_out", self)

    
    async def run_phase(self, phase):
        await Timer(1, "NS")
        p = packet(0)

        while self.data_out.try_put(p):
            sv.display("%0t: put data %0d", sv.time(), p.i)
            await Timer(10, "NS")
            p = packet(p.i + 1)

        sv.display("try_put status return: %0d", p.i)
        sv.display("%0t: do a blocking put", sv.time())
        await self.data_out.put(p)
        sv.display("%0t: blocking put succeeded", sv.time())



class consumer(UVMComponent):


    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.data_in = UVMGetPort("data_in", self)


    
    async def run_phase(self, phase):
        #100;  // fifo will fill up
        await Timer(100, "NS")  # FIFO will fill up
        sv.display("%0t: getting one", sv.time())

        p = []
        await self.data_in.get(p)
        p = p[0]  # Required for python-tlm now
        sv.display("%0t: received data %0d", sv.time(), p.i)
        #100;  // let the blocking put succeed
        p = []
        while self.data_in.try_get(p):
            p = p[0]
            sv.display("%0t: received data %0d", sv.time(), p.i)
            #10
            await Timer(10, "NS")
            p = []


class test(UVMTest):

    def __init__(self, name="", parent=None):
        super().__init__(name, parent)

    async def run_phase(self, phase):
        phase.raise_objection(None)
        #5us
        await Timer(5, "US")
        phase.drop_objection(None)
uvm_component_utils(test)


async def print_proc(fifo):
    for i in range(30):
        sv.display("%0t:   FIFO level %0d of %0d", sv.time(), fifo.used(), fifo.size())
        await Timer(10, "NS")
        #10


@cocotb.test()
async def module_top(dut):
    prod = producer("prod", None)
    cons = consumer("cons", None)
    fifo = UVMTLMFIFO("fifo", None, 10)

    prod.data_out.connect(fifo.put_export)
    cons.data_in.connect(fifo.get_export)

    proc1 = cocotb.fork(run_test("test"))
    proc2 = cocotb.fork(print_proc(fifo))
    await sv.fork_join([proc1, proc2])

#  initial begin
#    prod.data_out.connect(fifo.put_export)
#    cons.data_in.connect(fifo.get_export)
#
#    fork
#      run_test("test")
#    join
#  end
#
#endmodule
