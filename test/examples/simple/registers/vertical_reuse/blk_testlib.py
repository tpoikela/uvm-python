#//
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
#
from uvm.comps.uvm_test import UVMTest
from uvm.macros import *
import cocotb
from blk_seqlib import *
from uvm.base.sv import sv
from uvm.base.uvm_root import uvm_top
from blk_env import blk_env

from blk_seqlib import *

class blk_R_test(UVMTest):

    #
    #   blk_env env
    #
    def __init__(self, name="blk_R_test", parent=None):
        super().__init__(name, parent)
        self.env = None  # blk_env

    def build_phase(self, phase):
        if (self.env is None):
            arr = []
            if (sv.cast(arr, uvm_top.find("env$"), blk_env)):
                self.env = arr[0]
            else:
                uvm_fatal("NO_ENV_ERR", "test_top unable to find 'env'")

    
    async def run_phase(self, phase):
        reset_seq = None  # uvm_sequence_base
        seq = None  # blk_R_test_seq
        phase.raise_objection(self)

        rst_seq = dut_reset_seq.type_id.create("rst_seq", self)
        rst_seq.vif = self.env.apb.vif
        await rst_seq.start(None)

        self.env.model.reset()

        seq = blk_R_test_seq.type_id.create("blk_R_test_seq",self)
        seq.model = self.env.model
        await seq.start(None)

        phase.drop_objection(self)


uvm_component_utils(blk_R_test)
