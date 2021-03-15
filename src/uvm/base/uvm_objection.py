#
#//
#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2013      NVIDIA Corporation
#//   Copyright 2019-2021 Tuomas Poikela
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

import cocotb
from cocotb.triggers import Event, Timer
from .uvm_report_object import UVMReportObject
from .uvm_debug import uvm_debug
from .uvm_globals import *
from .uvm_object_globals import (UVM_RAISED, UVM_DROPPED, UVM_ALL_DROPPED)
from .sv import sv
from ..macros import (uvm_error, uvm_info, uvm_do_callbacks,
    uvm_do_callbacks_async)
from typing import List, Optional, Dict, Any
from .uvm_pool import UVMPool
from .uvm_callback import UVMCallback

UVM_USE_PROCESS_CONTAINER = 1


def classmethod_named(func):
    new_func = classmethod(func)
    setattr(new_func, '__name__', func.__name__)
    return new_func


class UVMObjectionEvents():
    def __init__(self):
        self.waiters = 0
        self.raised = Event('raised')
        self.dropped = Event('dropped')
        self.all_dropped = Event('all_dropped')


ObjContextDict = Dict[Any, 'UVMObjectionContextObject']
ObjContextList = List['UVMObjectionContextObject']


def get_name_depth(curr_obj_name: str) -> int:
    """ Returns the hier depth of the name """
    depth = 0
    for i in curr_obj_name:
        if i == ".":
            depth += 1
    return depth


def get_leaf_name(curr_obj_name: str) -> str:
    name = curr_obj_name
    rr = range(len(curr_obj_name)-1, -1, -1)
    for i in rr:
        if curr_obj_name[i] == ".":
            name = curr_obj_name[i+1:len(curr_obj_name)]
            break
    return name

#//------------------------------------------------------------------------------
#// Title: Objection Mechanism
#//------------------------------------------------------------------------------
#// The following classes define the objection mechanism and end-of-test
#// functionality, which is based on <uvm_objection>.
#//------------------------------------------------------------------------------

#//------------------------------------------------------------------------------
#//
#// Class: uvm_objection_callback
#//
#//------------------------------------------------------------------------------
#// The uvm_objection is the callback type that defines the callback
#// implementations for an objection callback. A user uses the callback
#// type uvm_objection_cbs_t to add callbacks to specific objections.
#//
#// For example:
#//
#//| class my_objection_cb extends uvm_objection_callback
#//|   function new(string name)
#//|     super.new(name)
#//|   endfunction
#//|
#//|   virtual function void raised (uvm_objection objection, uvm_object obj,
#//|       uvm_object source_obj, string description, int count)
#//|       `uvm_info("RAISED","%0t: Objection %s: Raised for %s", $time, objection.get_name(),
#//|       obj.get_full_name())
#//|   endfunction
#//| endclass
#//| ...
#//| initial begin
#//|   my_objection_cb cb = new("cb")
#//|   uvm_objection_cbs_t::add(null, cb); //typewide callback
#//| end


class UVMObjectionCallback(UVMCallback):
    def __init__(self, name):
        super().__init__(name)
#  // Function: raised
#  //
#  // Objection raised callback function. Called by <uvm_objection::raised>.
#
#  virtual function void raised (uvm_objection objection, uvm_object obj,
#      uvm_object source_obj, string description, int count)
#  endfunction
#
#  // Function: dropped
#  //
#  // Objection dropped callback function. Called by <uvm_objection::dropped>.
#
#  virtual function void dropped (uvm_objection objection, uvm_object obj,
#      uvm_object source_obj, string description, int count)
#  endfunction
#
#  // Function: all_dropped
#  //
#  // Objection all_dropped callback function. Called by <uvm_objection::all_dropped>.
#
#  virtual task all_dropped (uvm_objection objection, uvm_object obj,
#      uvm_object source_obj, string description, int count)
#  endtask
#
#endclass

#//------------------------------------------------------------------------------
#//
#// Class: uvm_objection
#//
#//------------------------------------------------------------------------------
#// Objections provide a facility for coordinating status information between
#// two or more participating components, objects, and even module-based IP.
#//
#// Tracing of objection activity can be turned on to follow the activity of
#// the objection mechanism. It may be turned on for a specific objection
#// instance with <uvm_objection::trace_mode>, or it can be set for all
#// objections from the command line using the option +UVM_OBJECTION_TRACE.
#//------------------------------------------------------------------------------


