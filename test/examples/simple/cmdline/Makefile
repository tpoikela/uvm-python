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
# >$ make MODULE=py_mod_name VLOG=hdl/my_vlog.v PLUSARGS='-aaa +bbb'
#

include ../MakefileCommon.mk

ifeq ($(UVM_TEST), )
PLUSARGS += "+UVM_TESTNAME=CmdLineTest"  # Selects the UVM test to run
else
PLUSARGS += "+UVM_TESTNAME=$(UVM_TEST)"  # Selects the UVM test to run
endif

PLUSARGS += "+UVM_VERBOSITY=UVM_HIGH"    # Selects the global verbosity
PLUSARGS += "+uvm_set_verbosity=uvm_test_top.my_comp,_ALL_,UVM_DEBUG,time,1000"
PLUSARGS += "+uvm_set_action=uvm_test_top.my_comp,SUPPRESS_FATAL,UVM_FATAL,UVM_LOG"
PLUSARGS += "+uvm_set_severity=uvm_test_top.my_*,FAT2WARN,UVM_FATAL,UVM_WARNING"
PLUSARGS += "+UVM_MAX_QUIT_COUNT=10"


# Used only in TestMaxQuitCount
ifeq ($(UVM_TEST), TestMaxQuitCount)
PLUSARGS += "+uvm_set_config_int=*,hex_to_match,0x789"
PLUSARGS += "+uvm_set_config_int=uvm_test_top.*,bin_to_match,0b10101010"
PLUSARGS += "+uvm_set_config_int=uvm_test_top.my_comp,dec_to_match,10000000000000000001"
PLUSARGS += "+uvm_set_config_int=*.my_comp,oct_to_match,'o456"
PLUSARGS += "+uvm_set_config_string=uvm_test_top.my_comp,tag,matched_correctly"
PLUSARGS += "+uvm_set_config_string=uvm_test_top.my_comp,str_with_ws,'str with whitespace[912]'"
PLUSARGS += "+UVM_TIMEOUT=200000,NO"
endif

TOPLEVEL := common_stub
MODULE   ?= test_cmdline_args

include $(shell cocotb-config --makefiles)/Makefile.sim
