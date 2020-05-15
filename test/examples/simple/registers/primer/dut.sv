// 
// -------------------------------------------------------------
//    Copyright 2004-2011 Synopsys, Inc.
//    Copyright 2010 Mentor Graphics Corporation
//    Copyright 2010 Cadence Design Systems, Inc.
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

`timescale 1ns/1ns
/* verilator lint_off CASEX */
/* verilator lint_off CASEINCOMPLETE */


module slave#(
    parameter int DMA_SIZE = 1024,
    parameter int NSESS = 128
)
(
   // apb_if    apb,
   input rst,
   input apb_pclk,
   input wire [31:0] apb_paddr,
   input        apb_psel,
   input        apb_penable,
   input        apb_pwrite,
   output [31:0] apb_prdata,
   input [31:0] apb_pwdata
);

reg [31:0] pr_data;
assign apb_prdata = (apb_psel && apb_penable && !apb_pwrite) ? pr_data : 'z;

typedef struct packed {
   reg [63:0] SRC;
   reg [63:0] DST;
} socket_t;

reg [ 7:0] INDEX;
socket_t[NSESS-1:0] SESSION;
reg[NSESS-1:0][63:0] DST;
reg[NSESS-1:0][31:0] TABLES;
reg[31:0] DMA[DMA_SIZE-1:0];

wire[9:0] paddr;
assign paddr = apb_paddr[11:2];

reg write_socket;
socket_t chosen_sock;

always @ (posedge apb_pclk)
  begin
   if (rst) begin
      INDEX <= 'h00;
      for (int i = 0; i < NSESS; i += 1) begin
         TABLES[i] <= 32'h0000_0000;
      end
      pr_data <= 32'h0;
      write_socket <= 1'b0;
   end
   else begin
       if (write_socket) begin
           assert(paddr < NSESS[9:0])
           else $error("paddr %0d out of range %0d", paddr, NSESS);
           SESSION[paddr] <= chosen_sock;
           write_socket <= 1'b0;
       end

      // Wait for a SETUP+READ or ENABLE+WRITE cycle
      if (apb_psel == 1'b1 && apb_penable == apb_pwrite) begin
         pr_data <= 32'h0;
         if (apb_pwrite) begin
            casex (apb_paddr[15:0])
              16'h0020: INDEX <= apb_pwdata[7:0];
              16'h0024: begin
                 TABLES[INDEX] <= apb_pwdata;
              end
              16'h1XX0: begin
                  chosen_sock.SRC[63:32] <= apb_pwdata;
                  write_socket <= 1'b1;
              end
              16'h1XX4: begin
                  chosen_sock.SRC[31: 0] <= apb_pwdata;
                  write_socket <= 1'b1;
              end
              16'h1XX8: begin
                  chosen_sock.DST[63:32] <= apb_pwdata;
                  write_socket <= 1'b1;
              end
              16'h1XXC: begin
                  chosen_sock.DST[31: 0] <= apb_pwdata;
                  write_socket <= 1'b1;
              end
              16'h2XXX: DMA[paddr] <= apb_pwdata;
            endcase
         end
         else begin
            casex (apb_paddr[15:0])
              16'h0000: pr_data <= {2'b00, 4'h0, 10'h176, 8'h5A, 8'h03};
              16'h0020: pr_data <= {24'h0000, INDEX};
              16'h0024: pr_data <= TABLES[INDEX];
              16'h1XX0: pr_data <= SESSION[apb_paddr[11:2]].SRC[63:32];
              16'h1XX4: pr_data <= SESSION[apb_paddr[11:2]].SRC[31: 0];
              16'h1XX8: pr_data <= SESSION[apb_paddr[11:2]].DST[63:32];
              16'h1XXC: pr_data <= SESSION[apb_paddr[11:2]].DST[31: 0];
              16'h2XXX: pr_data <= DMA[apb_paddr[11:2]];
            endcase
         end
      end
   end
end

`ifdef COCOTB_SIM
`ifdef VCD
initial begin
 $dumpfile ("slave_dut.vcd");
 $dumpvars (0, slave);
 for (int i = 0; i < 16; i++) $dumpvars(0, DMA[i]);
 #2ns;
end
`endif
`endif

endmodule

