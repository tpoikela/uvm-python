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
from cocotb.triggers import RisingEdge

from uvm.seq.uvm_sequence import UVMSequence
from uvm.macros import *
from uvm import (UVMConfigDb, run_test, uvm_object_utils)

from tb_env import tb_env

#import apb_pkg::*

#`include "reg_model.sv"
#`include "tb_env.sv"
#`include "testlib.sv"


class dut_reset_seq(UVMSequence):

    def __init__(self, name="dut_reset_seq"):
        super().__init__(name)
        self.tb_top = None

    @cocotb.coroutine
    def body(self):
        self.tb_top.rst = 1
        for i in range(5):
            yield RisingEdge(self.tb_top.clk)
        self.tb_top.rst = 0


uvm_object_utils(dut_reset_seq)


@cocotb.test()
def initial(dut):
    env = tb_env("env")
    #UVMConfigDb.set(env, "apb", "vif", tb_top.apb0)
    yield run_test()
