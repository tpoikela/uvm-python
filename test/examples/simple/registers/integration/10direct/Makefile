###############################################################################
# Copyright (c) 2013 Potential Ventures Ltd
# Copyright (c) 2013 SolarFlare Communications Inc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Potential Ventures Ltd,
#       SolarFlare Communications Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL POTENTIAL VENTURES LTD BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###############################################################################

# Makefile for testing python-uvm

# Usage:
# To execute tests in given file using given verilog source, you can do:
# >$ make MODULE=py_mod_name VLOG=hdl/my_vlog.v SIM_ARGS='-aaa +bbb'

COCOTB_HDL_TIMEUNIT=1ns
COCOTB_HDL_TIMEPRECISION=1ns

include ../../../MakefileCommon.mk
PYTHONPATH := $(WPWD)/../../../../integrated:$(PYTHONPATH)
PYTHONPATH := $(WPWD)/../common:$(PYTHONPATH)

# Var to choos if clock generated on Python or SV side
SV_CLOCK_GEN ?= 0
export SV_CLOCK_GEN

VERILOG_SOURCES := $(WPWD)/../common/dut.sv
ifeq ($(SV_CLOCK_GEN), 1)
	VERILOG_SOURCES := $(WPWD)/../common/dut_with_clkgen.sv \
					   $(WPWD)/../common/dut.sv
endif

ifeq ($(VCD), 1)
	COMPILE_ARGS += -DVCD=1
endif

UVM_SEQUENCE ?= UVMRegMemBuiltInSeq
PLUSARGS += +UVM_VERBOSITY=UVM_NONE
#PLUSARGS += +UVM_CONFIG_DB_TRACE=1 +UVM_DUMP_CMDLINE_ARGS
PLUSARGS += +UVM_SEQUENCE=$(UVM_SEQUENCE)
ifneq ($(UVM_TEST),)
    PLUSARGS += +UVM_TESTNAME=$(UVM_TEST) +UVM_RESOURCE_DB_TRACE
endif
TOPLEVEL := apb_slave
ifeq ($(SV_CLOCK_GEN), 1)
	TOPLEVEL := apb_slave_with_clkgen
endif
MODULE   ?= test_top

include $(shell cocotb-config --makefiles)/Makefile.sim
