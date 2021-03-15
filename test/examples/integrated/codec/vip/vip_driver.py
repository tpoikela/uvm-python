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

from cocotb.triggers import RisingEdge
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
        phase.raise_objection(self, "Resetting driver")
        self.vif.Tx = 0
        await self.m_interrupt()
        phase.drop_objection(self)

    async def reset_phase(self, phase):
        phase.raise_objection(self, "Resetting driver")
        uvm_info("VIP_DRV", "reset_phase started", UVM_LOW)
        await self.reset_and_suspend()
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


    #async
    #   def run_phase(self, phase):
    #      int    count = 0
    #      vip_tr tr
    #      
    #      vif.Tx = 1'bx
    #      
    #      while True:
    #         if (tr is not None  and  !m_interrupted)
    #           seq_item_port.item_done()
    #         m_interrupted = 0
    #
    #         // Reset and suspend
    #         m_suspended = 1
    #         wait (!m_suspend)
    #         m_suspended = 0
    #
    #         fork
    #            begin
    #               m_proc = process::self()
    #
    #               while True:
    #
    #                  // Suspend without reset
    #                  if (m_suspend):
    #                     m_suspended = 1
    #                     wait (!m_suspend)
    #                     m_suspended = 0
    #                  end
    #               
    #                  if (count == 0) send(8'hB2); // SYNC
    #
    #                  seq_item_port.try_next_item(tr)
    #                  
    #                  if (tr is None) send(8'h81); // IDLE
    #                  else begin
    #                     if (tr.chr == 8'h81  or  tr.chr == 8'hE7):
    #                        send(8'hE7); // ESC
    #                        if (count == 5):
    #                           send(8'hB2); // SYNC
    #                           count = 0
    #                        end
    #                        else count++
    #                     end
    #                     send(tr.chr)
    #                     
    #                     seq_item_port.item_done()
    #                     tr = None
    #                  end
    #                  count = (count + 1) % 6
    #               end
    #            end
    #         join
    #
    #      end
    #   endtask


    #async
    #   def send(self,input bit [7:0] data)
    #      pre_tx(data)
    #      `uvm_do_callbacks(vip_driver, vip_driver_cbs, pre_tx(self, data))
    #
    #      uvm_info("VIP/DRV/TX", sv.sformatf("Sending 0x%h", data),
    #                UVM_HIGH)
    #      
    #      repeat (8):
    #         yield FallingEdge(vif.clk)
    #         vif.Tx = data[7]
    #         data = {data[6:0], data[7]}
    #      end
    #
    #      post_tx(data)
    #      `uvm_do_callbacks(vip_driver, vip_driver_cbs, post_tx(self, data))
    #   endtask: send

    #async
    #   def pre_tx(self,ref bit [7:0] chr)
    #   endtask

    #async
    #   def post_tx(self,bit [7:0] chr)
    #   endtask

uvm_component_utils(vip_driver)
uvm_register_cb(vip_driver, vip_driver_cbs)
