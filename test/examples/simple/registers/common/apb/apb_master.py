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

from uvm.base.uvm_callback import *
import cocotb
from uvm.comps.uvm_driver import *
from uvm.macros import *
from cocotb.triggers import *

class apb_master_cbs(UVMCallback):
    
    async def trans_received(self, xactor, cycle):
        await Timer(0)

    
    async def trans_executed(self, xactor, cycle):
        await Timer(0)


class apb_master(UVMDriver):  # (apb_rw)

    def __init__(self, name, parent=None):
        super().__init__(name,parent)
        self.trig = None  # event
        self.sigs = None  # apb_vif
        self.cfg = None  # apb_config
        self.tr = None  # apb_rw
        #   endfunction


    def build_phase(self, phase):
        agent = None
        if (sv.cast(agent, self.get_parent(), apb_agent) and agent is not None):
            self.sigs = agent.vif
        else:
           if (not UVMConfigDb.get(self, "", "vif", sigs)):
              uvm_fatal("APB/DRV/NOVIF", "No virtual interface specified for self driver instance")
    #   endfunction

    #   def run_phase(self,uvm_phase phase)
    #      super().run_phase(phase)
    #
    #      self.sigs.mck.psel    <=  0
    #      self.sigs.mck.penable <=  0
    #
    #      while True:
    #         apb_rw tr
    #         yield Edge(self.sigs.mck)
    #
    #         seq_item_port.get_next_item(tr)
    #
    #         // TODO: QUESTA issue with hier ref to sequence via modport; need workaround?
    #	      if (!self.sigs.mck.triggered)
    #             yield Edge(self.sigs.mck)
    #
    #         self.trans_received(tr)
    #         `uvm_do_callbacks(apb_master,apb_master_cbs,trans_received(self,tr))
    #
    #	      case (tr.kind)
    #          apb_rw::READ:  self.read(tr.addr, tr.data);
    #          apb_rw::WRITE: self.write(tr.addr, tr.data)
    #         endcase
    #
    #         self.trans_executed(tr)
    #         `uvm_do_callbacks(apb_master,apb_master_cbs,trans_executed(self,tr))
    #
    #         seq_item_port.item_done()
    #	      ->trig
    #      end
    #   endtask: run_phase


    #   def read(self,input  bit   [31:0] addr,
    #                               output logic [31:0] data)
    #
    #      self.sigs.mck.paddr   <= addr
    #      self.sigs.mck.pwrite  <=  0
    #      self.sigs.mck.psel    <=  1
    #      yield Edge(self.sigs.mck)
    #      self.sigs.mck.penable <=  1
    #      yield Edge(self.sigs.mck)
    #      data = self.sigs.mck.prdata
    #      self.sigs.mck.psel    <=  0
    #      self.sigs.mck.penable <=  0
    #   endtask: read
    #
    #   def write(self,input bit [31:0] addr,
    #                                input bit [31:0] data)
    #      self.sigs.mck.paddr   <= addr
    #      self.sigs.mck.pwdata  <= data
    #      self.sigs.mck.pwrite  <=  1
    #      self.sigs.mck.psel    <=  1
    #      yield Edge(self.sigs.mck)
    #      self.sigs.mck.penable <=  1
    #      yield Edge(self.sigs.mck)
    #      self.sigs.mck.psel    <=  0
    #      self.sigs.mck.penable <=  0
    #   endtask: write
    #
    #   def trans_received(self,apb_rw tr)
    #   endtask
    #
    #   def trans_executed(self,apb_rw tr)
    #   endtask
    #endclass: apb_master
uvm_component_utils(apb_master)
