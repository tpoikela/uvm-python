#//
#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
#//    Copyright 2019-2021 Tuomas Poikela (tpoikela)
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
from cocotb.triggers import Timer

from uvm import *

from tb_env import tb_env
from vip import *

from apb.apb_if import apb_if

# Set to True to allow VIPs (drivers/monitors) raise/drop objections
# tpoikela: TODO This is not working properly at the moment
hier_objection = False


class test(UVMTest):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.env = tb_env("env")
        self.env.hier_objection = hier_objection


    def start_of_simulation_phase(self, phase):
        cs_ = UVMCoreService.get()
        top = cs_.get_root()

    def check_phase(self, phase):
        self.error = self.env.has_errors()
        if self.error:
            uvm_fatal("TEST FAILED", "check_phase of test threw fatal")


uvm_component_utils(test)


class tb_ctl_if():

    def __init__(self, clk, sclk, rst, intr):
        self.clk = clk
        self.sclk = sclk
        self.rst = rst
        self.intr = intr


async def do_reset_and_start_clocks(dut):
    await Timer(100, "NS")
    dut.rst <= 1
    await Timer(200, "NS")
    dut.clk <= 0
    dut.sclk <= 0
    await Timer(500, "NS")
    cocotb.fork(Clock(dut.clk, 50, "NS").start())
    cocotb.fork(Clock(dut.sclk, 250, "NS").start())


@cocotb.test()
async def test_codec(dut):

    # Create the interfaces and bus map for APB
    apb_bus_map = {"clk": "clk", "psel": "apb_psel", "penable": "apb_penable",
            "pwrite": "apb_pwrite", "prdata": "apb_prdata", "pwdata": "apb_pwdata",
            "paddr": "apb_paddr"}
    apb_vif = apb_if(dut, bus_map=apb_bus_map, name="")

    vip0 = vip_if(
        clk=dut.sclk,
        Tx=dut.rx,
        Rx=dut.tx
    )

    ctl = tb_ctl_if(
        clk=dut.clk,
        sclk=dut.sclk,
        rst=dut.rst,
        intr=dut.intr
    )


    UVMConfigDb.set(None, "env", "vif", ctl)
    UVMConfigDb.set(None, "env.apb", "vif", apb_vif)
    UVMConfigDb.set(None, "env.vip", "vif", vip0)

    cocotb.fork(do_reset_and_start_clocks(dut))

    await run_test()
