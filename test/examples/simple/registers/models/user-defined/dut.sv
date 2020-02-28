// 
// -------------------------------------------------------------
//    Copyright 2004-2011 Synopsys, Inc.
//    Copyright 2010 Mentor Graphics Corporation
//    All Rights Reserved Worldwide
// 
//    Licensed under the Apache License, Version 2.0 (the
//    "License"); you may not use this file except in
//    compliance with the License.  You may obtain a copy of
//    the License at
// 
//        http://www.apache.org/licenses/LICENSE-2.0
// 
//    Unless required by applicable law or agreed to in
//    writing, software distributed under the License is
//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
//    CONDITIONS OF ANY KIND, either express or implied.  See
//    the License for the specific language governing
//    permissions and limitations under the License.
// -------------------------------------------------------------
// 

`timescale 1ns/1ns

module dut(
    input clk,
    input reset,
    input[15:0] data_in,
    input[15:0] addr_in,
    input we,
    input read,
    output[15:0] data_out
);

reg [15:0][15:0] acp;
assign data_out = read ? acp[addr_in] : 16'hFFFF;

always_ff@(posedge clk or negedge reset)
    if (!reset)
        acp <= 0;
    else begin
        if (we) acp[addr_in] <= data_in;
    end

`ifndef VERILATOR
`ifdef COCOTB_SIM
initial begin
  $dumpfile ("gui.vcd");
  $dumpvars (0, dut);
  #1;
end
`endif
`endif

endmodule
