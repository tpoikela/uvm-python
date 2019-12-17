#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
#//    Copyright 2019 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//
#

import cocotb
from cocotb.triggers import Timer

from uvm.base import uvm_top, UVMCoreService, run_test, UVM_FINISHED, UVM_LOW
from uvm.comps import UVMTest
from uvm.macros import uvm_fatal, uvm_info
from uvm.reg.sequences import uvm_reg_hw_reset_seq

from tb_env import tb_env

#`include "uvm_pkg.sv"
#
#`include "regmodel.sv"
#`include "tb_env.sv"

#class tb_test extends uvm_test;
class tb_test(UVMTest):
    #
    def __init__(self, name="tb_test", parent=None):
        UVMTest.__init__(self, name, parent)
        self.dut = None

    #   virtual task run_phase(uvm_phase phase);
    @cocotb.coroutine
    def run_phase(self, phase):
        #tb_env env;
        #uvm_status_e   status;
        #uvm_reg_data_t data;

        phase.raise_objection(self)
        env = uvm_top.get_child("env")

        if (env is None):
            uvm_fatal("test", "Cannot find tb_env");

        env.regmodel.reset()

        #uvm_reg_sequence seq;
        #seq = uvm_reg_hw_reset_seq::type_id::create("seq");
        seq = uvm_reg_hw_reset_seq.type_id.create("seq")
        seq.model = env.regmodel
        yield seq.start(None)
        print("seq.start was called. Wait for seq state")
        yield seq.wait_for_sequence_state(UVM_FINISHED)

        uvm_info("Test", "Performing 257 writes...", UVM_LOW)
        
        for i in range(257):
           env.regmodel.user_acp.write(status, sv.random())
        env.regmodel.user_acp.mirror(status, UVM_CHECK)
        
        uvm_info("Test", "Resetting DUT...", UVM_LOW)
        self.dut.reset()
        env.regmodel.reset()
        env.regmodel.user_acp.mirror(status, UVM_CHECK)
        phase.drop_objection(self)
    #endclass
    

@cocotb.test()
def module_top(dut):
    
    cs_ = UVMCoreService.get()
    env = tb_env("env")
    test = tb_test("test")
    test.dut = dut
    
    svr = cs_.get_report_server()
    svr.set_max_quit_count(10)
    
    yield run_test()
    yield Timer(1)
