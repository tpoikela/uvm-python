#//
#// -------------------------------------------------------------
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2010-2011 Synopsys, Inc.
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

# Note: You can also import everything with 'from uvm import *'
from uvm.comps import UVMEnv
from uvm.macros import uvm_component_utils
from uvm.reg import UVMRegPredictor

from reg_model import reg_block_B
from apb.apb_agent import apb_agent
from apb.apb_rw import reg2apb_adapter


class tb_env(UVMEnv):

    #
    #   reg_block_B   regmodel
    #   apb_agent     apb
    #   uvm_reg_predictor#(apb_rw) predict

    def __init__(self, name="tb_env", parent=None):
        super().__init__(name, parent)
        self.regmodel = None
        self.apb = None
        self.predict = None


    def build_phase(self, phase):
        if self.regmodel is None:
            self.regmodel = reg_block_B.type_id.create("regmodel")
            self.regmodel.build()
            self.regmodel.lock_model()

        self.apb = apb_agent.type_id.create("apb", self)
        self.predict = UVMRegPredictor.type_id.create("predict", self)


    def connect_phase(self, phase):
        if self.regmodel.get_parent() is None:
            self.apb_adapter  = reg2apb_adapter("apb_adapter")
            self.regmodel.default_map.set_sequencer(self.apb.sqr, self.apb_adapter)
            self.regmodel.default_map.set_auto_predict(0)

            self.apb.mon.ap.connect(self.predict.bus_in)

            self.predict.map = self.regmodel.default_map
            self.predict.adapter = self.apb_adapter


uvm_component_utils(tb_env)
