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

import cocotb
from cocotb.triggers import *

from uvm.reg.uvm_reg_sequence import *
from uvm.reg.uvm_reg_model import *
from uvm.base.sv import sv
from uvm.macros import *
from uvm.seq.uvm_sequence import *
from reg_B import *


class dut_reset_seq(UVMSequence):

    def __init__(self, name="dut_reset_seq"):
        super().__init__(name)
        self.vif = None


    
    async def body(self):
        self.vif.rst <= 1
        for i in range(5):
            await FallingEdge(self.vif.clk)
        self.vif.rst <= 0


uvm_object_utils(dut_reset_seq)


class blk_R_test_seq(UVMRegSequence):


    def __init__(self, name="blk_R_test_seq"):
        super().__init__(name)
        self.model = None  # reg_block_B


    def check_status(self, status, msg):
        if status[0] != UVM_IS_OK:
            uvm_fatal(msg, "status not OK")

    
    async def body(self):
        status = 0
        n = 0

        # Initialize R with a random value then check against mirror
        data = sv.urandom()
        status = []
        await self.model.R.write(status, data, parent=self)
        self.check_status(status, "WRITE_FAIL")
        status = []
        await self.model.R.mirror(status, UVM_CHECK, parent=self)
        self.check_status(status, "MIRROR FAIL")

        # Perform a random number of INC operations
        n = (sv.urandom() % 7) + 3
        uvm_info("blk_R_test_seq", sv.sformatf("Incrementing R %0d times...", n), UVM_NONE)
        for i in range(n):
            status = []
            await self.model.CTL.write(status, reg_fld_B_CTL_CTL.INC, parent=self)
            self.check_status(status, "WRITE " + str(i) + " FAIL")
            data += 1
            self.model.R.predict(data)
        # Check the final value
        status = []
        await self.model.R.mirror(status, UVM_CHECK, parent=self)
        self.check_status(status, "MIRROR2 FAIL")

        # Perform a random number of DEC operations
        n = (sv.urandom() % 8) + 2
        uvm_info("blk_R_test_seq", sv.sformatf("Decrementing R %0d times...", n), UVM_NONE)
        for i in range(n):
            status = []
            await self.model.CTL.write(status, reg_fld_B_CTL_CTL.DEC, parent=self)
            self.check_status(status, "WRITE B." + str(i) + " FAIL (DEC OP)")
            data -= 1
            self.model.R.predict(data)

        # Check the final value
        status = []
        await self.model.R.mirror(status, UVM_CHECK, parent=self)
        self.check_status(status, "MIRROR3 FAIL")
        #
        # Reset the register and check
        status = []
        await self.model.CTL.write(status, reg_fld_B_CTL_CTL.CLR, parent=self)
        self.check_status(status, "WRITE4 FAIL")
        self.model.R.predict(0)
        status = []
        await self.model.R.mirror(status, UVM_CHECK, parent=self)
        self.check_status(status, "MIRROR4 FAIL")
        #   endtask
    #

uvm_object_utils(blk_R_test_seq)
