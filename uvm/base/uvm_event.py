
#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2014 NVIDIA Corportation
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

import cocotb
from cocotb.triggers import Event, Timer

from .sv import sv
from .uvm_object import UVMObject
from .uvm_queue import UVMQueue
from .uvm_debug import *

#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_event_base
#//
#// The uvm_event_base class is an abstract wrapper class around the SystemVerilog event
#// construct.  It provides some additional services such as setting self.callbacks
#// and maintaining the number of waiters.
#//
#//------------------------------------------------------------------------------

class UVMEventBase(UVMObject):
    #const static string type_name = "uvm_event_base";
    type_name = "uvm_event_base"

    #protected event      self.m_event;
    #protected int        self.num_waiters;
    #protected bit        on;
    #protected time       self.trigger_time=0;
    #protected uvm_event_callback  self.callbacks[$];

    # Function: new
    # Creates a new event object.
    def __init__(self, name=""):
        UVMObject.__init__(self, name)
        self.m_event = Event()
        self.num_waiters = 0
        self.on = False
        self.on_event = Event("on_event_" + name)
        self.trigger_time = 0
        self.callbacks = UVMQueue() # uvm_event_callback
        self.m_waiters = 0
        self.m_value_changed_event = Event("value_changed_event_" + name)
    # endfunction

    def set_value(self, key, value):
        setattr(self, key, value)
        self.m_value_changed_event.set()

    def set(self):
        if self.m_waiters > 0:
            self.on_event.set()

    @cocotb.coroutine
    def wait(self):
        if self.m_waiters == 0:
            self.on_event.clear()

        self.m_waiters += 1
        yield self.on_event.wait()
        self.m_waiters -= 1
        if self.m_waiters == 0:
            self.on_event.clear()
        # else-branch needed with Timer(0)

    #    //---------//
    #    // waiting //
    #    //---------//
    #
    #    // Task: wait_on
    #    //
    #    // Waits for the event to be activated for the first time.
    #    //
    #    // If the event has already been triggered, this task returns immediately.
    #    // If ~delta~ is set, the caller will be forced to wait a single delta #0
    #    // before returning. This prevents the caller from returning before
    #    // previously waiting processes have had a chance to resume.
    #    //
    #    // Once an event has been triggered, it will be remain "on" until the event
    #    // is <reset>.
    #    virtual task wait_on (bit delta = 0);
    @cocotb.coroutine
    def wait_on(self, delta=0):
        if self.on is True:
            if delta is True:
                #0;
                yield Timer(0)
            yield Timer(0)
            return
        self.num_waiters += 1
        while True:
            yield self.m_value_changed_event.wait()
            self.m_value_changed_event.clear()
            if self.on is True:
                break
        # endtask

    #    // Task: wait_off
    #    //
    #    // If the event has already triggered and is "on", this task waits for the
    #    // event to be turned "off" via a call to <reset>.
    #    //
    #    // If the event has not already been triggered, this task returns immediately.
    #    // If ~delta~ is set, the caller will be forced to wait a single delta #0
    #    // before returning. This prevents the caller from returning before
    #    // previously waiting processes have had a chance to resume.
    #
    #    virtual task wait_off (bit delta = 0);
    #        if (!self.on) begin
    #            if (delta)
    #                #0;
    #            return;
    #        end
    #        self.num_waiters++;
    #        @self.on;
    #    endtask

    #    // Task: wait_trigger
    #    //
    #    // Waits for the event to be triggered.
    #    //
    #    // If one process calls wait_trigger in the same delta as another process
    #    // calls <uvm_event#(T)::trigger>, a race condition occurs. If the call to wait occurs
    #    // before the trigger, this method will return in this delta. If the wait
    #    // occurs after the trigger, this method will not return until the next
    #    // trigger, which may never occur and thus cause deadlock.
    #
    @cocotb.coroutine
    def wait_trigger(self):
        self.num_waiters += 1
        yield self.m_event.wait()
        self.m_event.clear()
    # endtask

