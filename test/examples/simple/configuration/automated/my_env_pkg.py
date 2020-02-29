#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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
from cocotb.triggers import Timer
from uvm import (UVMEnv, UVMConfigDb, sv, uvm_top, UVM_DEFAULT)
from uvm.macros import *

from classA import A
from classB import B


class my_env(UVMEnv):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.debug = 0
        self.inst1 = None
        self.inst2 = None


    def build_phase(self, phase):
        super().build_phase(phase)
        UVMConfigDb.set(self, "inst1.u2", "v", 5)
        UVMConfigDb.set(self, "inst2.u1", "v", 3)
        UVMConfigDb.set(self, "inst1.*", "s", 0x10)

        sv.display("%s: In Build: debug = %0d", self.get_full_name(), self.debug)

        self.inst1 = A("inst1", self)
        self.inst2 = B("inst2", self)

    def connect_phase(self, phase):
        if self.inst1.u2.v != 5:
            uvm_error("CONF_VAL_ERR", "Value should 5 but got " +
                    str(self.inst1.u2.v))
        if self.inst1.u1.my_conf_obj is None:
            uvm_error("CONF_VAL_ERR", "Obj should've got value but was None")
        if self.inst1.u2.my_conf_obj is not None:
            uvm_error("CONF_VAL_ERR", "Obj should've got None but was something else")
        if self.inst1.u1.tag != 'I am tagged':
            uvm_error("STR_VAL_ERR", "Expected 'I am tagged'. Got: " +
                self.inst1.u1.tag)

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        uvm_top.print_topology()
        await Timer(10, "NS")
        phase.drop_objection(self)


uvm_component_utils_begin(my_env)
uvm_field_int('debug', UVM_DEFAULT)
uvm_component_utils_end(my_env)
