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
from uvm.base.uvm_config_db import UVMConfigDb
from uvm.base.sv import sv
from uvm.macros import *

from blk_env import blk_env
from reg_S import *

from apb.apb_agent import apb_agent
from apb.apb_rw import reg2apb_adapter


class sys_env(UVMEnv):

    #   reg_sys_S model

    def __init__(self, name="sys_env", parent=None):
        super().__init__(name, parent)
        self.blk0 = None  # blk_env
        self.blk1 = None  # blk_env
        self.model = None  # reg_sys_S
        self.apb = None  # apb_agent
        self.vif = None
        self.all_ok = False


    def build_phase(self, phase):
        super().build_phase(phase)
        arr = []
        if UVMConfigDb.get(self, "apb", "vif", arr) is False:
            uvm_fatal("APB/SYS_ENV/NO_VIF", "Could not get vif from config_db")
        self.vif = arr[0]

        self.blk0 = blk_env.type_id.create("blk0", self)
        self.blk1 = blk_env.type_id.create("blk1", self)
        UVMConfigDb.set(self.blk0, "apb", "vif", arr[0])
        UVMConfigDb.set(self.blk1, "apb", "vif", arr[0])

        if self.model is None:
            self.model = reg_sys_S.type_id.create("reg_sys_S", None,
                self.get_full_name())
            self.model.build()
            self.model.lock_model()


        self.blk0.model = self.model.B[0]
        self.blk1.model = self.model.B[1]
        #
        self.apb = apb_agent.type_id.create("apb", self)
        #   endfunction: build_phase


    def connect_phase(self, phase):
        if self.model.get_parent() is None:
            reg2apb = reg2apb_adapter()
            self.model.default_map.set_sequencer(self.apb.sqr,reg2apb)
            self.model.default_map.set_auto_predict()

    def extract_phase(self, phase):
        if self.apb.mon.num_items > 0 and self.apb.mon.errors == 0:
            self.all_ok = True
        else:
            uvm_error("SYS_ENV_ERR", sv.sformatf("num_items: %0d, mon.errors: %0d",
                self.apb.mon.num_items, self.apb.mon.errors))

    #endclass: sys_env

uvm_component_utils(sys_env)
