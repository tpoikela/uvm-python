#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use self file except in
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
from .apb_master import apb_master
from .apb_sequencer import apb_sequencer

class apb_agent(UVMAgent):


    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.sqr = None  # apb_sequencer
        self.drv = None  # apb_master
        self.mon = None  # apb_monitor
        self.vif = None  # apb_vif


    def build_phase(self, phase):
        self.sqr = apb_sequencer.type_id.create("sqr", self)
        self.drv = apb_master.type_id.create("drv", self)
        #      mon = apb_monitor.type_id.create("mon", self)

        arr = []
        if (not UVMConfigDb.get(self, "", "vif", arr)):
            uvm_fatal("APB/AGT/NOVIF", "No virtual interface specified for self agent instance")
        self.vif = arr[0]


    def connect_phase(self, phase):
        self.drv.seq_item_port.connect(self.sqr.seq_item_export)

    #endclass: apb_agent

uvm_component_utils(apb_agent)
