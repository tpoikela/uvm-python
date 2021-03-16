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

err_msg = ("Environment does not support jumping to phase %s from phase %s. " +
        "Only jumping to \"reset\" is supported")

timeout_ns = 200000 * 10


class rx_isr_seq(UVMRegSequence):

    def __init__(self, name=""):
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
        self.hier_objection = False


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
        self.vip.hier_objection = self.hier_objection

        self.ingress = sym_sb.type_id.create("ingress", self)
        self.egress = sym_sb.type_id.create("egress", self)
        self.adapt = apb2txrx.type_id.create("adapt", self)

        UVMConfigDb.set(self, "vip.sqr.main_phase", "default_sequence",
                vip_sentence_seq.type_id.get())
        UVMConfigDb.set(self, "tx_src.main_phase","default_sequence", vip_sentence_seq.type_id.get())

        self.m_isr = 0
        self.m_in_shutdown = 0
        self.pull_from_RxFIFO_thread = None

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



    # tpoikela: We should not fork anything in phase_started since it's not
    # async. The original SV example abuses this, and runs tasks.
    def phase_started(self, phase):
        name = phase.get_name()
        uvm_info("PHASE_STARTED/TB_ENV", "phase_started(): " + name, UVM_LOW)

        self.m_in_shutdown = 0
        #
        if name == "reset":
            # OK to jump back to reset phase
            if self.pull_from_RxFIFO_thread is not None:
                self.pull_from_RxFIFO_thread.kill()
                self.pull_from_RxFIFO_thread = None

        elif name == "main":
            self.pull_from_RxFIFO_thread = cocotb.fork(self.pull_from_RxFIFO(phase))

        elif name == "shutdown":
            self.m_in_shutdown = 1


    def phase_ended(self, phase):
        goto = phase.get_jump_target()
        name = phase.get_name()
        uvm_info("PHASE_ENDED/TB_ENV", "phase_ended(): " + name, UVM_LOW)

        # This environment supports jump to RESET *only*
        if goto is not None:
           if goto.get_name() != "reset":
               uvm_fatal("ENV/BADJMP", sv.sformatf(err_msg,
                   goto.get_name(), phase.get_name()))


        if phase.get_name() == "main":
            self.m_isr = sv.set_bit(self.m_isr, RX_ISR, 0)

        elif "shutdown":
            self.pull_from_RxFIFO_thread = None
            self.m_in_shutdown = 0


    async def pre_reset_phase(self, phase):
        phase.raise_objection(self, "Waiting for reset to be valid")
        while not (self.vif.rst.value.is_resolvable):
            await RisingEdge(self.vif.clk)
            uvm_info("WAIT_RST", "Waiting reset to become 0/1", UVM_MEDIUM)
        phase.drop_objection(self, "Reset is no longer X")

    async def reset_phase(self, phase):
        phase.raise_objection(self, "Env: Asserting reset for 10 clock cycles")

        uvm_info("TB/TRACE", "Resetting DUT...", UVM_NONE)

        self.vif.rst <= 1
        self.regmodel.reset()
        uvm_info("TB/TRACE", "Waiting VIP reset/suspend", UVM_NONE)
        await self.vip.reset_and_suspend()
        for _ in range(10):
            await RisingEdge(self.vif.clk)
        self.vif.rst <= 0
        uvm_info("TB/TRACE", "Waiting VIP resume", UVM_NONE)
        await self.vip.resume()

        self.m_isr = 0
        self.tx_src.stop_sequences()
        phase.drop_objection(self, "Env: HW reset done")


    async def pre_configure_phase(self, phase):
        phase.raise_objection(self, "Letting the interfaces go idle")
        uvm_info("TB/TRACE", "Configuring DUT...", UVM_NONE)
        for _ in range(10):
            await RisingEdge(self.vif.clk)
        phase.drop_objection(self, "Ready to configure")


    async def configure_phase(self, phase):
        phase.raise_objection(self, "Programming DUT")
        self.regmodel.IntMask.SA.set(1)

        self.regmodel.TxStatus.TxEn.set(1)
        self.regmodel.RxStatus.RxEn.set(1)

        # update the settings BUT without writing the TxRx data register
        status = []
        await self.regmodel.update(status);
        #	begin
        n = [self.regmodel.IntSrc, self.regmodel.IntMask,
                self.regmodel.TxStatus, self.regmodel.RxStatus]
        for reg in n:
            status = []
            await reg.update(status)
        phase.drop_objection(self, "Everything is ready to go")

    async def pre_main_phase_timeout(self):
        for _ in range(100 * 8):
            await RisingEdge(self.vif.sclk)
        uvm_fatal("TB/TIMEOUT", "VIP and/or DUT failed to acquire syncs")

    async def pre_main_phase(self, phase):
        phase.raise_objection(self, "Waiting for VIPs and DUT to acquire SYNC")
        uvm_info("TB/TRACE", "Synchronizing interfaces...", UVM_NONE)

        timeout = cocotb.fork(self.pre_main_phase_timeout())

        # Wait until the VIP has acquired symbol syncs
        while not self.vip.rx_mon.is_in_sync():
            await self.vip.rx_mon.wait_for_sync_change()

        while not self.vip.tx_mon.is_in_sync():
            await self.vip.tx_mon.wait_for_sync_change()

        timeout.kill()

        # Wait until the DUT has acquired symbol sync
        status = []
        await self.regmodel.RxStatus.mirror(status)
        if not self.regmodel.RxStatus.Align.get():
            self.regmodel.IntMask.set(0x000)
            self.regmodel.IntMask.SA.set(0b1)
            status = []
            await self.regmodel.IntMask.update(status)

            #wait (vif.intr)
            while self.vif.intr != 1:
                await RisingEdge(self.vif.clk)

        status = []
        await self.regmodel.IntMask.write(status, 0x000)
        status = []
        await self.regmodel.IntSrc.write(status, -1)
        phase.drop_objection(self, "Everyone is in SYNC")


    #
    # This task is a thread that will span the main and shutdown phase
    #
    async def pull_from_RxFIFO(self, phase):
        shutdown_ph = phase.find_by_name("shutdown")
        shutdown_ph.raise_objection(self, "Pulling data from RxFIFO")

        while True:
            self.m_isr = sv.set_bit(self.m_isr, RX_ISR, 0)
            #
            # When in shutdown, don't wait for the interrupt
            #   wait (vif.intr  or  m_in_shutdown)
            while self.vif.intr == 0 and self.m_in_shutdown == 0:
                await RisingEdge(self.vif.clk)

            #   m_isr[RX_ISR] = 1
            self.m_isr = sv.set_bit(self.m_isr, RX_ISR, 1)

            status = []
            await self.regmodel.IntSrc.mirror(status)
            if self.regmodel.IntSrc.SA.get():
                uvm_fatal("TB/DUT/SYNCLOSS", "DUT has lost SYNC")

            if not self.regmodel.IntSrc.RxHigh.get() and not self.m_in_shutdown:
                self.m_isr = sv.set_bit(self.m_isr, RX_ISR, 0)
                #wait (!m_isr)
                while self.m_isr == 1:
                    await RisingEdge(self.vif.clk)
                continue

            rx_seq = rx_isr_seq.type_id.create("rx_seq",None, self.get_full_name())
            rx_seq.model = self.regmodel
            await rx_seq.start(None)

            #   m_isr[RX_ISR] = 0
            self.m_isr = sv.set_bit(self.m_isr, RX_ISR, 0)

            if self.m_in_shutdown:
                shutdown_ph.drop_objection(self, "All data pulled from RxFIFO")
                break



    async def main_phase(self, phase):
        uvm_info("TB/TRACE", "Applying primary stimulus...", UVM_NONE)
        timeout_proc = cocotb.fork(self.timeout_and_finish(phase))
        main_proc = cocotb.fork(self.run_main_proc(phase))
        await sv.fork_join([timeout_proc, main_proc])

    async def timeout_and_finish(self, phase):
        await Timer(timeout_ns, "NS")
        obj = phase.get_objection()
        obj.display_objections()
        uvm_fatal("ERR/TIMEOUT", "$finish. Timeout reached")
        # $finish

    async def run_main_proc(self, phase):
        status = []
        ph_obj = phase.get_objection()
        phase.raise_objection(self, "Configuring ISR")
        self.regmodel.IntMask.set(0)
        self.regmodel.IntMask.SA.set(1)
        self.regmodel.IntMask.RxHigh.set(1)
        self.regmodel.IntMask.TxLow.set(1)
        await self.regmodel.IntMask.update(status)

        while True:
            phase.drop_objection(self, "ISR ready DUT-> stimulus")
            self.m_isr = sv.set_bit(self.m_isr, TX_ISR, 0)
            #   m_isr[TX_ISR] = 0

            uvm_info("TB_ENV", "Waiting vif.intr now", UVM_MEDIUM)
            while not self.vif.intr:
                await RisingEdge(self.vif.intr)
                #   wait (vif.intr)

            #   m_isr[TX_ISR] = 1
            self.m_isr = sv.set_bit(self.m_isr, TX_ISR, 1)
            phase.raise_objection(self, "Applying DUT-> stimulus")

            status = []
            await self.regmodel.IntSrc.mirror(status)
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
            status = []
            await self.regmodel.IntMask.update(status)

            # Stop supplying data once it is full
            # or the egress scoreboard has had enough
            while not self.regmodel.IntSrc.TxFull.get() > 0:
                phase.drop_objection(self, "Waiting for DUT-> stimulus from tx_src sequencer")
                tr = []
                await self.tx_src_seq_port.get_next_item(tr)
                self.tx_src_seq_port.item_done()
                phase.raise_objection(self, "Applying DUT-> stimulus from tx_src sequencer")
                await self.regmodel.TxRx.write(status, tr[0].chr)

                await self.regmodel.IntSrc.mirror(status)

            self.regmodel.IntMask.TxLow.set(1)
            await self.regmodel.IntMask.update(status)


    async def shutdown_phase(self, phase):
        phase.raise_objection(self, "Draining the DUT")

        uvm_info("TB/TRACE", "Draining the DUT...", UVM_NONE)

        if not regmodel.IntSrc.TxEmpty.get():
            # Wait for TxFIFO to be empty
            status = []
            self.regmodel.IntMask.write(status, 0x001)

            #wait (vif.intr)
            while vif.intr != 1:
                await RisingEdge(self.vif.clk)

        # Make sure the last symbol is transmitted
        # repeat (16) @(posedge vif.sclk)
        for _ in range(16):
            await RisingEdge(self.vif.clk)

        phase.drop_objection(self, "DUT is empty")


    def report_phase(self, phase):
        cs_ = UVMCoreService.get()
        svr = cs_.get_report_server()

        if (svr.get_severity_count(UVM_FATAL) +
                svr.get_severity_count(UVM_ERROR) == 0):
            print("** UVM TEST PASSED **\n")
        else:
            print("!! UVM TEST FAILED !!\n")

uvm_component_utils(tb_env)
