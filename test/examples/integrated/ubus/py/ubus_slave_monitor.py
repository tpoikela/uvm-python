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

import cocotb
from cocotb.triggers import Timer, RisingEdge

from uvm.comps import UVMMonitor
from ubus_transfer import *
from uvm.tlm1 import UVMAnalysisPort, UVMBlockingPeekImp
from uvm.base import *
from uvm.macros import uvm_info

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_slave_monitor
#//
#//------------------------------------------------------------------------------
#class ubus_slave_monitor extends uvm_monitor

DEBUG = False

def _print(msg):
    if DEBUG is True:
        uvm_info("UBUS_SLAVE_MON", msg, UVM_LOW)

class ubus_slave_monitor(UVMMonitor):

    #  // This property is the virtual interface needed for this component to drive
    #  // and view HDL signals.
    #  protected virtual ubus_if self.vif
    #
    #

    #  // The following property holds the transaction information currently
    #  // begin captured (by the collect_address_phase and data_phase methods). 
    #  protected ubus_transfer trans_collected
    #

    #  // monitor notifier that the address phase (and full item) has been collected
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
    #  covergroup cov_trans
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
    #  covergroup cov_trans_beat
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
    def __init__(self, name, parent=None):
        UVMMonitor.__init__(self, name, parent)
        #    cov_trans = new()
        #    cov_trans.set_inst_name({get_full_name(), ".cov_trans"})
        #    cov_trans_beat = new()
        #    cov_trans_beat.set_inst_name({get_full_name(), ".cov_trans_beat"})
        self.trans_collected = ubus_transfer()
        self.item_collected_port = UVMAnalysisPort("item_collected_port", self)
        self.addr_ph_imp = UVMBlockingPeekImp("addr_ph_imp", self)
        # The following two bits are used to control whether checks and coverage are
        # done both in the monitor class and the interface.
        self.checks_enable = True
        self.coverage_enable = True
        self.vif = None
        self.address_phase_grabbed = Event("address_phase_grabbed")
        #  // The following two unsigned integer properties are used by
        #  // check_addr_range() method to detect if a transaction is for this target.
        self.min_addr = 0x0000
        self.max_addr = 0xFFFF
        #  endfunction : new


    def build_phase(self, phase):
        arr = []
        if UVMConfigDb.get(self, "", "vif", arr):
            self.vif = arr[0]
        if self.vif is None:
            self.uvm_report_fatal("NOVIF", "virtual interface must be set for: " +
                self.get_full_name() + ".vif")
    #  endfunction: build_phase


    #  // set the monitor's address range
    #  function void set_addr_range(bit [15:0] min_addr, bit [15:0] max_addr)
    #    this.min_addr = min_addr
    #    this.max_addr = max_addr
    #  endfunction : set_addr_range

    #
    #  // get the monitor's min addr
    #  function bit [15:0] get_min_addr()
    #    return min_addr
    #  endfunction : get_min_addr

    #
    #  // get the monitor's max addr
    #  function bit [15:0] get_max_addr()
    #    return max_addr
    #  endfunction : get_max_addr


    
    async def run_phase(self, phase):
        #    fork
        forked_proc = cocotb.fork(self.collect_transactions())
        #    join
        await forked_proc
    #  endtask : run_phase

    # collect_transactions
    
    async def collect_transactions(self):
        await RisingEdge(self.vif.sig_reset)
        range_check = False
        while True:
            if (self.m_parent is not None):
                self.trans_collected.slave = self.m_parent.get_name()
            await self.collect_address_phase()
            range_check = self.check_addr_range()
            if (range_check):
                self.begin_tr(self.trans_collected)
                self.address_phase_grabbed.set()
                await self.collect_data_phase()
                uvm_info(self.get_type_name(), sv.sformatf("Transfer collected :\n%s",
                    self.trans_collected.sprint()), UVM_FULL)
                if (self.checks_enable):
                    self.perform_transfer_checks()
                if self.coverage_enable:
                    self.perform_transfer_coverage()
                self.item_collected_port.write(self.trans_collected)
        #  endtask : collect_transactions

    #  // check_addr_range
    def check_addr_range(self):
        if ((self.trans_collected.addr >= self.min_addr) and
                (self.trans_collected.addr <= self.max_addr)):
            return True
        return False
    #  endfunction : check_addr_range


    #  // collect_address_phase
    
    async def collect_address_phase(self):
        found = False
        while found is False:
            await RisingEdge(self.vif.sig_clock)
            if self.vif.sig_read.value.is_resolvable and self.vif.sig_write.value.is_resolvable:

                if self.vif.sig_read.value == 1 or self.vif.sig_write.value == 1:
                    addr = int(self.vif.sig_addr)
                    self.trans_collected.addr = addr

                    if self.vif.sig_size.value == 0:
                        self.trans_collected.size = 1
                    elif self.vif.sig_size.value == 1:
                        self.trans_collected.size = 2
                    elif self.vif.sig_size.value == 2:
                        self.trans_collected.size = 4
                    elif self.vif.sig_size.value == 3:
                        self.trans_collected.size = 8

                    self.trans_collected.data = [0] * self.trans_collected.size

                    if self.vif.sig_read.value == 0 and self.vif.sig_write.value == 0:
                        self.trans_collected.read_write = NOP
                    elif self.vif.sig_read.value == 1 and self.vif.sig_write.value == 0:
                        self.trans_collected.read_write = READ
                    elif self.vif.sig_read.value == 0 and self.vif.sig_write.value == 1:
                        self.trans_collected.read_write = WRITE
                    found = True
        #  endtask : collect_address_phase

    #
    #  // collect_data_phase
    
    async def collect_data_phase(self):
        if (self.trans_collected.read_write != NOP):
            for i in range(self.trans_collected.size):
                while True:
                    await RisingEdge(self.vif.sig_clock)
                    if self.vif.sig_wait.value == 0:
                        break
                self.trans_collected.data[i] = self.vif.sig_data.value
        self.end_tr(self.trans_collected)
        #  endtask : collect_data_phase

    #
    #  // perform_transfer_checks
    def perform_transfer_checks(self):
        self.check_transfer_size()
        self.check_transfer_data_size()

    #
    #  // check_transfer_size
    def check_transfer_size(self):
        trans_collected = self.trans_collected
        if (trans_collected.size == 1 or
                trans_collected.size == 2 or trans_collected.size == 4 or
                trans_collected.size == 8):
            pass
        else:
            uvm_error(self.get_type_name(), "Invalid transfer size!")
        #  endfunction : check_transfer_size

    #  // check_transfer_data_size
    def check_transfer_data_size(self):
        if (self.trans_collected.size != len(self.trans_collected.data)):
            uvm_error(self.get_type_name(), "Transfer size field / data size mismatch.")

    #  // perform_transfer_coverage
    def perform_transfer_coverage(self):
        pass  # TODO
        #    cov_trans.sample()
        #    for (int unsigned i = 0; i < trans_collected.size; i++):
        #      addr = trans_collected.addr + i
        #      data = trans_collected.data[i]
        #//Wait state inforamtion is not currently monitored.
        #//      wait_state = trans_collected.wait_state[i]
        #      cov_trans_beat.sample()
        #    end
        #  endfunction : perform_transfer_coverage

    
    async def peek(self, trans):
        _print("in blocking peek yielding to grabbed_wait")
        await self.address_phase_grabbed.wait()
        self.address_phase_grabbed.clear()
        _print("in blocking peek AFTER grabbed_wait: " +
            self.trans_collected.convert2string())
        trans.append(self.trans_collected)
        #  endtask : peek

    #
    #  virtual function void report_phase(uvm_phase phase)
    #    `uvm_info(get_full_name(),$sformatf("Covergroup 'cov_trans' coverage: %2f",
    #					cov_trans.get_inst_coverage()),UVM_LOW)
    #  endfunction

    #endclass : ubus_slave_monitor
uvm_component_utils(ubus_slave_monitor)

#  TODO // Provide implementations of virtual methods such as get_type_name and create
#  `uvm_component_utils_begin(ubus_slave_monitor)
#    `uvm_field_int(min_addr, UVM_DEFAULT)
#    `uvm_field_int(max_addr, UVM_DEFAULT)
#    `uvm_field_int(checks_enable, UVM_DEFAULT)
#    `uvm_field_int(coverage_enable, UVM_DEFAULT)
#  `uvm_component_utils_end
#


