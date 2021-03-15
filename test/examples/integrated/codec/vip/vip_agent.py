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

from uvm import *
from .vip_sequencer import vip_sequencer
from .vip_driver import vip_driver
from .vip_monitor import vip_monitor


class vip_agent(UVMAgent):


    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.hier_objection = False


    def build_phase(self, phase):
        self.sqr = vip_sequencer.type_id.create("sqr", self)
        self.drv = vip_driver.type_id.create("drv", self)
        self.tx_mon = vip_monitor.type_id.create("tx_mon", self)
        self.rx_mon = vip_monitor.type_id.create("rx_mon", self)

        self.rx_mon.hier_objection = self.hier_objection
        self.tx_mon.hier_objection = self.hier_objection
        self.drv.hier_objection = self.hier_objection

        vif = []
        if not UVMConfigDb.get(self, "", "vif", vif):
            uvm_fatal("VIP/AGT/NOVIF", "No virtual interface specified for self agent instance")
        self.vif = vif[0]
        UVMConfigDb.set(self, "tx_mon", "vif", self.vif.tx_mon)
        UVMConfigDb.set(self, "rx_mon", "vif", self.vif.rx)

    def connect_phase(self, phase):
        self.drv.seq_item_port.connect(self.sqr.seq_item_export)


    async def pre_reset_phase(self, phase):
        if self.hier_objection:
            phase.raise_objection(self, "Resetting agent")
        await self.reset_and_suspend()
        if self.hier_objection:
            print("vip_agent dropping objection")
            phase.drop_objection(self)


    async def reset_and_suspend(self):
        #fork
        await sv.fork_join([
           cocotb.fork(self.drv.reset_and_suspend()),
           cocotb.fork(self.tx_mon.reset_and_suspend()),
           cocotb.fork(self.rx_mon.reset_and_suspend())
        ])
        #join
        self.sqr.stop_sequences()

    async def suspend(self):
        await sv.fork_join([
        # fork
            cocotb.fork(self.drv.suspend()),
            cocotb.fork(self.tx_mon.suspend()),
            cocotb.fork(self.rx_mon.suspend()),
        ])
        # join

    async def resume(self):
        #      fork
        await sv.fork_join([
            cocotb.fork(self.drv.resume()),
            cocotb.fork(self.tx_mon.resume()),
            cocotb.fork(self.rx_mon.resume()),
        ])
        #      join

uvm_component_utils(vip_agent)
