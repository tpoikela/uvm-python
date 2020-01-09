#
#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use self file except in
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
# Walk through the test: #A thread *gen* will use a uvm_blocking_put_port to put
# a transaction.
#
# A *conv* thread will use a uvm_blocking_put_port to put a transaction,an
# uvm_blocking_get_port to get a transactions, and a uvm_analysis_ port to a
# write a transaction through it.
#
# Another thread *bfm* will use a uvm_blocking_get_port to only get the
# transactions that has been sent by the other threads.
#
# A *listener* will extends the uvm_subscriber, to implement the analysis port
# write function.
#
# A *producer* component will use uvm_blocking_put_port and uvm_analysis_port and
# a uvm_tlm_fifo, to connect the *gen* and *conv* put, get and analysis ports
# through the fifo exports.
#
# A *consumer* component will use uvm_blocking_put export and connect it directly
# to a fifo export, also will connect the *bfm*  get port to the fifo export
#
# At *top* env, the *producer*, *consumer*, and the *listener* will be connected
#

import cocotb
from cocotb.triggers import Timer

from uvm import *

#  //----------------------------------------------------------------------
#  // class transaction
#  //----------------------------------------------------------------------


class transaction(UVMTransaction):


    def copy(self, t):
        self.data = t.data
        self.rand("data", range(1 << 32))
        self.addr = t.addr
        self.rand("addr", range(1 << 32))
        #    endfunction

    def comp(self, a, b):
        return ((a.data == b.data)  and  (a.addr == b.addr))

    def clone(self):
        t = transaction()
        t.copy(self)
        return t

    def convert2string(self):
        s = sv.sformatf("[ addr = %x, data = %x ]", self.addr, self.data)
        return s
    #  endclass

#  //----------------------------------------------------------------------
#  // component gen
#  //----------------------------------------------------------------------

#  class gen(uvm_component):
#
#    uvm_blocking_put_port #(transaction) put_port
#
#    def __init__(self, name, parent)
#      super().__init__(name, parent)
#      put_port = new("put_port", self)
#    endfunction
#
#@cocotb.coroutine
#    def run_phase(self, phase):
#      transaction t
#      string msg
#
#      for(int i=0; i < 20; i++):
#        t = new()
#        assert(t.randomize())
#        `uvm_info("gen", sv.sformatf("sending  : %s", t.convert2string()), UVM_MEDIUM)
#        put_port.put(t)
#      end
#    endtask
#
#  endclass


#  //----------------------------------------------------------------------
#  // componenet conv
#  //----------------------------------------------------------------------
#  class conv(uvm_component):
#
#    uvm_blocking_put_port #(transaction) put_port
#    uvm_blocking_get_port #(transaction) get_port
#    uvm_analysis_port #(transaction) ap
#
#    def __init__(self, name, parent)
#      super().__init__(name, parent)
#      put_port = new("put_port", self)
#      get_port = new("get_port", self)
#      ap = new("analysis_port", self)
#    endfunction
#
#@cocotb.coroutine
#    def run_phase(self, phase):
#      transaction t
#
#      while True:
#        get_port.get(t)
#        ap.write(t)
#        put_port.put(t)
#      end
#    endtask
#
#  endclass

#
#  //----------------------------------------------------------------------
#  // componenet bfm
#  //----------------------------------------------------------------------
#  class bfm(uvm_component):
#
#    uvm_blocking_get_port #(transaction) get_port
#
#    def __init__(self, name, parent)
#      super().__init__(name, parent)
#      get_port = new("get_port", self)
#    endfunction
#
#@cocotb.coroutine
#    def run_phase(self, phase):
#      transaction t
#
#      while True:
#        get_port.get(t)
#        `uvm_info("bfm", sv.sformatf("receiving: %s", t.convert2string()),UVM_MEDIUM)
#      end
#    endtask
#
#  endclass


#  class listener(uvm_subscriber): #(transaction)
#    def __init__(self, name, parent)
#      super().__init__(name,parent)
#    endfunction // new
#
#    def void write(self,input transaction t):
#      `uvm_info(m_name, sv.sformatf("Received: %s", t.convert2string()), UVM_MEDIUM)
#    endfunction // write
#  endclass // listener


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
        #g = new("gen", self)
        #c = new("conv", self)
        #f = new("fifo", self)

    #
    #   def connect_phase(self, phase):
    #      g.put_port.connect(f.blocking_put_export);  // A
    #      c.get_port.connect(f.blocking_get_export);  // B
    #      c.put_port.connect(put_port); // C
    #      c.ap.connect(ap)
    #    endfunction
    #
    #  endclass
    #

#  //----------------------------------------------------------------------
#  // componenet consumer
#  //----------------------------------------------------------------------
#  class consumer(uvm_component):
#
#    uvm_blocking_put_export #(transaction) put_export
#
#    bfm b
#    uvm_tlm_fifo #(transaction) f
#
#    def __init__(self, name, parent)
#      super().__init__(name, parent)
#      put_export = new("put_export", self)
#      f = new("fifo", self)
#      b = new("bfm", self)
#    endfunction
#
#   def connect_phase(self, phase):
#      put_export.connect(f.blocking_put_export)
#      b.get_port.connect(f.blocking_get_export)
#    endfunction
#
#  endclass

#
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
        p = producer("producer", self)
        #      c = new("consumer", self)
        #      l = new("listener", self)
        #
        #      // Connections may also be done in the constructor, if you wish
        #      p.put_port.connect(c.put_export)
        #      p.ap.connect(l.analysis_export)
        #    endfunction

    @cocotb.coroutine
    def run_phase(self, phase):
        phase.raise_objection(self)
        uvm_info("ENV_TOP", "run_phase started", UVM_MEDIUM)
        yield Timer(100, "NS")
        phase.drop_objection(self)


#  //----------------------------------------------------------------------
#  // environment env
#  //----------------------------------------------------------------------
class env(UVMEnv):

    def __init__(self, name = "env"):
        super().__init__(name)
        t = top("top", self)


    #@cocotb.coroutine
    #    def run_phase(self, phase):
    #      phase.raise_objection(self)
    #      #1000;
    #      phase.drop_objection(self)
    #    endtask
    #
    #  endclass


#  //----------------------------------------------------------------------
#  // module test
#  //----------------------------------------------------------------------
@cocotb.test()
def module_top(dut):
    e = env("e")
    yield run_test()
