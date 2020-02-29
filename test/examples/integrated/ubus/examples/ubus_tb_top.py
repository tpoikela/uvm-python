#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela
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
#from cocotb.clock import Clock
from uvm.base import run_test, UVMDebug
from uvm.base.uvm_phase import UVMPhase

from test_lib import *
from ubus_if import ubus_if

UBUS_ADDR_WIDTH = 16

#UVMDebug.DEBUG = True
#UVMPhase.m_phase_trace = True



async def initial_run_test(dut, vif):
    from uvm.base import UVMCoreService
    cs_ = UVMCoreService.get()
    UVMConfigDb.set(None, "*", "vif", vif)
    await run_test()



async def initial_reset(vif):
    await Timer(5, "NS")
    vif.ubus_reset <= 1
    vif.ubus_clock <= 1
    vif.ubus_wait <= 0
    await Timer(51, "NS")
    vif.ubus_reset <= 0



async def always_clk(dut, ncycles):
    dut.ubus_clock <= 0
    n = 0
    print("EEE starting always_clk")
    while n < 2*ncycles:
        n += 1
        await Timer(5, "NS")
        next_val = not dut.ubus_clock.value
        dut.ubus_clock <= int(next_val)

#module ubus_tb_top;
@cocotb.test()
async def module_ubus_tb(dut):

    vif = ubus_if(dut)

    proc_run_test = cocotb.fork(initial_run_test(dut, vif))
    proc_reset = cocotb.fork(initial_reset(dut))
    proc_clk = cocotb.fork(always_clk(dut, 100))
    proc_vif = cocotb.fork(vif.start())

    await Timer(999, "NS")
    #await [proc_run_test, proc_clk.join()]
    await sv.fork_join([proc_run_test, proc_clk])
