
/* Mock module for testing py-uvm with cocotb and iverilog */
module uvm_test#(
    parameter int DW = 16
)
(
    input clk,
    input rst,
    input[DW-1:0] data_in,
    output[DW-1:0] data_out
);

reg[DW-1:0] data_reg;

always@(posedge clk or negedge rst)
    if (!rst)
        data_reg <= 0;
    else
        data_reg <= data_in;

endmodule
