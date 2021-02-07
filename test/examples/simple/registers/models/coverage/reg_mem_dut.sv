//---------------------------------------------------------------------------
// File: reg_mem_dut.sv
// Created on 2020-02-14
// Tuomas Poikela, tuomas.sakari.poikela@gmail.com
//
// Description: 
//---------------------------------------------------------------------------

`timescale 1ns/1ns

module reg_mem_dut#(
    parameter int DATA_WIDTH = 16,
    parameter int MEM_SIZE = 1024,
    parameter int ADDR_WIDTH = 16,
    parameter int MEM_ADDR_WIDTH = $clog2(MEM_SIZE),
    parameter int MEM_DATA_WIDTH = 8
)
(
    input clk,
    input rst,
    input we,
    input read,
    input[DATA_WIDTH-1:0] data_in,
    input[ADDR_WIDTH-1:0] addr_in,
    output logic[DATA_WIDTH-1:0] data_out
);

reg[MEM_DATA_WIDTH-1:0] mem[0:MEM_SIZE-1];
reg[DATA_WIDTH-1:0] reg_a, reg_b, data_reg;
reg addr_err;


wire[MEM_ADDR_WIDTH-1:0] mem_addr;
assign mem_addr = addr_in[MEM_ADDR_WIDTH-1:0];

wire mem_enable, reg_a_enable, reg_b_enable;

assign reg_a_enable = addr_in[15:12] == 4'h0;
assign reg_b_enable = addr_in[15:12] == 4'h1;
assign mem_enable = addr_in[15:12] == 4'h2;

always_comb begin
    if (mem_enable)
        data_out = {8'h00, mem[mem_addr]};
    else if (reg_a_enable)
        data_out = reg_a;
    else if (reg_b_enable)
        data_out = reg_b;
end

always_ff@(posedge clk or negedge rst)
if (rst == 1'b0) begin
    addr_err <= 1'b0;
    reg_a <= 16'h00A0;
    reg_b <= 16'h00A0;
    data_reg <= 16'h0;
end
else begin
    addr_err <= 1'b0;
    if (we) begin
        if (mem_enable)
            mem[mem_addr] <= data_in[MEM_DATA_WIDTH-1:0];
        else if (reg_a_enable)
            reg_a[15:0] <= {data_in[15:8], 4'hA, data_in[3:0]};
        else if (reg_b_enable)
            reg_b <= {data_in[15:8], 4'hA, data_in[3:0]};
        else
            addr_err <= 1'b1;
    end
    else if (read) begin
        if (mem_enable) begin
            data_reg <= {DATA_WIDTH{1'b0}};
            data_reg[MEM_DATA_WIDTH-1:0] <= mem[mem_addr];
        end
        else if (reg_a_enable)
            data_reg <= reg_a;
        else if (reg_b_enable)
            data_reg <= reg_b;
        else
            addr_err <= 1'b1;
    end
end

//`define VCD
`ifndef VERILATOR
`ifdef COCOTB_SIM
    `ifdef VCD
    initial begin
        $dumpfile ("reg_mem_dut.vcd");
        $dumpvars (0, reg_mem_dut);
        for (int i = 0; i < 16; i++) $dumpvars(0, mem[i]);
        #2ns;
    end
    `endif
`endif
`endif


endmodule: reg_mem_dut
