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


from uvm import (UVMEnv, uvm_component_utils)
#`include "reg_agent.sv"


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

    #   def build_phase(self,uvm_phase phase):
    #      regmodel = block_B.type_id.create("regmodel")
    #      regmodel.build()
    #      regmodel.lock_model()
    #
    #      bus = reg_agent#(dut).type_id.create("bus", self)
    #      predict = uvm_reg_predictor#(reg_rw).type_id.create("predict", self)
    #  endfunction: build_phase
    #
    #   def connect_phase(self,uvm_phase phase):
    #      reg2rw_adapter reg2rw  = new("reg2rw")
    #      regmodel.default_map.set_sequencer(bus.sqr, reg2rw)
    #
    #      predict.map = regmodel.default_map
    #      predict.adapter = reg2rw
    #      bus.mon.ap.connect(predict.bus_in)
    #      regmodel.default_map.set_auto_predict(0)
    #   endfunction
    #
    #endclass


uvm_component_utils(tb_env)
