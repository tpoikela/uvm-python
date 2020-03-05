#
#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
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

# About: factory
# This example will illustrate the usage of uvm_factory methods.

# To get more details about the factory related methods, check the file:
#   - uvm/src/base/uvm_factory.py


from uvm.macros import *
from uvm import *
from packet_pkg import packet
from gen_pkg import gen
from env_pkg import env


#
#  env e;  //you need to use something from the package to have the
#          //factory registration occur.
#


class mygen(gen):
    def __init__(self, name, parent):
        super().__init__(name, parent)


    def get_packet(self):
        uvm_info("PKTGEN", sv.sformatf("Getting a packet from %s (%s)",
            self.get_full_name(), self.get_type_name()), UVM_MEDIUM)
        return super().get_packet()


# Use the macro in a class to implement factory registration along with other
# utilities (create, get_type_name). To just do factory registration, use the
# macro `uvm_object_registry(mygen,"mygen")
uvm_component_utils(mygen)

class mypacket(packet):
    #    constraint ct10 { addr >= 0  and  addr <= 10; }

    def __init__(self, name="mypacket"):
        super().__init__(name)
        self.my_packet_prop = 123

# Use the macro in after the class to implement factory registration along with other
# utilities (create, get_type_name).
uvm_object_utils(mypacket)


@cocotb.test()
async def module_top(dut):
    cs_ = UVMCoreService.get()
    factory = cs_.get_factory()
    gen.type_id.set_inst_override(mygen.get_type(), "uvm_test_top.gen1")
    packet.type_id.set_type_override(mypacket.get_type())
    factory.print_factory(1)

    # If a string is used to run_test, run_test will used the string based factory
    # create method to create an object of the desired type.
    await run_test("env")
