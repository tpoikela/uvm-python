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

from uvm.base import sv
from uvm.comps import UVMScoreboard
from uvm.macros import uvm_component_utils, uvm_info
from uvm.tlm1 import UVMAnalysisImp
from ubus_transfer import *

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


    #  // memory_verify
    #  protected function void memory_verify(input ubus_transfer trans)
    def memory_verify(self, trans):
        data = 0
        exp = 0
        for i in range(trans.size):
            # Check to see if entry in associative array for this address when read
            # If so, check that transfer data matches associative array data.
            if (trans.addr + i) in self.m_mem_expected:
                if trans.read_write == READ:
                    data = trans.data[i]
                    uvm_info(self.get_type_name(),
                        sv.sformatf("%s to existing address...Checking address : %0h with data : %0h",
                            str(trans.read_write), int(trans.addr), int(data)), UVM_LOW)

                    if not (self.m_mem_expected[trans.addr + i] == trans.data[i]):
                        exp = self.m_mem_expected[trans.addr + i]
                        uvm_error(self.get_type_name(),
                          sv.sformatf("Read data mismatch.  Expected : %0h.  Actual : %0h",
                          exp, data))
                        self.sbd_error = True

                    self.num_init_reads += 1

                if trans.read_write == WRITE:
                    data = trans.data[i]
                    uvm_info(self.get_type_name(),
                      sv.sformatf("Op %s to existing address...Updating address : %0h with data : %0h",
                          str(trans.read_write), int(trans.addr + i), int(data)), UVM_LOW)
                    self.m_mem_expected[trans.addr + i] = trans.data[i]
                    self.num_writes += 1

            # Check to see if entry in associative array for this address
            # If not, update the location regardless if read or write.
            else:
                data = trans.data[i]
                uvm_info(self.get_type_name(),
                    sv.sformatf("%s to empty address...Updating address : %0h with data : %0h",
                    str(trans.read_write), int(trans.addr + i), int(data)), UVM_LOW)
                self.m_mem_expected[trans.addr + i] = trans.data[i]
                if trans.read_write == READ:
                    self.num_uninit_reads += 1
                elif (trans.read_write == WRITE):
                    self.num_writes += 1
        #  endfunction : memory_verify


    #  // report_phase
    #  virtual function void report_phase(uvm_phase phase)
    #    if(!disable_scoreboard):
    #      `uvm_info(get_type_name(),
    #        $sformatf("Reporting scoreboard information...\n%s", this.sprint()), UVM_LOW)
    #    end
    #  endfunction : report_phase

    #endclass : ubus_example_scoreboard
uvm_component_utils(ubus_example_scoreboard)
