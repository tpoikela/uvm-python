#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
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
from cocotb.clock import Clock

from uvm.macros import *
from uvm import (UVMConfigDb, run_test)

from tb_env import tb_env
from apb.apb_if import apb_if
from testlib import *


@cocotb.test()
async def initial(dut):
    env = tb_env("env", None)
    vif = apb_if(dut)
    UVMConfigDb.set(env, "apb", "vif", vif)
    UVMConfigDb.set(None, "", "dut", dut)
    #UVMConfigDb.set(env, "apb", "vif", tb_top.apb0)
    cocotb.fork(Clock(vif.clk, 10, "NS").start())
    await run_test()
