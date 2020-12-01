//
// -------------------------------------------------------------
//    Copyright 2010 Mentor Graphics Corporation
//    Copyright 2004-2011 Synopsys, Inc.
//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

`timescale 1ns/100ps

`include "blk_dut.sv"

module sys_dut #(
    parameter int BASE_ADDR='h100,
    parameter int NUM_BLKS = 2
)
(
   //apb_if    apb,
   input apb_pclk,
   input wire [31:0] apb_paddr,
   input        apb_psel,
   input        apb_penable,
   input        apb_pwrite,
   output [31:0] apb_prdata,
   input [31:0] apb_pwdata,

   input rst
);

/*
  genvar gk;
  generate
  for (gk = 0; gk <= NUM_BLKS; NUM_BLKS = NUM_BLKS + 1) begin: Blks
      blk_dut #(BASE_ADDR+'h100 * gk) i_blk_dut(.*);
  end
  endgenerate
*/

  blk_dut #(BASE_ADDR)        b1 (.*);
  blk_dut #(BASE_ADDR+'h100 ) b2(.*);

`ifndef VERILATOR
`ifdef COCOTB_SIM
initial begin
  $dumpfile ("vcd_sys_dut.vcd");
  $dumpvars (0, sys_dut);
  #2;
end
`endif
`endif

endmodule
