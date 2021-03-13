# Makefile for testing python-uvm

# Usage:
# To execute tests in given file using given verilog source, you can do:
# >$ make MODULE=py_mod_name VLOG=hdl/my_vlog.v SIM_ARGS='-aaa +bbb'


include ../../simple/MakefileCommon.mk
PYTHONPATH := $(WPWD)/../../integrated:$(PYTHONPATH)

# SIM_ARGS = ""
TOPLEVEL := dut
MODULE   ?= test_codec

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = dut.sv
else
    $(error "A valid value (verilog) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG)")
endif

ifneq ($(UVM_TEST),)
    PLUSARGS += +UVM_TESTNAME=$(UVM_TEST)
else
    PLUSARGS += +UVM_TESTNAME=test
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
