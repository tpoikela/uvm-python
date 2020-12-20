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


from uvm.comps.uvm_env import UVMEnv
from uvm.macros import *

from apb.apb_agent import apb_agent
from apb.apb_rw import reg2apb_adapter
from reg_B import reg_block_B


class blk_env(UVMEnv):


    def __init__(self, name="blk_env", parent=None):
        super().__init__(name, parent)
        self.model = None  # reg_block_B
        self.apb = None  # apb_agent
        self.all_ok = False

    def build_phase(self, phase):
        super().build_phase(phase)

        if self.model is None:
            self.model = reg_block_B.type_id.create("reg_blk_B")
            self.model.build()
            self.model.lock_model()
            self.apb = apb_agent.type_id.create("apb",self)


    def connect_phase(self, phase):
        if self.model.get_parent() is None:
            reg2apb = reg2apb_adapter()
            self.model.default_map.set_sequencer(self.apb.sqr, reg2apb)
            self.model.default_map.set_auto_predict()


    def report_phase(self, phase):
        if self.apb is not None and self.apb.error is False:
            self.all_ok = True
        elif self.apb is not None and self.apb.error is True:
            uvm_error("BLK_ENV", "Found errors in APB agent")


uvm_component_utils(blk_env)
