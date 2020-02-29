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

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_master_monitor
#//
#//------------------------------------------------------------------------------

#class ubus_master_monitor extends uvm_monitor
class ubus_master_monitor(UVMMonitor):
    #
    #  // This property is the virtual interfaced needed for this component to drive
    #  // and view HDL signals. 
    #  protected virtual ubus_if vif
    #
    #  // The following two bits are used to control whether checks and coverage are
    #  // done both in the monitor class and the interface.
    #  bit checks_enable = 1
    #  bit coverage_enable = 1
    #
    #  uvm_analysis_port #(ubus_transfer) item_collected_port
    #
    #  // The following property holds the transaction information currently
    #  // begin captured (by the collect_address_phase and data_phase methods). 
    #  protected ubus_transfer trans_collected
    #
    #  // Fields to hold trans addr, data and wait_state.
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
    #  // Transfer collected beat covergroup
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
    #  // Provide implementations of virtual methods such as get_type_name and create
    #  `uvm_component_utils_begin(ubus_master_monitor)
    #    `uvm_field_int(master_id, UVM_DEFAULT)
    #    `uvm_field_int(checks_enable, UVM_DEFAULT)
    #    `uvm_field_int(coverage_enable, UVM_DEFAULT)
    #  `uvm_component_utils_end
    #

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
        self.master_id = 0
        #  endfunction : new


    def build_phase(self, phase):
        arr = []
        if UVMConfigDb.get(self, "", "vif", arr):
            self.vif = arr[0]
        if self.vif is None:
            self.uvm_report_fatal("NOVIF", "virtual interface must be set for: " +
                self.get_full_name() + ".vif")
        arr = []
        if UVMConfigDb.get(self, "", "master_id", arr):
            self.master_id = arr[0]


    
    async def run_phase(self, phase):
        self.uvm_report_info(self.get_full_name() + " MASTER ID", sv.sformatf(" = %0d",
            self.master_id), UVM_MEDIUM)
        #    fork
        forked_proc = cocotb.fork(self.collect_transactions())
        #    join
        await forked_proc
        #  endtask : run_phase

    #  // collect_transactions
    
    async def collect_transactions(self):
        await Timer(0, "NS")
        while True:
            await RisingEdge(self.vif.sig_clock)
            if (self.m_parent is not None):
                self.trans_collected.master = self.m_parent.get_name()
            await self.collect_arbitration_phase()
            await self.collect_address_phase()
            await self.collect_data_phase()
            uvm_info(self.get_full_name(), sv.sformatf("Transfer collected :\n%s",
                self.trans_collected.sprint()), UVM_MEDIUM)
            if (self.checks_enable):
                self.perform_transfer_checks()
            if (self.coverage_enable):
                self.perform_transfer_coverage()
            self.item_collected_port.write(self.trans_collected)

        #  endtask : collect_transactions

    #  // collect_arbitration_phase
    
    async def collect_arbitration_phase(self):
        #    @(posedge vif.sig_request[master_id])
        #    @(posedge vif.sig_clock iff vif.sig_grant[master_id] === 1)
        while True:
            await RisingEdge(self.vif.sig_request)
            sig_req = self.vif.sig_req[self.master_id]
            if sig_req == 1:
                break

        while True:
            await RisingEdge(self.vif.sig_clock)
            grant = int(self.vif.sig_gnt[self.master_id])
            if grant == 1:
                break
        self.begin_tr(self.trans_collected)
        #  endtask : collect_arbitration_phase

    #  // collect_address_phase
    #  virtual protected task collect_address_phase()
    
    async def collect_address_phase(self):
        await RisingEdge(self.vif.sig_clock)
        self.trans_collected.addr = int(self.vif.sig_addr.value)
        sig_size = int(self.vif.sig_size)

        #case (vif.sig_size)
        if sig_size == 0:
            self.trans_collected.size = 1
        elif sig_size == 1:
            self.trans_collected.size = 2
        elif sig_size == 2:
            self.trans_collected.size = 4
        elif sig_size == 3:
            self.trans_collected.size = 8
        self.trans_collected.data = [0] * self.trans_collected.size

        sig_read = int(self.vif.sig_read)
        sig_write = int(self.vif.sig_write)
        read_write = sig_read << 1 | sig_write
        if read_write == 0:
            self.trans_collected.read_write = NOP
        elif read_write == 2:
            self.trans_collected.read_write = READ
        elif read_write == 1:
            self.trans_collected.read_write = WRITE
        #  endtask : collect_address_phase


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


    def perform_transfer_checks(self):
        self.check_transfer_size()
        self.check_transfer_data_size()


    #  // check_transfer_size
    def check_transfer_size(self):
        trans_collected = self.trans_collected
        if (trans_collected.size == 1 or
                trans_collected.size == 2 or trans_collected.size == 4 or
                trans_collected.size == 8):
            pass
        else:
            uvm_error(self.get_type_name(), "Invalid transfer size!")


    #  // check_transfer_data_size
    def check_transfer_data_size(self):
        if (self.trans_collected.size != len(self.trans_collected.data)):
            uvm_error(self.get_type_name(), "Transfer size field / data size mismatch.")


    #  // perform_transfer_coverage
    #  virtual protected function void perform_transfer_coverage()
    #    cov_trans.sample()
    #    for (int unsigned i = 0; i < trans_collected.size; i++) begin
    #      addr = trans_collected.addr + i
    #      data = trans_collected.data[i]
    #//Wait state is not currently monitored
    #//      wait_state = trans_collected.wait_state[i]
    #      cov_trans_beat.sample()
    #    end
    #  endfunction : perform_transfer_coverage
    def perform_transfer_coverage(self):
        pass  # TODO

    #
    #  virtual function void report_phase(uvm_phase phase)
    #    `uvm_info(get_full_name(),$sformatf("Covergroup 'cov_trans' coverage: %2f",
    #					cov_trans.get_inst_coverage()),UVM_LOW)
    #  endfunction
    #
    #endclass : ubus_master_monitor
uvm_component_utils(ubus_master_monitor)
