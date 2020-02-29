#//----------------------------------------------------------------------
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2010 Mentor Graphics Corporation
#//   Copyright 2010-2011 Cadence Design Systems, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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


import cocotb
from uvm.comps.uvm_test import UVMTest
from uvm.macros import *
from uvm.base.uvm_root import uvm_top
from uvm.base.sv import sv
from sys_seqlib import *
from sys_env import *


class sys_R_test(UVMTest):

    def __init__(self, name="sys_R_test", parent=None):
        super().__init__(name, parent)
        self.env = None  # sys_env

    def build_phase(self, phase):
        env = []
        if self.env is None:
            if sv.cast(env, uvm_top.find("env$"), sys_env) is True:
                self.env = env[0]
            else:
                uvm_fatal("SYS_TEST/NO_ENV", "Unable to find/cast sys_env")

    
    async def run_phase(self, phase):
        # reset_seq = None  # uvm_sequence_base
        seq = None  # sys_R_test_seq
        phase.raise_objection(self)

        # dut_reset_seq rst_seq
        rst_seq = dut_reset_seq.type_id.create("rst_seq", self)
        rst_seq.vif = self.env.vif
        await rst_seq.start(None)
        self.env.model.reset()

        seq = sys_R_test_seq.type_id.create("sys_R_test_seq",self)
        seq.model = self.env.model
        await seq.start(None)

        phase.drop_objection(self)

    #endclass

uvm_component_utils(sys_R_test)
