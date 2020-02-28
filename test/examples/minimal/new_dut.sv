`timescale 1ns/1ns
module new_dut(input clk, input rst, output[7:0] byte_out);
    assign byte_out = 8'hAB;
endmodule: new_dut
