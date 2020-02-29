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

import cocotb
from cocotb.triggers import Timer

from uvm.base.uvm_component import UVMComponent
from uvm.macros import uvm_fatal, uvm_component_utils
from uvm.base.uvm_config_db import UVMConfigDb

#//
#// Generic phase timer
#//
#// All time-out values are interprted in ns
#//
#// To set time-out values:
#//
#// - For one phase:
#//
#//   uvm_config_db#(time)::set(null, "global_timer.main", "timeout", 100);
#//
#// - For multiple phases:
#//
#//   uvm_config_db#(time)::set(null, "global_timer.pre*", "timeout", 100);
#//


class tb_timer(UVMComponent):

    m_global = None

    def __init__(self, name, parent=None):
        super().__init__(name, parent)


    
    async def run_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "run", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in run phase")

    #
    
    async def pre_reset_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "pre_reset", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in pre_reset phase")

    #
    
    async def reset_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "reset", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in reset phase")

    #
    
    async def post_reset_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "post_reset", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in post_reset phase")

    #
    
    async def pre_configure_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "pre_configure", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in pre_configure phase")

    #
    
    async def configure_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "configure", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in configure phase")

    #
    
    async def post_configure_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "post_configure", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in post_configure phase")

    #
    
    async def pre_main_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "pre_main", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in pre_main phase")

    #
    
    async def main_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "main", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in main phase")

    #
    
    async def post_main_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "post_main", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in post_main phase")

    #
    
    async def pre_shutdown_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "pre_shutdown", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in pre_shutdown phase")

    #
    
    async def shutdown_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "shutdown", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in shutdown phase")

    #
    
    async def post_shutdown_phase(self, phase):
        t = []
        if (UVMConfigDb.get(self, "post_shutdown", "timeout", t) and t[0] > 0):
            await Timer(t[0], "NS")
            uvm_fatal("TIMEOUT", "Time-out expired in post_shutdown phase")



uvm_component_utils(tb_timer)

#tb_timer.m_global = tb_timer("global_timer", None)
