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
#class tb_env(uvm_env):
    #   `uvm_component_utils(tb_env)
    #
    #   def __init__(self, name, parent=None)
    #      super().__init__(name, parent)
    #   endfunction
    #
    #   def void build_phase(self,uvm_phase phase):
    #      UVMConfigDb.set(None, "global_timer.*",    "timeout", 1000)
    #      UVMConfigDb.set(None, "global_timer.main", "timeout", 3000)
    #      UVMConfigDb.set(None, "global_timer.run",  "timeout", 0)
    #   endfunction
    #
    #   
    #@cocotb.coroutine
    #   def reset_phase(self, phase):
    #      phase.raise_objection(self)
    #      yield Timer(20, )
    #      phase.drop_objection(self)
    #   endtask
    #   
    #@cocotb.coroutine
    #   def configure_phase(self, phase):
    #      phase.raise_objection(self)
    #      yield Timer(200, )
    #      phase.drop_objection(self)
    #   endtask
    #   
    #@cocotb.coroutine
    #   def main_phase(self, phase):
    #      phase.raise_objection(self)
    #      yield Timer(1000, )
    #      phase.drop_objection(self)
    #   endtask
    #
    #@cocotb.coroutine
    #   def shutdown_phase(self, phase):
    #      phase.raise_objection(self)
    #      yield Timer(10, )
    #      phase.drop_objection(self)
    #   endtask
from uvm.comps.uvm_env import *
from uvm.macros import *
from uvm.base.uvm_config_db import *
import cocotb
    #endclass
