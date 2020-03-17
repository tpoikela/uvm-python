#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
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

from uvm.base.uvm_component import *
from uvm.macros import *
from uvm import *

from apb.apb_agent import apb_agent
from reg_model import reg_block_slave
from apb.apb_rw import reg2apb_adapter


class tb_env(UVMComponent):

    #    reg_block_slave model;
    #    apb_agent apb
    #
    def __init__(self, name, parent=None):
        super().__init__(name,parent)
        self.model = None  # type: reg_block_slave
        self.apb = None  # type: apb_agent


    def build_phase(self, phase):
        dut = []
        if UVMConfigDb.get(self, "", "dut", dut):
            dut = dut[0]
        if self.model is None:
            self.model = reg_block_slave.type_id.create("model", self)
            if hasattr(dut, 'NSESS'):
                self.model.nsession = dut.NSESS.value
            elif sv.test_plusargs("NSESS"):
                self.model.nsession = sv.value_plusargs("NSESS")
            else:
                self.model.nsession = 128
            self.model.build()
            self.model.lock_model()

        self.apb = apb_agent.type_id.create("apb", self)


    def connect_phase(self, phase):
        fname = open('uvm_logfile.txt', 'w+')
        self.set_report_default_file_hier(fname)
        self.set_report_severity_action_hier(UVM_INFO, UVM_LOG | UVM_DISPLAY)
        if self.model.get_parent() is None:
            reg2apb = reg2apb_adapter()
            self.model.default_map.set_sequencer(self.apb.sqr, reg2apb)
            self.model.default_map.set_auto_predict(1)



    def end_of_elaboration(self):
        self.model.print_obj()



uvm_component_utils(tb_env)
