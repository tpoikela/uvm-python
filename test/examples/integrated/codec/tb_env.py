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


from cocotb.triggers import RisingEdge, Timer

from uvm import *

from apb.apb_rw import reg2apb_adapter
from apb.apb_agent import apb_agent
from reg_model import reg_dut
from vip import *
from sym_sb import sym_sb
from apb2txrx import apb2txrx


class rx_isr_seq(UVMRegSequence):

    def __init__(self, name = ""):
        super().__init__(name)


    async def pre_body(self):
        self.regmodel = model

    async def body(self):
        status = 0
        
        # Keep reading data until FIFO is empty
        while not self.regmodel.IntSrc.RxEmpty.get():
            status = []
            await self.regmodel.TxRx.mirror(status)
            status = []
            await self.regmodel.IntSrc.mirror(status)

uvm_object_utils(rx_isr_seq)

TX_ISR = 0
RX_ISR = 1

class tb_env(UVMEnv):

    #   local uvm_status_e   status
    #   local uvm_reg_data_t data
    #   local bit [1:0]      m_isr

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.vif = None
        self.apb = None
        self.reg_dut = None
        self.regmodel = None
        self.tx_src = None
        self.tx_src_seq_port = None
        self.ingress = None
        self.egress = None
        self.adapt = None
        self.m_isr = 0x0


    def build_phase(self, phase):
        vif = []
        if not UVMConfigDb.get(self, "", "vif", vif):
           uvm_fatal("TB/ENV/NOVIF", "No virtual interface specified for environment instance")
        self.vif = vif[0]

        self.apb = apb_agent.type_id.create("apb", self)
        if self.regmodel is None:
           self.regmodel = reg_dut.type_id.create("regmodel",None,self.get_full_name())
           self.regmodel.build()
           self.regmodel.lock_model()

        self.tx_src = vip_sequencer.type_id.create("tx_src", self)
        self.tx_src_seq_port = UVMSeqItemPullPort("tx_src_seq_port", self)
        self.vip = vip_agent.type_id.create("vip", self)

        self.ingress = sym_sb.type_id.create("ingress", self)
        self.egress = sym_sb.type_id.create("egress", self)
        self.adapt = apb2txrx.type_id.create("adapt", self)

        UVMConfigDb.set(self, "vip.sqr.main_phase", "default_sequence",
                vip_sentence_seq.type_id.get())
        UVMConfigDb.set(self, "tx_src.main_phase","default_sequence", vip_sentence_seq.type_id.get())
    
        self.m_isr = 0

    def has_errors(self):
        return self.ingress.error or self.egress.error


    def connect_phase(self, phase):
        if self.regmodel.get_parent() is None:
            self.reg2apb = reg2apb_adapter()
            self.regmodel.default_map.set_sequencer(self.apb.sqr,self.reg2apb)
            self.regmodel.default_map.set_auto_predict(1)
    
        self.tx_src_seq_port.connect(self.tx_src.seq_item_export)
    
        self.apb.mon.ap.connect(self.adapt.apb)
    
        self.vip.tx_mon.ap.connect(self.ingress.expected)
        self.vip.rx_mon.ap.connect(self.egress.observed)
        self.adapt.tx_ap.connect(self.egress.expected)
        self.adapt.rx_ap.connect(self.ingress.observed)


    #   local bit m_in_shutdown = 0
    #   local process pull_from_RxFIFO_thread

    # tpoikela: We should not fork anything in phase_started since it's not
    # async. The original SV example abuses this, and runs tasks.
    def phase_started(self, phase):
        name = phase.get_name()
        uvm_info("PHASE_STARTED/TB_ENV", "phase_started(): " + name, UVM_LOW)
        #      
        #      m_in_shutdown = 0
        #
        #      case (name)
        #       "reset":
        #          // OK to jump back to reset phase
        #          if (pull_from_RxFIFO_thread is not None):
        #             pull_from_RxFIFO_thread.kill()
        #             pull_from_RxFIFO_thread = None
        #          end
        #       
        #       "main":
        #          fork
        #             begin
        #                pull_from_RxFIFO_thread = process::self()
        #                pull_from_RxFIFO(phase)
        #             end
        #          join_none
        #       
        #       "shutdown":
        #          m_in_shutdown = 1
        #
        #      endcase
        #   endfunction


    #   def phase_ended(self, phase):
    #      uvm_phase goto = phase.get_jump_target()
    #
    #      // This environment supports jump to RESET *only*
    #      if (goto is not None):
    #         if (goto.get_name() != "reset"):
    #            uvm_fatal("ENV/BADJMP", sv.sformatf("Environment does not support jumping to phase %s from phase %s. Only jumping to \"reset\" is supported",
    #                                               goto.get_name(), phase.get_name()))
    #         end
    #      end
    #      
    #      case (phase.get_name())
    #       "main":
    #          m_isr[TX_ISR] = 0
    #       
    #       "shutdown":
    #          begin
    #             pull_from_RxFIFO_thread = None
    #             m_in_shutdown = 0
    #          end
    #      endcase
    #   endfunction


    #async
    #   def pre_reset_phase(self, phase):
    #      phase.raise_objection(self, "Waiting for reset to be valid")
    #      wait (vif.rst != 1'bx)
    #      phase.drop_objection(self, "Reset is no longer X")
    #   endtask

    async def reset_phase(self, phase):
        phase.raise_objection(self, "Asserting reset for 10 clock cycles")
    
        uvm_info("TB/TRACE", "Resetting DUT...", UVM_NONE)
        
        self.vif.rst <= 1
        self.regmodel.reset()
        self.vip.reset_and_suspend()
        for i in range(10):
            await RisingEdge(self.vif.clk)
        self.vif.rst = 0
        self.vip.resume()
    
        self.m_isr = 0
        self.tx_src.stop_sequences()
        phase.drop_objection(self, "HW reset done")


    async def pre_configure_phase(self, phase):
        phase.raise_objection(self, "Letting the interfaces go idle")
        uvm_info("TB/TRACE", "Configuring DUT...", UVM_NONE)
        for i in range(10):
            await RisingEdge(self.vif.clk)
        phase.drop_objection(self, "Ready to configure")


    #async
    #   def configure_phase(self, phase):
    #      phase.raise_objection(self, "Programming DUT")
    #      regmodel.IntMask.SA.set(1)
    #      
    #      regmodel.TxStatus.TxEn.set(1)
    #      regmodel.RxStatus.RxEn.set(1)
    #      
    #      // update the settings BUT without writing the TxRx data register
    #      // regmodel.update(status);
    #	begin
    #		uvm_reg n[]='{regmodel.IntSrc, regmodel.IntMask, regmodel.TxStatus, regmodel.RxStatus}
    #		foreach(n[idx])
    #			n[idx].update(status)
    #	end	
    #
    #      phase.drop_objection(self, "Everything is ready to go")
    #   endtask


    #async
    #   def pre_main_phase(self, phase):
    #      phase.raise_objection(self, "Waiting for VIPs and DUT to acquire SYNC")
    #
    #      uvm_info("TB/TRACE", "Synchronizing interfaces...", UVM_NONE)
    #
    #      fork
    #         begin
    #            repeat (100 * 8) @(posedge vif.sclk)
    #            uvm_fatal("TB/TIMEOUT",
    #                       "VIP and/or DUT failed to acquire syncs")
    #         end
    #      join_none
    #
    #      // Wait until the VIP has acquired symbol syncs
    #      while (!vip.rx_mon.is_in_sync()):
    #         vip.rx_mon.wait_for_sync_change()
    #      end
    #      while (!vip.tx_mon.is_in_sync()):
    #         vip.tx_mon.wait_for_sync_change()
    #      end
    #
    #      // Wait until the DUT has acquired symbol sync
    #      regmodel.RxStatus.mirror(status)
    #      if (!regmodel.RxStatus.Align.get()):
    #         regmodel.IntMask.set( 0x000)
    #         regmodel.IntMask.SA.set( 0b1)
    #         regmodel.IntMask.update(status)
    #         wait (vif.intr)
    #      end
    #      regmodel.IntMask.write(status,  0x000)
    #      regmodel.IntSrc.write(status, -1)
    #
    #      phase.drop_objection(self, "Everyone is in SYNC")
    #   endtask


    #
    # This task is a thread that will span the main and shutdown phase
    #
    #async
    #   def pull_from_RxFIFO(self, phase)
    #      uvm_phase shutdown_ph = phase.find_by_name("shutdown")
    #      shutdown_ph.raise_objection(self, "Pulling data from RxFIFO")
    #      
    #      while True:
    #         m_isr[RX_ISR] = 0
    #
    #         // When in shutdown, don't wait for the interrupt
    #         wait (vif.intr  or  m_in_shutdown)
    #
    #         m_isr[RX_ISR] = 1
    #               
    #         regmodel.IntSrc.mirror(status)
    #         if (regmodel.IntSrc.SA.get()):
    #            uvm_fatal("TB/DUT/SYNCLOSS", "DUT has lost SYNC")
    #         end
    #         if (!regmodel.IntSrc.RxHigh.get()  and  !m_in_shutdown):
    #            m_isr[RX_ISR] = 0
    #            wait (!m_isr)
    #            continue
    #         end
    #
    #         begin
    #            uvm_reg_sequence rx_seq = rx_isr_seq.type_id.create("rx_seq",,get_full_name())
    #            rx_seq.model = regmodel
    #            rx_seq.start(None)
    #         end
    #         m_isr[RX_ISR] = 0
    #
    #         if (m_in_shutdown):
    #            shutdown_ph.drop_objection(self, "All data pulled from RxFIFO")
    #            break
    #         end
    #      end
    #   endtask



    async def main_phase(self, phase):
        uvm_info("TB/TRACE", "Applying primary stimulus...", UVM_NONE)
        timeout_proc = cocotb.fork(self.timeout_and_finish())
        main_proc = cocotb.fork(self.run_main_proc(phase))
        await sv.fork_join([timeout_proc, main_proc])

    async def timeout_and_finish(self):
        await Timer(2000000, "NS")
        obj = phase.get_objection()
        obj.display_objections()
        uvm_fatal("ERR/TIMEOUT", "$finish. Timeout reached")
        # $finish

    async def run_main_proc(self, phase):
        ph_obj = phase.get_objection()
        phase.raise_objection(self, "Configuring ISR")
        self.regmodel.IntMask.set(0)
        self.regmodel.IntMask.SA.set(1)
        self.regmodel.IntMask.RxHigh.set(1)
        self.regmodel.IntMask.TxLow.set(1)
        self.regmodel.IntMask.update(status)

        while True:
            phase.drop_objection(self, "ISR ready DUT-> stimulus")
            self.m_isr = sv.set_bit(self.m_isr, TX_ISR, 0)
            #   m_isr[TX_ISR] = 0
            #
            while self.vif.intr:
                await RisingEdge(self.vif.clk)
                #   wait (vif.intr)

            #   m_isr[TX_ISR] = 1
            self.m_isr = sv.set_bit(self.m_isr, TX_ISR, 1)
            phase.raise_objection(self, "Applying DUT-> stimulus")

            self.regmodel.IntSrc.mirror(status)
            if not self.regmodel.IntSrc.TxLow.get():
                self.m_isr = sv.set_bit(self.m_isr, TX_ISR, 1)
                # m_isr[TX_ISR] = 0
                while self.m_isr == 0x0:
                    #wait (!m_isr)
                    await RisingEdge(self.vif.clk)
                continue

            #   m_isr[TX_ISR] = 0
            self.m_isr = sv.set_bit(self.m_isr, TX_ISR, 0)

            self.regmodel.IntMask.TxLow.set(0)
            self.regmodel.IntMask.update(status)
            #   
            #   // Stop supplying data once it is full
            #   // or the egress scoreboard has had enough
            #   while (!regmodel.IntSrc.TxFull.get() > 0):
            #      vip_tr tr
            #
            #      phase.drop_objection(self, "Waiting for DUT-> stimulus from tx_src sequencer")
            #      tx_src_seq_port.get_next_item(tr)
            #      tx_src_seq_port.item_done()
            #      phase.raise_objection(self, "Applying DUT-> stimulus from tx_src sequencer")
            #      regmodel.TxRx.write(status, tr.chr)
            #
            #      regmodel.IntSrc.mirror(status)
            #   end
            #
            #   regmodel.IntMask.TxLow.set(1)
            #   regmodel.IntMask.update(status)
            #end


    #async
    #   def shutdown_phase(self, phase):
    #      phase.raise_objection(self, "Draining the DUT")
    #
    #      uvm_info("TB/TRACE", "Draining the DUT...", UVM_NONE)
    #
    #      if (!regmodel.IntSrc.TxEmpty.get()):
    #         // Wait for TxFIFO to be empty
    #         regmodel.IntMask.write(status,  0x001)
    #         wait (vif.intr)
    #      end
    #      // Make sure the last symbol is transmitted
    #      repeat (16) @(posedge vif.sclk)
    #
    #      phase.drop_objection(self, "DUT is empty")
    #   endtask
    #
    #   
    #   def report_phase(self, phase):
    #       uvm_coreservice_t cs_ = uvm_coreservice_t::get()
    #
    #      uvm_report_server svr
    #      svr = cs_.get_report_server()
    #
    #      if (svr.get_severity_count(UVM_FATAL) +
    #          svr.get_severity_count(UVM_ERROR) == 0)
    #         $write("** UVM TEST PASSED **\n")
    #      else
    #         $write("!! UVM TEST FAILED !!\n")

uvm_component_utils(tb_env)
