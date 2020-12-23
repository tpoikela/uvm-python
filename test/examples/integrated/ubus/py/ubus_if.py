#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela
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
from cocotb.triggers import RisingEdge, Timer, Combine, Edge, FallingEdge

from uvm.base.sv import sv_if, sv

#/******************************************************************************
#
#  FILE : ubus_if.py
#
# ******************************************************************************/

class ubus_if(sv_if):

    #  // Actual Signals
    #  logic       [15:0] sig_request;
    #  logic       [15:0] sig_grant;
    #  logic              sig_wait;
    #  logic              sig_error;
    #
    #  logic              rw;

    #assign sig_data = rw ? sig_data_out : 8'bz;
    def __init__(self, dut):
        bus_map = {"sig_reset": "reset", "sig_clock": "clock", "sig_size":
                "size", "sig_read": "read", "sig_write": "write",
                "sig_bip": "bip", "sig_start": "start", "sig_addr": "addr",
                "sig_data": "data", "sig_data_out": "data",
                "sig_error": "error", "sig_wait": "wait",
                "sig_request": "req_master_0",
                "sig_grant": "gnt_master_0"}
        sv_if.__init__(self, dut, "ubus", bus_map)
        self.slave_en = 0
        self.sig_req = [dut.ubus_req_master_0, dut.ubus_req_master_1]
        self.sig_gnt = [dut.ubus_gnt_master_0, dut.ubus_gnt_master_1]
        # Control flags
        self.has_checks = True
        self.has_coverage = True

    
    async def start(self):
        a = cocotb.fork(self.drive_data())
        b = cocotb.fork(self.always())
        c = cocotb.fork(self.always_assertions())
        await sv.fork_join([a, b, c])
        # await [a, b, c]

    
    async def drive_data(self):
        while True:
            await Combine(Edge(self.sig_data_out), Edge(self.sig_data))
            if self.slave_en == 1:
                self.sig_data <= self.sig_data_out.value

    
    async def always(self):
        if self.has_checks is True:
            while True:
                await RisingEdge(self.sig_reset)
        else:
            await Timer(0, "NS")


    
    async def always_assertions(self):
        while True:
            await FallingEdge(self.sig_clock)
        #// Coverage and assertions to be implemented here.
        #
        #always @(negedge sig_clock)
        #begin
        #
        #// Address must not be X or Z during Address Phase
        #assertAddrUnknown:assert property (
        #                  disable iff(!has_checks) 
        #                  ($onehot(sig_grant) |-> !$isunknown(sig_addr)))
        #                  else
        #                    $error("ERR_ADDR_XZ\n Address went to X or Z \
        #                            during Address Phase");
        #
        #// Read must not be X or Z during Address Phase
        #assertReadUnknown:assert property ( 
        #                  disable iff(!has_checks) 
        #                  ($onehot(sig_grant) |-> !$isunknown(sig_read)))
        #                  else
        #                    $error("ERR_READ_XZ\n READ went to X or Z during \
        #                            Address Phase");
        #
        #// Write must not be X or Z during Address Phase
        #assertWriteUnknown:assert property ( 
        #                   disable iff(!has_checks) 
        #                   ($onehot(sig_grant) |-> !$isunknown(sig_write)))
        #                   else
        #                     $error("ERR_WRITE_XZ\n WRITE went to X or Z during \
        #                             Address Phase");
        #
        #// Size must not be X or Z during Address Phase
        #assertSizeUnknown:assert property ( 
        #                  disable iff(!has_checks) 
        #                  ($onehot(sig_grant) |-> !$isunknown(sig_size)))
        #                  else
        #                    $error("ERR_SIZE_XZ\n SIZE went to X or Z during \
        #                            Address Phase");
        #
        #
        #// Wait must not be X or Z during Data Phase
        #assertWaitUnknown:assert property ( 
        #                  disable iff(!has_checks) 
        #                  ($onehot(sig_grant) |=> !$isunknown(sig_wait)))
        #                  else
        #                    $error("ERR_WAIT_XZ\n WAIT went to X or Z during \
        #                            Data Phase");
        #
        #
        #// Error must not be X or Z during Data Phase
        #assertErrorUnknown:assert property ( 
        #                   disable iff(!has_checks) 
        #                   ($onehot(sig_grant) |=> !$isunknown(sig_error)))
        #                   else
        #                    $error("ERR_ERROR_XZ\n ERROR went to X or Z during \
        #                            Data Phase");
        #
        #
        #//Reset must be asserted for at least 3 clocks each time it is asserted
        #assertResetFor3Clocks: assert property (
        #                       disable iff(!has_checks) 
        #                       ($rose(sig_reset) |=> sig_reset[*2]))
        #                       else 
        #                         $error("ERR_SHORT_RESET_DURING_TEST\n",
        #                                "Reset was asserted for less than 3 clock \
        #                                 cycles");
        #
        #// Only one grant is asserted
        #//assertSingleGrant: assert property (
        #//                   disable iff(!has_checks)
        #//                   (sig_start |=> $onehot0(sig_grant)))
        #//                   else
        #//                     $error("ERR_GRANT\n More that one grant asserted");
        #
        #// Read and write never true at the same time
        #assertReadOrWrite: assert property (
        #                   disable iff(!has_checks) 
        #                   ($onehot(sig_grant) |-> !(sig_read && sig_write)))
        #                   else
        #                     $error("ERR_READ_OR_WRITE\n Read and Write true at \
        #                             the same time");
        #
