# Minimal Makefile for uvm-python minimal example
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES ?= new_dut.sv
TOPLEVEL := new_dut
MODULE   ?= new_test

PYTHONPATH := ../../../src:$(PYTHONPATH)
export PYTHONPATH

include $(shell cocotb-config --makefiles)/Makefile.sim
