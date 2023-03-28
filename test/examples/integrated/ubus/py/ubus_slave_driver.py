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
from cocotb.triggers import RisingEdge, FallingEdge, NullTrigger

from uvm.base import *
from uvm.comps import UVMDriver
from uvm.macros import uvm_component_utils

from ubus_transfer import *

@uvm_component_utils
class ubus_slave_driver(UVMDriver):

    def __init__(self, name, parent):
        UVMDriver.__init__(self, name, parent)
        # The 'virtual interface' used to drive and view HDL signals.
        self.vif = None
        self.tag = "UBUS_SLAVE_DRIVER_" + name
        self.mask = 0xFF

    def build_phase(self, phase):
        super().build_phase(phase)
        uvm_info(self.tag, "build_phase started", UVM_MEDIUM)
        arr = []
        if UVMConfigDb.get(self, "", "vif", arr):
            self.vif = arr[0]
        if self.vif is None:
            self.uvm_report_fatal("NOVIF", "virtual interface must be set for: " +
                self.get_full_name() + ".vif")

    async def run_phase(self, phase):
        # Fork the async tasks and get handles to them
        fork_get = cocotb.start_soon(self.get_and_drive())
        fork_reset = cocotb.start_soon(self.reset_signals())
        # Then we can wait for both procs to finish
        await sv.fork_join([fork_get, fork_reset])

    async def get_and_drive(self):
        await NullTrigger()
        await FallingEdge(self.vif.sig_reset)
        while True:
            await RisingEdge(self.vif.sig_clock)
            req = []
            await self.seq_item_port.get_next_item(req)
            await self.respond_to_transfer(req[0])
            self.seq_item_port.item_done()

    async def reset_signals(self):
        while True:
            await RisingEdge(self.vif.sig_reset)
            self.vif.sig_error.value = 0
            self.vif.sig_wait.value  = 0
            self.vif.slave_en  = 0
    
    async def respond_to_transfer(self, resp):
        if resp.read_write != NOP:
            self.vif.sig_error.value = 0
            for i in range(resp.size):
                if resp.read_write == READ:
                    self.vif.slave_en = 1
                    self.vif.sig_data_out.value = resp.data[i] & self.mask
                if resp.wait_state[i] > 0:
                    self.vif.sig_wait.value = 1
                    for j in range(resp.wait_state[i]):
                        await RisingEdge(self.vif.sig_clock)
                self.vif.sig_wait.value = 0
                await RisingEdge(self.vif.sig_clock)
                resp.data[i] = int(self.vif.sig_data)
            self.vif.slave_en = 0
            self.vif.sig_wait.value = 0  # 1'bz
            self.vif.sig_error.value = 0  # 1'bz
        else:
            await NullTrigger()
