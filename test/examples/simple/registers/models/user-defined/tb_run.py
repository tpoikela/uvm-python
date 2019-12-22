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
from cocotb.clock import Clock

from uvm.base import (uvm_top, UVMCoreService, run_test, UVM_FINISHED, UVM_LOW,
        sv, UVMDebug, UVMConfigDb)
from uvm.comps import UVMTest
from uvm.macros import uvm_fatal, uvm_info
from uvm.reg.sequences import uvm_reg_hw_reset_seq
from uvm.reg.uvm_reg_model import *

from tb_env import tb_env

#UVMDebug.DEBUG = True

class MyClock():

    def __init__(self, dut):
        self.dut = dut

    @cocotb.coroutine
    def start(self, n):
        c = Clock(self.dut.clk, 10, 'ns')
        clk_fork = cocotb.fork(c.start())
        yield Timer(n, "NS")
        clk_fork.kill()

class tb_test(UVMTest):
    #
    def __init__(self, name="tb_test", parent=None):
        UVMTest.__init__(self, name, parent)
        self.dut = None

    def build_phase(self, phase):
        UVMTest.build_phase(self, phase)
        self.env = tb_env.type_id.create("env", self)
        UVMConfigDb.set(self.env, "bus", "dut", self.dut)


    #   virtual task run_phase(uvm_phase phase);
    @cocotb.coroutine
    def run_phase(self, phase):

        phase.raise_objection(self)
        env = self.get_child("env")

        if env is None:
            uvm_fatal("test", "Cannot find tb_env")

        env.regmodel.reset()

        clk_fork = cocotb.fork(MyClock(self.dut).start(100))

        #uvm_reg_sequence seq;
        seq = uvm_reg_hw_reset_seq.type_id.create("reg_hw_rst_seq")
        seq.model = env.regmodel
        print("Before seq.start. Wait for seq state")
        yield seq.start(None)
        print("seq.start was called. Wait for seq state")
        yield seq.wait_for_sequence_state(UVM_FINISHED)
        print("AFTER yield seq.wait_for_sequence_state(UVM_FINISHED)")

        nwrites = 16
        uvm_info("Test", "Performing " + str(nwrites) + " writes...", UVM_LOW)

        for i in range(nwrites):
            status = []
            uvm_info("WRITE", sv.sformatf("Write[%0d] now", i), UVM_LOW)
            yield env.regmodel.user_acp.write(status, sv.random())
        status = []
        yield env.regmodel.user_acp.mirror(status, UVM_CHECK)

        uvm_info("Test", "Resetting DUT...", UVM_LOW)
        self.dut.reset <= 0
        yield Timer(5, "NS")
        self.dut.reset <= 1
        env.regmodel.reset()
        env.regmodel.user_acp.mirror(status, UVM_CHECK)
        clk_fork.kill()
        phase.drop_objection(self)
    #endclass


@cocotb.test()
def module_top(dut):

    cs_ = UVMCoreService.get()
    test = tb_test("test")
    test.dut = dut

    svr = cs_.get_report_server()
    svr.set_max_quit_count(10)

    yield run_test()
    yield Timer(1)
