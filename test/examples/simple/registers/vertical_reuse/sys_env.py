#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
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


from uvm.comps.uvm_env import *
from uvm.macros import *

from blk_env import blk_env
from apb.apb_agent import apb_agent
from reg_S import *


class sys_env(UVMEnv):

    #   reg_sys_S model

    def __init__(self, name="sys_env", parent=None):
        super().__init__(name, parent)
        self.blk0 = None  # blk_env
        self.blk1 = None  # blk_env
        self.model = None  # reg_sys_S
        self.apb = None  # apb_agent


    def build_phase(self, phase):
        super().build_phase(phase)

        self.blk0 = blk_env.type_id.create("blk0", self)
        self.blk1 = blk_env.type_id.create("blk1", self)

        if self.model is None:
            self.model = reg_sys_S.type_id.create("reg_sys_S",None,
                self.get_full_name())
            self.model.build()
            self.model.lock_model()


        #      blk0.model = model.B[0]
        #      blk1.model = model.B[1]
        #
        self.apb = apb_agent.type_id.create("apb", self)
        #   endfunction: build_phase


    #   def connect_phase(self, phase):
    #      if (model.get_parent() is None):
    #         reg2apb_adapter reg2apb = new
    #         model.default_map.set_sequencer(apb.sqr,reg2apb)
    #         model.default_map.set_auto_predict()
    #      end
    #   endfunction
    #
    #endclass: sys_env

uvm_component_utils(sys_env)
