// 
// -------------------------------------------------------------
//    Copyright 2004-2011 Synopsys, Inc.
//    Copyright 2010 Mentor Graphics Corporation
//    Copyright 2020 Tuomas Poikela (tpoikela)
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

/* Test DUT which has one register FIFO. */

`timescale 1ns/1ns

module dut #(
   parameter int BASE_ADDR='h0
) (
   input apb_pclk,
   input rst,
   input wire [31:0] apb_paddr,
   input        apb_psel,
   input        apb_penable,
   input        apb_pwrite,
   output [31:0] apb_prdata,
   input [31:0] apb_pwdata
);

reg [31:0] fifo[8];
reg [2:0]  w_idx;
reg [2:0]  r_idx;
reg [3:0]  used;
reg [31:0] pr_data;

wire in_range;

wire [31:0] pr_addr;

assign in_range = (apb_paddr - BASE_ADDR) == 0; // only 1 reg
assign pr_addr = apb_paddr - BASE_ADDR;

assign apb_prdata = (apb_psel && apb_penable && !apb_pwrite && in_range) ? pr_data : 'z;

always @ (posedge apb_pclk)
  begin
   if (rst) begin
       foreach (fifo[i])
           fifo[i] <= 'h0;
      w_idx <= 0;
      r_idx <= 0;
      used <= 0;
   end
   else begin
      // Wait for a SETUP+READ or ENABLE+WRITE cycle
      if (apb_psel == 1'b1 && apb_penable == apb_pwrite && pr_addr == 'h0) begin
         pr_data <= 32'h0;
         if (apb_pwrite) begin
           if (used != 8) begin
             fifo[w_idx] <= apb_pwdata;
             w_idx       <= w_idx + 1;
             used        <= used + 1;
           end
         end
         else begin
           if (used != 0) begin
             pr_data <= fifo[r_idx];
             fifo[r_idx] <= 'h0; // just for debug; not necessary
             r_idx   <= r_idx + 1;
             used    <= used - 1;
           end
         end
      end
   end
end

`ifdef COCOTB_SIM
initial begin
    $dumpfile("./dut.vcd");
    $dumpvars(0, dut);
end
`endif

endmodule


