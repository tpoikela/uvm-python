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

from uvm.base.sv import sv, semaphore
from uvm.base import UVMComponent, UVM_HIGH, UVM_MEDIUM, UVM_INFO
from uvm.tlm1 import UVMBlockingPutImp, UVMGetPort
from uvm.macros import uvm_component_utils, uvm_info


class consumer(UVMComponent):
    #
    #  uvm_blocking_put_imp #(T,consumer #(T)) in
    #  uvm_get_port #(T) out

    def __init__(self, name, parent=None):
        UVMComponent.__init__(self, name, parent)
        self.input = UVMBlockingPutImp("in",self)
        self.out = UVMGetPort("out",self,0)
        self.count = 0
        self.lock = semaphore(1)

    
    async def run_phase(self, phase):
        while self.out.size():
            print("consumer run_phase in while-loop")
            p = []
            await self.out.get(p)
            await self.put(p[0])

    
    async def put(self, p):
        print("consumer put() called with count " + str(self.count))
        await self.lock.get()
        self.count += 1
        self.accept_tr(p)
        await Timer(10, "NS")
        #    #10
        self.begin_tr(p)
        #    #30; 
        await Timer(10, "NS")
        self.end_tr(p)
        uvm_info("consumer", sv.sformatf("Received %0s local_count=%0d",
            p.get_name(),self.count), UVM_MEDIUM)
        if self.uvm_report_enabled(UVM_HIGH,UVM_INFO,""):
             p.print_obj()
        self.lock.put()
    #endclass

uvm_component_utils(consumer)
#    `uvm_field_int(count,UVM_ALL_ON + UVM_READONLY + UVM_DEC)
#  `uvm_component_utils_end