class UVMObjection(UVMReportObject):
    m_objections = []  # static uvm_objection[$]
    #  `uvm_register_cb(uvm_objection, uvm_objection_callback)
    #
    #  protected bit     self.m_trace_mode
    #  protected int     self.m_source_count[uvm_object]
    #  protected int     self.m_total_count [uvm_object]
    #  protected time    self.m_drain_time  [uvm_object]
    #  protected uvm_objection_events self.m_events [uvm_object]
    #  /*protected*/ bit     self.m_top_all_dropped
    #
    #  protected uvm_root self.m_top
    #
    #
    #  //// Drain Logic
    #
    #  // The context pool holds used context objects, so that
    #  // they're not constantly being recreated.  The maximum
    #  // number of contexts in the pool is equal to the maximum
    #  // number of simultaneous drains you could have occuring,
    #  // both pre and post forks.
    #  //
    #  // There's the potential for a programmability within the
    #  // library to dictate the largest this pool should be allowed
    #  // to grow, but that seems like overkill for the time being.
    #  local static uvm_objection_context_object UVMObjection.m_context_pool[$]
    m_context_pool = []

    # Notified when m_scheduled_list is not empty
    m_scheduled_list_not_empty_event = Event('m_scheduled_list_not_empty_event')

    #  // These are the active drain processes, which have been
    #  // forked off by the background process.  A raise can
    #  // use this array to kill a drain.
    #`ifndef UVM_USE_PROCESS_CONTAINER
    #  local process self.m_drain_proc[uvm_object]
    #`else
    #  local process_container_c self.m_drain_proc[uvm_object]
    #`endif

    #  // These are the contexts which have been scheduled for
    #  // retrieval by the background process, but which the
    #  // background process hasn't seen yet.
    #  local static uvm_objection_context_object m_scheduled_list[$]
    m_scheduled_list: ObjContextList = []

    #  // Once a context is seen by the background process, it is
    #  // removed from the scheduled list, and placed in the forked
    #  // list.  At the same time, it is placed in the scheduled
    #  // contexts array.  A re-raise can use the scheduled contexts
    #  // array to detect (and cancel) the drain.
    #  local uvm_objection_context_object self.m_scheduled_contexts[uvm_object]

    #  // Once the forked drain has actually started (this occurs
    #  // ~1 delta AFTER the background process schedules it), the
    #  // context is removed from the above array and list, and placed
    #  // in the forked_contexts list.
    #  local uvm_objection_context_object self.m_forked_contexts[uvm_object]
    #
    #  protected bit self.m_prop_mode = 1

    #  // Function: new
    #  //
    #  // Creates a new objection instance. Accesses the command line
    #  // argument +UVM_OBJECTION_TRACE to turn tracing on for
    #  // all objection objects.
    #
    def __init__(self, name=""):
        #uvm_cmdline_processor clp
        #uvm_coreservice_t cs_
        trace_args = []  # string [$]
        UVMReportObject.__init__(self, name)
        from .uvm_coreservice import UVMCoreService
        cs_ = UVMCoreService.get()
        #cs_ = uvm_coreservice_t::get()
        self.m_top = cs_.get_root()

        self.m_cleared = 0  # protected bit /* for checking obj count<0 */

        self.m_forked_list: ObjContextList = []  # uvm_objection_context_object[$]

        self.m_scheduled_contexts: ObjContextDict = {}  # uvm_objection_context_object[uvm_object]
        self.m_forked_contexts: ObjContextDict = {}  # uvm_objection_context_object[uvm_object]

        self.m_source_count = {}  # int[uvm_object]
        self.m_total_count = {}  # int[uvm_object]
        self.m_drain_time = {}  # time [uvm_object]
        self.m_events: Dict[Any, UVMObjectionEvents] = {}  # uvm_objection_events[uvm_object]
        self.m_top_all_dropped = 0

        self.m_drain_proc = {}  # process_container_c [uvm_object]

        self.set_report_verbosity_level(self.m_top.get_report_verbosity_level())

        # Get the command line trace mode setting
        #clp = uvm_cmdline_processor::get_inst()
        from .uvm_cmdline_processor import UVMCmdlineProcessor
        clp = UVMCmdlineProcessor.get_inst()

        self.m_prop_mode = 1
        self.m_trace_mode = 0
        if clp.get_arg_matches("+UVM_OBJECTION_TRACE", trace_args):
            self.m_trace_mode = 1
        UVMObjection.m_objections.append(self)

    #  // Function: trace_mode
    #  //
    #  // Set or get the trace mode for the objection object. If no
    #  // argument is specified (or an argument other than 0 or 1)
    #  // the current trace mode is unaffected. A trace_mode of
    #  // 0 turns tracing off. A trace mode of 1 turns tracing on.
    #  // The return value is the mode prior to being reset.
    #
    def trace_mode(self, mode=-1):
        trace_mode = self.m_trace_mode
        if mode == 0:
            self.m_trace_mode = 0
        elif mode == 1:
            self.m_trace_mode = 1
        return trace_mode

    #  // Function- m_report
    #  //
    #  // Internal method for reporting count updates
    #
    def m_report(self, obj, source_obj, description: str, count: int, action: str) -> None:
        _count = 0
        if obj in self.m_source_count:
            _count = self.m_source_count[obj]
        _total = 0
        if obj in self.m_total_count:
            _total = self.m_total_count[obj]
        if (not uvm_report_enabled(UVM_NONE, UVM_INFO,"OBJTN_TRC") or (not self.m_trace_mode)):
            return

        descr = ""
        if description != "":
            descr = " (" + description + ")"

        if source_obj is obj:
            name = obj.get_full_name()
            if name == "":
                name = "uvm_top"
            uvm_report_info("OBJTN_TRC",
                sv.sformatf("Object %0s %0s %0d objection(s)%s: count=%0d  total=%0d",
                name, action, count, descr, _count, _total), UVM_NONE)
        else:
            cpath = 0
            last_dot = 0
            sname = source_obj.get_full_name()
            nm = obj.get_full_name()
            _max = sname.len()
            if sname.len() > nm.len():
                _max = nm.len()

            # For readability, only print the part of the source obj hierarchy underneath
            # the current object.
            while ((sname[cpath] == nm[cpath]) and (cpath < _max)):
                if (sname[cpath] == "."):
                    last_dot = cpath
                cpath += 1

            if last_dot:
                sname = sname.substr(last_dot+1, sname.len())

        name = obj.get_full_name()
        if name == "":
            name = "uvm_top"
        act_type = "subtracted"
        if action == "raised":
            act_type = "added"
        act_dir = "from"
        if action == "raised":
            act_dir = "to"
        uvm_report_info("OBJTN_TRC",
            sv.sformatf("Object %0s %0s %0d objection(s) %0s its total (%s from"
            " source object %s%s): count=%0d  total=%0d", name, act_type, count,
            act_dir, action, sname, descr, _count, _total), UVM_NONE)

    #  // Function- m_get_parent
    #  //
    #  // Internal method for getting the parent of the given ~object~.
    #  // The ultimate parent is uvm_top, UVM's implicit top-level component.
    #
    def m_get_parent(self, obj):
        comp = None
        seq = None
        if hasattr(obj, 'get_parent'):
            comp = obj
            obj = comp.get_parent()
        elif hasattr(obj, 'get_sequencer'):
            seq = obj
            obj = seq.get_sequencer()
        else:
            obj = self.m_top
        if obj is None:
            obj = self.m_top
        return obj


    #  // Function- m_propagate
    #  //
    #  // Propagate the objection to the objects parent. If the object is a
    #  // component, the parent is just the hierarchical parent. If the object is
    #  // a sequence, the parent is the parent sequence if one exists, or
    #  // it is the attached sequencer if there is no parent sequence.
    #  //
    #  // obj : the uvm_object on which the objection is being raised or lowered
    #  // source_obj : the root object on which the end user raised/lowered the
    #  //   objection (as opposed to an anscestor of the end user object)a
    #  // count : the number of objections associated with the action.
    #  // raise : indicator of whether the objection is being raised or lowered. A
    #  //   1 indicates the objection is being raised.
    #
    def m_propagate(self, obj, source_obj, description, count, raise_, in_top_thread):
        if obj is not None and obj != self.m_top:
            parent_obj = self.m_get_parent(obj)
            if raise_:
                self.m_raise(parent_obj, source_obj, description, count)
            else:
                self.m_drop(parent_obj, source_obj, description, count, in_top_thread)

    #  // Group: Objection Control
    #
    #  // Function: set_propagate_mode
    #  // Sets the propagation mode for this objection.
    #  //
    #  // By default, objections support hierarchical propagation for
    #  // components.  For example, if we have the following basic
    #  // component tree:
    #  //
    #  //| uvm_top.parent.child
    #  //
    #  // Any objections raised by 'child' would get propagated
    #  // down to parent, and then to uvm_test_top.  Resulting in the
    #  // following counts and totals:
    #  //
    #  //|                      | count | total |
    #  //| uvm_top.parent.child |     1 |    1  |
    #  //| uvm_top.parent       |     0 |    1  |
    #  //| uvm_top              |     0 |    1  |
    #  //|
    #  //
    #  // While propagations such as these can be useful, if they are
    #  // unused by the testbench then they are simply an unnecessary
    #  // performance hit.  If the testbench is not going to use this
    #  // functionality, then the performance can be improved by setting
    #  // the propagation mode to 0.
    #  //
    #  // When propagation mode is set to 0, all intermediate callbacks
    #  // between the ~source~ and ~top~ will be skipped.  This would
    #  // result in the following counts and totals for the above objection:
    #  //
    #  //|                      | count | total |
    #  //| uvm_top.parent.child |     1 |    1  |
    #  //| uvm_top.parent       |     0 |    0  |
    #  //| uvm_top              |     0 |    1  |
    #  //|
    #  //
    #  // Since the propagation mode changes the behavior of the objection,
    #  // it can only be safely changed if there are no objections ~raised~
    #  // or ~draining~.  Any attempts to change the mode while objections
    #  // are ~raised~ or ~draining~ will result in an error.
    #  //
    #  function void set_propagate_mode (bit prop_mode)
    #     if (!self.m_top_all_dropped && (get_objection_total() != 0)) begin
    #        `uvm_error("UVM/BASE/OBJTN/PROP_MODE",
    #                   {"The propagation mode of '", this.get_full_name(),
    #                    "' cannot be changed while the objection is raised ",
    #                    "or draining!"})
    #        return
    #     end
    #
    #     self.m_prop_mode = prop_mode
    #  endfunction : set_propagate_mode

    #  // Function: get_propagate_mode
    #  // Returns the propagation mode for this objection.
    def get_propagate_mode(self) -> int:
        return self.m_prop_mode

    #  // Function: raise_objection
    #  //
    #  // Raises the number of objections for the source ~object~ by ~count~, which
    #  // defaults to 1.  The ~object~ is usually the ~this~ handle of the caller.
    #  // If ~object~ is not specified or ~null~, the implicit top-level component,
    #  // <uvm_root>, is chosen.
    #  //
    #  // Raising an objection causes the following.
    #  //
    #  // - The source and total objection counts for ~object~ are increased by
    #  //   ~count~. ~description~ is a string that marks a specific objection
    #  //   and is used in tracing/debug.
    #  //
    #  // - The objection's <raised> virtual method is called, which calls the
    #  //   <uvm_component::raised> method for all of the components up the
    #  //   hierarchy.
    #  //
    def raise_objection(self, obj=None, description="", count=1):
        if obj is None:
            obj = self.m_top
        self.m_cleared = 0
        self.m_top_all_dropped = 0
        uvm_debug(self, 'raise_objection', obj.get_name() + " Starting to raise objection")
        self.m_raise(obj, obj, description, count)

    #  // Function- m_raise
    def m_raise(self, obj, source_obj, description="", count=1):
        idx = 0
        ctxt = None  # uvm_objection_context_object

        # Ignore raise if count is 0
        if count == 0:
            return

        if obj in self.m_total_count:
            self.m_total_count[obj] += count
        else:
            self.m_total_count[obj] = count

        if source_obj == obj:
            if obj in self.m_source_count:
                self.m_source_count[obj] += count
            else:
                self.m_source_count[obj] = count

        if self.m_trace_mode:
            self.m_report(obj,source_obj,description,count,"raised")

        self.raised(obj, source_obj, description, count)

        # Handle any outstanding drains...
        # First go through the scheduled list
        idx = 0
        m_scheduled_list = UVMObjection.m_scheduled_list
        # while idx < len(m_scheduled_list):
        for entry in m_scheduled_list:
            if ((entry.obj == obj) and
                    (entry.objection == self)):
                # Caught it before the drain was forked
                ctxt = entry
                del m_scheduled_list[idx]
                break
            idx += 1

        # If it's not there, go through the forked list
        if ctxt is None:
            idx = 0
            while idx < len(self.m_forked_list):
                if self.m_forked_list[idx].obj == obj:
                    # Caught it after the drain was forked,
                    # but before the fork started
                    ctxt = self.m_forked_list[idx]
                    del self.m_forked_list[idx]
                    del self.m_scheduled_contexts[ctxt.obj]
                    break
                idx += 1

        # If it's not there, go through the forked contexts
        if ctxt is None:
            if obj in self.m_forked_contexts:
                # Caught it with the forked drain running
                ctxt = self.m_forked_contexts[obj]
                del self.m_forked_contexts[obj]
                # Kill the drain

        uvm_debug(self, 'm_raise', obj.get_name() + " ENDING FUNC")
        # TODO
        #if UVM_USE_PROCESS_CONTAINER:
        #    self.m_drain_proc[obj].kill()
        #    del self.m_drain_proc[obj]
        #else:
        #    self.m_drain_proc[obj].p.kill()
        #    del self.m_drain_proc[obj]
        uvm_debug(self, 'm_raise', obj.get_name() + " NEVER GETS HERE")

        if ctxt is None:
            # If there were no drains, just propagate as usual
            if not self.m_prop_mode and obj != self.m_top:
                uvm_debug(self, 'm_raise', obj.get_name() + " XXX NEVER GETS HERE")
                self.m_raise(self.m_top,source_obj,description,count)
            elif obj != self.m_top:
                self.m_propagate(obj, source_obj, description, count, 1, 0)

        else:
            # Otherwise we need to determine what exactly happened

            # Determine the diff count, if it's positive, then we're
            # looking at a 'raise' total, if it's negative, then
            # we're looking at a 'drop', but not down to 0.  If it's
            # a 0, that means that there is no change in the total.
            diff_count = count - ctxt.count

            if diff_count != 0:
                # Something changed
                if diff_count > 0:
                    # we're looking at an increase in the total
                    if not self.m_prop_mode and obj != self.m_top:
                        self.m_raise(self.m_top, source_obj, description, diff_count)
                    elif obj != self.m_top:
                        self.m_propagate(obj, source_obj, description, diff_count, 1, 0)
                else:
                    # we're looking at a decrease in the total
                    # The count field is always positive...
                    diff_count = -diff_count
                    if not self.m_prop_mode and obj != self.m_top:
                        self.m_drop(self.m_top, source_obj, description, diff_count)
                    elif obj != self.m_top:
                        self.m_propagate(obj, source_obj, description, diff_count, 0, 0)

            # Cleanup
            ctxt.clear()
            UVMObjection.m_context_pool.append(ctxt)
        #  endfunction

    #  // Function: drop_objection
    #  //
    #  // Drops the number of objections for the source ~object~ by ~count~, which
    #  // defaults to 1.  The ~object~ is usually the ~this~ handle of the caller.
    #  // If ~object~ is not specified or ~null~, the implicit top-level component,
    #  // <uvm_root>, is chosen.
    #  //
    #  // Dropping an objection causes the following.
    #  //
    #  // - The source and total objection counts for ~object~ are decreased by
    #  //   ~count~. It is an error to drop the objection count for ~object~ below
    #  //   zero.
    #  //
    #  // - The objection's <dropped> virtual method is called, which calls the
    #  //   <uvm_component::dropped> method for all of the components up the
    #  //   hierarchy.
    #  //
    #  // - If the total objection count has not reached zero for ~object~, then
    #  //   the drop is propagated up the object hierarchy as with
    #  //   <raise_objection>. Then, each object in the hierarchy will have updated
    #  //   their ~source~ counts--objections that they originated--and ~total~
    #  //   counts--the total number of objections by them and all their
    #  //   descendants.
    #  //
    #  // If the total objection count reaches zero, propagation up the hierarchy
    #  // is deferred until a configurable drain-time has passed and the
    #  // <uvm_component::all_dropped> callback for the current hierarchy level
    #  // has returned. The following process occurs for each instance up
    #  // the hierarchy from the source caller:
    #  //
    #  // A process is forked in a non-blocking fashion, allowing the ~drop~
    #  // call to return. The forked process then does the following:
    #  //
    #  // - If a drain time was set for the given ~object~, the process waits for
    #  //   that amount of time.
    #  //
    #  // - The objection's <all_dropped> virtual method is called, which calls the
    #  //   <uvm_component::all_dropped> method (if ~object~ is a component).
    #  //
    #  // - The process then waits for the ~all_dropped~ callback to complete.
    #  //
    #  // - After the drain time has elapsed and all_dropped callback has
    #  //   completed, propagation of the dropped objection to the parent proceeds
    #  //   as described in <raise_objection>, except as described below.
    #  //
    #  // If a new objection for this ~object~ or any of its descendants is raised
    #  // during the drain time or during execution of the all_dropped callback at
    #  // any point, the hierarchical chain described above is terminated and the
    #  // dropped callback does not go up the hierarchy. The raised objection will
    #  // propagate up the hierarchy, but the number of raised propagated up is
    #  // reduced by the number of drops that were pending waiting for the
    #  // all_dropped/drain time completion. Thus, if exactly one objection
    #  // caused the count to go to zero, and during the drain exactly one new
    #  // objection comes in, no raises or drops are propagated up the hierarchy,
    #  //
    #  // As an optimization, if the ~object~ has no set drain-time and no
    #  // registered callbacks, the forked process can be skipped and propagation
    #  // proceeds immediately to the parent as described.
    #
    def drop_objection(self, obj=None, description="", count=1):
        if obj is None:
            obj = self.m_top
        uvm_debug(self, 'drop_objection', obj.get_name() + " Starting to drop objection")

        self.m_drop(obj, obj, description, count, 0)

    #  // Function- m_drop
    #
    def m_drop(self, obj, source_obj, description="", count=1,
            in_top_thread=0):
        # Ignore drops if the count is 0
        if count == 0:
            return

        if obj not in self.m_total_count or (count > self.m_total_count[obj]):
            if self.m_cleared:
                return
            uvm_report_fatal("OBJTN_ZERO", ("Object '" + obj.get_full_name()
              + "' attempted to drop total objection '" + self.get_name() + "' count below zero. " +
              "Description: '" + description + "' source_obj: " +
              source_obj.get_name()))
            return

        if obj == source_obj:
            if obj not in self.m_source_count or (count > self.m_source_count[obj]):
                if self.m_cleared:
                    return
                uvm_report_fatal("OBJTN_ZERO", ("Object \"" + obj.get_full_name()
                  + "\" attempted to drop source objection '" + self.get_name() + "' count below zero"))
                return
            self.m_source_count[obj] -= count

        self.m_total_count[obj] -= count

        if self.m_trace_mode:
            self.m_report(obj,source_obj,description,count,"dropped")

        self.dropped(obj, source_obj, description, count)

        # if count != 0, no reason to fork
        if self.m_total_count[obj] != 0:
            if not self.m_prop_mode and obj != self.m_top:
                self.m_drop(self.m_top,source_obj,description, count, in_top_thread)
            elif obj != self.m_top:
                self.m_propagate(obj, source_obj, description, count, 0, in_top_thread)
        else:
            ctxt = None  # uvm_objection_context_object
            if (len(UVMObjection.m_context_pool) > 0):
                ctxt = UVMObjection.m_context_pool.pop(0)
            else:
                ctxt = UVMObjectionContextObject()

            ctxt.obj = obj
            ctxt.source_obj = source_obj
            ctxt.description = description
            ctxt.count = count
            ctxt.objection = self
            # Need to be thread-safe, let the background
            # process handle it.

            # Why don't we look at in_top_thread here?  Because
            # a re-raise will kill the drain at object that it's
            # currently occuring at, and we need the leaf-level kills
            # to not cause accidental kills at branch-levels in
            # the propagation.

            # Using the background process just allows us to
            # separate the links of the chain.
            UVMObjection.m_scheduled_list.append(ctxt)
            UVMObjection.m_scheduled_list_not_empty_event.set()
        #end // else: !if(self.m_total_count[obj] != 0)


    # Function: clear
    #
    # Immediately clears the objection state. All counts are cleared and the
    # any processes waiting on a call to wait_for(UVM_ALL_DROPPED, uvm_top)
    # are released.
    #
    # The caller, if a uvm_object-based object, should pass its 'this' handle
    # to the ~obj~ argument to document who cleared the objection.
    # Any drain_times set by the user are not affected.
    #
    def clear(self, obj=None):
        name = ""
        ctxt = None  # uvm_objection_context_object
        idx = 0

        uvm_debug(self, 'clear', 'START')
        if obj is None:
            obj = self.m_top

        name = obj.get_full_name()
        if name == "":
            name = "uvm_top"

        if (self.m_top_all_dropped is False and
                self.get_objection_total(self.m_top) > 0):
            uvm_report_warning("OBJTN_CLEAR",("Object '" + name
                + "' cleared objection counts for " + self.get_name()))
        # Should there be a warning if there are outstanding objections
        self.m_source_count = {}
        self.m_total_count = {}

        # Remove any scheduled drains from the static queue
        idx = 0
        while (idx < len(UVMObjection.m_scheduled_list)):
            if (UVMObjection.m_scheduled_list[idx].objection == self):
                UVMObjection.m_scheduled_list[idx].clear()
                UVMObjection.m_context_pool.append(UVMObjection.m_scheduled_list[idx])
                del UVMObjection.m_scheduled_list[idx]
            else:
                idx += 1

        # Scheduled contexts and m_forked_lists have duplicate
        # entries... clear out one, free the other.
        self.m_scheduled_contexts = {}
        while len(self.m_forked_list) > 0:
            self.m_forked_list[0].clear()
            UVMObjection.m_context_pool.append(self.m_forked_list[0])
            front = self.m_forked_list[0]
            self.m_forked_list[0].remove(front)

        # running drains have a context and a process
        for o in self.m_forked_contexts:
            if UVM_USE_PROCESS_CONTAINER:
                self.m_drain_proc[o].kill()
                del self.m_drain_proc[o]
            else:
                self.m_drain_proc[o].p.kill()
                del self.m_drain_proc[o]

            self.m_forked_contexts[o].clear()
            UVMObjection.m_context_pool.append(self.m_forked_contexts[o])
            del self.m_forked_contexts[o]

        self.m_top_all_dropped = False
        self.m_cleared = 1
        if self.m_top in self.m_events:
            self.m_events[self.m_top].all_dropped.set()

    #  // m_execute_scheduled_forks
    #  // -------------------------
    #  // background process; when non

    @classmethod
    async def m_execute_scheduled_forks(cls):
        while True:
            #wait(UVMObjection.m_scheduled_list.size() != 0)
            uvm_debug(cls, 'm_execute_scheduled_forks', 'waiting list to not be empty')
            await UVMObjection.m_scheduled_list_not_empty_event.wait()
            UVMObjection.m_scheduled_list_not_empty_event.clear()

            if len(UVMObjection.m_scheduled_list) != 0:
                # Save off the context before the fork
                c = UVMObjection.m_scheduled_list.pop(0)

                # A re-raise can use this to figure out props (if any)
                objection = c.objection
                #rm if objection is not None:
                objection.m_scheduled_contexts[c.obj] = c
                # The fork below pulls out from the forked list
                objection.m_forked_list.append(c)
                # The fork will guard the m_forked_drain call, but
                # a re-raise can kill self.m_forked_list contexts in the delta
                # before the fork executes.
                pproc = cocotb.fork(cls.m_execute_scheduled_forks_fork_join_none(c))
                #else:
                #    uvm_error("UVMObjection", "Null objection in objection context")


    @classmethod
    async def m_execute_scheduled_forks_fork_join_none(cls,
            c: 'UVMObjectionContextObject'):
        objection = c.objection  # automatic uvm_objection
        # Check to maike sure re-raise didn't empty the fifo
        uvm_debug(cls, 'm_execute_scheduled_forks_fork_join_none', 'check list len')
        if len(objection.m_forked_list) > 0:
            #uvm_objection_context_object ctxt
            ctxt = objection.m_forked_list.pop(0)
            # Clear it out of scheduled
            del objection.m_scheduled_contexts[ctxt.obj]

            # Move it in to forked (so re-raise can figure out props)
            objection.m_forked_contexts[ctxt.obj] = ctxt
            # Save off our process handle, so a re-raise can kill it...

            # TODO
            #if UVM_USE_PROCESS_CONTAINER == 0:
            #    objection.m_drain_proc[ctxt.obj] = process::self()
            #else:
            #    process_container_c c = new(process::self())
            #    objection.m_drain_proc[ctxt.obj]=c

            # Execute the forked drain
            await objection.m_forked_drain(ctxt.obj, ctxt.source_obj, ctxt.description,
                    ctxt.count, 1)
            # Cleanup if we survived (no re-raises)
            if ctxt.obj in objection.m_drain_proc:
                del objection.m_drain_proc[ctxt.obj]
            else:
                pass

            # tpoikela: Added check since ctxt.obj becomes None
            #if ctxt.obj in objection.m_forked_contexts:
            del objection.m_forked_contexts[ctxt.obj]
            # Clear out the context object (prevent memory leaks)
            ctxt.clear()
            # Save the context in the pool for later reuse
            UVMObjection.m_context_pool.append(ctxt)
        #rm await uvm_zero_delay()

    #  // m_forked_drain
    #  // -------------
    #  task m_forked_drain (uvm_object obj,
    #                       uvm_object source_obj,
    #                       string description="",
    #                       int count=1,
    #                       int in_top_thread=0)

    async def m_forked_drain(self, obj, source_obj, description="", count=1,
            in_top_thread=0):
        #rm diff_count = 0

        if obj in self.m_drain_time:
            # pass
            # TODO `uvm_delay(self.m_drain_time[obj])
            await Timer(self.m_drain_time[obj])

        if self.m_trace_mode:
            self.m_report(obj,source_obj,description,count,"all_dropped")

        await self.all_dropped(obj,source_obj,description, count)

        # wait for all_dropped cbs to complete
        await uvm_zero_delay()
        # TODO wait fork

        # we are ready to delete the 0-count entries for the current
        # object before propagating up the hierarchy.
        if obj in self.m_source_count and self.m_source_count[obj] == 0:
            del self.m_source_count[obj]

        if obj in self.m_total_count and self.m_total_count[obj] == 0:
            del self.m_total_count[obj]

        if not self.m_prop_mode and obj != self.m_top:
            self.m_drop(self.m_top,source_obj,description, count, 1)
        elif obj != self.m_top:
            self.m_propagate(obj, source_obj, description, count, 0, 1)

    #  // m_init_objections
    #  // -----------------
    #
    #  // Forks off the single background process
    @classmethod
    async def m_init_objections(cls):
        #uvm_debug(cls, 'm_init_objections', "Forking m_execute_scheduled_forks")
        pproc = cocotb.fork(cls.m_execute_scheduled_forks())
        #await uvm_zero_delay()

    #  // Function: set_drain_time
    #  //
    #  // Sets the drain time on the given ~object~ to ~drain~.
    #  //
    #  // The drain time is the amount of time to wait once all objections have
    #  // been dropped before calling the all_dropped callback and propagating
    #  // the objection to the parent.
    #  //
    #  // If a new objection for this ~object~ or any of its descendants is raised
    #  // during the drain time or during execution of the all_dropped callbacks,
    #  // the drain_time/all_dropped execution is terminated.
    #
    #  // AE: set_drain_time(drain,obj=null)?
    def set_drain_time(self, obj=None, drain=0):
        if obj is None:
            obj = self.m_top
            self.m_drain_time[obj] = drain

    #  //----------------------
    #  // Group: Callback Hooks
    #  //----------------------

    #  // Function: raised
    #  //
    #  // Objection callback that is called when a <raise_objection> has reached ~obj~.
    #  // The default implementation calls <uvm_component::raised>.
    #
    def raised(self, obj, source_obj, description, count):
        if hasattr(obj, 'raised'):
            obj.raised(self, source_obj, description, count)
        # TODO `uvm_do_callbacks(uvm_objection,uvm_objection_callback,raised(this,obj,source_obj,description,count))
        uvm_do_callbacks(self, UVMObjectionCallback, 'raised', self,obj,source_obj,description,count)
        if obj in self.m_events:
            self.m_events[obj].raised.set()

    #  // Function: dropped
    #  //
    #  // Objection callback that is called when a <drop_objection> has reached ~obj~.
    #  // The default implementation calls <uvm_component::dropped>.
    #
    #  virtual function void dropped (uvm_object obj,
    #                                 uvm_object source_obj,
    #                                 string description,
    #                                 int count)
    def dropped(self, obj, source_obj, description, count):
        comp = obj
        #if($cast(comp,obj))
        comp.dropped(self, source_obj, description, count)
        # TODO `uvm_do_callbacks(uvm_objection,uvm_objection_callback,dropped(this,obj,source_obj,description,count))
        uvm_do_callbacks(self,UVMObjectionCallback,'dropped', self,obj,source_obj,description,count)
        if obj in self.m_events:
            self.m_events[obj].dropped.set()


    #  // Function: all_dropped
    #  //
    #  // Objection callback that is called when a <drop_objection> has reached ~obj~,
    #  // and the total count for ~obj~ goes to zero. This callback is executed
    #  // after the drain time associated with ~obj~. The default implementation
    #  // calls <uvm_component::all_dropped>.
    #  virtual task all_dropped (uvm_object obj,
    #                            uvm_object source_obj,
    #                            string description,
    #                            int count)
    async def all_dropped(self, obj, source_obj, description, count):
        comp = obj
        await comp.all_dropped(self, source_obj, description, count)
        # TODO `uvm_do_callbacks(uvm_objection,uvm_objection_callback,all_dropped(this,obj,source_obj,description,count))
        await uvm_do_callbacks_async(self, UVMObjectionCallback, 'all_dropped', self,obj, source_obj, description, count)
        if obj in self.m_events:
            self.m_events[obj].all_dropped.set()
        if obj == self.m_top:
            self.m_top_all_dropped = 1
    #  endtask

    #  //------------------------
    #  // Group: Objection Status
    #  //------------------------
    #
    #  // Function: get_objectors
    #  //
    #  // Returns the current list of objecting objects (objects that
    #  // raised an objection but have not dropped it).
    #
    #  function void get_objectors(ref uvm_object list[$])
    #    list.delete()
    #    foreach (self.m_source_count[obj]) list.push_back(obj)
    #  endfunction

    #  // Task: wait_for
    #  //
    #  // Waits for the raised, dropped, or all_dropped ~event~ to occur in
    #  // the given ~obj~. The task returns after all corresponding callbacks
    #  // for that event have been executed.
    #  //
    #  task wait_for(uvm_objection_event objt_event, uvm_object obj=null)
    async def wait_for(self, objt_event, obj=None):
        if obj is None:
            obj = self.m_top

        if (obj in self.m_events) is False:
            self.m_events[obj] = UVMObjectionEvents()

        self.m_events[obj].waiters += 1
        if objt_event == UVM_RAISED:
            await self.m_events[obj].raised.wait()
        elif objt_event == UVM_DROPPED:
            await self.m_events[obj].dropped.wait()
        elif objt_event == UVM_ALL_DROPPED:
            await self.m_events[obj].all_dropped.wait()

        self.m_events[obj].waiters -= 1

        if self.m_events[obj].waiters == 0:
            del self.m_events[obj]

    #
    #   task wait_for_total_count(uvm_object obj=null, int count=0)
    #     if (obj==null)
    #       obj = self.m_top
    #
    #     if(!self.m_total_count.exists(obj) && count == 0)
    #       return
    #     if (count == 0)
    #        wait (!self.m_total_count.exists(obj) && count == 0)
    #     else
    #        wait (self.m_total_count.exists(obj) && self.m_total_count[obj] == count)
    #   endtask


    #  // Function: get_objection_count
    #  //
    #  // Returns the current number of objections raised by the given ~object~.
    #
    def get_objection_count(self, obj=None):
        if obj is None:
            obj = self.m_top

        if obj not in self.m_source_count:
            return 0
        return self.m_source_count[obj]

    #  // Function: get_objection_total
    #  //
    #  // Returns the current number of objections raised by the given ~object~
    #  // and all descendants.
    #
    def get_objection_total(self, obj=None):
        uvm_debug(self, 'get_objection_total', 'START')
        if obj is None:
            obj = self.m_top

        if obj not in self.m_total_count:
            uvm_debug(self, 'get_objection_total', 'Returning 0')
            return 0
        else:
            cnt = self.m_total_count[obj]
            uvm_debug(self, 'get_objection_total', 'Returning cnt ' + str(cnt))
            return self.m_total_count[obj]


    #  // Function: get_drain_time
    #  //
    #  // Returns the current drain time set for the given ~object~ (default: 0 ns).
    #
    #  function time get_drain_time (uvm_object obj=null)
    #    if (obj==null)
    #      obj = self.m_top
    #
    #    if (!self.m_drain_time.exists(obj))
    #      return 0
    #    return self.m_drain_time[obj]
    #  endfunction
    #
    #

    #  // m_display_objections
    #
    def m_display_objections(self, obj=None, show_header=1):
        blank="                                                                                   "
        s = ""
        total = 0
        lst = UVMPool()
        curr_obj = None
        depth = 0
        name = ""
        this_obj_name = ""
        curr_obj_name = ""

        for o in self.m_total_count:
            theobj = o
            if self.m_total_count[o] > 0:
                lst[theobj.get_full_name()] = theobj

        if obj is None:
            obj = self.m_top

        total = self.get_objection_total(obj)
        s = sv.sformatf("The total objection count is %0d\n",total)

        if total == 0:
            return s

        s = s + "---------------------------------------------------------\n"
        s = s + "Source  Total   \n"
        s = s + "Count   Count   Object\n"
        s = s + "---------------------------------------------------------\n"

        this_obj_name = obj.get_full_name()
        curr_obj_name = this_obj_name

        while True:
            curr_obj = lst[curr_obj_name]

            # determine depth, count dots "." in the name
            depth = get_name_depth(curr_obj_name)

            # determine leaf name
            name = get_leaf_name(curr_obj_name)

            if curr_obj_name == "":
                name = "uvm_top"
            else:
                depth += 1

            # print it
            src_count = 0
            if curr_obj in self.m_source_count:
                src_count = self.m_source_count[curr_obj]
            total_count = 0
            if curr_obj in self.m_total_count:
                total_count = self.m_total_count[curr_obj]
            s += sv.sformatf("%d       %d       %s'%s'\n", src_count, total_count,
                    blank[0:2*depth], name)

            if not ((lst.has_next() and
                    curr_obj_name[0:len(this_obj_name)] == this_obj_name)):
                break
            curr_obj_name = lst.next()

        s = s + "---------------------------------------------------------\n"

        return s



    def convert2string(self):
        return self.m_display_objections(self.m_top,1)

    #
    #  // Function: display_objections
    #  //
    #  // Displays objection information about the given ~object~. If ~object~ is
    #  // not specified or ~null~, the implicit top-level component, <uvm_root>, is
    #  // chosen. The ~show_header~ argument allows control of whether a header is
    #  // output.
    def display_objections(self, obj=None, show_header=1):
        m = self.m_display_objections(obj,show_header)
        uvm_info("UVM/OBJ/DISPLAY", m, UVM_NONE)

    #
    #  // Below is all of the basic data stuff that is needed for a uvm_object
    #  // for factory registration, printing, comparing, etc.
    #
    #  typedef uvm_object_registry#(uvm_objection,"uvm_objection") type_id
    #  static function type_id get_type()
    #    return type_id::get()
    #  endfunction
    #
    #  function uvm_object create (string name="")
    #    uvm_objection tmp = new(name)
    #    return tmp
    #  endfunction
    #
    #  virtual function string get_type_name ()
    #    return "uvm_objection"
    #  endfunction

    def do_copy(self, rhs):
        _rhs = rhs
        # $cast(_rhs, rhs)
        self.m_source_count = _rhs.m_source_count
        self.m_total_count  = _rhs.m_total_count
        self.m_drain_time   = _rhs.m_drain_time
        self.m_prop_mode    = _rhs.self.m_prop_mode


