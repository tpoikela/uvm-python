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
from cocotb.triggers import Timer
from cocotb.utils import get_sim_time
from enum import Enum, auto

from uvm.base.sv import sv
from uvm.base.uvm_debug import UVMDebug
from uvm.base.uvm_globals import run_test
from uvm.base.uvm_phase import UVMPhase
from uvm.comps import UVMDriver, UVMEnv
from uvm.macros import *
from uvm.seq import UVMSequence, UVMSequenceItem, UVMSequencer
from uvm.base.uvm_component import UVMComponent
from uvm.tlm2.uvm_tlm2_time import UVMTlmTime
from uvm.tlm2.uvm_tlm2_sockets import UVMTlmBTargetSocket,\
    UVMTlmBInitiatorSocket
from uvm.base.sv import sformatf


class kind_e(Enum):
    READ=auto
    WRITE=auto
     
class apb_rw(UVMSequenceItem):
   
    def __init__(self, name = "apb_rw"):
        super().__init__(name)
        self.addr = 0
        self.data = 0
        self.kind = kind_e.READ

    def convert2string(self):
        return sv.sformatf("kind=%s addr=%0h data=%0h",kind,addr,data)
uvm_object_utils(apb_rw)
 
class initiator(UVMComponent):
 
    def __init__(self, name="initiator", parent=None):
        super().__init__(name, parent)
        self.sock = UVMTlmBInitiatorSocket("sock", self)
 
    #//
    #// Execute a simple read-modify-write
    #//
    @cocotb.coroutine
    def run_phase(self, phase):
        rw = apb_rw();
        delay = UVMTlmTime()

        phase.raise_objection(self)
      
#                rw = apb_rw.type_id.create("rw",self.get_full_name())
        rw = apb_rw("rw")
        rw.kind = kind_e.READ
        rw.addr = 0x0000FF00

        print("--> transport (1)")
        yield self.sock.b_transport(rw, delay);
        print("<-- transport (1)")              
 
        #// Ok to reuse the same RW instance
        rw.kind = kind_e.WRITE
        rw.data = ~rw.data

        print("--> transport (2)")
        yield self.sock.b_transport(rw, delay)
        print("<-- transport (2)")

        phase.drop_objection(self)
 
uvm_component_utils(initiator)
 
class target(UVMComponent):

    def __init__(self, name="target", parent=None):
        super().__init__(name, parent)
        self.sock = UVMTlmBTargetSocket("sock", self)
        self.m_data = 0xDEADBEEF

    @cocotb.coroutine
    def b_transport(self, rw, delay):
        
        print("b_transport")
        
        if rw.addr == 0x0000FF00:
            if (rw.kind == kind_e.READ):
                rw.data = self.m_data
            else:
                self.m_data = rw.data

        yield Timer(5)

    def start_of_simulation_phase(self, phase):
        uvm_info("TRGT/RPT/START", sformatf("m_data: 'h%x", self.m_data), UVM_NONE)

    def report_phase(self, phase):
        uvm_info("TRGT/RPT/FINAL", sformatf("m_data: 'h%x", self.m_data), UVM_NONE)

uvm_component_utils(UVMComponent)

class tb_env(UVMComponent):

    def __init__(self, name="tb_env", parent=None):
        super().__init__(name, parent)

    def build_phase(self, phase):
#                self.master = initiator.type_id.create("master", self)
        self.master = initiator("master", self)
#                self.slave  = target.type_id.create("slave", self)
        self.slave  = target("slave", self)

    def connect_phase(self, phase):
        self.master.sock.connect(self.slave.sock)

uvm_component_utils(tb_env)
 
 
@cocotb.test()
def test_module_top(dut):
    env = tb_env("tb_env")
    
    yield run_test()

