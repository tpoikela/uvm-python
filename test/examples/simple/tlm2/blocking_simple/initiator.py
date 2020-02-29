#//----------------------------------------------------------------------
#//   Copyright 2010-2011 Mentor Graphics Corporation
#//   Copyright 2010-2011 Synopsys, Inc
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
from uvm import (UVMComponent, uvm_component_utils, UVMTLMTime,
    UVMTLMBInitiatorSocket)

from uvm.macros import *
from apb_rw import apb_rw


class initiator(UVMComponent):
    #   uvm_tlm_b_initiator_socket#(apb_rw) sock


    def __init__(self, name="initiator", parent=None):
        super().__init__(name, parent)
        self.sock = UVMTLMBInitiatorSocket("sock", self)  # (apb_rw)("sock", self)

    #   //
    #   // Execute a simple read-modify-write
    #   //
    
    async def run_phase(self, phase):
        delay = UVMTLMTime()
        phase.raise_objection(self)
        for i in range(10):
            rw = apb_rw.type_id.create("rw",None,self.get_full_name())
            rw.kind = apb_rw.READ
            rw.addr = 0x0000FF00
            rw.data = i + 1

            await self.sock.b_transport(rw, delay)

            # Ok to reuse the same RW instance
            rw.kind = apb_rw.WRITE
            rw.data = ~rw.data

            await self.sock.b_transport(rw, delay)
        phase.drop_objection(self)


uvm_component_utils(initiator)
