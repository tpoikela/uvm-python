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
#//   permissions and limitaions under the License.
#//----------------------------------------------------------------------

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from uvm.base import UVMObject, sv, UVMConfigDb, UVM_HIGH
from uvm.macros import uvm_component_utils, uvm_object_utils
from uvm.comps import UVMMonitor
from uvm.tlm1 import UVMAnalysisPort

from ubus_transfer import *

#//------------------------------------------------------------------------------
#//
#// CLASS: slave_address_map_info
#//
#// The following class is used to determine which slave should respond
#// to a transfer on the bus
#//------------------------------------------------------------------------------

#class slave_address_map_info extends uvm_object
class slave_address_map_info(UVMObject):

    def __init__(self, name="slave_address_map_info"):
        UVMObject.__init__(self, name)
        self.min_addr = 0
        self.max_addr = 0


    def set_address_map(self, min_addr, max_addr):
        self.min_addr = min_addr
        self.max_addr = max_addr

    def get_min_add(self):
        return self.min_addr

    def get_max_add(self):
        return self.max_addr


uvm_object_utils(slave_address_map_info)
#  `uvm_object_utils_begin(slave_address_map_info)
#    `uvm_field_int(min_addr, UVM_DEFAULT)
#    `uvm_field_int(max_addr, UVM_DEFAULT)
#  `uvm_object_utils_end


#// Enumerated for ubus bus state

#typedef enum {RST_START, RST_STOP, NO_OP, ARBI, ADDR_PH, ADDR_PH_ERROR,
#  DATA_PH} ubus_bus_state
RST_START = 0
RST_STOP = 1
NO_OP = 2
ARBI = 3
ADDR_PH = 4
ADDR_PH_ERROR = 5
DATA_PH = 6


#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_status
#//
#//------------------------------------------------------------------------------

class ubus_status(UVMObject):
    #
    def __init__(self, name="ubus_status"):
        UVMObject.__init__(self, name)
        self.bus_state = RST_START

uvm_object_utils(ubus_status)

#  `uvm_object_utils_begin(ubus_status)
#    `uvm_field_enum(ubus_bus_state, bus_state, UVM_DEFAULT)
#  `uvm_object_utils_end
#


#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_bus_monitor
#//
#//------------------------------------------------------------------------------
#class ubus_bus_monitor extends uvm_monitor

