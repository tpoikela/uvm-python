#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

import cocotb
#from cocotb.triggers import *
from cocotb.clock import Clock

from uvm import (uvm_fatal, uvm_info, UVMConfigDb, run_test,
    UVM_NONE, uvm_has_verilator)

from apb.apb_if import apb_if
from sys_env import sys_env
from sys_testlib import *


@cocotb.test()
async def initial(dut):
    if uvm_has_verilator() is False:
        print("dut parameter #NUM_BLKS: " + str(dut.NUM_BLKS))
    env = sys_env("env")
    vif = apb_if(dut)
    UVMConfigDb.set(env, "apb", "vif", vif)
    c = Clock(dut.apb_pclk, 10, 'ns')
    cocotb.fork(c.start())
    await run_test()

    if env.all_ok is False:
        uvm_fatal("ALL_NOT_OK", "env.all_ok == False, something went wrong!")
    else:
        uvm_info("ALL_OK", "*** TEST PASSED ***", UVM_NONE)
