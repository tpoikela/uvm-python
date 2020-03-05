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
#class producer #(type T=packet) extends uvm_component

import cocotb
from cocotb.triggers import Timer

from uvm.base.sv import sv
from uvm.base import (
        UVMComponent, UVMConfigDb, UVM_MEDIUM, UVM_NONE, UVM_HIGH, UVM_INFO)
from uvm.tlm1 import UVMBlockingPutPort
from uvm.macros import uvm_component_utils, uvm_info
from packet import packet


class producer(UVMComponent):
    #
    #  uvm_blocking_put_port #(T) out
    #
    def __init__(self, name, parent=None,T=packet):
        UVMComponent.__init__(self, name, parent)
        self.out = UVMBlockingPutPort("out", self)
        self.num_packets = 10
        nn = []
        self.T = T
        self.add_objection = True
        self.proto = self.T("my_packet")
        if UVMConfigDb.get(self, "", "num_packets", nn):
            self.num_packets = nn[0]

    
    async def run_phase(self, phase):
        if self.add_objection:
            phase.raise_objection(self)
        num = ""
        uvm_info("producer", "Starting with packet " + str(self.num_packets), UVM_MEDIUM)

        for count in range(self.num_packets):

            p = self.proto.clone()

            num = str(count)
            p.set_name(self.get_name() + "-" + num)
            p.set_initiator(self)

            if self.recording_detail != UVM_NONE:
                p.enable_recording(self.get_tr_stream("packet_stream"))

            p.randomize()
            uvm_info("producer", sv.sformatf("Sending %s",p.get_name()), UVM_MEDIUM)

            if self.uvm_report_enabled(UVM_HIGH,UVM_INFO,""):
                p.print_obj()

            await self.out.put(p)
            await Timer(10, "NS")

        uvm_info("producer", "Exiting.", UVM_MEDIUM)
        if self.add_objection:
            phase.drop_objection(self)


uvm_component_utils(producer)
#    `uvm_field_object(proto, UVM_ALL_ON + UVM_REFERENCE)
#    `uvm_field_int(num_packets, UVM_ALL_ON + UVM_DEC)
#    `uvm_field_int(count, UVM_ALL_ON + UVM_DEC + UVM_READONLY)
#  `uvm_component_utils_end
