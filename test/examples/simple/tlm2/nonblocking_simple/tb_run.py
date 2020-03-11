#//----------------------------------------------------------------------
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
#from uvm_pkg import *
#`include "uvm_macros.svh"
#
#`include "usb_xfer.sv"
#`include "host.sv"
#`include "device.sv"
#`include "tb_env.sv"

import cocotb
from tb_env import tb_env
from uvm import run_test

@cocotb.test()
async def tlm2_nb_simple_test(dut):
    env = tb_env("env")
    await run_test()
