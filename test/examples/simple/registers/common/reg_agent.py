#//------------------------------------------------------------------------------
#// Copyright 2010-2011 Synopsys, Inc.
#// Copyright 2010-2011 Cadence Design Systems, Inc.
#// Copyright 2019 Tuomas Poikela (tpoikela)
#// All Rights Reserved Worldwide
#//
#// Licensed under the Apache License, Version 2.0 (the "License"); you may
#// not use this file except in compliance with the License.  You may obtain
#// a copy of the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#// Unless required by applicable law or agreed to in writing, software
#// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
#// License for the specific language governing permissions and limitations
#// under the License.
#//------------------------------------------------------------------------------

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.binary import BinaryValue

from uvm.base import *
from uvm.reg import UVMRegAdapter
from uvm.reg.uvm_reg_model import *
from uvm.macros import *
from uvm.comps import *
from uvm.seq import *

class reg_rw(UVMSequenceItem):
    #
    #   rand bit          read
    #   rand bit   [31:0] addr
    #   rand logic [31:0] data
    #   rand bit   [3:0] byte_en
    #
    #   `uvm_object_utils_begin(reg_rw)
    #     `uvm_field_int(read, UVM_ALL_ON | UVM_NOPACK)
    #     `uvm_field_int(addr, UVM_ALL_ON | UVM_NOPACK)
    #     `uvm_field_int(data, UVM_ALL_ON | UVM_NOPACK)
    #     `uvm_field_int(byte_en, UVM_ALL_ON | UVM_NOPACK)
    #   `uvm_object_utils_end
    #
    def __init__(self, name="reg_rw"):
        UVMSequenceItem.__init__(self, name)
        r32b = range(0, (1 << 32) - 1)
        self.read = False
        self.rand('read', [False, True])
        self.addr = 0
        self.rand('addr', r32b)
        self.data = 0
        self.rand('data', r32b)
        self.byte_en = 0x0
        self.rand('byte_en', list(range(0, 16)))

    def convert2string(self):
        tt = "WRITE"
        if self.read:
            tt = "READ"
        return sv.sformatf("%s addr=%0h data=%0h be=%b",
                tt,self.addr,self.data,self.byte_en)
    #endclass: reg_rw
uvm_object_utils(reg_rw)


class reg_sequencer(UVMSequencer):  #(reg_rw)

    def __init__(self, name, parent=None):
        super().__init__(name, parent)

    #endclass : reg_sequencer
uvm_component_utils(reg_sequencer)


class reg_monitor(UVMMonitor):
    #
    #   uvm_analysis_port#(reg_rw) ap

    def __init__(self, name, parent=None):
        UVMMonitor.__init__(self, name, parent)
        self.ap = UVMAnalysisPort("ap", self)
    #endclass: reg_monitor


class reg_driver(UVMComponent):

    #   uvm_seq_item_pull_port #(reg_rw) seqr_port
    #   local uvm_component m_parent

    def __init__(self, name, parent=None):
        UVMComponent.__init__(self, name, parent)
        self.m_parent = parent
        self.seqr_port = UVMSeqItemPullPort("seqr_port",self)
        self.T = reg_rw
        self.dut = None
        self.n_bits = 32
        #endfunction


    
    async def run_phase(self, phase):
        mon = self.m_parent.get_child("mon")
        while True:
            rw = []  # reg_rw
            await self.seqr_port.peek(rw)  # aka 'get_next_rw'
            rw = rw[0]
            await self.drive_transaction(rw)
            mon.ap.write(rw)
            rw = []
            await self.seqr_port.get(rw)  # aka 'item_done'
    #   endtask

    
    async def drive_transaction(self, rw):
        if rw.read is False:
            wdata = BinaryValue(value=rw.data,n_bits=self.n_bits)
            await RisingEdge(self.dut.clk)
            await Timer(0)
            self.dut.we <= 1
            self.dut.data_in <= wdata
            self.dut.addr_in <= rw.addr

            for i in range(2):
                await RisingEdge(self.dut.clk)
            await Timer(0)
            self.dut.we <= 0
            uvm_info("REG_DRIVER WRITE", "Wrote value to DUT: " + str(rw.data) +
                ' addr:' + str(rw.addr), UVM_LOW)
        else:
            await RisingEdge(self.dut.clk)
            self.dut.addr_in <= rw.addr
            self.dut.read <= 0x1
            await RisingEdge(self.dut.clk)
            rw.data = self.dut.data_out.value.integer
            await RisingEdge(self.dut.clk)
            self.dut.read <= 0x0
            uvm_info("REG_DRIVER READ", "Read value from DUT: " + str(rw.data) +
                ' addr:' + str(rw.addr), UVM_LOW)
            #rw.data = 0x6666
    #endclass
uvm_component_utils(reg_driver)


#class reg_agent #(type DO=int) extends uvm_agent
class reg_agent(UVMAgent):
    #
    #   reg_sequencer   sqr
    #   reg_driver#(DO) drv
    #   reg_monitor     mon
    #
    #   `uvm_component_param_utils_begin(reg_agent#(DO))
    #      `uvm_field_object(sqr, UVM_ALL_ON)
    #      `uvm_field_object(drv, UVM_ALL_ON)
    #      `uvm_field_object(mon, UVM_ALL_ON)
    #   `uvm_component_utils_end
    #
    def __init__(self, name, parent=None):
        UVMAgent.__init__(self, name, parent)
        self.sqr = reg_sequencer("sqr", self)
        self.drv = reg_driver("drv", self)
        self.mon = reg_monitor("mon", self)

    def build_phase(self, phase):
        UVMAgent.build_phase(self, phase)
        dut = []
        if not UVMConfigDb.get(self, "", "dut", dut):
            uvm_fatal("REG_AGENT", "No 'dut' found inf config DB")
        self.drv.dut = dut[0]

    def connect_phase(self, phase):
        self.drv.seqr_port.connect(self.sqr.seq_item_export)
    #endclass
uvm_component_utils(reg_agent)


class reg2rw_adapter(UVMRegAdapter):
    #
    def __init__(self, name="reg2rw_adapter"):
        UVMRegAdapter.__init__(self, name)
        self.supports_byte_enable = True

    def reg2bus(self, rw):
        bus = reg_rw.type_id.create("rw")
        bus.read    = (rw.kind == UVM_READ)
        bus.addr    = rw.addr
        bus.data    = rw.data
        bus.byte_en = rw.byte_en
        return bus

    def bus2reg(self, bus_item, rw):
        bus = bus_item
        #if (!$cast(bus,bus_item)) begin
        #    uvm_fatal("NOT_REG_TYPE","Provided bus_item is not of the correct type")
        #    return
        rw.kind    = UVM_WRITE
        if (bus.read):
            rw.kind = UVM_READ
        rw.addr    = bus.addr
        rw.data    = bus.data
        rw.byte_en = bus.byte_en
        rw.status  = UVM_IS_OK
        return rw

    #endclass
uvm_object_utils(reg2rw_adapter)
