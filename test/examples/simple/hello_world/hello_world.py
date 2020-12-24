#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela (tpoikela)
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
from cocotb.clock import Clock

from cocotb.triggers import Timer
from uvm.base.uvm_globals import run_test
from top import top

@cocotb.test()
async def hello_world(dut):
    #  initial begin
    #    $timeformat(-9,0," ns",5);
    #    uvm_default_table_printer.knobs.name_width=20;
    #    uvm_default_table_printer.knobs.type_width=50;
    #    uvm_default_table_printer.knobs.size_width=10;
    #    uvm_default_table_printer.knobs.value_width=14;
    #    uvm_config_int::set(null, "top.producer1","num_packets",2);
    #    uvm_config_int::set(null, "top.producer2","num_packets",4);
    #    uvm_config_int::set(null, "*","recording_detail",UVM_LOW);
    #    //uvm_default_printer = uvm_default_tree_printer;
    #    uvm_default_printer.knobs.reference=0;

    # Required by ghdl, otherwise sim ends in fatal error
    cocotb.fork(Clock(dut.clk, 10, "NS").start())
    mytop = top("top", parent=None)
    #    uvm_default_table_printer.knobs.type_width=20;
    await run_test()

    if mytop.error:
        raise Exception("mytop had errors")
