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

from uvm.comps.uvm_env import UVMEnv
from uvm import (UVMConfigDb, sv, uvm_top, uvm_info, uvm_error, UVM_MEDIUM)
from classA import ClassA
from classB import ClassB


class my_env(UVMEnv):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.debug = 0
        self.inst1 = None
        self.inst2 = None


    def build_phase(self, phase):
        super().build_phase(phase)
        arr = []
        if UVMConfigDb.get(self, "", "debug", arr) is True:
            self.debug = arr[0]
        UVMConfigDb.set(self, "inst1.u2", "v", 5)
        UVMConfigDb.set(self, "inst2.u1", "v", 3)
        UVMConfigDb.set(self, "inst1.*", "s", 0x10)

        sv.display("%s: In Build: debug = %0d", self.get_full_name(), self.debug)

        self.inst1 = ClassA("inst1", self)
        self.inst2 = ClassB("inst2", self)
        if UVMConfigDb.get(uvm_top, "topenv", "should_match", arr):
            uvm_info("MATCH_OK", "should_match found from DB", UVM_MEDIUM)
        else:
            uvm_error("MATCH_ERROR", "should_match NOT found from DB")


    def get_type_name(self):
        return "my_env"

    def do_print(self, printer):
        printer.print_field("debug", self.debug, 1)


    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        uvm_top.print_topology()
        await Timer(10, "NS")
        phase.drop_objection(self)
