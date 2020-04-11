# Common makefile for uvm-python examples

TOPLEVEL_LANG ?= verilog

MAKEDIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
UVM_PYTHON ?= $(MAKEDIR)/../../../src

ifeq ($(OS),Msys)
WPWD=$(shell sh -c 'pwd -W')
PYTHONPATH := $(UVM_PYTHON):$(PYTHONPATH):.
#PYTHONPATH := $(UVM_PYTHON):$(UVM_PYTHON)/base:$(PYTHONPATH)
#PYTHONPATH := $(WPWD)/../../../..:$(PYTHONPATH)
else
WPWD=$(shell pwd)
PYTHONPATH := $(UVM_PYTHON):$(PYTHONPATH):.
#PYTHONPATH := $(WPWD)/model:$(PYTHONPATH):.
#PYTHONPATH := $(UVM_PYTHON):$(UVM_PYTHON)/base:$(PYTHONPATH)
#PYTHONPATH := $(WPWD)/../../../..:$(PYTHONPATH)
endif

export PYTHONPATH

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES ?= $(MAKEDIR)/common_stub.v
else
    $(error "A valid value (verilog) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG)")
endif

ifneq ($(VLOG),)
	VERILOG_SOURCES := $(VLOG)
endif

ifneq ($(UVM_TEST),)
	SIMARGS += +UVM_TESTNAME=$(UVM_TEST)
endif
