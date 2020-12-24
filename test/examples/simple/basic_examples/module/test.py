#----------------------------------------------------------------------
#   Copyright 2007-2010 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010-2011 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#----------------------------------------------------------------------

import cocotb
from cocotb.triggers import Timer
from cocotb.utils import get_sim_time

from uvm import UVMObject, UVMComponent, UVMDebug
# from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_config_db import UVMConfigDb, UVMConfigDbOptions
from uvm.base.uvm_root import uvm_top
from uvm.base.sv import sv
from uvm.base.uvm_object_globals import UVM_HEX
from uvm.base.uvm_globals import run_test
from uvm.macros.uvm_message_defines import uvm_error

UVMDebug.no_debug()

#----------------------------------------------------------------------
# lower
#----------------------------------------------------------------------


class lower(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.data = 0
        self.str = ""

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(10)
        print("{}: {} HI".format(get_sim_time(), self.get_full_name()))
        phase.drop_objection(self)

    def get_type_name(self):
        return "lower"

    def build_phase(self, phase):
        val_arr = []
        if UVMConfigDb.get(self, "", "data", val_arr):
            self.data = val_arr[0]
        val_arr = []
        if UVMConfigDb.get(self, "", "str", val_arr):
            self.str = val_arr[0]

    def do_print(self, printer):
        printer.print_field("data", self.data, 32)
        printer.print_string("str", self.str)

#----------------------------------------------------------------------
# myunit
#----------------------------------------------------------------------


class myunit(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        UVMConfigDbOptions.turn_on_tracing()

        self.corr_data1 = 55
        self.corr_data2 = 101
        UVMConfigDb.set(self, "l1", "str", "hi")
        UVMConfigDb.set(self, "*", "data", 0x100)
        UVMConfigDb.set(self, "l1", "data", self.corr_data1)
        UVMConfigDb.set(self, "l2", "data", self.corr_data2)

        self.l1 = lower("l1", self)
        self.l2 = lower("l2", self)
        self.l1.data = 0x30
        self.l2.data = 0x40
        self.a = [None] * 5
        for i in range(5):
            self.a[i] = i*i

    
    async def run_phase(self, phase):
        # Check config from initial block
        if self.l1.data != self.corr_data1:
            uvm_error("BADCFG", sv.sformatf("Expected l1.data = %0d, got %0d",
                self.corr_data1, self.l1.data))
        if self.l2.data != self.corr_data2:
            uvm_error("BADCFG", sv.sformatf("Expected l2.data = %0d, got %0d",
                self.corr_data2, self.l2.data))
        if self.l1.str != self.l2.str and self.l1.str != "hi":
            uvm_error("BADCFG", sv.sformatf(
                "Expected l1.str = \"hi\" and l2.str = \"hi\", got l1.str = \"%s\" and l2.str = \"%s\"",
                self.l1.str, self.l2.str))
        phase.raise_objection(self)
        await Timer(10)
        #10 $display("%0t: %s HI", $time, get_full_name());
        phase.drop_objection(self)

    def get_type_name(self):
        return "myunit"

    def do_print(self, printer):
        printer.print_array_header("a", len(self.a))
        for i in range(len(self.a)):
            printer.print_field(sv.sformatf("a[%0d]", i), self.a[i], 32, UVM_HEX, "[")
        printer.print_array_footer()

#----------------------------------------------------------------------
# mydata
#----------------------------------------------------------------------

class mydata(UVMObject):
    #`uvm_object_registry(mydata,"mydata")

    def __init__(self, name=""):
        UVMObject.__init__(self, name)

    def create(self, name="mydata"):
        d = mydata()
        d.set_name(name)
        return d

    def get_type_name(self):
        return "mydata"


#----------------------------------------------------------------------
# top
#----------------------------------------------------------------------

@cocotb.test()
async def test_module_top(dut):

    mu = myunit("mu", None)
    bar = mydata()

    uvm_top.finish_on_completion = 0
    UVMConfigDb.set(None, "mu.*", "data", 101)
    UVMConfigDb.set(None, "mu.*", "str", "hi")
    UVMConfigDb.set(None, "mu.l1", "data", 55)
    UVMConfigDb.set(None, "mu.*", "obj", bar)
    mu.print_obj()
    await run_test()
    mu.print_obj()
