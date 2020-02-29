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
from uvm.base.sv import sv
from uvm.base.uvm_callback import *
from uvm.comps.uvm_monitor import UVMMonitor
from uvm.macros import *
from uvm.tlm1 import UVMAnalysisPort
from cocotb.triggers import *
from apb import *


class apb_monitor_cbs(UVMCallback):
    def trans_observed(self, xactor, cycle):
        pass


class apb_monitor(UVMMonitor):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.ap = UVMAnalysisPort("ap", self)  # uvm_analysis_port#(apb_rw)
        self.cfg = None  # apb_config
        self.tr = None  # apb_rw
        self.sigs = None
    #   endfunction: new

    def build_phase(self, phase):
        agent = []
        if (sv.cast(agent, self.get_parent(), apb_agent) and len(agent) == 1):
            self.sigs = agent[0].vif
        else:
            tmp = []
            if (not UVMConfigDb.get(self, "", "vif", tmp)):
                uvm_fatal("APB/MON/NOVIF",
                   "No virtual interface specified for self monitor instance")
            self.sigs = tmp[0]

    
    async def run_phase(self, phase):
        super().run_phase(phase)
        while True:
            tr = None
    
            # Wait for a SETUP cycle
            while True:
                await Edge(self.sigs.pck)
                if (self.sigs.pck.psel != 1 or
                   self.sigs.pck.penable != 0):
                    break
    
            tr = apb_rw.type_id.create("tr", self)
    
            tr.kind = apb_rw.READ
            if (self.sigs.pck.pwrite):
                tr.kind = apb_rw.WRITE
            tr.addr = self.sigs.pck.paddr
    
            await Edge(self.sigs.pck)
            if (self.sigs.pck.penable != 1):
                uvm_error("APB", "APB protocol violation: SETUP cycle not followed by ENABLE cycle")
            tr.data = self.sigs.pck.pwdata
            if (tr.kind == apb_rw.READ):
                tr.data = self.sigs.pck.prdata
    
            self.trans_observed(tr)
            uvm_do_callbacks(apb_monitor,apb_monitor_cbs,
                    self.trans_observed(self, tr))
            self.ap.write(tr)

    def trans_observed(self, tr):
        pass

    #endclass: apb_monitor
uvm_component_utils(apb_monitor)
