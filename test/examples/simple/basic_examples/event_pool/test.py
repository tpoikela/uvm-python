
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
from uvm.base.sv import sv

from uvm.macros import uvm_error
from uvm.base.uvm_global_vars import uvm_default_table_printer



async def trig_event(e):
    await Timer(100, "NS")
    e.trigger()
    await Timer(1, "NS")


async def trig_data_event(e):
    await Timer(50, "NS")
    e.trigger(0x1234)
    await Timer(1, "NS")


async def wait_on_evt(e):
    await e.wait_on()


@cocotb.test()
async def test_test(dut):

    ep = UVMEventPool("ep")
    cs_ = UVMCoreService.get()

    e = None
    e = ep.get("fred")
    e = ep.get("george")
    e_data = ep.get('evt_data')
    uvm_default_table_printer.knobs.reference = 0
    ep.print_obj()

    trig_proc = cocotb.fork(trig_event(e))
    cocotb.fork(trig_data_event(e_data))
    await e_data.wait_trigger()
    await e.wait_on()
    e.reset()
    await Timer(1, "NS")
    trig_proc = cocotb.fork(trig_event(e))
    evt_proc = cocotb.fork(wait_on_evt(e))
    await sv.fork_join([trig_proc, evt_proc])

    svr = None  # uvm_report_server
    svr = cs_.get_report_server()
    svr.report_summarize()
    time_ok = sv.realtime("NS") == 202
    data_ok = e_data.get_trigger_data() == 0x1234
    if data_ok and time_ok and (svr.get_severity_count(UVM_FATAL) +
            svr.get_severity_count(UVM_ERROR) == 0):
        print("** UVM TEST PASSED **\n")
    else:
        if data_ok is False:
            uvm_error("DATA_ERROR", "Exp: {}, Got: {}".format(0x1234,
                e_data.get_trigger_data()))
        if time_ok is False:
            uvm_error("TIME_ERROR", "Exp: {}, Got: {}".format(202,
                sv.realtime("NS")))
        raise Exception("!! UVM TEST FAILED !!\n")
