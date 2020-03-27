#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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

from uvm.base import *
from uvm.comps import UVMAgent
from uvm.macros import uvm_component_utils, uvm_info

from ubus_slave_monitor import ubus_slave_monitor
from ubus_slave_driver import ubus_slave_driver
from ubus_slave_sequencer import ubus_slave_sequencer

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_slave_agent
#//
#//------------------------------------------------------------------------------


class ubus_slave_agent(UVMAgent):

    #  // constructor
    def __init__(self, name, parent):
        UVMAgent.__init__(self, name, parent)
        self.driver = None
        self.sequencer = None
        self.monitor = None
        self.tag = "UBUS_SLAVE_AGENT_" + name

    #  // build_phase
    def build_phase(self, phase):
        UVMAgent.build_phase(self, phase)
        self.monitor = ubus_slave_monitor.type_id.create("u_slv_monitor", self)
        if self.get_is_active() == UVM_ACTIVE:
            self.driver = ubus_slave_driver.type_id.create("u_slv_driver", self)
            self.sequencer = ubus_slave_sequencer.type_id.create("u_slv_sequencer",
                    self)

    # connect_phase
    def connect_phase(self, phase):
        if self.get_is_active() == UVM_ACTIVE:
            uvm_info(self.tag, "Connecting comps in active mode now",
                    UVM_MEDIUM)
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
            self.sequencer.addr_ph_port.connect(self.monitor.addr_ph_imp)


uvm_component_utils(ubus_slave_agent)
