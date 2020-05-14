
`timescale 1ns/1ps

module common_stub(
    input clk, input rst
);

reg[7:0] word;
/* Does nothing */

always_ff@(posedge clk or negedge rst)
    if (!rst) word <= 8'h00;
    else word <= word + 8'h01;

endmodule
