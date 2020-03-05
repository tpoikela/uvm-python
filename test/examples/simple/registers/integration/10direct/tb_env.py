#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
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

import cocotb
from cocotb.triggers import Timer, RisingEdge

from uvm.macros import *
from uvm.base import sv, UVMConfigDb, UVMComponent
from uvm.reg import UVMRegPredictor

from regmodel import dut_regmodel
from apb.apb_agent import apb_agent
from apb.apb_rw import reg2apb_adapter

EXPLICIT_MON = 1

#//
#// This example shows how to integrate a register model
#// directly onto a bus sequencer.
#//
#// By default, the mirror in the register model is updated implicitly.
#// For explicit monitoring, define the `EXPLICIT_MON macro
#//


class tb_env(UVMComponent):


    def __init__(self, name, parent=None):
        super().__init__(name,parent)
        self.regmodel = None  # dut_regmodel
        self.Aapb = None  # apb_agent
        self.seq = None  # uvm_reg_sequence
        self.vif = None
        if EXPLICIT_MON:
            self.apb2reg_predictor = None  # uvm_reg_predictor#(apb_rw)


    def build_phase(self, phase):
        if self.regmodel is None:
            self.regmodel = dut_regmodel.type_id.create("regmodel",None,self.get_full_name())
            self.regmodel.build()
            self.regmodel.lock_model()

            self.apb = apb_agent.type_id.create("apb", self)
        if EXPLICIT_MON:
            self.apb2reg_predictor = UVMRegPredictor("apb2reg_predictor", self)

        hdl_root = "dut"
        sv.value_plusargs("ROOT_HDL_PATH=%s",hdl_root)  # cast to 'void' removed
        self.regmodel.set_hdl_path_root(hdl_root)
        vif = []
        if UVMConfigDb.get(self, "apb", "vif", vif):
            self.vif = vif[0]
        else:
            uvm_fatal("NO_VIF", "Could not find vif from config DB")


    def connect_phase(self, phase):
        if self.apb is not None:
            self.reg2apb = reg2apb_adapter('adapter')
            self.regmodel.default_map.set_sequencer(self.apb.sqr, self.reg2apb)
            if EXPLICIT_MON:
                self.apb2reg_predictor.map = self.regmodel.default_map
                self.apb2reg_predictor.adapter = self.reg2apb
                self.regmodel.default_map.set_auto_predict(0)
                self.apb.mon.ap.connect(self.apb2reg_predictor.bus_in)
            else:
                self.regmodel.default_map.set_auto_predict(1)
            self.regmodel.print_obj()


    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        if self.seq is None:
            uvm_fatal("NO_SEQUENCE","Env's sequence is not defined. Nothing to do. Exiting.")
            return

        # begin : do_reset
        uvm_info("RESET","Performing reset of 5 cycles", UVM_LOW)
        self.vif.rst <= 1
        for _ in range(5):
            await RisingEdge(self.vif.clk)
        self.vif.rst <= 0

        await Timer(100, "NS")

        uvm_info("START_SEQ", "Starting sequence '" + self.seq.get_name() + "'", UVM_LOW)
        self.seq.model = self.regmodel
        await self.seq.start(None)
        phase.drop_objection(self)


uvm_component_utils(tb_env)
