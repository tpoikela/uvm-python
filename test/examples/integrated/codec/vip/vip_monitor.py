#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
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


#typedef class vip_monitor
#class vip_monitor_cbs(uvm_callback):
    #    def rxed(self,vip_monitor xactor, ref bit [7:0] chr):;endfunction
    #endclass

from cocotb.triggers import RisingEdge, FallingEdge

from uvm import *

class vip_monitor(UVMMonitor):

    #   uvm_analysis_port#(vip_tr) ap
    #
    #   `uvm_register_cb(vip_monitor, vip_monitor_cbs)
    #
    #   vip_rx_vif vif
    #
    #   local process m_proc
    #
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.ap = UVMAnalysisPort("ap", self)

        self.m_in_sync   = 0
        self.m_suspend   = 1
        self.m_suspended = 1
        self.m_proc = None
        self.m_evt_sync_changed = Event("evt_sync_changed")
        self.hier_objection = False

    def is_in_sync(self):
        return self.m_in_sync

    async def wait_for_sync_change(self):
        await self.m_evt_sync_changed.wait()
        self.m_evt_sync_changed.clear()


    def build_phase(self, phase):
        vif = []
        if not UVMConfigDb.get(self, "", "vif", vif):
            uvm_fatal("VIP/MON/NOVIF", "No virtual interface specified for self monitor instance")
        self.vif = vif[0]

    async def reset_phase(self, phase):
        if self.hier_objection:
            phase.raise_objection(self, "Resetting monitor")
        uvm_info("VIP_MON", "reset_phase started", UVM_MEDIUM)
        await self.reset_and_suspend()
        if self.hier_objection:
            phase.drop_objection(self, "VIP monitor has been reset")


    #
    #   //
    #   // Abruptly interrupt and suspend this monitor
    #   //
    async def reset_and_suspend(self):
        self.m_suspend = 1
        if self.m_proc is not None:
           self.m_proc.kill()
           self.m_proc = None
           #wait (m_suspended)
           while self.m_suspended != 1:
               await RisingEdge(self.vif.clk)

    async def suspend(self):
        await self.reset_and_suspend()


    async def resume(self):
        self.m_suspend = 0
        while self.m_suspended != 0:
           await RisingEdge(self.vif.clk)


    def set_in_sync(self, val):
        self.m_in_sync = val
        self.m_evt_sync_changed.set()

    async def run_phase(self, phase):
        while True:
            self.m_suspended = 1
            self.set_in_sync(0)

            #wait (!m_suspend)
            while self.m_suspend != 0:
                await RisingEdge(self.vif.clk)
            self.m_suspended = 0
            self.m_proc = cocotb.fork(self.run_phase_fork(phase))
            await sv.fork_join([self.m_proc])


    async def run_phase_fork(self, phase):
        symbol = 0
        #m_proc = process::self();
        #
        while True:
            ok = 0
            escaped = 0

            uvm_info("VIP/MON/SYM", "Looking for SYNC", UVM_MEDIUM)

            # First, acquire symbol sync
            symbol = 0x00
            while symbol != 0xB2:
                await FallingEdge(self.vif.clk)
                #symbol = {symbol[6:0], vif.Rx}
                #symbol = (symbol << 1) | (0x1 & self.vif.Rx.value)
                symbol = self.get_symbol(symbol)

            uvm_info("VIP/MON/SYM1", "Found first SYNC", UVM_MEDIUM)

            # Must now find 3 more, 7 symbols apart
            ok = 1
            num_sync = 0
            for _ in range(3):
                for _ in range(7 * 8):
                    await FallingEdge(self.vif.clk)
                    #symbol = {symbol[6:0], vif.Rx}
                    symbol = self.get_symbol(symbol)

                if symbol == 0xB2:
                    num_sync += 1
                    uvm_info("VIP/MON/SYM/FR", "Found another SYNC, " + str(num_sync), UVM_MEDIUM)
                else:
                    uvm_info("VIP/MON/SYM/FR", "SYNC not found. Got: " + hex(symbol), UVM_MEDIUM)
                    ok = 0
                    break
            if ok:
                self.set_in_sync(1)
            else:
                uvm_info("VIP/MON/SYNC/NOT_ACQ", "SYNC NOT acquired!", UVM_MEDIUM)
                break

            uvm_info("VIP/MON/SYNC/ACQ", "SYNC acquired!", UVM_MEDIUM)
            escaped = 0

            while self.m_in_sync:
                for _ in range(6):
                    for _ in range(8):
                    # repeat (8):
                        await FallingEdge(self.vif.clk)
                        #symbol = {symbol[6:0], vif.Rx}
                        symbol = self.get_symbol(symbol)
                    if escaped or (symbol != 0x81 and symbol != 0xE7):
                        # vip_tr tr

                        self.rxed(symbol)
                        # TODO uvm_do_callbacks(vip_monitor, vip_monitor_cbs, rxed(self, symbol))
                        uvm_info("VIP/MON/RX", sv.sformatf("Received 0x%h", symbol),
                            UVM_HIGH)

                        tr = vip_tr.type_id.create("tr",None,self.get_full_name())
                        tr.chr = symbol
                        self.ap.write(tr)

                        escaped = 0
                    elif (symbol == 0xE7):
                        escaped = 1

                # Check that we are still in SYNC
                for _ in range(8):
                    await FallingEdge(self.vif.clk)
                    #symbol = {symbol[6:0], vif.Rx}
                    symbol = self.get_symbol(symbol)
                if symbol != 0xB2:
                    self.set_in_sync(0)
                    uvm_warning("VIP/MON/SYNC/LOST", "SYNC lost!")

    def get_symbol(self, symbol):
        if self.vif.Rx.value.is_resolvable:
            return (0xFF & (symbol << 1)) | (0x1 & self.vif.Rx.value)
        return 0

    #   virtual protected def rxed(self,ref bit [7:0] chr):
    #   endfunction

uvm_component_utils(vip_monitor)
