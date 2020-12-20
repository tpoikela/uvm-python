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

from uvm.comps.uvm_agent import UVMAgent
from uvm.base import UVMConfigDb
from uvm.macros import *
from uvm.tlm1 import *
from .apb_master import apb_master
from .apb_sequencer import apb_sequencer
from .apb_monitor import apb_monitor


class apb_agent(UVMAgent):


    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.sqr = None  # apb_sequencer
        self.drv = None  # apb_master
        self.mon = None  # apb_monitor
        self.vif = None  # apb_vif
        self.error = False
        #self.ap = UVMAnalysisExport("ap", self)


    def build_phase(self, phase):
        self.sqr = apb_sequencer.type_id.create("sqr", self)
        self.drv = apb_master.type_id.create("drv", self)
        self.mon = apb_monitor.type_id.create("mon", self)

        arr = []
        if UVMConfigDb.get(self, "", "vif", arr):
            self.vif = arr[0]
        if self.vif is None:
            uvm_fatal("APB/AGT/NOVIF", "No virtual interface specified for apb_agent instance")


    def connect_phase(self, phase):
        self.drv.seq_item_port.connect(self.sqr.seq_item_export)
        #self.mon.ap.connect(self.ap)

    def extract_phase(self, phase):
        if self.mon.errors > 0:
            self.error = True
        if self.mon.num_items == 0:
            uvm_error("APB/AGT", "APB monitor did not get any items")
            self.error = True


uvm_component_utils(apb_agent)
