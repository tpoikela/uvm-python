#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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
#//------------------------------------------------------------------------------

from cocotb.triggers import Timer

from .sv import sv
from .uvm_object import UVMObject
from .uvm_event import UVMEvent
from .uvm_object_globals import UVM_BIN, UVM_DEC
from .uvm_globals import uvm_zero_delay


class UVMBarrier(UVMObject):
    """
    The UVMBarrier class provides a multiprocess synchronization mechanism. Note
    that this is only for cocotb-based simulation, not real multiprocessing.
    It enables a set of processes to block until the desired number of processes
    get to the synchronization point, at which time all of the processes are
    released.
    """


    #  // Function: new
    #  //
    #  // Creates a new barrier object.
    #
    def __init__(self, name="", threshold=0):
        super().__init__(name)
        self.m_event = UVMEvent({"barrier_",name})
        self.threshold = threshold
        self.num_waiters = 0
        self.auto_reset = 1
        self.at_threshold = 0



    #  // Task: wait_for
    #  //
    #  // Waits for enough processes to reach the barrier before continuing.
    #  //
    #  // The number of processes to wait for is set by the <set_threshold> method.
    async def wait_for(self):
        if self.at_threshold:
            return

        self.num_waiters += 1

        if self.num_waiters >= self.threshold:
            if not self.auto_reset:
                self.at_threshold=1
            self.m_trigger()
            return

        await self.m_event.wait_trigger()


    #  // Function: reset
    #  //
    #  // Resets the barrier. This sets the waiter count back to zero.
    #  //
    #  // The threshold is unchanged. After reset, the barrier will force processes
    #  // to wait for the threshold again.
    #  //
    #  // If the ~wakeup~ bit is set, any currently waiting processes will
    #  // be activated.
    def reset(self, wakeup=1):
        self.at_threshold = 0
        if self.num_waiters:
            if wakeup:
                self.m_event.trigger()
            else:
                self.m_event.reset()
        self.num_waiters = 0


    #  // Function: set_auto_reset
    #  //
    #  // Determines if the barrier should reset itself after the threshold is
    #  // reached.
    #  //
    #  // The default is on, so when a barrier hits its threshold it will reset, and
    #  // new processes will block until the threshold is reached again.
    #  //
    #  // If auto reset is off, then once the threshold is achieved, new processes
    #  // pass through without being blocked until the barrier is reset.
    def set_auto_reset(self, value=1):
        self.at_threshold = 0
        self.auto_reset = value


    #  // Function: set_threshold
    #  //
    #  // Sets the process threshold.
    #  //
    #  // This determines how many processes must be waiting on the barrier before
    #  // the processes may proceed.
    #  //
    #  // Once the ~threshold~ is reached, all waiting processes are activated.
    #  //
    #  // If ~threshold~ is set to a value less than the number of currently
    #  // waiting processes, then the barrier is reset and waiting processes are
    #  // activated.
    def set_threshold(self, threshold):
        self.threshold = threshold
        if threshold <= self.num_waiters:
            self.reset(1)



    #  // Function: get_threshold
    #  //
    #  // Gets the current threshold setting for the barrier.
    def get_threshold(self):
        return self.threshold


    #  // Function: get_num_waiters
    #  //
    #  // Returns the number of processes currently waiting at the barrier.
    #
    def get_num_waiters(self):
        return self.num_waiters


    #  // Function: cancel
    #  //
    #  // Decrements the waiter count by one. This is used when a process that is
    #  // waiting on the barrier is killed or activated by some other means.
    def cancel(self):
        self.m_event.cancel()
        self.num_waiters = self.m_event.get_num_waiters()


    type_name = "UVMBarrier"

    def create(self, name=""):
        v = UVMBarrier(name)
        return v

    def get_type_name(self):
        return UVMBarrier.type_name


    async def m_trigger(self):
        self.m_event.trigger()
        self.num_waiters = 0
        await uvm_zero_delay()  # self process was last to wait; allow other procs to resume first


    def do_print(self, printer):
        printer.print_field_int("threshold", self.threshold, sv.bits(self.threshold),
                UVM_DEC, ".", "int")
        printer.print_field_int("num_waiters", self.num_waiters, sv.bits(self.num_waiters),
                UVM_DEC, ".", "int")
        printer.print_field_int("at_threshold", self.at_threshold, sv.bits(self.at_threshold),
                UVM_BIN, ".", "bit")
        printer.print_field_int("auto_reset", self.auto_reset, sv.bits(self.auto_reset), UVM_BIN,
                ".", "bit")


    def do_copy(self, rhs):
        b = rhs
        super().do_copy(rhs)
        #    if(!sv.cast(b, rhs)  or  (b is None)) return
        self.threshold = b.threshold
        self.num_waiters = b.num_waiters
        self.at_threshold = b.at_threshold
        self.auto_reset = b.auto_reset
        self.m_event = b.m_event
