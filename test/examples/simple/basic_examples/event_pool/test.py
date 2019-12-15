
#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#----------------------------------------------------------------------

#
# About: 'ep' event poll
# This test is a simple test that will cover the creation of two uvm_events using the uvm_event_pool.
# Then use the uvm_event_pool methods to print those objects.
#
# For a full documentation of the uvm_event and uvm_event_pool, check the files:
#	- uvm/src/base/uvm_event.svh
#	- uvm/src/base/uvm_event.sv
#

import cocotb
from cocotb.triggers import Timer

from uvm.base.uvm_coreservice import UVMCoreService
from uvm.base.uvm_pool import UVMEventPool
from uvm.base.uvm_globals import UVM_FATAL, UVM_ERROR

from uvm.base.uvm_global_vars import uvm_default_table_printer

@cocotb.test()
def test_test(dut):

    ep = UVMEventPool("ep")
    #uvm_event_pool ep=new("ep");

    cs_ = UVMCoreService.get()

    e = None
    e = ep.get("fred")
    e = ep.get("george")
    uvm_default_table_printer.knobs.reference = 0
    ep.print()

    svr = None  # uvm_report_server
    svr = cs_.get_report_server()
    svr.report_summarize()
    if (svr.get_severity_count(UVM_FATAL) +
            svr.get_severity_count(UVM_ERROR) == 0):
        print("** UVM TEST PASSED **\n")
    else:
        raise Exception("!! UVM TEST FAILED !!\n")
    yield Timer(0)
