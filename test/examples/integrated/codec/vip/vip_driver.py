#//
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

from cocotb.triggers import RisingEdge, FallingEdge
from uvm import *


class vip_driver_cbs(UVMCallback):
    async def pre_tx(self, xactor, char):
        pass
    async def post_tx(self, xactor, char):
        pass

class vip_driver(UVMDriver):


    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.m_interrupted = 0
        self.m_proc = None
        self.hier_objection = False
        self.tr = None


    def build_phase(self, phase):
        agent = self.get_parent()
        if agent is not None:
            self.vif = agent.vif.tx
        else:
            vif = []
            if not UVMConfigDb.get(self, "", "vif", vif):
                uvm_fatal("VIP/DRV/NOVIF", "No virtual interface specified for self driver instance")
            self.vif = vif[0]

        self.m_suspend   = 1
        self.m_suspended = 1

    async def pre_reset_phase(self, phase):
        if self.hier_objection:
            phase.raise_objection(self, "Resetting driver")
        self.vif.Tx <= 0
        await self.m_interrupt()
        if self.hier_objection:
            phase.drop_objection(self)

    async def reset_phase(self, phase):
        if self.hier_objection:
            phase.raise_objection(self, "Resetting driver")
        uvm_info("VIP_DRV", "reset_phase started", UVM_LOW)
        await self.reset_and_suspend()
        if self.hier_objection:
            phase.drop_objection(self, "VIP driver has been reset")


    # Abruptly interrupt and suspend this driver
    async def m_interrupt(self):
        self.m_suspend = 1
        if self.m_proc is not None:
            m_proc.kill()
            self.m_proc = None
            self.m_interrupted = 1
            # TODO sv.wait(m_suspended)


    async def reset_and_suspend(self):
        self.vif.Tx <= 0
        await self.m_interrupt()


    async def suspend(self):
        self.m_suspend = 1
        #      wait (m_suspended)
        while self.m_suspended != 1:
            await RisingEdge(self.vif.clk)

    async def resume(self):
        self.m_suspend = 0
        #wait (!m_suspended)
        while self.m_suspended != 0:
            await RisingEdge(self.vif.clk)


    async def run_phase(self, phase):
        self.count = 0

        # self.vif.Tx = 1'bx

        while True:
            if self.tr is not None and not self.m_interrupted:
                self.seq_item_port.item_done()
            self.m_interrupted = 0

            # Reset and suspend
            self.m_suspended = 1
            #wait (!m_suspend)
            while self.m_suspend != 0:
                await RisingEdge(self.vif.clk)
            self.m_suspended = 0
            self.m_proc = cocotb.fork(self.run_phase_fork(phase))
            await sv.fork_join([self.m_proc])

    async def run_phase_fork(self, phase):
        await Timer(2000, "NS")
        while True:

            # Suspend without reset
            if self.m_suspend:
                self.m_suspended = 1
                # wait (!m_suspend)
                while self.m_suspend != 0:
                    await RisingEdge(self.vif.clk)
                self.m_suspended = 0

            if self.count == 0:
                await self.send(0xB2)  # SYNC

            tr = []
            await self.seq_item_port.try_next_item(tr)
            if len(tr) > 0:
                self.tr = tr[0]

            if self.tr is None:
                await self.send(0x81)  # IDLE
            else:
                if self.tr.chr == 0x81 or self.tr.chr == 0xE7:
                    await self.send(0xE7)  # ESC
                    if self.count == 5:
                        await self.send(0xB2)  # SYNC
                        self.count = 0
                    else:
                        self.count += 1
                await self.send(self.tr.chr)

                self.seq_item_port.item_done()
                self.tr = None
            self.count = (self.count + 1) % 6


    async def send(self, data):
        await self.pre_tx(data)
        #      `uvm_do_callbacks(vip_driver, vip_driver_cbs, pre_tx(self, data))
        uvm_info("VIP/DRV/TX", sv.sformatf("Sending 0x%h", data), UVM_HIGH)

        for _ in range(8):
            await FallingEdge(self.vif.clk)
            #vif.Tx = data[7]
            msb = (0x80 & data) >> 7
            self.vif.Tx <= msb
            #data = {data[6:0], data[7]}
            data = (0xFF & (data << 1)) | msb

        #      post_tx(data)
        #      `uvm_do_callbacks(vip_driver, vip_driver_cbs, post_tx(self, data))
        #   endtask: send

    async def pre_tx(self, char):
        pass

    async def post_tx(self, char):
        pass

uvm_component_utils(vip_driver)
uvm_register_cb(vip_driver, vip_driver_cbs)
