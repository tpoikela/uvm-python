#//----------------------------------------------------------------------
#//   Copyright 2010 Mentor Graphics Corporation
#//   Copyright 2010-2011 Synopsys, Inc
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


import cocotb
from cocotb.triggers import Timer
from uvm import *
from apb_rw import apb_rw


class target(UVMComponent):

    #   local bit [31:0] m_data
    #   uvm_tlm_b_target_socket #(target, apb_rw) sock


    def __init__(self, name="target", parent=None):
        super().__init__(name, parent)
        self.sock = UVMTLMBTargetSocket("sock", self)
        self.m_data = 0xDEADBEEF
        self.num_transport = 0


    
    async def b_transport(self, rw, delay):
        if rw.addr == 0x0000FF00:
            delay.incr(5, 1)
            if rw.kind == apb_rw.READ:
                rw.data = self.m_data
            else:
                self.m_data = rw.data
        self.num_transport += 1
        await Timer(5, "NS")


    def start_of_simulation_phase(self, phase):
        uvm_info("TRGT/RPT/START", sv.sformatf("m_data: 'h%h", self.m_data), UVM_NONE)


    def report_phase(self, phase):
        uvm_info("TRGT/RPT/FINAL", sv.sformatf("m_data: 'h%h", self.m_data), UVM_NONE)


uvm_component_utils(target)
