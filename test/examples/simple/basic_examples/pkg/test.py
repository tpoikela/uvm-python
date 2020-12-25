#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela (tpoikela)
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
from cocotb.utils import get_sim_time
from cocotb.clock import Clock

from uvm import UVMObject, UVMComponent, UVMDebug, UVM_HEX, uvm_fatal
from uvm.base.sv import sv
from uvm.base.uvm_globals import run_test
from uvm.base.uvm_config_db import UVMConfigDb, UVMConfigDbOptions
from uvm.base.uvm_coreservice import UVMCoreService
from uvm.base.uvm_global_vars import uvm_default_tree_printer

from uvm.macros import uvm_object_utils

#  //--------------------------------------------------------------------
#  // lower
#  //--------------------------------------------------------------------


class lower(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.data = 0
        self.str = ""
        self.comp_id = -1

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(10, "NS")
        print("{}: {} HI".format(get_sim_time(), self.get_full_name()))
        await Timer(10, "NS")
        if self.comp_id == 2:
            uvm_fatal("COMP_ID_2", "run_phase() should be killed before fatal")
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


#  //--------------------------------------------------------------------
#  // myunit
#  //--------------------------------------------------------------------
class myunit(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.l1 = lower("l1", self)
        self.l1.comp_id = 1
        self.l2 = lower("l2", self)
        # TODO set this to cause fatal: self.l2.comp_id = 2
        UVMConfigDb.set(self, "l1", "str", "hi")
        UVMConfigDb.set(self, "*", "data", 0x100)
        self.l1.data = 0x30
        self.l2.data = 0x40
        self.a = [None] * 5
        for i in range(5):
            self.a[i] = i*i

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(10, "NS")
        #10 $display("%0t: %s HI", $time, get_full_name())
        phase.drop_objection(self)

    def get_type_name(self):
        return "myunit"

    def do_print(self, printer):
        printer.print_array_header("a", len(self.a))
        for i in range(len(self.a)):
            printer.print_field(sv.sformatf("a[%0d]", i), self.a[i], 32, UVM_HEX, "[")
        printer.print_array_footer()

#  // Factory registration
#
#  //--------------------------------------------------------------------
#  // lower_wrapper
#  //--------------------------------------------------------------------
#  class lower_wrapper extends uvm_object_wrapper
#
#    function uvm_component create_component(string name, uvm_component parent)
#      lower u
#      u = new(name, parent)
#      return u
#    endfunction
#
#    function string get_type_name()
#      return "lower"
#    endfunction
#
#    static function bit register_me(); uvm_coreservice_t cs_ = uvm_coreservice_t::get()
#
#      uvm_factory factory = cs_.get_factory()
#      lower_wrapper w; w = new
#      factory.register(w)
#      return 1
#    endfunction
#
#    static bit is_registered = register_me()


#  //--------------------------------------------------------------------
#  // myunit_wrapper
#  //--------------------------------------------------------------------
#  class myunit_wrapper extends uvm_object_wrapper
#
#    function uvm_component create_component(string name, uvm_component parent)
#      myunit u
#      u = new(name, parent)
#      return u
#    endfunction
#
#    function string get_type_name()
#      return "myunit"
#    endfunction
#
#    static function bit register_me(); uvm_coreservice_t cs_ = uvm_coreservice_t::get()
#
#      uvm_factory factory = cs_.get_factory()
#      myunit_wrapper w; w = new
#      factory.register(w)
#      return 1
#    endfunction
#
#    static bit is_registered = register_me()
#  endclass
#

#  //--------------------------------------------------------------------
#  // mydata
#  //--------------------------------------------------------------------

class mydata(UVMObject):
    #    `uvm_object_utils(mydata)
    #
    def __init__(self, name="mydata"):
        UVMObject.__init__(self, name)
uvm_object_utils(UVMObject)

#  //--------------------------------------------------------------------
#  // mydata_wrapper
#  //--------------------------------------------------------------------
#  class mydata_wrapper extends uvm_object_wrapper
#
#    function uvm_object create_object(string name="")
#      mydata u
#      u = new
#      if(name !="") u.set_name(name)
#      return u
#    endfunction
#
#    function string get_type_name()
#      return "myobject"
#    endfunction
#
#    static function bit register_me(); uvm_coreservice_t cs_ = uvm_coreservice_t::get()
#
#      uvm_factory factory = cs_.get_factory()
#      mydata_wrapper w; w = new
#      factory.register(w)
#      return 1
#    endfunction
#
#    static bit is_registered = register_me()
#  endclass
#`endif


#----------------------------------------------------------------------
# top
#----------------------------------------------------------------------


async def initial1():
    await run_test()


async def initial2(mu):
    await Timer(5, "NS")
    if mu.l1 is not None:
        print(str(mu.l1.get_name()))
        # TODO seems to be failing with async-await
        #mu.l1.kill()
    else:
        raise Exception("Oh no.")


@cocotb.test()
async def test_module_top(dut):
    mu = myunit("mu", None)
    bar = mydata()
    cs_ = UVMCoreService.get()
    factory = cs_.get_factory()

    UVMConfigDb.set(None, "mu.*", "data", 101)
    UVMConfigDb.set(None, "mu.*", "str", "hi")
    UVMConfigDb.set(None, "mu.l1", "data", 55)
    UVMConfigDb.set(None, "mu.*", "obj", bar)
    mu.print_config_settings("", None, 1)
    uvm_default_printer = uvm_default_tree_printer
    mu.print_obj()
    factory.print_factory(1)
    mu.print_obj()

    # tpoikela: Clock required by ghdl, otherwise scheduler throws error
    cocotb.fork(Clock(dut.clk, 10, "NS").start())

    # Fork 2 initial tasks
    task1 = cocotb.fork(initial1())
    task2 = cocotb.fork(initial2(mu))
    await sv.fork_join([task1, task2])
