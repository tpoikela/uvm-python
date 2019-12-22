#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------

from uvm.comps import UVMScoreboard
from uvm.macros import uvm_component_utils
from uvm.tlm1 import UVMAnalysisImp

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_example_scoreboard
#//
#//------------------------------------------------------------------------------
#class ubus_example_scoreboard extends uvm_scoreboard


class ubus_example_scoreboard(UVMScoreboard):
    #
    #  uvm_analysis_imp#(ubus_transfer, ubus_example_scoreboard) item_collected_export
    #
    #
    #  protected int unsigned m_mem_expected[int unsigned]
    #
    #  // Provide implementations of virtual methods such as get_type_name and create
    #  `uvm_component_utils_begin(ubus_example_scoreboard)
    #    `uvm_field_int(disable_scoreboard, UVM_DEFAULT)
    #    `uvm_field_int(num_writes, UVM_DEFAULT|UVM_DEC)
    #    `uvm_field_int(num_init_reads, UVM_DEFAULT|UVM_DEC)
    #    `uvm_field_int(num_uninit_reads, UVM_DEFAULT|UVM_DEC)
    #  `uvm_component_utils_end
    #

    def __init__(self, name, parent):
        UVMScoreboard.__init__(self, name, parent)
        self.disable_scoreboard = False
        self.num_writes = 0
        self.num_init_reads = 0
        self.num_uninit_reads = 0
        self.sbd_error = False
        self.m_mem_expected = {}

    #  //build_phase
    def build_phase(self, phase):
        self.item_collected_export = UVMAnalysisImp("item_collected_export", self)

    #  // write
    #  virtual function void write(ubus_transfer trans)
    def write(self, trans):
        if self.disable_scoreboard is False:
            self.memory_verify(trans)
        #  endfunction : write


    #  // memory_verify
    #  protected function void memory_verify(input ubus_transfer trans)
    def memory_verify(self, trans):
        data = 0
        exp = 0
        self.sbd_error = True
        #    for (int i = 0; i < trans.size; i++) begin
        #      // Check to see if entry in associative array for this address when read
        #      // If so, check that transfer data matches associative array data.
        #      if (m_mem_expected.exists(trans.addr + i)) begin
        #        if (trans.read_write == READ) begin
        #          data = trans.data[i]
        #          `uvm_info(get_type_name(),
        #            $sformatf("%s to existing address...Checking address : %0h with data : %0h", 
        #            trans.read_write.name(), trans.addr, data), UVM_LOW)
        #          assert(m_mem_expected[trans.addr + i] == trans.data[i]) else begin
        #            exp = m_mem_expected[trans.addr + i]
        #            `uvm_error(get_type_name(),
        #              $sformatf("Read data mismatch.  Expected : %0h.  Actual : %0h", 
        #              exp, data))
        #	      sbd_error = 1
        #          end
        #          num_init_reads++
        #        end
        #        if (trans.read_write == WRITE) begin
        #          data = trans.data[i]
        #          `uvm_info(get_type_name(),
        #            $sformatf("%s to existing address...Updating address : %0h with data : %0h", 
        #            trans.read_write.name(), trans.addr + i, data), UVM_LOW)
        #          m_mem_expected[trans.addr + i] = trans.data[i]
        #          num_writes++
        #        end
        #      end
        #      // Check to see if entry in associative array for this address
        #      // If not, update the location regardless if read or write.
        #      else begin
        #        data = trans.data[i]
        #        `uvm_info(get_type_name(),
        #          $sformatf("%s to empty address...Updating address : %0h with data : %0h", 
        #          trans.read_write.name(), trans.addr + i, data), UVM_LOW)
        #        m_mem_expected[trans.addr + i] = trans.data[i]
        #        if(trans.read_write == READ)
        #          num_uninit_reads++
        #        else if (trans.read_write == WRITE)
        #          num_writes++
        #      end
        #    end
        #  endfunction : memory_verify


    #  // report_phase
    #  virtual function void report_phase(uvm_phase phase)
    #    if(!disable_scoreboard) begin
    #      `uvm_info(get_type_name(),
    #        $sformatf("Reporting scoreboard information...\n%s", this.sprint()), UVM_LOW)
    #    end
    #  endfunction : report_phase

    #endclass : ubus_example_scoreboard
uvm_component_utils(ubus_example_scoreboard)
