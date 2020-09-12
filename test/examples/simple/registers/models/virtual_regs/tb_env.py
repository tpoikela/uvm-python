#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2019 Tuomas Poikela (tpoikela)
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
from cocotb.triggers import Timer

from uvm.comps import UVMEnv
from uvm.macros import uvm_component_utils

from regmodel import block_B
from common import reg_agent, reg2rw_adapter
from uvm.reg.uvm_reg_predictor import UVMRegPredictor


class dut_rw():

    @classmethod
    
    async def rw(rw, dut):
        if (rw.addr == 0x0000):
            #'h0000: // acp (MSB)
            if (rw.read):
                rw.data = dut.acp[15:8]
        elif (rw.addr == 0x0001):  # 'h0001: // acp (LSB)
            if (rw.read):
                rw.data = dut.acp[7:0]
            else:
                dut.acp += 1
        #1;
        await Timer(1, "NS")
        # $write("%s\n", rw.convert2string());
#endclass

#class tb_env extends uvm_env;
class tb_env(UVMEnv):
    #
    def __init__(self, name="tb_env", parent=None):
        UVMEnv.__init__(self, name, parent)
        #   block_B   regmodel;
        #   reg_agent#(dut_rw) bus;
        #   uvm_reg_predictor#(reg_rw) predict;

    def build_phase(self, phase):
        self.regmodel = block_B.type_id.create("regmodel")
        self.regmodel.build()
        self.regmodel.lock_model()
        
        self.bus = reg_agent.type_id.create("bus", self)
        self.predict = UVMRegPredictor.type_id.create("predict", self)
        
        self.regmodel.set_hdl_path_root("dut");
        #  endfunction: build_phase

    def connect_phase(self, phase):
        reg2rw  = reg2rw_adapter("reg2rw")
        self.regmodel.default_map.set_sequencer(self.bus.sqr, reg2rw)
        
        self.predict.map = self.regmodel.default_map
        self.predict.adapter = reg2rw
        self.bus.mon.ap.connect(self.predict.bus_in)
        self.regmodel.default_map.set_auto_predict(0)

    #endclass
uvm_component_utils(tb_env)