class ubus_bus_monitor(UVMMonitor):
    #
    #  // The virtual interface used to view HDL signals.
    #  protected virtual ubus_if vif
    #
    #  // Property indicating the number of transactions occuring on the ubus.
    #  protected int unsigned num_transactions = 0
    #
    #  // The following two bits are used to control whether checks and coverage are
    #  // done both in the bus monitor class and the interface.
    #  bit checks_enable = 1
    #  bit coverage_enable = 1
    #
    #  // Analysis ports for the item_collected and state notifier.
    #  uvm_analysis_port #(ubus_transfer) item_collected_port
    #  uvm_analysis_port #(ubus_status) state_port
    #
    #  // The state of the ubus
    #  protected ubus_status status
    #
    #  // The following property holds the transaction information currently
    #  // being captured (by the collect_address_phase and data_phase methods).
    #  protected ubus_transfer trans_collected
    #
    #  // Events needed to trigger covergroups
    #  protected event cov_transaction
    #  protected event cov_transaction_beat
    #
    #  // Fields to hold trans data and wait_state.  No coverage of dynamic arrays.
    #  protected bit [15:0] addr
    #  protected bit [7:0] data
    #  protected int unsigned wait_state
    #
    #  // Transfer collected covergroup
    #  covergroup cov_trans @cov_transaction
    #    option.per_instance = 1
    #    trans_start_addr : coverpoint trans_collected.addr {
    #      option.auto_bin_max = 16; }
    #    trans_dir : coverpoint trans_collected.read_write
    #    trans_size : coverpoint trans_collected.size {
    #      bins sizes[] = {1, 2, 4, 8}
    #      illegal_bins invalid_sizes = default; }
    #    trans_addrXdir : cross trans_start_addr, trans_dir
    #    trans_dirXsize : cross trans_dir, trans_size
    #  endgroup : cov_trans
    #
    #  // Transfer collected data covergroup
    #  covergroup cov_trans_beat @cov_transaction_beat
    #    option.per_instance = 1
    #    beat_addr : coverpoint addr {
    #      option.auto_bin_max = 16; }
    #    beat_dir : coverpoint trans_collected.read_write
    #    beat_data : coverpoint data {
    #      option.auto_bin_max = 8; }
    #    beat_wait : coverpoint wait_state {
    #      bins waits[] = { [0:9] }
    #      bins others = { [10:$] }; }
    #    beat_addrXdir : cross beat_addr, beat_dir
    #    beat_addrXdata : cross beat_addr, beat_data
    #  endgroup : cov_trans_beat
    #

    #  // new - constructor
    def __init__(self, name, parent):
        UVMMonitor.__init__(self, name, parent)
        #    cov_trans = new()
        #    cov_trans.set_inst_name({get_full_name(), ".cov_trans"})
        #    cov_trans_beat = new()
        #    cov_trans_beat.set_inst_name({get_full_name(), ".cov_trans_beat"})
        self.trans_collected = ubus_transfer()
        self.item_collected_port = UVMAnalysisPort("item_collected_port", self)
        self.state_port = UVMAnalysisPort("state_port", self)
        self.status = ubus_status("status")

        # The following property is used to store slave address map
        # slave_address_map_info slave_addr_map[string]
        self.slave_addr_map = {}

        self.checks_enable = True
        self.coverage_enable = True
        #  endfunction : new

    #  // set_slave_configs
    def set_slave_configs(self, slave_name, min_addr=0, max_addr=0):
        self.slave_addr_map[slave_name] = slave_address_map_info()
        self.slave_addr_map[slave_name].set_address_map(min_addr, max_addr)
        #  endfunction : set_slave_configs


    def build_phase(self, phase):
        vif = []
        if not (UVMConfigDb.get(self, "", "vif", vif)):
            uvm_fatal("NOVIF", ("virtual interface must be set for: " + self.get_full_name()
                + ".vif"))
        self.vif = vif[0]

    #  // run phase
    
    async def run_phase(self, phase):
        #    fork
        reset_proc = cocotb.fork(self.observe_reset())
        collect_proc = cocotb.fork(self.collect_transactions())
        #    join
        #await [reset_proc, collect_proc.join()]
        await sv.fork_join([reset_proc, collect_proc])
        #  endtask : run_phase
    #

    #  // observe_reset
    
    async def observe_reset(self):
        #    fork
        
        async def rst_start():
            while True:
                await RisingEdge(self.vif.sig_reset)
                self.status.bus_state = RST_START
            self.state_port.write(self.status)

        
        async def rst_stop():
            while True:
                await RisingEdge(self.vif.sig_reset)
                self.status.bus_state = RST_STOP
                self.state_port.write(self.status)

        start_proc = cocotb.fork(rst_start())
        stop_proc = cocotb.fork(rst_stop())

        #await [start_proc, stop_proc.join()]
        await sv.fork_join([start_proc, stop_proc])
        #    join
        #  endtask : observe_reset


    #  // collect_transactions
    
    async def collect_transactions(self):
        while True:
            await self.collect_arbitration_phase()
            await self.collect_address_phase()
            await self.collect_data_phase()
            uvm_info("UBUS_MON", sv.sformatf("Transfer collected :\n%s",
                self.trans_collected.sprint()), UVM_HIGH)
            if (self.checks_enable):
                self.perform_transfer_checks()
            if (self.coverage_enable):
                self.perform_transfer_coverage()
            self.item_collected_port.write(self.trans_collected)
        #  endtask : collect_transactions

    #  // collect_arbitration_phase
    
    async def collect_arbitration_phase(self):
        tmpStr = ""
        # @(posedge vif.sig_clock iff (vif.sig_grant != 0))
        while True:
            await RisingEdge(self.vif.sig_clock)
            if self.vif.sig_grant != 0:
                break
        self.status.bus_state = ARBI
        self.state_port.write(self.status)
        self.begin_tr(self.trans_collected)
        # Check which grant is asserted to determine which master is performing
        # the transfer on the bus.
        #for (int j = 0; j <= 15; j++):
        for j in range(16):
            if (self.vif.sig_grant.value[j] == 1):
                tmpStr = sv.sformatf("masters[%0d]", j)
                self.trans_collected.master = tmpStr
                break
        #  endtask : collect_arbitration_phase
        #

    #  // collect_address_phase
    
    async def collect_address_phase(self):
        await RisingEdge(self.vif.sig_clock)
        self.trans_collected.addr = int(self.vif.sig_addr.value)
        sig_size = int(self.vif.sig_size)
        if sig_size == 0:
            self.trans_collected.size = 1
        elif sig_size == 1:
            self.trans_collected.size = 2
        elif sig_size == 2:
            self.trans_collected.size = 4
        elif sig_size == 3:
            self.trans_collected.size = 8

        self.trans_collected.data = [0] * self.trans_collected.size

        vec = int((int(self.vif.sig_read) << 1) & int(self.vif.sig_write))
        if vec == 0:
            self.trans_collected.read_write = NOP
            self.status.bus_state = NO_OP
            self.state_port.write(self.status)
        elif vec == 1:
            self.trans_collected.read_write = READ
            self.status.bus_state = ADDR_PH
            self.state_port.write(self.status)
        elif vec == 2:
            self.trans_collected.read_write = WRITE
            self.status.bus_state = ADDR_PH
            self.state_port.write(self.status)
        elif vec == 3:
            self.status.bus_state = ADDR_PH_ERROR
            self.state_port.write(self.status)
            if (self.checks_enable):
                uvm_error(self.get_type_name(),
                "Read and Write true at the same time")
        #  endtask : collect_address_phase
        #

    #  // collect_data_phase
    
    async def collect_data_phase(self):
        if (self.trans_collected.read_write != NOP):
            self.check_which_slave()
            for i in range(self.trans_collected.size):
                self.status.bus_state = DATA_PH
                self.state_port.write(self.status)
                while True:
                    await RisingEdge(self.vif.sig_clock)
                    if self.vif.sig_wait == 0:
                        break
                self.trans_collected.data[i] = self.vif.sig_data
            self.num_transactions += 1
            self.end_tr(self.trans_collected)
        else:
            await Timer(0)
        #  endtask : collect_data_phase
        #

    #  // check_which_slave
    def check_which_slave(self):
        slave_name = ""
        slave_found = False

        for slave_name in self.slave_addr_map:
            if (self.slave_addr_map[slave_name].get_min_addr() <= self.trans_collected.addr
              and self.trans_collected.addr <=
              self.slave_addr_map[slave_name].get_max_addr()):
                self.trans_collected.slave = slave_name
                self.slave_found = True
            if self.slave_found is True:
                break

        if slave_found is False:
            uvm_error(self.get_type_name(),
                sv.sformatf("Master attempted a transfer at illegal address 16'h%0h",
                self.trans_collected.addr))
        #  endfunction : check_which_slave
        #

    #  // perform_transfer_checks
    def perform_transfer_checks(self):
        self.check_transfer_size()
        self.check_transfer_data_size()
        #  endfunction : perform_transfer_checks

    #  // check_transfer_size
    def check_transfer_size(self):
        pass
        #   if (trans_collected.read_write != NOP):
        #    assert_transfer_size : assert(trans_collected.size == 1 ||
        #      trans_collected.size == 2 || trans_collected.size == 4 ||
        #      trans_collected.size == 8) else begin
        #      `uvm_error(get_type_name(),
        #        "Invalid transfer size!")
        #    end
        #   end
        #  endfunction : check_transfer_size


    #  // check_transfer_data_size
    def check_transfer_data_size(self):
        pass
        #    if (trans_collected.size != trans_collected.data.size())
        #      `uvm_error(get_type_name(),
        #        "Transfer size field / data size mismatch.")
        #  endfunction : check_transfer_data_size


    #  // perform_transfer_coverage
    def perform_transfer_coverage(self):
        pass
        #    if (trans_collected.read_write != NOP):
        #      -> cov_transaction
        #      for (int unsigned i = 0; i < trans_collected.size; i++):
        #        addr = trans_collected.addr + i
        #        data = trans_collected.data[i]
        #        //wait_state = trans_collected.wait_state[i]
        #        -> cov_transaction_beat
        #      end
        #    end
        #  endfunction : perform_transfer_coverage

    #endclass : ubus_bus_monitor
uvm_component_utils(ubus_bus_monitor)

#  // Provide implementations of virtual methods such as get_type_name and create
#  `uvm_component_utils_begin(ubus_bus_monitor)
#    `uvm_field_int(checks_enable, UVM_DEFAULT)
#    `uvm_field_int(coverage_enable, UVM_DEFAULT)
#    `uvm_field_int(num_transactions, UVM_DEFAULT)
#    `uvm_field_aa_object_string(slave_addr_map, UVM_DEFAULT)
#  `uvm_component_utils_end
