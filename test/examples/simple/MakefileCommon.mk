# Common makefile for uvm-python examples
#

COCOTB_HDL_TIMEUNIT ?= 1ns
COCOTB_HDL_TIMEPRECISION ?= 1ns

TOPLEVEL_LANG ?= verilog

MAKEDIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
UVM_PYTHON ?= $(MAKEDIR)/../../../src

ifeq ($(OS),Msys)
WPWD=$(shell sh -c 'pwd -W')
PYTHONPATH := $(UVM_PYTHON):$(PYTHONPATH):.
else
WPWD=$(shell pwd)
PYTHONPATH := $(UVM_PYTHON):$(PYTHONPATH):.
endif

export PYTHONPATH

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES ?= $(MAKEDIR)/common_stub.sv
else ifeq ($(TOPLEVEL_LANG),vhdl)
    VHDL_SOURCES ?= $(MAKEDIR)/common_stub.vhd
else
    $(error "A valid value (verilog) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG)")
endif

ifneq ($(VLOG),)
	VERILOG_SOURCES := $(VLOG)
endif

ifneq ($(UVM_TEST),)
    ifeq ($(TOPLEVEL_LANG),vhdl)
	    SIMARGS += -- +UVM_TESTNAME=$(UVM_TEST)
    else
	    SIMARGS += +UVM_TESTNAME=$(UVM_TEST)
	endif
endif
