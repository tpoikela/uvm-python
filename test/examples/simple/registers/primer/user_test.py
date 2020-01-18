#// 
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
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
#
#class user_test_seq(uvm_reg_sequence):
    #
    #   def __init__(self, name="user_test_seq")
    #      super().__init__(name)
    #    self.addr = None  # type: bit
    #    self.data = None  # type: logic
    #   endfunction : new
    #
    #   rand bit   [31:0] addr
    #   rand logic [31:0] data
    #   
    #   `uvm_object_utils(user_test_seq)
    #   
    #@cocotb.coroutine
    #   def body(self)
    #      reg_block_slave model
    #
    #      sv.cast(model, self.model)
    #      
    #      // Randomize the content of 10 random indexed registers
    #      repeat (10):
    #         bit [7:0]         idx = sv.urandom
    #         uvm_reg_data_t    data = sv.urandom
    #         uvm_status_e status
    #
    #         model.TABLES[idx].write(status, data, .parent(self))
    #      end
    #
    #      // Find which indexed registers are non-zero
    #      foreach (model.TABLES[i]):
    #         uvm_reg_data_t    data
    #         uvm_status_e status
    #         
    #         model.TABLES[i].read(status, data)
    #         if (data != 0) $write("TABLES[%0d] is 0x%h...\n", i, data)
    #      end
    #   endtask : body
    #
    #endclass : user_test_seq
#
#
from uvm.reg.uvm_reg_sequence import *
from uvm.macros import *
import cocotb
#
