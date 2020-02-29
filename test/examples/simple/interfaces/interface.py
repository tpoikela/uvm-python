#//
#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
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

import cocotb
from cocotb.triggers import *

from uvm.base.uvm_resource_db import UVMResourceDb
from uvm.base.sv import sv_if, sv

from uvm.base.uvm_component import *
from uvm.comps.uvm_env import *
from uvm.base.uvm_resource_db import *
from uvm import run_test



# About: uvm_exmples/mechanism/interfaces
# This example will illustrate how to create a pin interface and mod port interfaces for a simple dut.
# Connect a component "driver" to the pin interfaces, then to the dut.


#//----------------------------------------------------------------------
#// interface mem_pins_if
#//----------------------------------------------------------------------

class pin_if(sv_if):

    def __init__(self, dut):
        self.signals = ['clk', 'address', 'wr_data', 'rd_data', 'rst', 'rw',
            'req', 'ack', 'err']
        bus_map = {}
        for sig in self.signals:
            bus_map[sig] = sig
        super().__init__(dut, '', bus_map)
        self.slave_mp = self
        self.master_mp = self
        self.monitor_mp = self
        #  bit [15:0] address
        #  bit [7:0]  wr_data
        #  bit [7:0] rd_data
        #  bit rst
        #  bit rw
        #  bit req
        #  bit ack
        #  bit err

        #  modport master_mp(
        #   input  clk,
        #   input  rst,
        #   output address,
        #   output wr_data,
        #   input  rd_data,
        #   output req,
        #   output rw,
        #   input  ack,
        #   input  err );

        #  modport slave_mp(
        #   input  clk,
        #   input  rst,
        #   input  address,
        #   input  wr_data,
        #   output rd_data,
        #   input  req,
        #   input  rw,
        #   output ack,
        #   output err );

        #  modport monitor_mp(
        #   input  clk,
        #   input  rst,
        #   input  address,
        #   input  wr_data,
        #   input  rd_data,
        #   input  req,
        #   input  rw ,
        #   input  ack,
        #   input  err )


#//---------------------------------------------------------------------
#// component driver
#//----------------------------------------------------------------------


class driver(UVMComponent):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.pif = None

    def connect_phase(self, phase):
        arr = []
        sv.sv_assert(UVMResourceDb.read_by_name(self.get_full_name(), 'pif', arr))
        self.pif = arr[0]

    
    async def run_phase(self, phase):
        while True:
            await FallingEdge(self.pif.clk)
            uvm_info("driver", "posedge clk", UVM_NONE)


#//----------------------------------------------------------------------
#// environment env
#//----------------------------------------------------------------------

class env(UVMEnv):
    #
    #  local pin_vif pif
    #  driver d
    #
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.d = driver("driver", self)
        self.pif = None


    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        phase.drop_objection(self)



#//----------------------------------------------------------------------
#// module clkgen
#//----------------------------------------------------------------------


async def module_clkgen(clk):
    while True:
        await Timer(5, "NS")
        clk <= 1
        await Timer(5, "NS")
        clk <= 0


#//----------------------------------------------------------------------
#// module top
#//----------------------------------------------------------------------

@cocotb.test()
async def module_top(dut):

    pif = pin_if(dut) #  pin_if pif(clk)
    ck_proc = cocotb.fork(module_clkgen(pif.clk))
    #ck = clkgen(pif.clk) #  clkgen ck(clk)

    #d = dut(pif.slave_mp)

    e = env("e_env")
    UVMResourceDb.set("env.driver", "pif", pif)
    UVMResourceDb.dump()
    await run_test()
