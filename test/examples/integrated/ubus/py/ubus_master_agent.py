#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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
from uvm.macros import uvm_component_utils

from ubus_master_monitor import ubus_master_monitor
from ubus_master_driver import ubus_master_driver
from ubus_master_sequencer import ubus_master_sequencer

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_master_agent
#//
#//------------------------------------------------------------------------------


class ubus_master_agent(UVMAgent):
    #
    #  ubus_master_driver driver;
    #  uvm_sequencer#(ubus_transfer) sequencer;
    #  ubus_master_monitor monitor;
    #
    #  // Provide implementations of virtual methods such as get_type_name and create
    #  `uvm_component_utils_begin(ubus_master_agent)
    #    `uvm_field_int(master_id, UVM_DEFAULT)
    #  `uvm_component_utils_end
    #
    #  // new - constructor
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.master_id = 0
        self.driver = None
        self.sequencer = None
        self.monitor = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.monitor = ubus_master_monitor.type_id.create("monitor", self)
        if self.get_is_active() == UVM_ACTIVE:
            self.driver = ubus_master_driver.type_id.create("driver", self)
            self.sequencer = ubus_master_sequencer.type_id.create("sequencer",
                    self)

        arr = []
        if UVMConfigDb.get(self, "*", "master_id", arr) is True:
            self.master_id = arr[0]
        UVMConfigDb.set(self, "", "master_id", self.master_id)

    # connect_phase
    def connect_phase(self, phase):
        if self.get_is_active() == UVM_ACTIVE:
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
            self.sequencer.addr_ph_port.connect(self.monitor.addr_ph_imp)
        #  endfunction : connect_phase


uvm_component_utils(ubus_master_agent)
