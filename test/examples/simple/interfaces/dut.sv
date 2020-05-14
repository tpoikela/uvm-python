//---------------------------------------------------------------------------
// File: dut.sv
// Created on 2020-01-31
// CERN EP-ESE-ME
// Tuomas Poikela, tuomas.sakari.poikela@gmail.com
//
// Description:
//---------------------------------------------------------------------------

`timescale 1ns/1ns

interface pin_if (input clk);
  bit [15:0] address;
  bit [7:0]  wr_data;
  bit [7:0] rd_data;
  bit rst;
  bit rw;
  bit req;
  bit ack;
  bit err;

  modport master_mp(
   input  clk,
   input  rst,
   output address,
   output wr_data,
   input  rd_data,
   output req,
   output rw,
   input  ack,
   input  err );

  modport slave_mp(
   input  clk,
   input  rst,
   input  address,
   input  wr_data,
   output rd_data,
   input  req,
   input  rw,
   output ack,
   output err );

  modport monitor_mp(
   input  clk,
   input  rst,
   input  address,
   input  wr_data,
   input  rd_data,
   input  req,
   input  rw ,
   input  ack,
   input  err );
endinterface

//----------------------------------------------------------------------
// module dut
//----------------------------------------------------------------------

module master_dut#(
    parameter int ADDR_WIDTH = 16,
    parameter int DW = 8
)
(
  input clk,
  input rst,
  output [ADDR_WIDTH-1:0] address,
  output [DW-1:0]  wr_data,
  input [DW-1:0] rd_data,
  output rw,
  output req,
  input ack,
  input err
);

reg[15:0] count;

  always_ff@(posedge clk or negedge rst) begin
    if (!rst) begin
      count <= '0;
    end else begin
      count <= count + 1;
      $display({"dut: ", "posedge clk: %0d"}, count);
      //...
    end
  end
endmodule
