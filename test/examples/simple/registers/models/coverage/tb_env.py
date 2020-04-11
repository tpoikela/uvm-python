#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
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

from uvm import (UVMEnv, uvm_component_utils, UVMRegPredictor)
from common.reg_agent import (reg_agent, reg2rw_adapter)
from regmodel import block_B


class dut():
    #   static bit [3:0] Ra_F1 = 0
    #   static bit [3:0] Ra_F2 = 0
    #   static bit [3:0] Rb_F1 = 0
    #   static bit [3:0] Rb_F2 = 0
    #   static bit [7:0] M[1024]

    @classmethod
    def rw(cls, rw):
        pass
        #      casez (rw.addr)
        #        0x0000: // Ra
        #          if (rw.read) rw.data = {16'h00, Ra_F2, Ra_F1}
        #          else begin
        #             if (rw.byte_en[0]) Ra_F1 = rw.data[ 7:0]
        #             if (rw.byte_en[0]) Ra_F2 = rw.data[15:8]
        #          end
        #        0x0100: // Rb
        #          if (rw.read) rw.data = {16'h00, Rb_F2, Rb_F1}
        #          else begin
        #             if (rw.byte_en[0]) Rb_F1 = rw.data[ 7:0]
        #             if (rw.byte_en[0]) Rb_F2 = rw.data[15:8]
        #          end
        #        0b001000??_????????: // M
        #          if (rw.read) rw.data = {24'h00, M[rw.addr[9:0]]}
        #          else begin
        #             if (rw.byte_en[0]) M[rw.addr[9:0]] = rw.data[ 7:0]
        #          end
        #      endcase
        #      yield Timer(1, )
        #      // $write("%s\n", rw.convert2string());
        #   endtask
        #endclass


class tb_env(UVMEnv):

    #   block_B   regmodel
    #   reg_agent#(dut) bus
    #   uvm_reg_predictor#(reg_rw) predict

    def __init__(self, name="tb_env", parent=None):
        super().__init__(name, parent)
        self.regmodel = None
        self.bus = None
        self.predict = None

    def build_phase(self, phase):
        self.regmodel = block_B.type_id.create("regmodel")
        self.regmodel.build()
        self.regmodel.lock_model()

        self.bus = reg_agent.type_id.create("bus", self)
        self.bus.set_nbits(16)
        self.predict = UVMRegPredictor.type_id.create("predict", self)


    def connect_phase(self, phase):
        self.reg2rw  = reg2rw_adapter("reg2rw")
        self.regmodel.default_map.set_sequencer(self.bus.sqr, self.reg2rw)

        self.predict.map = self.regmodel.default_map
        self.predict.adapter = self.reg2rw
        self.bus.mon.ap.connect(self.predict.bus_in)
        self.regmodel.default_map.set_auto_predict(0)

    #endclass


uvm_component_utils(tb_env)