#    // Task: wait_ptrigger
#    //
#    // Waits for a persistent trigger of the event. Unlike <wait_trigger>, this
#    // views the trigger as persistent within a given time-slice and thus avoids
#    // certain race conditions. If this method is called after the trigger but
#    // within the same time-slice, the caller returns immediately.
#
#    virtual task wait_ptrigger ();
#        if (self.m_event.triggered)
#            return;
#        self.num_waiters++;
#        @self.m_event;
#    endtask
#
#
#    // Function: get_trigger_time
#    //
#    // Gets the time that this event was last triggered. If the event has not been
#    // triggered, or the event has been reset, then the trigger time will be 0.
#
#    virtual function time get_trigger_time ();
#        return self.trigger_time;
#    endfunction
#
#
#    //-------//
#    // state //
#    //-------//
#
#    // Function: is_on
#    //
#    // Indicates whether the event has been triggered since it was last reset.
#    //
#    // A return of 1 indicates that the event has triggered.
#
#    virtual function bit is_on ();
#        return (self.on == 1);
#    endfunction
#
#
#    // Function: is_off
#    //
#    // Indicates whether the event has been triggered or been reset.
#    //
#    // A return of 1 indicates that the event has not been triggered.
#
#    virtual function bit is_off ();
#        return (self.on == 0);
#    endfunction
#
#
#    // Function: reset
#    //
#    // Resets the event to its off state. If ~wakeup~ is set, then all processes
#    // currently waiting for the event are activated before the reset.
#    //
#    // No self.callbacks are called during a reset.
#
#    virtual function void reset (bit wakeup = 0);
#        event e;
#        if (wakeup)
#            ->self.m_event;
#        self.m_event = e;
#        self.num_waiters = 0;
#        self.set_value("on", False)
#        self.trigger_time = 0;
#    endfunction
#
#
#
#    //--------------//
#    // waiters list //
#    //--------------//
#
#    // Function: cancel
#    //
#    // Decrements the number of waiters on the event.
#    //
#    // This is used if a process that is waiting on an event is disabled or
#    // activated by some other means.
#
#    virtual function void cancel ();
#        if (self.num_waiters > 0)
#            self.num_waiters--;
#    endfunction
#
#
#    // Function: get_num_waiters
#    //
#    // Returns the number of processes waiting on the event.
#
#    virtual function int get_num_waiters ();
#        return self.num_waiters;
#    endfunction
#
#
#    virtual function string get_type_name();
#        return type_name;
#    endfunction
#
#
#    virtual function void do_print (uvm_printer printer);
#        printer.print_field_int("self.num_waiters", self.num_waiters, $bits(self.num_waiters), UVM_DEC, ".", "int");
#        printer.print_field_int("on", self.on, $bits(self.on), UVM_BIN, ".", "bit");
#        printer.print_time("self.trigger_time", self.trigger_time);
#        printer.m_scope.down("self.callbacks");
#        foreach(self.callbacks[e]) begin
#            printer.print_object($sformatf("[%0d]",e), self.callbacks[e], "[");
#        end
#        printer.m_scope.up();
#    endfunction
#
#
#    virtual function void do_copy (uvm_object rhs);
#        uvm_event_base e;
#        super.do_copy(rhs);
#        if(!$cast(e, rhs) || (e==null)) return;
#
#        self.m_event = e.self.m_event;
#        self.num_waiters = e.self.num_waiters;
#        self.set_value("on", e.on)
#        self.trigger_time = e.self.trigger_time;
#        self.callbacks.delete();
#        self.callbacks = e.self.callbacks;
#
#    endfunction
#
#endclass

