#//
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

#
# About: examples/uvm_tlm/bidir
# This example will illustrate how to create two threads one is the master and the other
# is the slave. The two threads are completely independent, each one of the two threads
# has two types of ports interfaces puts and gets.
#
# The communication between the two channel will be done through a uvm_tlm_req_rsp channel,
# which can handle the dual Request and Response of each thread
#
# This example will use The uvm_tlm_req_rsp channel, transaction-level ports, and the messaging
# facilities as part of the UVM library.

import cocotb
from uvm import *


#//----------------------------------------------------------------------
#// class master
#//----------------------------------------------------------------------

class master(UVMComponent):
    #
    #  uvm_blocking_put_port #(int) req_port
    #  uvm_blocking_get_port #(int) rsp_port
    #
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.req_port = UVMBlockingPutPort("req_port", self)
        self.rsp_port = UVMBlockingGetPort("rsp_port", self)

    
    async def run_phase(self, phase):
        req_proc = cocotb.fork(self.request_process())
        rsp_proc = cocotb.fork(self.response_process())
        await sv.fork_join([req_proc, rsp_proc])
        #    fork
        #      request_process
        #      response_process
        #    join


    
    async def request_process(self):
        request_str = ""
        for i in range(10):
          request_str = sv.sformatf("%d", i)
          self.uvm_report_info("sending request   ", request_str, UVM_MEDIUM)
          await self.req_port.put(i)


    
    async def response_process(self):
        response = 0
        response_str = ""
        while True:
            arr = []
            await self.rsp_port.get(arr);   
            response = arr[0]
            response_str = sv.sformatf("%d", response)
            self.uvm_report_info("receiving response", response_str)



#//----------------------------------------------------------------------
#// class slave
#//----------------------------------------------------------------------

class slave(UVMComponent):


    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.req_port = UVMBlockingGetPort("req_port", self)
        self.rsp_port = UVMBlockingPutPort("rsp_port", self)

    
    async def run_phase(self, phase):
        request = 0
        response = 0
        request_str = ""
        response_str = ""

        while True:
            arr = []
            await self.req_port.get(arr)
            request = arr[0]
            request_str = sv.sformatf("%d", request)
            self.uvm_report_info("receiving request  ", request_str, UVM_MEDIUM)
            response = request
            response_str = sv.sformatf("%d", response)
            self.uvm_report_info("sending response   ", response_str, UVM_MEDIUM)
            await self.rsp_port.put(response)
           

#//----------------------------------------------------------------------
#// class bidir_env
#//----------------------------------------------------------------------

class bidir_env(UVMEnv):


    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.m = master("master", self)
        self.s = slave("slave", self)
        self.req_rsp = UVMTLMReqRspChannel("req_rsp_channel", self)


    def connect_phase(self, phase):
        self.m.req_port.connect(self.req_rsp.blocking_put_request_export)
        self.m.rsp_port.connect(self.req_rsp.blocking_get_response_export)
        self.s.req_port.connect(self.req_rsp.blocking_get_request_export)
        self.s.rsp_port.connect(self.req_rsp.blocking_put_response_export)


    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        #10
        await Timer(10, "NS")
        phase.drop_objection(self)


#//----------------------------------------------------------------------
#// module top
#//----------------------------------------------------------------------

@cocotb.test()
async def module_top(dut):
    env = bidir_env("env", None)
    uvm_info("TOP_ENV", "top-level env is " + env.get_name(), UVM_LOW)
    await run_test()

