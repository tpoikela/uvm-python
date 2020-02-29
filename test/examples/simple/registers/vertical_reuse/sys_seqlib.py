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

from uvm import sv
from uvm.seq import UVMSequence
from uvm.reg.uvm_reg_sequence import *
from uvm.macros import *

from blk_seqlib import *


class dut_reset_seq(UVMSequence):
    #
    def __init__(self, name="dut_reset_seq"):
        super().__init__(name)
        self.vif = None

    #
    
    async def body(self):
        self.vif.rst <= 1
        for i in range(5):
            await FallingEdge(self.vif.clk)
        self.vif.rst <= 0

    #endclass

uvm_object_utils(dut_reset_seq)


class sys_R_test_seq(UVMRegSequence):

    def __init__(self, name="sys_R_test_seq"):
        super().__init__(name)
        self.model = None  # reg_sys_S


    
    async def body(self):
        if self.model is None:
            uvm_fatal("NO_REG","RegModel model handle is None")
            return
        for i in range(2):
            await self.start_blk_seq(i)


    
    async def start_blk_seq(self, i):
        # fork
        seq = blk_R_test_seq.type_id.create(sv.sformatf("blk_seq%0d",i),
                None, self.get_full_name())
        seq.model = self.model.B[i]
        await seq.start(None, self)
        #end join_none


    #endclass

uvm_object_utils(sys_R_test_seq)