#------------------------------------------------------------------------------
#
# CLASS: uvm_event#(T)
#
# The uvm_event class is an extension of the abstract uvm_event_base class.
#
# The optional parameter ~T~ allows the user to define a data type which
# can be passed during an event trigger.
#------------------------------------------------------------------------------
class UVMEvent(UVMEventBase): #(type T=uvm_object) extends uvm_event_base;
    type_name = "uvm_event"
    # local T self.trigger_data;

    # Function: new
    #
    # Creates a new event object.
    def __init__(self, name=""):
        UVMEventBase.__init__(self, name)
        self.trigger_data = None

    #endfunction

    # Task: wait_trigger_data
    #
    # This method calls <uvm_event_base::wait_trigger> followed by <get_trigger_data>.
    @cocotb.coroutine
    def wait_trigger_data(self): #, output T data);
        yield self.wait_trigger();
    #    data = get_trigger_data();
    #    endtask

    #    // Task: wait_ptrigger_data
    #    //
    #    // This method calls <uvm_event_base::wait_ptrigger> followed by <get_trigger_data>.
    #
    #    virtual task wait_ptrigger_data (output T data);
    #        wait_ptrigger();
    #        data = get_trigger_data();
    #    endtask
    #
    #
    #    //------------//
    #    // triggering //
    #    //------------//
    #
    #    // Function: trigger
    #    //
    #    // Triggers the event, resuming all waiting processes.
    #    //
    #    // An optional ~data~ argument can be supplied with the enable to provide
    #    // trigger-specific information.
    #
    def trigger(self, data=None):
        skip = False
        if self.callbacks.size() > 0:
            for i in range(0, self.callbacks.size()):
                #uvm_event_callback#(T) tmp=self.callbacks[i];
                tmp = self.callbacks.get(i)
            skip = skip + tmp.pre_trigger(self, data)
        if skip is False:
            self.m_event.set(data)
            if self.callbacks.size() > 0:
                for i in range(0, self.callbacks.size()):
                    #uvm_event_callback#(T) tmp=self.callbacks[i];
                    tmp = self.callbacks[i]
                    tmp.post_trigger(self,data)
            self.num_waiters = 0
            self.set_value("on", True)
            self.trigger_time = sv.realtime()
            self.trigger_data = data
    # endfunction


    # Function: get_trigger_data
    #
    # Gets the data, if any, provided by the last call to <trigger>.
    def get_trigger_data (self):
        return self.trigger_data

    def get_type_name(self):
        return UVMEvent.type_name
    #    endfunction

    #     //-----------//
    #    // callbacks //
    #    //-----------//
    #
    #    // Function: add_callback
    #    //
    #    // Registers a callback object, ~cb~, with this event. The callback object
    #    // may include pre_trigger and post_trigger functionality. If ~append~ is set
    #    // to 1, the default, ~cb~ is added to the back of the callback list. Otherwise,
    #    // ~cb~ is placed at the front of the callback list.
    #
    #    virtual function void add_callback (uvm_event_callback#(T) cb, bit append=1);
    #        for (int i=0;i<self.callbacks.size();i++) begin
    #            if (cb == self.callbacks[i]) begin
    #                uvm_report_warning("CBRGED","add_callback: Callback already registered. Ignoring.", UVM_NONE);
    #                return;
    #            end
    #        end
    #        if (append)
    #            self.callbacks.push_back(cb);
    #        else
    #            self.callbacks.push_front(cb);
    #    endfunction
    #
    #
    #    // Function: delete_callback
    #    //
    #    // Unregisters the given callback, ~cb~, from this event.
    #
    #    virtual function void delete_callback (uvm_event_callback#(T) cb);
    #        for (int i=0;i<self.callbacks.size();i++) begin
    #            if (cb == self.callbacks[i]) begin
    #                self.callbacks.delete(i);
    #                return;
    #            end
    #        end
    #        uvm_report_warning("CBNTFD", "delete_callback: Callback not found. Ignoring delete request.", UVM_NONE);
    #    endfunction

    #    virtual function void do_print (uvm_printer printer);
    #        super.do_print(printer);
    #        printer.print_object("trigger_data", self.trigger_data);
    #    endfunction

    #    virtual function void do_copy (uvm_object rhs);
    #        uvm_event#(T) e;
    #        super.do_copy(rhs);
    #        if(!$cast(e, rhs) || (e==null)) return;
    #        self.trigger_data = e.trigger_data;
    #    endfunction // do_copy

    #   virtual function uvm_object create(string name="");
    #        uvm_event#(T) v;
    #        v=new(name);
    #        return v;
    #    endfunction

    # endclass

