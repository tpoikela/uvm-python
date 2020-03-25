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

from uvm.comps import UVMEnv
from uvm.macros import *
from uvm.base import *
from ubus_bus_monitor import ubus_bus_monitor
from ubus_slave_agent import ubus_slave_agent
from ubus_master_agent import ubus_master_agent

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_env
#//
#//------------------------------------------------------------------------------
#class ubus_env extends uvm_env
class ubus_env(UVMEnv):
    #
    #  // Virtual Interface variable
    #  protected virtual interface ubus_if vif
    #
    #
    #  // The following two bits are used to control whether checks and coverage are
    #  // done both in the bus monitor class and the interface.
    #  bit intf_checks_enable = 1; 
    #  bit intf_coverage_enable = 1
    #
    #  // Components of the environment
    #  ubus_bus_monitor bus_monitor
    #  ubus_master_agent masters[]
    #  ubus_slave_agent slaves[]
    #
    #  // Provide implementations of virtual methods such as get_type_name and create
    #  `uvm_component_utils_begin(ubus_env)
    #    `uvm_field_int(has_bus_monitor, UVM_DEFAULT)
    #    `uvm_field_int(num_masters, UVM_DEFAULT)
    #    `uvm_field_int(num_slaves, UVM_DEFAULT)
    #    `uvm_field_int(intf_checks_enable, UVM_DEFAULT)
    #    `uvm_field_int(intf_coverage_enable, UVM_DEFAULT)
    #  `uvm_component_utils_end
    #

    #  // new - constructor
    def __init__(self, name, parent):
        UVMEnv.__init__(self, name, parent)
        self.monitor = None
        self.masters = []
        self.slaves = []
        self.vif = None
        # Control properties
        self.has_bus_monitor = True
        self.num_masters = 1
        self.num_slaves = 1

    #  // build_phase
    def build_phase(self, phase):
        inst_name = ""
        super().build_phase(phase)

        arr = []
        if UVMConfigDb.get(None, "*", "vif", arr):
            uvm_info("GOT_VIF", "vif was received from configDb", UVM_HIGH)
            self.vif = arr[0]

        if self.vif is None:
            self.uvm_report_fatal("NOVIF","virtual interface must be set for: " +
                    self.get_full_name() + ".vif")

        if self.has_bus_monitor is True:
            self.bus_monitor = ubus_bus_monitor.type_id.create("bus_monitor", self)

        arr = []
        if UVMConfigDb.get(self, "", "num_masters", arr) is True:
            self.num_masters = arr[0]

        for i in range(self.num_masters):
            inst_name = sv.sformatf("masters[%0d]", i)
            master = ubus_master_agent.type_id.create(inst_name, self)
            self.masters.append(master)
            UVMConfigDb.set(self, inst_name + ".monitor", "master_id", i)
            UVMConfigDb.set(self, inst_name + ".driver", "master_id", i)

        arr = []
        if UVMConfigDb.get(self, "", "num_slaves", arr) is True:
            self.num_slaves = arr[0]

        for i in range(self.num_slaves):
            inst_name = sv.sformatf("slaves[%0d]", i)
            self.slaves.append(ubus_slave_agent.type_id.create(inst_name, self))


    #
    #  // set_slave_address_map
    def set_slave_address_map(self, slave_name, min_addr, max_addr):
        tmp_slave_monitor = None
        if self.bus_monitor is not None:
            # Set slave address map for bus monitor
            self.bus_monitor.set_slave_configs(slave_name, min_addr, max_addr)

        # Set slave address map for slave monitor
        mon = self.lookup(slave_name + ".monitor")
        tmp_slave_monitor = mon
        if hasattr(mon, 'set_addr_range'):
            tmp_slave_monitor.set_addr_range(min_addr, max_addr)
        #  endfunction : set_slave_address_map

    #
    #  // update_vif_enables
    #  protected task update_vif_enables()
    #    forever begin
    #      @(intf_checks_enable || intf_coverage_enable)
    #      vif.has_checks <= intf_checks_enable
    #      vif.has_coverage <= intf_coverage_enable
    #    end
    #  endtask : update_vif_enables
    #
    #  // implement run task
    #  task run_phase(uvm_phase phase)
    #    fork
    #      update_vif_enables()
    #    join
    #  endtask : run_phase
    #
    #endclass : ubus_env
uvm_component_utils(ubus_env)
