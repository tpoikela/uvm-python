//---------------------------------------------------------------------------
// File: dut_with_clkgen.sv
// Created on 2024-03-17
// 
// Tuomas Poikela, tuomas.sakari.poikela@gmail.com
//
// Description: 
//---------------------------------------------------------------------------
//
module apb_slave_with_clkgen#(
    parameter int MEM_SIZE = 128,
    parameter int NSOCKETS = 64,
    parameter int ID_REGISTER = {2'b00, 4'h0, 10'h176, 8'h5A, 8'h03},
    parameter int ADDR_WIDTH = 16
)
(
    output logic apb_pclk,
    input wire rst,
    input wire [31:0] apb_paddr,
    input wire        apb_psel,
    input wire        apb_penable,
    input wire        apb_pwrite,
    output wire [31:0] apb_prdata,
    input wire [31:0] apb_pwdata
);

// Instantiate the apb_slave
apb_slave#(
    .MEM_SIZE(MEM_SIZE),
    .NSOCKETS(NSOCKETS),
    .ID_REGISTER(ID_REGISTER),
    .ADDR_WIDTH(ADDR_WIDTH)
) apb_slave_inst (
    .apb_pclk(apb_pclk),
    .rst(rst),
    .apb_paddr(apb_paddr),
    .apb_psel(apb_psel),
    .apb_penable(apb_penable),
    .apb_pwrite(apb_pwrite),
    .apb_prdata(apb_prdata),
    .apb_pwdata(apb_pwdata)
);

initial begin
    apb_pclk = 1'b0;
    forever #5ns apb_pclk = ~apb_pclk;
end

endmodule: apb_slave_with_clkgen
