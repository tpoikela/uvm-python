#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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


from uvm.base import *
from uvm.comps import UVMEnv
from uvm.macros import uvm_component_utils
from ubus_example_scoreboard import ubus_example_scoreboard

from ubus_env import ubus_env


class ubus_example_tb(UVMEnv):
    #  // Provide implementations of virtual methods such as get_type_name and create

    def __init__(self, name, parent=None):
        UVMEnv.__init__(self, name, parent)
        self.scoreboard0 = None
        self.ubus0 = None

    #  // build_phase
    def build_phase(self, phase):
        UVMEnv.build_phase(self, phase)

        num_masters = []
        if UVMConfigDb.get(self, "ubus0", "num_masters", num_masters):
            num_masters = num_masters[0]
        else:
            num_masters = 1
        UVMConfigDb.set(self, "ubus0", "num_masters", num_masters)

        num_slaves = []
        if UVMConfigDb.get(self, "ubus0", "num_slaves", num_slaves):
            num_slaves = num_slaves[0]
        else:
            num_slaves = 1
        UVMConfigDb.set(self, "ubus0", "num_slaves", num_slaves)

        self.ubus0 = ubus_env.type_id.create("ubus0", self)
        self.scoreboard0 = ubus_example_scoreboard.type_id.create("scoreboard0",
            self)

    def connect_phase(self, phase):
        # Connect slave0 monitor to scoreboard
        self.ubus0.slaves[0].monitor.item_collected_port.connect(
            self.scoreboard0.item_collected_export)

    def end_of_elaboration_phase(self, phase):
        # Set up slave address map for ubus0 (basic default)
        self.ubus0.set_slave_address_map("slaves[0]", 0, 0xffff)


uvm_component_utils(ubus_example_tb)
