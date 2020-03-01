#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------


#  // This simple example shows how the uvm_test_done objection is
#  // used to coordinate end of test activity. For an example of
#  // using end of test coordination in the context of a full
#  // environment, refer to the xbus example.
#
#  // In this example, a drain time of 10 is set on the component.
#  // The component then forks 4 processes which consume different
#  // amounts of time. When the last process is done (time 50),
#  // the drain time takes effect. The test is completed at time
#  // 60.
#
#  // The example also shows usage of the component objection
#  // callbacks. In this case, the dropped callback is used, but
#  // the raised and all_dropped work similarly (except the
#  // all dropped is a time-consuming task).

import cocotb
from cocotb.triggers import Timer

from uvm.comps.uvm_test import *
from uvm.macros import *
from uvm import *


class simple_test(UVMTest):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.sem = UVMMailbox(1)
        self.sem.try_put(1)
        #self.sem.debug_enabled = True
        self.proc_finished = {}
        self.largest_delay = 50


    async def run_phase(self, phase):
        # Set a drain time on the objection if needed
        uvm_info("drain", "Setting drain time of 10", UVM_NONE)

        # DEPRECATED
        #uvm_test_done.set_drain_time(self, 10)

        # Run a bunch of processes in parallel
        #fork
        p0 = cocotb.fork(self.doit(35, phase, 0))
        p1 = cocotb.fork(self.doit(25, phase, 1))
        p2 = cocotb.fork(self.doit(self.largest_delay, phase, 2))
        p3 = cocotb.fork(self.doit(15, phase, 3))
        p4 = cocotb.fork(self.do_without_object(self.largest_delay + 5, 4))

        uvm_info("all_procs_forked", "Proceeding to await proc4", UVM_NONE)

        # p4 runs longest, but does not raise objection, so simulation should
        # terminate at largest_delay, not when p4 finishes (+5)
        await p4
        #yield [p0.join(), p1.join(), p2.join(), p3.join(), ]
        #join

    s_inst = 0
    # A simple task that consumes some time.

    async def doit(self, delay, phase, _id):
        arr = []
        # Raise an objection before starting the activity
        phase.raise_objection(self)
        await self.sem.get(arr)
        inst = simple_test.s_inst
        simple_test.s_inst += 1
        await self.sem.put(1)

        uvm_info("doit", sv.sformatf("Starting doit (%0d) with delay %0t",
            inst, delay), UVM_NONE)
        await Timer(delay, "NS")
        uvm_info("doit", sv.sformatf("Ending doit (%0d)", inst), UVM_NONE)

        # Drop the objection when done
        arr = []
        await self.sem.get(arr)
        self.proc_finished[_id] = True
        await self.sem.put(1)
        phase.drop_objection(self)
        uvm_info("doit", sv.sformatf("Really finished now (%0d)", inst), UVM_NONE)


    async def do_without_object(self, delay, _id):
        await Timer(1, "NS")
        arr = []
        await self.sem.get(arr)
        inst = simple_test.s_inst
        simple_test.s_inst += 1
        await self.sem.put(1)

        uvm_info("doit", sv.sformatf("Starting doit (%0d) with delay %0t",
            inst, delay), UVM_NONE)
        await Timer(delay, "NS")
        uvm_info("doit", sv.sformatf("Ending doit (%0d)", inst), UVM_NONE)

        # Drop the objection when done
        arr = []
        await self.sem.get(arr)
        self.proc_finished[_id] = True
        await self.sem.put(1)

    # Use an objection callback do something when objections are raised or
    # dropped (or all dropped). This example prints some information on each
    # drop.
    def dropped(self, objection, source_obj, description, count):
        uvm_info("dropped",
            sv.sformatf("%d objection(s) dropped from %s, total count is now %0d",
            count, source_obj.get_full_name, objection.get_objection_total(self)),
            UVM_NONE)


    # Check various conditions such as processses finishes and simulation time
    # to verify that objections are working correctly
    def check_phase(self, phase):
        ids = [0, 1, 2, 3]
        for _id, i in enumerate(ids):
            if _id not in self.proc_finished:
                uvm_fatal("PROC_NOT_FINISHED",
                "Inst {} not found from finished procs".format(_id))
            else:
                uvm_info("PROC_OK", "Proc {} finished OK".format(_id), UVM_NONE)

        if 5 in self.proc_finished:
            uvm_fatal("WRONG_PROC_FINISHED", "Proc 5 must not finish")
        finish_time = sv.realtime("NS")
        if finish_time != self.largest_delay:
            uvm_fatal("WRONG_FINISH_TIME", "Exp: {}, Got: {}".format(
                self.largest_delay, finish_time))


# Register with the factory.
uvm_component_utils(simple_test)


@cocotb.test()
async def initial(dut):
    # Run the test
    await run_test("simple_test")
