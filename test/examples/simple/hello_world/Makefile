# Makefile for testing python-uvm

# Usage:
# To execute tests in given file using given verilog source, you can do:
# >$ make MODULE=py_mod_name VLOG=hdl/my_vlog.v SIM_ARGS='-aaa +bbb'

include ../MakefileCommon.mk

# SIM_ARGS = ""
TOPLEVEL := common_stub
MODULE   ?= hello_world

include $(shell cocotb-config --makefiles)/Makefile.sim
