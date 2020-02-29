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
from uvm.macros import uvm_info, uvm_component_utils
from uvm import *
#from packet_pkg import p
from gen_pkg import gen


class env(UVMEnv):
    #    gen gen1
    #

    def __init__(self, name, parent):
        super().__init__(name, parent)
        # use the factory to create the generator
        self.gen1 = gen.type_id.create("gen1", self)


    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        uvm_default_tree_printer.knobs.separator = ""
        for i in range(5):
            await Timer(15, "NS")
            p = self.gen1.get_packet()
            if hasattr(p, 'my_packet_prop') is False:
                uvm_fatal("PKT_ERR", "Wrong packet type created: " + str(p))
            uvm_info("PKTGEN", sv.sformatf("Got packet: %s", p.sprint(uvm_default_tree_printer)), UVM_NONE)
        await Timer(15, "NS")
        phase.drop_objection(self)


#    //Use the macro in a class to implement factory registration along with other
#    //utilities (create, get_type_name). For only factory registration, use the
#    // macro `uvm_component_registry(env,"env").
uvm_component_utils(env)
