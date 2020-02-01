#// 
#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
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
#
#
#program test
#
from uvm.comps.uvm_test import *
from uvm.macros import *
import cocotb
#from uvm_pkg import *
#`include "uvm_macros.svh"
#`include "tb_timer.svh"
#`include "tb_env.svh"
#
#tb_env env
#
#
#class test(uvm_test):
    #   `uvm_component_utils(test)
    #
    #   def __init__(self, name, parent=None)
    #      super().__init__(name, parent)
    #   endfunction
    #
    #@cocotb.coroutine
    #   def pre_main_phase(self, phase):
    #      phase.raise_objection(self)
    #      yield Timer(100, )
    #      phase.drop_objection(self)
    #   endtask
    #   
    #@cocotb.coroutine
    #   def main_phase(self, phase):
    #      phase.raise_objection(self)
    #      // Will cause a time-out
    #      // because we forgot to drop the objection
    #   endtask
    #   
    #@cocotb.coroutine
    #   def shutdown_phase(self, phase):
    #      phase.raise_objection(self)
    #      yield Timer(100, )
    #      phase.drop_objection(self)
    #   endtask
    #endclass
#
#
#initial
#begin
#   env = new("env")
#   run_test("test")
#end
#
#endprogram
