#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
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

import cocotb
from cocotb.triggers import *

from uvm.base.uvm_callback import *
from uvm.base.uvm_config_db import *
from uvm.comps.uvm_driver import UVMDriver
from uvm.macros import *

from .apb_rw import *


class apb_master_cbs(UVMCallback):
    
    async def trans_received(self, xactor, cycle):
        await Timer(1, "NS")

    
    async def trans_executed(self, xactor, cycle):
        await Timer(1, "NS")


class apb_master(UVMDriver):  #(apb_rw)


    #   event trig
    #   apb_vif sigs
    #   apb_config cfg
    #
    def __init__(self, name, parent=None):
        super().__init__(name,parent)
        self.trig = Event("trans_exec")  # event
        self.sigs = None  # apb_vif
        self.cfg = None  # apb_config
        self.tag = "APB_MASTER"


    def build_phase(self, phase):
        super().build_phase(phase)
        agent = self.get_parent()
        if agent is not None:
            self.sigs = agent.vif
        else:
            arr = []
            if (not UVMConfigDb.get(self, "", "vif", arr)):
                uvm_fatal("APB/DRV/NOVIF", "No virtual interface specified for self driver instance")
            else:
                self.sigs = arr[0]


    
    async def run_phase(self, phase):
        uvm_info("APB_MASTER", "apb_master run_phase started", UVM_MEDIUM)

        self.sigs.psel    <= 0
        self.sigs.penable <= 0

        while True:
            await self.drive_delay()

            tr = []
            await self.seq_item_port.get_next_item(tr)
            tr = tr[0]
            uvm_info("APB_MASTER", "Driving trans into DUT: " + tr.convert2string(), UVM_DEBUG)

            #if (not self.sigs.clk.triggered):
            #yield Edge(self.sigs.clk)
            await self.drive_delay()
            #yield RisingEdge(self.sigs.clk)
            #yield Timer(1, "NS")

            await self.trans_received(tr)
            #uvm_do_callbacks(apb_master,apb_master_cbs,trans_received(self,tr))

            if tr.kind == apb_rw.READ:
                data = []
                await self.read(tr.addr, data)
                tr.data = data[0]
            elif tr.kind == apb_rw.WRITE:
                await self.write(tr.addr, tr.data)

            await self.trans_executed(tr)
            #uvm_do_callbacks(apb_master,apb_master_cbs,trans_executed(self,tr))

            self.seq_item_port.item_done()
            self.trig.set()
            #->trig
        #   endtask: run_phase


    
    async def read(self, addr, data):
        uvm_info(self.tag, "Doing APB read to addr " + str(addr), UVM_MEDIUM)

        self.sigs.paddr   <= addr
        self.sigs.pwrite  <= 0
        self.sigs.psel    <= 1
        await self.drive_delay()
        self.sigs.penable <= 1
        await self.drive_delay()
        data.append(int(self.sigs.prdata))
        self.sigs.psel    <= 0
        self.sigs.penable <= 0
        #   endtask: read


    
    async def write(self, addr, data):
        uvm_info(self.tag, "Doing APB write to addr " + str(addr), UVM_MEDIUM)
        self.sigs.paddr   <= addr
        self.sigs.pwdata  <= data
        self.sigs.pwrite  <= 1
        self.sigs.psel    <= 1
        await self.drive_delay()
        self.sigs.penable <= 1
        await self.drive_delay()
        self.sigs.psel    <= 0
        self.sigs.penable <= 0
        uvm_info(self.tag, "Finished APB write to addr " + str(addr), UVM_MEDIUM)
        #   endtask: write


    
    async def drive_delay(self):
        await RisingEdge(self.sigs.clk)
        await Timer(1, "NS")

    
    async def trans_received(self, tr):
        await Timer(1, "NS")

    
    async def trans_executed(self, tr):
        await Timer(1, "NS")


uvm_component_utils(apb_master)