#// TODO: change to plusarg
#//`define UVM_DEFAULT_TIMEOUT 9200s

#//------------------------------------------------------------------------------
#//
#// Class- uvm_test_done_objection DEPRECATED
#//
#// Provides built-in end-of-test coordination
#//------------------------------------------------------------------------------

#class uvm_test_done_objection extends uvm_objection
    #
    #   protected static uvm_test_done_objection m_inst
    #  protected bit m_forced
    #
    #  // For communicating all objections dropped and end of phasing
    #  local  bit m_executing_stop_processes
    #  local  int m_n_stop_threads
    #
    #
    #  // Function- new DEPRECATED
    #  //
    #  // Creates the singleton test_done objection. Users must not call
    #  // this method directly.
    #
    #  function new(string name="uvm_test_done")
    #    super.new(name)
    #  endfunction
    #
    #
    #  // Function- qualify DEPRECATED
    #  //
    #  // Checks that the given ~object~ is derived from either <uvm_component> or
    #  // <uvm_sequence_base>.
    #
    #  virtual function void qualify(uvm_object obj=null,
    #                                bit is_raise,
    #                                string description)
    #    uvm_component c
    #    uvm_sequence_base s
    #    string nm = is_raise ? "raise_objection" : "drop_objection"
    #    string desc = description == "" ? "" : {" (\"", description, "\")"}
    #    if(! ($cast(c,obj) || $cast(s,obj))) begin
    #      uvm_report_error("TEST_DONE_NOHIER", {"A non-hierarchical object, '",
    #        obj.get_full_name(), "' (", obj.get_type_name(),") was used in a call ",
    #        "to uvm_test_done.", nm,"(). For this objection, a sequence ",
    #        "or component is required.", desc })
    #    end
    #  endfunction
    #
    #  // Below are basic data operations needed for all uvm_objects
    #  // for factory registration, printing, comparing, etc.
    #
    #  typedef uvm_object_registry#(uvm_test_done_objection,"uvm_test_done") type_id
    #  static function type_id get_type()
    #    return type_id::get()
    #  endfunction
    #
    #  function uvm_object create (string name="")
    #    uvm_test_done_objection tmp = new(name)
    #    return tmp
    #  endfunction
    #
    #  virtual function string get_type_name ()
    #    return "uvm_test_done"
    #  endfunction
    #
    #  static function uvm_test_done_objection get()
    #    if(m_inst == null)
    #      m_inst = uvm_test_done_objection::type_id::create("run")
    #    return m_inst
    #  endfunction
    #
    #endclass

#// Have a pool of context objects to use
#class uvm_objection_context_object
class UVMObjectionContextObject:

    def __init__(self):
        """
           uvm_object obj
           uvm_object source_obj
           string description
           int    count
           uvm_objection objection
        """
        self.obj = None
        self.source_obj = None
        self.description = ""
        self.count = 0
        #self.objection: Optional[UVMObjection] = None
        self.objection = UVMObjection()

    def clear(self):
        """
        Clears the values stored within the object,
        preventing memory leaks from reused objects
        """
        self.obj = None
        self.source_obj = None
        self.description = ""
        self.count = 0
        self.objection = UVMObjection()


#// Typedef - Exists for backwards compat
#typedef uvm_objection uvm_callbacks_objection




#`endif
#
