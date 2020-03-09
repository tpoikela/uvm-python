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

# About: hierarchy
# This test is supposed to test the hierarchical connection
# between ports of hierarchical threads using a uvm_tlm_fifo exports.
#
# Walk through the test:
# ======================
# 1. A thread *gen* will use a uvm_blocking_put_port to put a transaction.
#
# 2. A *conv* thread will use a uvm_blocking_put_port to put a transaction,an
# uvm_blocking_get_port to get a transactions, and a uvm_analysis_ port to a
# write a transaction through it.
#
# 3. Another thread *bfm* will use a uvm_blocking_get_port to only get the
# transactions that has been sent by the other threads.
#
# 4. A *listener* will extends the uvm_subscriber, to implement the analysis port
# write function.
#
# 5. A *producer* component will use uvm_blocking_put_port and uvm_analysis_port and
# a uvm_tlm_fifo, to connect the *gen* and *conv* put, get and analysis ports
# through the fifo exports.
#
# 6. A *consumer* component will use uvm_blocking_put export and connect it directly
# to a fifo export, also will connect the *bfm*  get port to the fifo export
#
# 7. At *top* env, the *producer*, *consumer*, and the *listener* will be connected
#

import cocotb
from cocotb.triggers import Timer

from uvm import *

#  //----------------------------------------------------------------------
#  // class transaction
#  //----------------------------------------------------------------------


class transaction(UVMTransaction):


    def __init__(self, name='trans'):
        super().__init__(name)
        self.addr = 0
        self.data = 0
        self.rand("data", range(1 << 32))
        self.rand("addr", range(1 << 32))

    def do_copy(self, t):
        self.data = t.data
        self.addr = t.addr
        #    endfunction

    def do_compare(self, a, b):
        return a.data == b.data and a.addr == b.addr

    def do_clone(self):
        t = transaction()
        t.copy(self)
        return t

    def convert2string(self):
        s = sv.sformatf("[ addr = %s, data = %s ]", hex(self.addr), hex(self.data))
        return s
    #  endclass
uvm_object_utils(transaction)

#  //----------------------------------------------------------------------
#  // component gen
#  //----------------------------------------------------------------------

class gen(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.put_port = UVMBlockingPutPort("put_port", self)
        self.num_items = 0

    
    async def run_phase(self, phase):
        for i in range(20):
            t = transaction()
            if not t.randomize():
                uvm_error("GEN", "Failed to randomize transaction")
            uvm_info("gen", sv.sformatf("sending  : %s", t.convert2string()), UVM_MEDIUM)
            await self.put_port.put(t)
            self.num_items += 1


#  //----------------------------------------------------------------------
#  // componenet conv
#  //----------------------------------------------------------------------

class conv(UVMComponent):


    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.put_port = UVMBlockingPutPort("put_port", self)
        self.get_port = UVMBlockingGetPort("get_port", self)
        self.ap = UVMAnalysisPort("analysis_port", self)

    
    async def run_phase(self, phase):
        while True:
            t = []
            await self.get_port.get(t)
            t = t[0]
            self.ap.write(t)
            await self.put_port.put(t)

    #  endclass

#
#  //----------------------------------------------------------------------
#  // componenet bfm
#  //----------------------------------------------------------------------

class bfm(UVMComponent):
    #
    #    uvm_blocking_get_port #(transaction) get_port
    #
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.get_port = UVMBlockingGetPort("get_port", self)

    
    async def run_phase(self, phase):

        while True:
            t = []
            await self.get_port.get(t)
            t = t[0]
            uvm_info("bfm", sv.sformatf("receiving: %s", t.convert2string()),UVM_MEDIUM)

    #  endclass


class listener(UVMSubscriber): #(transaction)
    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.num_items = 0

    def write(self, t):
        uvm_info(self.m_name, sv.sformatf("Received: %s", t.convert2string()), UVM_MEDIUM)
        self.num_items += 1


#  //----------------------------------------------------------------------
#  // componenet producer
#  //----------------------------------------------------------------------
#  // begin codeblock producer
class producer(UVMComponent):
    #
    #    uvm_blocking_put_port #(transaction) put_port
    #    uvm_analysis_port #(transaction) ap
    #
    #    gen g
    #    conv c
    #    uvm_tlm_fifo #(transaction) f
    #
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.put_port = UVMBlockingPutPort("put_port", self)
        self.ap = UVMAnalysisPort("analysis_port", self)
        self.g = gen("gen", self)
        self.c = conv("conv", self)
        self.f = UVMTLMFIFO("fifo", self)


    def connect_phase(self, phase):
        self.g.put_port.connect(self.f.blocking_put_export)  # A
        self.c.get_port.connect(self.f.blocking_get_export)  # B
        self.c.put_port.connect(self.put_port) # C
        self.c.ap.connect(self.ap)

    #  endclass
    #

#  //----------------------------------------------------------------------
#  // componenet consumer
#  //----------------------------------------------------------------------
class consumer(UVMComponent):
    #
    #    uvm_blocking_put_export #(transaction) put_export
    #
    #    bfm b
    #    uvm_tlm_fifo #(transaction) f
    #
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.put_export = UVMBlockingPutExport("put_export", self)
        self.f = UVMTLMFIFO("fifo", self)
        self.b = bfm("bfm", self)

    def connect_phase(self, phase):
       self.put_export.connect(self.f.blocking_put_export)
       self.b.get_port.connect(self.f.blocking_get_export)


#  //----------------------------------------------------------------------
#  // componenet top
#  //----------------------------------------------------------------------

class top(UVMEnv):
    #
    #    producer p
    #    consumer c
    #    listener l
    #
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.p = producer("producer", self)
        self.c = consumer("consumer", self)
        self.list = listener("listener", self)

        # Connections may also be done in the constructor, if you wish
        self.p.put_port.connect(self.c.put_export)
        self.p.ap.connect(self.list.analysis_export)

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        uvm_info("ENV_TOP", "run_phase started", UVM_MEDIUM)
        await Timer(100, "NS")
        phase.drop_objection(self)


    def check_phase(self, phase):
        if self.list.num_items == 0:
            uvm_fatal("TOP_ENV", "Listener got 0 items")


#  //----------------------------------------------------------------------
#  // environment env
#  //----------------------------------------------------------------------
class env(UVMEnv):

    def __init__(self, name="env"):
        super().__init__(name)
        self.t = top("top", self)


    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(900, "NS")
        phase.drop_objection(self)


#  //----------------------------------------------------------------------
#  // module test
#  //----------------------------------------------------------------------
@cocotb.test()
async def module_top(dut):
    e = env("e")
    await run_test()
