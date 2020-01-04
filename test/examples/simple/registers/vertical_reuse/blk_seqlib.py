#// 
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#// 
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use self file except in
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
from cocotb.triggers import *

from uvm.reg.uvm_reg_sequence import *
from uvm.reg.uvm_reg_model import *
from uvm.base.sv import sv
from uvm.macros import *
from uvm.seq.uvm_sequence import *


class dut_reset_seq(UVMSequence):

    def __init__(self, name="dut_reset_seq"):
        super().__init__(name)
        self.vif = None


    @cocotb.coroutine
    def body(self):
        self.vif.rst <= 1
        for i in range(5):
            yield FallingEdge(self.vif.clk)
        self.vif.rst <= 0


uvm_object_utils(dut_reset_seq)


class blk_R_test_seq(uvm_reg_sequence):


    def __init__(self, name="blk_R_test_seq"):
        super().__init__(name)
        self.model = None  # reg_block_B


    @cocotb.coroutine
    def body(self):
        status = 0
        n = 0

        print("YYY Starting blk_R_test_seq")
        # Initialize R with a random value then check against mirror
        data = sv.urandom()
        status = []
        yield self.model.R.write(status, data, parent=self)
        if status[0] != UVM_IS_OK:
            uvm_fatal("WRITE FAIL", "status not OK")
        print("YYY After R.write blk_R_test_seq")
        status = []
        yield self.model.R.mirror(status, UVM_CHECK, parent=self)
        if status[0] != UVM_IS_OK:
            uvm_fatal("MIRROR FAIL", "status not OK")
        print("YYY After R.mirror blk_R_test_seq")

        # Perform a random number of INC operations
        n = (sv.urandom() % 7) + 3
        uvm_info("blk_R_test_seq", sv.sformatf("Incrementing R %0d times...", n), UVM_NONE)
        #      repeat (n):
        #         model.CTL.write(status, reg_fld_B_CTL_CTL::INC, .parent(self))
        #         data++
        #         void'(model.R.predict(data))
        #      end
        #      // Check the final value
        #      model.R.mirror(status, UVM_CHECK, .parent(self))
        #
        #      // Perform a random number of DEC operations
        #      n = (sv.urandom() % 8) + 2
        #      `uvm_info("blk_R_test_seq", sv.sformatf("Decrementing R %0d times...", n), UVM_NONE)
        #      repeat (n):
        #         model.CTL.write(status, reg_fld_B_CTL_CTL::DEC, .parent(self))
        #         data--
        #         void'(model.R.predict(data))
        #      end
        #      // Check the final value
        #      model.R.mirror(status, UVM_CHECK, .parent(self))
        #
        #      // Reset the register and check
        #      model.CTL.write(status, reg_fld_B_CTL_CTL::CLR, .parent(self))
        #      void'(model.R.predict(0))
        #      model.R.mirror(status, UVM_CHECK, .parent(self))
        #   endtask
    #   
uvm_object_utils(blk_R_test_seq)
