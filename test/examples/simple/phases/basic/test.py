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

#//----------------------------------------------------------------------
#// This example illustrates basic hierarchy construction and test phasing
#//----------------------------------------------------------------------

import cocotb
from cocotb.triggers import Timer
from uvm import (UVMComponent, sv, UVMEnv, run_test, uvm_info, uvm_fatal,
    UVM_NONE, uvm_error, UVMCoreService, UVM_ERROR)

CORRECT_PHASES = ['build', 'connect', 'end_of_elaboration',
    'start_of_simulation',
    'run', 'pre_reset', 'reset', 'post_reset', 'pre_configure', 'configure',
    'post_configure', 'pre_main', 'main', 'post_main', 'pre_shutdown',
    'shutdown', 'post_shutdown',
    'extract', 'check', 'report', 'final']

#  //Create a topology
#  //            top
#  //       |            |
#  //     u1(A)         u2(A)
#  //    |     |      |        |
#  //   b1(B) d1(D)  b1(B)    d1(D)

# Define new base class with phase_started/ended callbacks.

test_duration = 10


class VerifComp(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.phases_started = []
        self.phases_ended = []
        self.correct = False

    def phase_started(self, phase):
        self.phases_started.append(phase.get_name())

    def phase_ended(self, phase):
        self.phases_ended.append(phase.get_name())

    def final_phase(self, phase):
        if self.phases_started != CORRECT_PHASES:
            uvm_error("PHASES_STARTED_FAIL", self.get_name() + ": " +
                    str(self.phases_started))
        else:
            self.correct = True
            uvm_info("PHASES_STARTED_OK", self.get_name() + ": " + str(self.phases_started),
                UVM_NONE)


# No run phase
class D(VerifComp):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def build_phase(self, phase):
        sv.display("%0t: %0s:  build", sv.time("NS"), self.get_full_name())

    def end_of_elaboration_phase(self, phase):
        sv.display("%0t: %0s:  end_of_elaboration", sv.time("NS"), self.get_full_name())

    def start_of_simulation_phase(self, phase):
        sv.display("%0t: %0s:  start_of_simulation", sv.time("NS"), self.get_full_name())

    def extract_phase(self, phase):
        sv.display("%0t: %0s:  extract", sv.time("NS"), self.get_full_name())

    def check_phase(self, phase):
        sv.display("%0t: %0s:  check", sv.time("NS"), self.get_full_name())

    def report_phase(self, phase):
        sv.display("%0t: %0s:  report", sv.time("NS"), self.get_full_name())

    #  endclass


#  //Has run phase
class B(VerifComp):
    #    rand logic [7:0] delay
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.delay = 0
        self.rand('delay', range(0, (1 << 8) - 1))

    def build_phase(self, phase):
        sv.display("%0t: %0s:  build", sv.time("NS"), self.get_full_name())

    def end_of_elaboration_phase(self, phase):
        sv.display("%0t: %0s:  end_of_elaboration", sv.time("NS"), self.get_full_name())

    def start_of_simulation_phase(self, phase):
        sv.display("%0t: %0s:  start_of_simulation", sv.time("NS"), self.get_full_name())

    def extract_phase(self, phase):
        sv.display("%0t: %0s:  extract", sv.time("NS"), self.get_full_name())

    def check_phase(self, phase):
        sv.display("%0t: %0s:  check", sv.time("NS"), self.get_full_name())

    def report_phase(self, phase):
        sv.display("%0t: %0s:  report", sv.time("NS"), self.get_full_name())

    
    async def run_phase(self, phase):
        sv.display("%0t: %0s:  start run phase", sv.time("NS"), self.get_full_name())
        await Timer(self.delay, "NS")
        sv.display("%0t: %0s:  end run phase", sv.time("NS"), self.get_full_name())


# Has run phase and contains subcomponents
class A(VerifComp):
    #    rand B b1
    #    rand D d1
    #    rand logic [7:0] delay
    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.b1 = B("b1", self)
        self.d1 = D("d1", self)
        self.delay = 0
        self.rand('delay', range(0, (1 << 8) - 1))

    def build_phase(self, phase):
        sv.display("%0t: %0s:  build", sv.time("NS"), self.get_full_name())

    def end_of_elaboration_phase(self, phase):
        sv.display("%0t: %0s:  end_of_elaboration", sv.time("NS"), self.get_full_name())

    def start_of_simulation_phase(self, phase):
        sv.display("%0t: %0s:  start_of_simulation", sv.time("NS"), self.get_full_name())

    def extract_phase(self, phase):
        sv.display("%0t: %0s:  extract", sv.time("NS"), self.get_full_name())

    def check_phase(self, phase):
        sv.display("%0t: %0s:  check", sv.time("NS"), self.get_full_name())

    def report_phase(self, phase):
        sv.display("%0t: %0s:  report", sv.time("NS"), self.get_full_name())

    
    async def run_phase(self, phase):
        sv.display("%0t: %0s:  start run phase", sv.time("NS"), self.get_full_name())
        await Timer(self.delay, "NS")
        sv.display("%0t: %0s:  end run phase", sv.time("NS"), self.get_full_name())


class AA(VerifComp):
    #    rand A a
    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.a = A("a", self)


# Top level contains two A components
class top(UVMEnv):
    #    rand AA a1
    #    rand AA a2

    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.a1 = AA("a1", self)
        self.a2 = AA("a2", self)

    def build_phase(self, phase):
        sv.display("%0t: %0s:  build", sv.time("NS"), self.get_full_name())

    def end_of_elaboration_phase(self, phase):
        sv.display("%0t: %0s:  end_of_elaboration", sv.time("NS"), self.get_full_name())

    def start_of_simulation_phase(self, phase):
        sv.display("%0t: %0s:  start_of_simulation", sv.time("NS"), self.get_full_name())

    def extract_phase(self, phase):
        sv.display("%0t: %0s:  extract", sv.time("NS"), self.get_full_name())

    def check_phase(self, phase):
        sv.display("%0t: %0s:  check", sv.time("NS"), self.get_full_name())

    def report_phase(self, phase):
        sv.display("%0t: %0s:  report", sv.time("NS"), self.get_full_name())

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        sv.display("%0t: %0s:  start run phase", sv.time("NS"), self.get_full_name())
        await Timer(test_duration, "NS")
        sv.display("%0t: %0s:  end run phase", sv.time("NS"), self.get_full_name())
        phase.drop_objection(self)



@cocotb.test()
async def initial_begin(dut):
    t = top("top", None)
    # Randomize all of the delays
    t.randomize()  # cast to 'void' removed
    await run_test()
    if sv.realtime("NS") != test_duration:
        uvm_fatal("TIME_ERR", "Exp: {}, Got: {}".format(
            test_duration, sv.realtime("NS")))
    svr = UVMCoreService.get().get_report_server()
    num_errors = svr.get_severity_count(UVM_ERROR)
    if num_errors > 0:
        uvm_fatal("SERVER_HAD_ERRORS", "Num UVM_ERRORS: {}".format(num_errors))
