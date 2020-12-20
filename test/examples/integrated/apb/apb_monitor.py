#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
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
from cocotb.triggers import *

from uvm.base.uvm_callback import *
from uvm.comps.uvm_monitor import UVMMonitor
from uvm.tlm1 import *
from uvm.macros import *

from .apb_rw import *


class apb_monitor_cbs(UVMCallback):
    def trans_observed(self, xactor, cycle):
        pass


class apb_monitor(UVMMonitor):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.ap = UVMAnalysisPort("ap", self)
        self.sigs = None  # passive
        self.cfg = None  # apb_config
        self.errors = 0
        self.num_items = 0
        self.tag = "APB_MONITOR"


    def build_phase(self, phase):
        super().build_phase(phase)
        agent = self.get_parent()
        if agent is not None:
            self.sigs = agent.vif
        else:
            arr = []
            if UVMConfigDb.get(self, "", "vif", arr):
                uvm_info("APB/MON/NOVIF", "Got vif through ConfigDb for APB monitor instance")
                self.sigs = arr[0]
        if self.sigs is None:
            uvm_fatal("APB/MON/NOVIF", "No virtual interface specified for self monitor instance")


    
    async def run_phase(self, phase):
        while True:
            tr = None

            # Wait for a SETUP cycle
            while True:
                await self.sample_delay()
                if (self.sigs.psel == 1 and
                   self.sigs.penable == 0):
                    break

            tr = apb_rw.type_id.create("tr", self)

            tr.kind = apb_rw.READ
            if int(self.sigs.pwrite) == 1:
                tr.kind = apb_rw.WRITE
            tr.addr = self.sigs.paddr.value.integer

            await self.sample_delay()
            if int(self.sigs.penable) != 1:
                val = int(self.sigs.penable)
                self.errors += 1
                uvm_error("APB", "APB protocol violation: SETUP cycle not followed by ENABLE cycle"
                        + " |Exp: 1, got: " + str(val))

            if tr.kind == apb_rw.READ:
                tr.data = self.sigs.prdata.value.integer
            else:
                tr.data = self.sigs.pwdata.value.integer

            self.trans_observed(tr)
            #TODO uvm_do_callbacks(apb_monitor,apb_monitor_cbs, self.trans_observed(self, tr))
            self.num_items += 1
            self.ap.write(tr)
            uvm_info(self.tag, "Sampled APB item: " + tr.convert2string(),
                UVM_HIGH)

    def trans_observed(self, tr):
        pass


    
    async def sample_delay(self):
        await RisingEdge(self.sigs.clk)
        await Timer(1, "NS")

uvm_component_utils(apb_monitor)
