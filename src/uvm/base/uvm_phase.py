#
#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010-2013 Synopsys, Inc.
#   Copyright 2013      NVIDIA Corporation
#   Copyright 2013      Cisco Systems, Inc.
#   Copyright 2019      Tuomas Poikela
#
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
#
#   python-uvm NOTE: All code ported from SystemVerilog UVM 1.2 to
#   python. Original code structures (including comments)
#   preserved where possible.
#----------------------------------------------------------------------

from typing import Dict, List
import cocotb
from cocotb.triggers import Event, Combine

from ..macros.uvm_object_defines import uvm_object_utils
from ..macros.uvm_message_defines import uvm_fatal, uvm_info
from ..macros.uvm_callback_defines import uvm_do_callbacks
from .uvm_callback import UVMCallback
from .uvm_cmdline_processor import UVMCmdlineProcessor
from .uvm_debug import uvm_debug
from .uvm_globals import (get_cs, uvm_report_error, uvm_report_info,
        uvm_wait_for_nba_region, uvm_zero_delay)
from .uvm_mailbox import UVMMailbox
from .uvm_object import UVMObject
from .uvm_object_globals import (UVM_ALL_DROPPED, UVM_DEBUG, UVM_EQ, UVM_GT, UVM_GTE, UVM_HIGH,
                                 UVM_LOW, UVM_LT, UVM_LTE, UVM_MEDIUM, UVM_NE, UVM_PHASE2STR,
                                 UVM_PHASE_CLEANUP, UVM_PHASE_DOMAIN, UVM_PHASE_DONE,
                                 UVM_PHASE_DORMANT, UVM_PHASE_ENDED, UVM_PHASE_EXECUTING,
                                 UVM_PHASE_IMP, UVM_PHASE_JUMPING, UVM_PHASE_NODE,
                                 UVM_PHASE_READY_TO_END, UVM_PHASE_SCHEDULE, UVM_PHASE_SCHEDULED,
                                 UVM_PHASE_STARTED, UVM_PHASE_SYNCING, UVM_PHASE_TERMINAL,
                                 UVM_PHASE_UNINITIALIZED)
from .uvm_objection import UVMObjection
from .sv import sv

def UVM_PH_TRACE(ID,MSG,PH,VERB):
    uvm_info(ID, (sv.sformatf("Phase '%0s' (id=%0d) ", PH.get_full_name(),
        PH.get_inst_id()) + MSG), UVM_LOW)


def ph2str(state) -> str:
    if state is not None:
        return UVM_PHASE2STR[state]
    return "<State: NONE>"


#async def my_combine(events):
#    pproc = []
#    for e in events:
#        e.clear()
#
#        async def my_task(ee):
#            await ee.wait()
#        my_fork  = cocotb.fork(my_task(e))
#        pproc.append(my_fork)
#    for pp in pproc:
#        # Crashes after this call
#        await pp.join()

#------------------------------------------------------------------------------
#
# Section: Phasing Definition classes
#
#------------------------------------------------------------------------------
#
# The following class are used to specify a phase and its implied functionality.
#


#------------------------------------------------------------------------------
#
# Class: uvm_phase_state_change
#
#------------------------------------------------------------------------------
# Phase state transition descriptor.
# Used to describe the phase transition that caused a
# <uvm_phase_cb::phase_state_changed()> callback to be invoked.

class UVMPhaseStateChange(UVMObject):

    def __init__(self, name="uvm_phase_state_change"):
        UVMObject.__init__(self, name)
        # Implementation -- do not use directly
        self.m_phase = None
        self.m_prev_state = None
        self.m_jump_to = None

    def get_state(self):
        """
        Returns the state the phase just transitioned to.
        Functionally equivalent to <uvm_phase::get_state()>.

        Returns:
        """
        return self.m_phase.get_state()

    def get_prev_state(self):
        """
        Returns the state the phase just transitioned from.

        Returns:
        """
        return self.m_prev_state

    def jump_to(self):
        """
        If the current state is `UVM_PHASE_ENDED` or `UVM_PHASE_JUMPING` because of
        a phase jump, returns the phase that is the target of jump.
        Returns `None` otherwise.

        Returns:
        """
        return self.m_jump_to


uvm_object_utils(UVMPhaseStateChange)


class UVMPhase(UVMObject):
    """
    Class: uvm_phase



    This base class defines everything about a phase: behavior, state, and context.

    To define behavior, it is extended by UVM or the user to create singleton
    objects which capture the definition of what the phase does and how it does it.
    These are then cloned to produce multiple nodes which are hooked up in a graph
    structure to provide context: which phases follow which, and to hold the state
    of the phase throughout its lifetime.
    UVM provides default extensions of this class for the standard runtime phases.
    VIP Providers can likewise extend this class to define the phase functor for a
    particular component context as required.

    This base class defines everything about a phase: behavior, state, and context.

    To define behavior, it is extended by UVM or the user to create singleton
    objects which capture the definition of what the phase does and how it does it.
    These are then cloned to produce multiple nodes which are hooked up in a graph
    structure to provide context: which phases follow which, and to hold the state
    of the phase throughout its lifetime.
    UVM provides default extensions of this class for the standard runtime phases.
    VIP Providers can likewise extend this class to define the phase functor for a
    particular component context as required.

    *Phase Definition*

    Singleton instances of those extensions are provided as package variables.
    These instances define the attributes of the phase (not what state it is in)
    They are then cloned into schedule nodes which point back to one of these
    implementations, and calls its virtual task or function methods on each
    participating component.
    It is the base class for phase functors, for both predefined and
    user-defined phases. Per-component overrides can use a customized imp.

    To create custom phases, do not extend uvm_phase directly: see the
    three predefined extended classes below which encapsulate behavior for
    different phase types: task, bottom-up function and top-down function.

    Extend the appropriate one of these to create a uvm_YOURNAME_phase class
    (or YOURPREFIX_NAME_phase class) for each phase, containing the default
    implementation of the new phase, which must be a uvm_component-compatible
    delegate, and which may be a ~null~ implementation. Instantiate a singleton
    instance of that class for your code to use when a phase handle is required.
    If your custom phase depends on methods that are not in uvm_component, but
    are within an extended class, then extend the base YOURPREFIX_NAME_phase
    class with parameterized component class context as required, to create a
    specialized functor which calls your extended component class methods.
    This scheme ensures compile-safety for your extended component classes while
    providing homogeneous base types for APIs and underlying data structures.

    *Phase Context*

    A schedule is a coherent group of one or mode phase/state nodes linked
    together by a graph structure, allowing arbitrary linear/parallel
    relationships to be specified, and executed by stepping through them in
    the graph order.
    Each schedule node points to a phase and holds the execution state of that
    phase, and has optional links to other nodes for synchronization.

    The main operations are: construct, add phases, and instantiate
    hierarchically within another schedule.

    Structure is a DAG (Directed Acyclic Graph). Each instance is a node
    connected to others to form the graph. Hierarchy is overlaid with m_parent.
    Each node in the graph has zero or more successors, and zero or more
    predecessors. No nodes are completely isolated from others. Exactly
    one node has zero predecessors. This is the root node. Also the graph
    is acyclic, meaning for all nodes in the graph, by following the forward
    arrows you will never end up back where you started but you will eventually
    reach a node that has no successors.

    *Phase State*

    A given phase may appear multiple times in the complete phase graph, due
    to the multiple independent domain feature, and the ability for different
    VIP to customize their own phase schedules perhaps reusing existing phases.
    Each node instance in the graph maintains its own state of execution.

    *Phase Handle*

    Handles of this type uvm_phase are used frequently in the API, both by
    the user, to access phasing-specific API, and also as a parameter to some
    APIs. In many cases, the singleton phase handles can be
    used (eg. <uvm_run_phase::get()>) in APIs. For those APIs that need to look
    up that phase in the graph, this is done automatically.
    """
    m_phase_trace = False
    m_use_ovm_run_semantic = False
    m_phase_hopper = UVMMailbox()
    m_executing_phases: Dict['UVMPhase', bool] = {}  # UVMPhase -> bool

    #--------------------
    # Group: Construction
    #--------------------

    # Function: new
    #
    # Create a new phase node, with a name and a note of its type
    #   name   - name of this phase
    #   type   - a value in <uvm_phase_type>
    #
    def __init__(self, name="uvm_phase", phase_type=UVM_PHASE_SCHEDULE, parent=None):
        UVMObject.__init__(self, name)
        self.m_phase_type = phase_type
        self.m_state = UVM_PHASE_UNINITIALIZED

        self.m_ready_to_end_count = 0
        self.max_ready_to_end_iter = 20
        self.m_successors: Dict['UVMPhase', bool] = {}  # UVMPhase -> bit
        self.m_predecessors: Dict['UVMPhase', bool] = {}  # UVMPhase -> bit
        self.m_end_node = None
        self.m_sync: List['UVMPhase'] = []  # UVMPhase
        self.m_imp = None  # UVMPhase to call when we execute this node
        self.m_phase_done_event = Event(name + '_phase_done_event')
        self.m_phase_synced_event = Event(name + '_phase_synced')
        self.m_phase_set_state_event = Event(name + '_set_state_event')
        self.phase_done = None  # uvm_objection

        self.m_phase_proc = None  # TODO process
        self.m_num_procs_not_yet_returned = 0

        self.m_is_task_phase = False

        # Implementation - Jumping
        self.m_jump_bkwd = False
        self.m_jump_fwd = False
        self.m_jump_phase = None
        self.m_premature_end = False

        # The common domain is the only thing that initializes self.m_state.  All
        # other states are initialized by being 'added' to a schedule.
        if (name == "common") and (phase_type == UVM_PHASE_DOMAIN):
            self.set_state(UVM_PHASE_DORMANT)

        self.m_run_count = 0
        self.m_parent = parent

        clp = UVMCmdlineProcessor.get_inst()

        val = []
        if clp.get_arg_value("+UVM_PHASE_TRACE", val):
            UVMPhase.m_phase_trace = 1
        else:
            UVMPhase.m_phase_trace = 0
        val = []
        if clp.get_arg_value("+UVM_USE_OVM_RUN_SEMANTIC", val):
            UVMPhase.m_use_ovm_run_semantic = 1
        else:
            UVMPhase.m_use_ovm_run_semantic = 0

        if parent is None and (phase_type == UVM_PHASE_SCHEDULE or
                  phase_type == UVM_PHASE_DOMAIN):
            #self.m_parent = self
            self.m_end_node = UVMPhase(name + ' end', UVM_PHASE_TERMINAL, self)
            self.m_successors[self.m_end_node] = True
            self.m_end_node.m_predecessors[self] = True

    # tpoikela: Used instead of $cast() to check phase type
    def is_task_phase(self):
        return self.m_is_task_phase

    # Function: get_phase_type
    # Returns the phase type as defined by <uvm_phase_type>
    def get_phase_type(self):
        return self.m_phase_type

    def get_phase_done_event(self):
        return self.m_phase_done_event

    def get_phase_synced_event(self):
        return self.m_phase_synced_event


    def set_state(self, state):
        if state is None:
            raise Exception('Proper state not given. Must be ' + str(UVM_PHASE2STR))
        uvm_debug(self, 'set_state', (self.get_name() + ': ' +
                ph2str(self.m_state) + ' => ' + ph2str(state)))
        self.m_state = state
        self.m_phase_set_state_event.set()
        if self.m_state == UVM_PHASE_DONE:
            self.m_phase_done_event.set()
        if self.m_state >= UVM_PHASE_SYNCING:
            self.m_phase_synced_event.set()


    #  //-------------
    #  // Group: State
    #  //-------------
    #
    # Function: get_state
    # Accessor to return current state of this phase
    def get_state(self):
        return self.m_state

    #  // Function: get_run_count
    #  //
    #  // Accessor to return the integer number of times this phase has executed
    #  //
    def get_run_count(self):
        return self.m_run_count


    #  // Function: find_by_name
    #  //
    #  // Locate a phase node with the specified ~name~ and return its handle.
    #  // With ~stay_in_scope~ set, searches only within this phase's schedule or
    #  // domain.
    #  //
    #  extern function uvm_phase find_by_name(string name, bit stay_in_scope=1)
    def find_by_name(self, name: str, stay_in_scope=1):
        # TODO: full search
        if self.get_name() == name:
            return self
        find_by_name = self.m_find_predecessor_by_name(name,stay_in_scope,self)
        if find_by_name is None:
            find_by_name = self.m_find_successor_by_name(name,stay_in_scope,self)
        return find_by_name

    #  Function: find
    #
    #  Locate the phase node with the specified ~phase~ IMP and return its handle.
    #  With ~stay_in_scope~ set, searches only within this phase's schedule or
    #  domain.
    #
    def find(self, phase, stay_in_scope=True):
        uvm_debug(self, "find()", "called with self as {}, phase {}".format(self, phase))
        if phase is None:
            raise Exception('UVMPhase.find(): Phase is None')
        # TBD full search
        # in_scope = stay_in_scope ? " staying within scope" : ""
        # print(("\nFIND node '" + phase.get_name() +"' within " + get_name()
        #+ " (scope " + self.m_phase_type.name() +")" + in_scope))
        found = None
        if phase == self.m_imp or phase == self:
            return phase

        found = self.m_find_predecessor(phase, stay_in_scope, self)
        if found is None:
            found = self.m_find_successor(phase, stay_in_scope, self)
        return found

    # Function: is
    #
    # returns 1 if the containing uvm_phase refers to the same phase
    # as the phase argument, 0 otherwise
    #
    #  extern function bit is(uvm_phase phase)
    def _is(self, phase):
        return (self.m_imp == phase or self == phase)

    # Function: is_before
    #
    # Returns 1 if the containing uvm_phase refers to a phase that is earlier
    # than the phase argument, 0 otherwise
    #
    def is_before(self, phase):
        # $display("this=%s is before phase=%s?",get_name(),phase.get_name())
        #  TODO: add support for 'stay_in_scope=1' functionality
        return not self._is(phase) and self.m_find_successor(phase,0,self) is not None

    # Function: is_after
    #
    # returns 1 if the containing uvm_phase refers to a phase that is later
    # than the phase argument, 0 otherwise
    #
    def is_after(self, phase):
        #  //$display("this=%s is after phase=%s?",get_name(),phase.get_name())
        #  // TODO: add support for 'stay_in_scope=1' functionality
        return not self._is(phase) and self.m_find_predecessor(phase,0,self) is not None

    #-----------------
    # Group: Callbacks
    #-----------------
    #
    # Function: exec_func
    #
    # Implements the functor/delegate functionality for a function phase type
    #   comp  - the component to execute the functionality upon
    #   phase - the phase schedule that originated this phase call
    #
    def exec_func(self, comp, phase):
        raise Exception('virtual function')

    # Function: exec_task
    #
    # Implements the functor/delegate functionality for a task phase type
    #   comp  - the component to execute the functionality upon
    #   phase - the phase schedule that originated this phase call
    #
    #  virtual task exec_task(uvm_component comp, uvm_phase phase); endtask

    #----------------
    # Group: Schedule
    #----------------
    #
    # Function: add
    #
    # Build up a schedule structure inserting phase by phase, specifying linkage
    #
    # Phases can be added anywhere, in series or parallel with existing nodes
    #
    #   phase        - handle of singleton derived imp containing actual functor.
    #                  by default the new phase is appended to the schedule
    #   with_phase   - specify to add the new phase in parallel with this one
    #   after_phase  - specify to add the new phase as successor to this one
    #   before_phase - specify to add the new phase as predecessor to this one
    #
    def add(self, phase, with_phase=None, after_phase=None, before_phase=None):
        new_node = None
        begin_node = None
        end_node = None
        tmp_node = None
        state_chg = None
        if phase is None:
            uvm_fatal("PH/NULL", "add: phase argument is null")

        if with_phase is not None and with_phase.get_phase_type() == UVM_PHASE_IMP:
            nm = with_phase.get_name()
            with_phase = self.find(with_phase)
            if with_phase is None:
                uvm_fatal("PH_BAD_ADD", ("cannot find with_phase '" + nm
                    + "' within node '" + self.get_name() + "'"))

        if before_phase is not None and before_phase.get_phase_type() == UVM_PHASE_IMP:
            nm = before_phase.get_name()
            before_phase = self.find(before_phase)
            if before_phase is None:
                uvm_fatal("PH_BAD_ADD", ("cannot find before_phase '" + nm
                  + "' within node '" + self.get_name() + "'"))

        if after_phase is not None and after_phase.get_phase_type() == UVM_PHASE_IMP:
            nm = after_phase.get_name()
            after_phase = self.find(after_phase)
            if after_phase is None:
                uvm_fatal("PH_BAD_ADD",("cannot find after_phase '" + nm
                  + "' within node '" + self.get_name() + "'"))

        if with_phase is not None and (after_phase is not None or before_phase
                is not None):
            uvm_fatal("PH_BAD_ADD",
                    "cannot specify both 'with' and 'before/after' phase relationships")

        if before_phase == self or after_phase == self.m_end_node or with_phase == self.m_end_node:
            uvm_fatal("PH_BAD_ADD",
                    "cannot add before begin node, after end node, or with end nodes")

        # If we are inserting a new "leaf node"
        if phase.get_phase_type() == UVM_PHASE_IMP:
            uvm_debug(self, 'add', 'ph_type == UVM_PHASE_IMP ph_name: ' +
                    phase.get_name())
            new_node = UVMPhase(phase.get_name(),UVM_PHASE_NODE,self)
            new_node.m_imp = phase
            begin_node = new_node
            end_node = new_node

            # The phase_done objection is only required
            # for task-based nodes
            #if ($cast(tp, phase)) begin
            if phase.is_task_phase():
                #if new_node.get_name() == "run":
                #    DEPRECATED
                #    new_node.phase_done = uvm_test_done_objection.get()
                #else: # Other task based phase
                uvm_debug(self, 'add', ("Adding objection to phase " +
                    phase.get_name()))
                new_node.phase_done = UVMObjection(phase.get_name() + "_objection")
            else:
                uvm_debug(self, 'add', (phase.get_name() +
                    " is not task-based phase, so no objections"))
        else:  # We are inserting an existing schedule
            uvm_debug(self, "add", "We are inserting an existing schedule")
            begin_node = phase
            end_node   = phase.m_end_node
            phase.m_parent = self

        # If no before/after/with specified, insert at end of this schedule
        if (with_phase is None) and (after_phase is None) and (before_phase is
                None):
            uvm_debug(self, 'add', 'All phases null, setting before phase')
            before_phase = self.m_end_node

        if UVMPhase.m_phase_trace:
            typ = phase.get_phase_type()
            uvm_report_info("PH/TRC/ADD_PH", (self.get_name() + " (" + self.m_phase_type.name()
                + ") ADD_PHASE: phase=" + phase.get_full_name() + " ("
                + typ.name() + ", inst_id=" + "{}".format(phase.get_inst_id())
                + ")"), UVM_DEBUG)
            #" with_phase=",   (with_phase == null)   ? "null" : with_phase.get_name(),
            #" after_phase=",  (after_phase == null)  ? "null" : after_phase.get_name(),
            #" before_phase=", (before_phase == null) ? "null" : before_phase.get_name(),
            #" new_node=",     (new_node == null)     ? "null" : {new_node.get_name(),
            #                                                     " inst_id=",
            #                                                     $sformatf("%0d",new_node.get_inst_id())},
            #" begin_node=",   (begin_node == null)   ? "null" : begin_node.get_name(),
            #" end_node=",     (end_node == null)     ? "null" : end_node.get_name()},UVM_DEBUG)


        # INSERT IN PARALLEL WITH 'WITH' PHASE
        if with_phase is not None:
            begin_node.m_predecessors = with_phase.m_predecessors
            end_node.m_successors = with_phase.m_successors
            for pred in with_phase.m_predecessors:
                pred.m_successors[begin_node] = 1
            for succ in with_phase.m_successors:
                succ.m_predecessors[end_node] = 1
        # INSERT BEFORE PHASE
        elif before_phase is not None and after_phase is None:
            begin_node.m_predecessors = before_phase.m_predecessors
            end_node.m_successors[before_phase] = 1
            for pred in before_phase.m_predecessors:
                del pred.m_successors[before_phase]
                pred.m_successors[begin_node] = 1
            before_phase.m_predecessors = {}
            before_phase.m_predecessors[end_node] = 1
        # INSERT AFTER PHASE
        elif before_phase is None and after_phase is not None:
            end_node.m_successors = after_phase.m_successors
            begin_node.m_predecessors[after_phase] = 1
            for succ in after_phase.m_successors:
                del succ.m_predecessors[after_phase]
                succ.m_predecessors[end_node] = 1
            after_phase.m_successors = {}
            after_phase.m_successors[begin_node] = 1
        # IN BETWEEN 'BEFORE' and 'AFTER' PHASES
        elif before_phase is not None and after_phase is not None:
            if not after_phase.is_before(before_phase):
                uvm_fatal("PH_ADD_PHASE", ("Phase '" + before_phase.get_name()
                         + "' is not before phase '" + after_phase.get_name() + "'"))
            # before and after? add 1 pred and 1 succ
            begin_node.m_predecessors[after_phase] = 1
            end_node.m_successors[before_phase] = 1
            after_phase.m_successors[begin_node] = 1
            before_phase.m_predecessors[end_node] = 1
            if before_phase in after_phase.m_successors:
                del after_phase.m_successors[before_phase]
                del before_phase.m_successors[after_phase]

        # Transition nodes to DORMANT state
        if new_node is None:
            tmp_node = phase
        else:
            tmp_node = new_node
        uvm_debug(self, "add", "GOT here. tmp_node is: " + tmp_node.convert2string())
        state_chg = UVMPhaseStateChange.type_id.create(tmp_node.get_name())
        state_chg.m_phase = tmp_node
        state_chg.m_jump_to = None
        state_chg.m_prev_state = tmp_node.m_state
        tmp_node.m_state = UVM_PHASE_DORMANT
        uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', tmp_node, state_chg)

    #  // Function: get_parent
    #  //
    #  // Returns the parent schedule node, if any, for hierarchical graph traversal
    #  //
    def get_parent(self):
        return self.m_parent

    #   Function: get_full_name
    #   Returns the full path from the enclosing domain down to this node.
    #   The singleton IMP phases have no hierarchy.
    #
    def get_full_name(self):
        if self.m_phase_type == UVM_PHASE_IMP:
            return self.get_name()
        get_full_name = self.get_domain_name()
        sch = self.get_schedule_name()
        if sch != "":
            get_full_name = get_full_name + "." + sch
        if self.m_phase_type != UVM_PHASE_DOMAIN and self.m_phase_type != UVM_PHASE_SCHEDULE:
            get_full_name = get_full_name + "." + self.get_name()
        return get_full_name

    # Function: get_schedule
    #
    #  Returns the topmost parent schedule node, if any, for hierarchical graph traversal
    #
    def get_schedule(self, hier=False):
        sched = self
        if hier is True:
            while (sched.m_parent is not None and (sched.m_parent.get_phase_type()
                    == UVM_PHASE_SCHEDULE)):
                sched = sched.m_parent
        if sched.m_phase_type == UVM_PHASE_SCHEDULE:
            return sched
        if sched.m_phase_type == UVM_PHASE_NODE:
            if (self.m_parent is not None and self.m_parent.m_phase_type !=
                    UVM_PHASE_DOMAIN):
                return self.m_parent
        return None

    #  // Function: get_schedule_name
    #  //
    #  // Returns the schedule name associated with this phase node
    #  //
    #
    def get_schedule_name(self, hier=False):
        #uvm_phase sched
        s = ""
        sched = self.get_schedule(hier)
        if sched is None:
            return ""
        s = sched.get_name()
        while (sched.m_parent is not None and sched.m_parent != sched and
                (sched.m_parent.get_phase_type() == UVM_PHASE_SCHEDULE)):
            sched = sched.m_parent
            sep = ""
            if len(s) > 0:
                sep = "."
            s = sched.get_name() + sep + s
        return s

    # Function: get_domain
    # Returns the enclosing domain
    #
    def get_domain(self):
        phase = self
        while (phase is not None) and (phase.m_phase_type != UVM_PHASE_DOMAIN):
          phase = phase.m_parent
        if phase is None:
            return None
        return phase
    #   if(!$cast(get_domain,phase))
    #       `uvm_fatal("PH/INTERNAL", "get_domain: self.m_phase_type is DOMAIN but $cast to uvm_domain fails")
    #
    #  // Function: get_imp
    #  //
    #  // Returns the phase implementation for this this node.
    #  // Returns ~null~ if this phase type is not a UVM_PHASE_LEAF_NODE.
    #  //
    #  extern function uvm_phase get_imp()
    #

    #  // Function: get_domain_name
    #  //
    #  // Returns the domain name associated with this phase node
    #  //
    #  extern function string get_domain_name()
    def get_domain_name(self):
        domain = self.get_domain()
        if domain is None:
            return "unknown"
        return domain.get_name()

    #  // Function: get_adjacent_predecessor_nodes
    #  //
    #  // Provides an array of nodes which are predecessors to
    #  // ~this~ phase node.  A 'predecessor node' is defined
    #  // as any phase node which lies prior to ~this~ node in
    #  // the phase graph, with no nodes between ~this~ node and
    #  // the predecessor node.
    #  //
    #  extern function void get_adjacent_predecessor_nodes(ref uvm_phase pred[])
    #

    #  // Function: get_adjacent_successor_nodes
    #  //
    #  // Provides an array of nodes which are successors to
    #  // ~this~ phase node.  A 'successor's node' is defined
    #  // as any phase node which comes after ~this~ node in
    #  // the phase graph, with no nodes between ~this~ node
    #  // and the successor node.
    #  //
    #function void uvm_phase::get_adjacent_successor_nodes(ref uvm_phase succ[])
    def get_adjacent_successor_nodes(self):
        done = False
        successors = {}  #bit successors[uvm_phase]
        idx = 0

        # Get all successors (including TERMINALS, SCHEDULES, etc.)
        for s in self.m_successors:
            successors[s] = 1

        # Replace any terminal / schedule nodes with their successors, recursively.
        #do begin
        #   done = 1
        #   foreach (successors[s]) begin
        #      if (s.get_phase_type() != UVM_PHASE_NODE) begin
        #         successors.delete(s)
        #         foreach (s.m_successors[next_s])
        #           successors[next_s] = 1
        #         done = 0
        #      end
        #   end
        #end while (!done)
        done = False
        while (True):
            done = True
            keys = list(successors.keys())
            for s in keys:
                if s.get_phase_type() != UVM_PHASE_NODE:
                    del successors[s]
                    for next_s in s.m_successors:
                        successors[next_s] = 1
                    done = False
            if done:
                break

        succ = []
        for s in successors:
            succ.append(s)
        return succ
    #endfunction : get_adjacent_successor_nodes

    #  //-----------------------
    #  // Group: Phase Done Objection
    #  //-----------------------
    #  //
    #  // Task-based phase nodes within the phasing graph provide a <uvm_objection>
    #  // based interface for prolonging the execution of the phase.  All other
    #  // phase types do not contain an objection, and will report a fatal error
    #  // if the user attempts to ~raise~, ~drop~, or ~get_objection_count~.
    #
    #  // Function- m_report_null_objection
    #  // Simplifies the reporting of ~null~ objection errors
    def m_report_null_objection(self, obj, description, count, action):
        m_action = ""
        m_addon = ""
        m_obj_name = "uvm_top"
        if obj is not None:
            m_obj_name = obj.get_full_name()

        if action == "raise" or action == "drop":
            if count != 1:
                m_action = "{} {} objections".format(action, count)
            else:
                m_action = "{} an objection".format(action)
        elif action == "get_objection_count":
            m_action = "call get_objection_count"

        if self.get_phase_type() == UVM_PHASE_IMP:
             m_addon = (" (This is a UVM_PHASE_IMP, you have to query the "
                     + "schedule to find the UVM_PHASE_NODE)")
        uvm_report_error("UVM/PH/NULL_OBJECTION", (
            "'{}' attempted to {} on '{}', however '{}' is not a task-based phase node! {}".format(
            m_obj_name, m_action, self.get_name(), self.get_name(), m_addon)))


    #  // Function: get_objection
    #  //
    #  // Return the <uvm_objection> that gates the termination of the phase.
    #  //
    def get_objection(self):
        return self.phase_done


    #  // Function: raise_objection
    #  //
    #  // Raise an objection to ending this phase
    #  // Provides components with greater control over the phase flow for
    #  // processes which are not implicit objectors to the phase.
    #  //
    #  //|   while(1) begin
    #  //|     some_phase.raise_objection(this)
    #  //|     ...
    #  //|     some_phase.drop_objection(this)
    #  //|   end
    #  //|   ...
    #  //
    def raise_objection(self, obj, description="", count=1):
        if self.phase_done is not None:
            if obj is not None:
                uvm_debug(self, 'raise_objection', 'obj: {}'.format(obj.get_name()))
            self.phase_done.raise_objection(obj, description, count)
        else:
            self.m_report_null_objection(obj, description, count, "raise")

    #
    #  // Function: drop_objection
    #  //
    #  // Drop an objection to ending this phase
    #  //
    #  // The drop is expected to be matched with an earlier raise.
    #  //
    def drop_objection(self, obj, description="", count=1):
        if self.get_name() == 'reset':
            print("EEE object dropping reset obj now " + obj.get_name())
        if self.phase_done is not None:
            if self.get_name() == 'reset':
                print("Dropping reset objection\n" +
                        self.phase_done.convert2string())
            self.phase_done.drop_objection(obj,description,count)
        else:
            self.m_report_null_objection(obj, description, count, "drop")

    #
    #  // Function: get_objection_count
    #  //
    #  // Returns the current number of objections to ending this phase raised by the given ~object~.
    #  //
    #  extern virtual function int get_objection_count( uvm_object obj=null )
    #
    #  //-----------------------
    #  // Group: Synchronization
    #  //-----------------------
    #  // The functions 'sync' and 'unsync' add soft sync relationships between nodes
    #  //
    #  // Summary of usage:
    #  //| my_phase.sync(.target(domain)
    #  //|              [,.phase(phase)[,.with_phase(phase)]])
    #  //| my_phase.unsync(.target(domain)
    #  //|                [,.phase(phase)[,.with_phase(phase)]])
    #  //
    #  // Components in different schedule domains can be phased independently or in sync
    #  // with each other. An API is provided to specify synchronization rules between any
    #  // two domains. Synchronization can be done at any of three levels:
    #  //
    #  // - the domain's whole phase schedule can be synchronized
    #  // - a phase can be specified, to sync that phase with a matching counterpart
    #  // - or a more detailed arbitrary synchronization between any two phases
    #  //
    #  // Each kind of synchronization causes the same underlying data structures to
    #  // be managed. Like other APIs, we use the parameter dot-notation to set
    #  // optional parameters.
    #  //
    #  // When a domain is synced with another domain, all of the matching phases in
    #  // the two domains get a 'with' relationship between them. Likewise, if a domain
    #  // is unsynched, all of the matching phases that have a 'with' relationship have
    #  // the dependency removed. It is possible to sync two domains and then just
    #  // remove a single phase from the dependency relationship by unsyncing just
    #  // the one phase.
    #
    #
    #  // Function: sync
    #  //
    #  // Synchronize two domains, fully or partially
    #  //
    #  //   target       - handle of target domain to synchronize this one to
    #  //   phase        - optional single phase in this domain to synchronize,
    #  //                  otherwise sync all
    #  //   with_phase   - optional different target-domain phase to synchronize with,
    #  //                  otherwise use ~phase~ in the target domain
    #  //
    #  extern function void sync(uvm_domain target,
    #                            uvm_phase phase=null,
    #                            uvm_phase with_phase=null)
    #
    #  // Function: unsync
    #  //
    #  // Remove synchronization between two domains, fully or partially
    #  //
    #  //   target       - handle of target domain to remove synchronization from
    #  //   phase        - optional single phase in this domain to un-synchronize,
    #  //                  otherwise unsync all
    #  //   with_phase   - optional different target-domain phase to un-synchronize with,
    #  //                  otherwise use ~phase~ in the target domain
    #  //
    #  extern function void unsync(uvm_domain target,
    #                              uvm_phase phase=null,
    #                              uvm_phase with_phase=null)
    #
    #
    #  // Function: wait_for_state
    #  //
    #  // Wait until this phase compares with the given ~state~ and ~op~ operand.
    #  // For <UVM_EQ> and <UVM_NE> operands, several <!-- <uvm_phase_states> --> can be
    #  // supplied by ORing their enum constants, in which case the caller will
    #  // wait until the phase state is any of (UVM_EQ) or none of (UVM_NE) the
    #  // provided states.
    #  //
    #  // To wait for the phase to be at the started state or after
    #  //
    #  //| wait_for_state(UVM_PHASE_STARTED, UVM_GTE)
    #  //
    #  // To wait for the phase to be either started or executing
    #  //
    #  //| wait_for_state(UVM_PHASE_STARTED | UVM_PHASE_EXECUTING, UVM_EQ)
    #  //
    #  extern task wait_for_state(uvm_phase_state state, uvm_wait_op op=UVM_EQ)

    async def wait_for_state(self, state, op=UVM_EQ):
        func = None
        if op == UVM_EQ:
            def func():
                return state & self.m_state != 0
        elif op == UVM_NE:
            def func():
                return ((state & self.m_state) == 0)
        elif op == UVM_GTE:
            def func():
                return self.m_state >= state
        elif op == UVM_LT:
            def func():
                return self.m_state < state
        elif op == UVM_LTE:
            def func():
                return self.m_state <= state
        elif op == UVM_GT:
            def func():
                return self.m_state > state
        else:
            raise Exception('IMPL for wait_for_state not finished yet')
        await self._wait_state_change_func(func)


    async def _wait_state_change_func(self, func):
        while True:
            await self.m_phase_set_state_event.wait()
            self.m_phase_set_state_event.clear()
            if func():
                break

    #
    #
    #  //---------------
    #  // Group: Jumping
    #  //---------------
    #
    #  // Force phases to jump forward or backward in a schedule
    #  //
    #  // A phasing domain can execute a jump from its current phase to any other.
    #  // A jump passes phasing control in the current domain from the current phase
    #  // to a target phase. There are two kinds of jump scope:
    #  //
    #  // - local jump to another phase within the current schedule, back- or forwards
    #  // - global jump of all domains together, either to a point in the master
    #  //   schedule outwith the current schedule, or by calling jump_all()
    #  //
    #  // A jump preserves the existing soft synchronization, so the domain that is
    #  // ahead of schedule relative to another synchronized domain, as a result of
    #  // a jump in either domain, will await the domain that is behind schedule.
    #  //
    #  // *Note*: A jump out of the local schedule causes other schedules that have
    #  // the jump node in their schedule to jump as well. In some cases, it is
    #  // desirable to jump to a local phase in the schedule but to have all
    #  // schedules that share that phase to jump as well. In that situation, the
    #  // jump_all static function should be used. This function causes all schedules
    #  // that share a phase to jump to that phase.

    #  // Function: jump
    #  //
    #  // Jump to a specified ~phase~. If the destination ~phase~ is within the current
    #  // phase schedule, a simple local jump takes place. If the jump-to ~phase~ is
    #  // outside of the current schedule then the jump affects other schedules which
    #  // share the phase.
    #  //
    #  extern function void jump(uvm_phase phase)

    #  // Function: set_jump_phase
    #  //
    #  // Specify a phase to transition to when phase is complete.
    #  // Note that this function is part of what jump() does; unlike jump()
    #  // it does not set the flag to terminate the phase prematurely.
    #  extern function void set_jump_phase(uvm_phase phase)

    #  // Function: end_prematurely
    #  //
    #  // Set a flag to cause the phase to end prematurely.
    #  // Note that this function is part of what jump() does; unlike jump()
    #  // it does not set a jump_phase to go to after the phase ends.
    def end_prematurely(self):
        self.m_premature_end = 1
        #endfunction

    #  // Function- jump_all
    #  //
    #  // Make all schedules jump to a specified ~phase~, even if the jump target is local.
    #  // The jump happens to all phase schedules that contain the jump-to ~phase~
    #  // i.e. a global jump.
    #  //
    #  extern static function void jump_all(uvm_phase phase)


    #  // Function: get_jump_target
    #  //
    #  // Return handle to the target phase of the current jump, or ~null~ if no jump
    #  // is in progress. Valid for use during the phase_ended() callback
    #  //
    #  extern function uvm_phase get_jump_target()
    def get_jump_target(self):
        return self.m_jump_phase


    #// m_find_predecessor
    #// ------------------
    #
    def m_find_predecessor(self, phase: 'UVMPhase', stay_in_scope=True, orig_phase=None):
        uvm_debug(self, 'm_find_pred', "called with phase as {}, orig_phase {}".format(
            phase, orig_phase))
        if phase is None:
            return None
        uvm_debug(self, 'm_find_pred', "  Comparing now {} to {} and self {}".format(phase, self.m_imp,
                self))
        if phase == self.m_imp or phase == self:
            uvm_debug(self, 'm_find_pred', "returning self now from")
            return self
        for key in self.m_predecessors.keys():
            uvm_debug(self, 'm_find_pred', "  key is now {}".format(key))
            pred = key
            if orig_phase is None:
                orig = self
            else:
                orig = orig_phase
            uvm_debug(self, 'm_find_pred', "pred is {}, orig is {}".format(pred, orig))
            if (not stay_in_scope or
                    (pred.get_schedule() == orig.get_schedule()) or
                    (pred.get_domain() == orig.get_domain())):
                found = pred.m_find_predecessor(phase,stay_in_scope,orig)
                return found
        uvm_debug(self, 'm_find_pred', "Did not find precessors for " +
                str(phase))
        return None

    #// m_find_successor
    #// ----------------
    #
    # @return uvm_phase
    def m_find_successor(self, phase: 'UVMPhase', stay_in_scope=True, orig_phase=None):
        found = None
        #uvm_debug(self, 'm_find_succ', "called with phase as {}, orig_phase {}".format(
        #        phase, orig_phase))

        if phase is None:
            return None
        if phase == self.m_imp or phase == self:
            return self
        for succ in self.m_successors.keys():
            uvm_debug(self, 'm_find_succ', "succ is now {}".format(succ))
            orig = None
            if orig_phase is None:
                orig = self
            else:
                orig = orig_phase
            if (not stay_in_scope or
                    (succ.get_schedule() == orig.get_schedule()) or
                    (succ.get_domain() == orig.get_domain())):
                found = succ.m_find_successor(phase,stay_in_scope,orig)
                return found
        return None


    #  extern function uvm_phase m_find_predecessor_by_name(string name, bit stay_in_scope=1, uvm_phase orig_phase=null)
    def m_find_predecessor_by_name(self, name, stay_in_scope=1, orig_phase=None):
        found = None
        if self.get_name() == name:
            return self
        for pred in self.m_predecessors:
            orig = self if (orig_phase is None) else orig_phase
            if (not stay_in_scope or
                    (pred.get_schedule() == orig.get_schedule()) or
                    (pred.get_domain() == orig.get_domain())):
                found = pred.m_find_predecessor_by_name(name,stay_in_scope,orig)
                if found is not None:
                    return found
        return None

    #  extern function uvm_phase m_find_successor_by_name(string name, bit stay_in_scope=1, uvm_phase orig_phase=null)
    def m_find_successor_by_name(self, name, stay_in_scope=1, orig_phase=None):
        found = None
        if self.get_name() == name:
            return self
        for succ in self.m_successors:
            orig = self if (orig_phase is None) else orig_phase
            if (not stay_in_scope or
                    (succ.get_schedule() == orig.get_schedule()) or
                    (succ.get_domain() == orig.get_domain())):
                found = succ.m_find_successor_by_name(name,stay_in_scope,orig)
                if found is not None:
                    return found
        return None


    #  extern function void m_print_successors()

    #
    #  // Implementation - Callbacks
    #  //---------------------------
    #  // Provide the required component traversal behavior. Called by execute()
    #  virtual function void traverse(uvm_component comp,
    #                                 uvm_phase phase,
    #                                 uvm_phase_state state)
    #  endfunction

    #  // Provide the required per-component execution flow. Called by traverse()
    def execute(self, comp, phase):
        pass

    #
    #  // Implementation - Schedule
    #  //--------------------------
    #  // Track the currently executing real task phases (used for debug)
    #  function uvm_phase get_begin_node(); if (m_imp != null) return this; return null; endfunction
    #  function uvm_phase get_end_node();   return self.m_end_node; endfunction

    #  // Implementation - Synchronization
    #  //---------------------------------

    def get_ready_to_end_count(self):
        return self.m_ready_to_end_count

    # Internal implementation, more efficient than calling get_predessor_nodes on all
    # of the successors returned by get_adjacent_successor_nodes
    #function void uvm_phase::get_predecessors_for_successors(output bit pred_of_succ[uvm_phase])
    def get_predecessors_for_successors(self, pred_of_succ):
        done = False
        successors = []  #uvm_phase[]
        successors = self.get_adjacent_successor_nodes()

        # get all predecessors to these successors
        #for s in successors:
        for s in range(len(successors)):
            #for pred in successors[s].m_predecessors:
            for pred in successors[s].m_predecessors:
                if pred == self:
                    uvm_debug(self, 'get_predecessors_for_successor', self.get_name()
                        + " ZZZ self found from pred_of_succ")
                pred_of_succ[pred] = 1

        # replace any terminal nodes with their predecessors, recursively.
        # we are only interested in "real" phase nodes
        done = False
        while (not done):
            done = True
            # tpoikela: Make a copy of keys because dict can be modified in loop
            items = list(pred_of_succ.keys())
            for pred in items:
                if pred.get_phase_type() != UVM_PHASE_NODE:
                    del pred_of_succ[pred]
                    for next_pred in pred.m_predecessors:
                        pred_of_succ[next_pred] = 1
                    done = False

        # remove ourselves from the list
        if self.get_name() != 'final':
            del pred_of_succ[self]


    async def m_wait_for_pred(self):
        pred_of_succ = {}  # bit [uvm_phase]
        self.get_predecessors_for_successors(pred_of_succ)
        await uvm_zero_delay()

        # wait for predecessors to successors (real phase nodes, not terminals)
        # mostly debug msgs
        for sibling in pred_of_succ:

            if UVMPhase.m_phase_trace:
                s = sv.sformatf("Waiting for phase '%s' (%0d) to be READY_TO_END. Current state is %s",
                    sibling.get_name(),sibling.get_inst_id(),sibling.m_state.name())
                UVM_PH_TRACE("PH/TRC/WAIT_PRED_OF_SUCC",s,self,UVM_HIGH)

            await sibling.wait_for_state(UVM_PHASE_READY_TO_END, UVM_GTE)

            if UVMPhase.m_phase_trace:
                s = sv.sformatf("Phase '%s' (%0d) is now READY_TO_END. Releasing phase",
                    sibling.get_name(),sibling.get_inst_id())
                UVM_PH_TRACE("PH/TRC/WAIT_PRED_OF_SUCC",s,self,UVM_HIGH)


        if UVMPhase.m_phase_trace:
            if len(pred_of_succ) > 0:
                s = "( "
                for key in pred_of_succ:
                    pred = key
                    s = s + pred.get_full_name() + " "
                s = s + ")"
                UVM_PH_TRACE("PH/TRC/WAIT_PRED_OF_SUCC",
                      "*** All pred to succ " + s + " in READY_TO_END state, so ending phase ***",self,UVM_HIGH)
            else:
                UVM_PH_TRACE("PH/TRC/WAIT_PRED_OF_SUCC",
                          "*** No pred to succ other than myself, so ending phase ***",self,UVM_HIGH)

        #  #0; // LET ANY WAITERS WAKE UP
        await uvm_zero_delay()


    #  extern function void clear(uvm_phase_state state = UVM_PHASE_DORMANT)
    #// for internal graph maintenance after a forward jump
    def clear(self, state=UVM_PHASE_DORMANT):
        self.set_state(state)
        self.m_phase_proc = None
        if self.phase_done is not None:
            self.phase_done.clear(self)


    #  extern function void clear_successors(
    #                             uvm_phase_state state = UVM_PHASE_DORMANT,
    #                             uvm_phase end_state=null)
    #// clear_successors
    #// ----------------
    #// for internal graph maintenance after a forward jump
    #// - called only by execute_phase()
    #// - depth-first traversal of the DAG, calliing clear() on each node
    #// - do not clear the end phase or beyond
    def clear_successors(self, state=UVM_PHASE_DORMANT, end_state=None):
        if self == end_state:
            return
        self.clear(state)
        for succ in self.m_successors:
            succ.clear_successors(state, end_state)


    # m_run_phases
    # ------------

    # This task contains the top-level process that owns all the phase
    # processes.  By hosting the phase processes here we avoid problems
    # associated with phase processes related as parents/children
    @classmethod
    async def m_run_phases(cls):
        cs = get_cs()
        top = cs.get_root()
        uvm_debug(cls, 'm_run_phases', 'Forking all phases in while-True')

        # initiate by starting first phase in common domain

        from .uvm_domain import UVMDomain
        ph = UVMDomain.get_common_domain()
        uvm_debug(cls, 'm_run_phases', 'common domain OK')
        if not UVMPhase.m_phase_hopper.try_put(ph):
            raise Exception('Could not add phase to phase_hopper mailbox')

        while True:
            qphase = []
            await UVMPhase.m_phase_hopper.get(qphase)  # Should block?
            #fork
            uvm_debug(cls, 'm_run_phases', 'Calling execute phase with |' +
                    str(qphase[0].get_name()) + '|')
            cocotb.fork(qphase[0].execute_phase())
            #join_none
            await uvm_zero_delay()
            #0;  // let the process start running


    # execute_phase
    # -------------
    async def execute_phase(self):
        task_phase = None
        state_chg = None

        cs = get_cs()
        top = cs.get_root()  # UVMRoot
        uvm_debug(self, 'execute_phase', 'Waiting predecessors to finish ' +
            self.get_name())

        # If we got here by jumping forward, we must wait for
        # all its predecessor nodes to be marked DONE.
        # (the next conditional speeds this up)
        # Also, this helps us fast-forward through terminal (end) nodes
        await self._wait_all_predecessors_done()
        uvm_debug(self, 'execute_phase', 'All predecessors are DONE ' +
            self.get_name())

        # If DONE (by, say, a forward jump), return immed
        if self.m_state == UVM_PHASE_DONE:
            uvm_debug(self, 'execute_phase', 'PHASE_DONE_REACHED - returning now')
            return

        state_chg = UVMPhaseStateChange(self.get_name())
        state_chg.m_phase      = self
        state_chg.m_jump_to    = None

        #---------
        # SYNCING:
        #---------
        # Wait for phases with which we have a sync()
        # relationship to be ready. Sync can be 2-way -
        # this additional state avoids deadlock.
        state_chg.m_prev_state = self.m_state
        self.set_state(UVM_PHASE_SYNCING)
        uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
        await uvm_zero_delay()
        uvm_debug(self, 'execute_phase', 'Checking for wait_phases_synced')

        if len(self.m_sync) > 0:
            uvm_debug(self, 'execute_phase', 'Waiting for wait_phases_synced ' +
                self.get_name())
            await self._wait_phases_synced()

        self.m_run_count += 1
        if UVMPhase.m_phase_trace is True:
            UVM_PH_TRACE("PH/TRC/STRT","Starting phase",self,UVM_LOW)

        # If we're a schedule or domain, then "fake" execution
        if self.m_phase_type != UVM_PHASE_NODE:
            uvm_debug(self, 'execute_phase', 'schedule/domain, faking execution')
            state_chg.m_prev_state = self.m_state
            self.set_state(UVM_PHASE_STARTED)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)

            await uvm_zero_delay()

            state_chg.m_prev_state = self.m_state
            self.set_state(UVM_PHASE_EXECUTING)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)

            await uvm_zero_delay()
        else:  # PHASE NODE
            uvm_debug(self, 'execute_phase', 'PHASE_NODE, setting phase to started')
            #---------
            # STARTED:
            #---------
            state_chg.m_prev_state = self.m_state

            self.set_state(UVM_PHASE_STARTED)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)

            # Task-phases must use yield here
            if not self.m_imp.is_task_phase():
                self.m_imp.traverse(top,self, UVM_PHASE_STARTED)
            else:
                await self.m_imp.traverse(top,self, UVM_PHASE_STARTED)

            self.m_ready_to_end_count = 0  # reset the ready_to_end count when phase starts
            await uvm_zero_delay()  # LET ANY WAITERS WAKE UP

            if not self.m_imp.is_task_phase():
                #-----------
                # EXECUTING: (function phases)
                #-----------
                uvm_debug(self, 'execute_phase', 'Exec non-task (function) phase now')
                state_chg.m_prev_state = self.m_state
                self.set_state(UVM_PHASE_EXECUTING)
                uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
                await uvm_zero_delay() # LET ANY WAITERS WAKE UP
                uvm_debug(self, 'execute_phase', 'Will traverse something now')
                self.m_imp.traverse(top,self,UVM_PHASE_EXECUTING)
            else:
                task_phase = self.m_imp  # was $cast(task_phase, m_imp)
                # Execute task phase (which can consume time/fork procs)
                UVMPhase.m_executing_phases[self] = 1
                state_chg.m_prev_state = self.m_state
                self.set_state(UVM_PHASE_EXECUTING)

                uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
                #fork : master_phase_process
                #self.m_phase_proc = process::self()
                #-----------
                # EXECUTING: (task phases)
                #-----------
                uvm_debug(self, 'execute_phase', "Forking now task_phase for uvm_top")
                task_proc = cocotb.fork(task_phase.traverse(top, self, UVM_PHASE_EXECUTING))
                #wait(0); // stay alive for later kill
                #join_none

                await uvm_wait_for_nba_region()  # Give sequences, etc. a chance to object
                await self.wait_for_criterion_for_end_phase(state_chg)
                uvm_debug(self, 'execute_phase', "End criterion reached for " +
                        top.get_name())
        #  end # PHASE_NODE

        uvm_debug(self, 'execute_phase', 'Now deleting self from executing phases')
        if self in UVMPhase.m_executing_phases:
            del UVMPhase.m_executing_phases[self]
        else:
            pass
            #uvm_fatal('NOT_IN_EXEC', 'self not in executing phases')

        # ---------
        #  JUMPING:
        # ---------
        #
        #  If jump_to() was called then we need to kill all the successor
        #  phases which may still be running and then initiate the new
        #  phase.  The return is necessary so we don't start new successor
        #  phases.  If we are doing a forward jump then we want to set the
        #  state of this phase's successors to UVM_PHASE_DONE.  This
        #  will let us pretend that all the phases between here and there
        #  were executed and completed.  Thus any dependencies will be
        #  satisfied preventing deadlocks.
        #  GSA TBD insert new jump support
        #
        if self.m_phase_type == UVM_PHASE_NODE:
            if self.m_premature_end:
                if self.m_jump_phase is not None:
                    state_chg.m_jump_to = self.m_jump_phase
                    uvm_report_info("PH_JUMP", (
                        "phase {} (schedule {}, domain {}) is jumping to phase {}".format(
                            self.get_name(), self.get_schedule_name(), self.get_domain_name(),
                            self.m_jump_phase.get_name())), UVM_MEDIUM)
                else:
                    uvm_report_info("PH_JUMP", (
                        "phase {} (schedule {}, domain {}) is ending prematurely".format(
                            self.get_name(), self.get_schedule_name(),
                            self.get_domain_name())), UVM_MEDIUM)

                #0; // LET ANY WAITERS ON READY_TO_END TO WAKE UP
                await uvm_zero_delay()

                if UVMPhase.m_phase_trace:
                    UVM_PH_TRACE("PH_END","ENDING PHASE PREMATURELY",self,UVM_MEDIUM)
            else:
                # WAIT FOR PREDECESSORS:  // WAIT FOR PREDECESSORS:
                # function phases only
                if task_phase is None:
                    await self.m_wait_for_pred()

            #-------
            # ENDED:
            #-------
            # execute 'phase_ended' callbacks
            if UVMPhase.m_phase_trace:
                UVM_PH_TRACE("PH_END","ENDING PHASE",self,UVM_MEDIUM)
            state_chg.m_prev_state = self.m_state
            self.set_state(UVM_PHASE_ENDED)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
            if self.m_imp is not None:
                if self.m_imp.is_task_phase():
                    await self.m_imp.traverse(top,self, UVM_PHASE_ENDED)
                else:
                    self.m_imp.traverse(top,self, UVM_PHASE_ENDED)
            uvm_debug(self, "execute_phase", "MMM KKK SSS ZZZ before yield")
            await uvm_zero_delay()
            uvm_debug(self, "execute_phase", "Phase ended after yield")
            #0; // LET ANY WAITERS WAKE UP

            #---------
            # CLEANUP:
            #---------
            # kill this phase's threads
            uvm_debug(self, "execute_phase", "Starting cleanup of |"
                    + self.m_imp.get_name() + "|")
            state_chg.m_prev_state = self.m_state
            if self.m_premature_end:
                self.set_state(UVM_PHASE_JUMPING)
            else:
                self.set_state(UVM_PHASE_CLEANUP)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
            if self.m_phase_proc is not None:
                self.m_phase_proc.kill()
                self.m_phase_proc = None
            await uvm_zero_delay()
            #0; // LET ANY WAITERS WAKE UP
            uvm_debug(self, "execute_phase", "Cleanup DONE |" + self.m_imp.get_name() + "|")
            if self.phase_done is not None:
                nn = self.get_name()
                uvm_debug(self, "execute_phase", nn + "| clear() now after DONE |" +
                        self.m_imp.get_name() + "|")
                self.phase_done.clear()

        #------
        # DONE:
        #------
        self.m_premature_end = False
        if self.m_jump_fwd or self.m_jump_bkwd:
            if self.m_jump_fwd:
                self.clear_successors(UVM_PHASE_DONE,self.m_jump_phase)
            self.m_jump_phase.clear_successors()
        else:
            if UVMPhase.m_phase_trace:
                UVM_PH_TRACE("PH/TRC/DONE","Completed phase",self,UVM_LOW)
            state_chg.m_prev_state = self.m_state
            self.set_state(UVM_PHASE_DONE)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
            uvm_debug(self, 'exec_phase', 'DONE after uvm_callbacks done')
            self.m_phase_proc = None
            await uvm_zero_delay()  # 0; // LET ANY WAITERS WAKE UP
        await uvm_zero_delay()  # 0; // LET ANY WAITERS WAKE UP
        if self.phase_done is not None:
            self.phase_done.clear()

        #-----------
        # SCHEDULED:
        #-----------
        if self.m_jump_fwd or self.m_jump_bkwd:
            UVMPhase.m_phase_hopper.try_put(self.m_jump_phase)
            self.m_jump_phase = None
            self.m_jump_fwd = False
            self.m_jump_bkwd = False

        # If more successors, schedule them to run now
        elif len(self.m_successors) == 0:
            #top.m_phase_all_done= True
            uvm_debug(self, 'execute_phase', ('name: ' + self.get_name() +
                ' - notify phases done OK'))
            top.m_phase_all_done_event.set()
        else:
            # execute all the successors
            for key in self.m_successors.keys():
                uvm_debug(self, 'execute_phase', self.get_name() +
                    ' has more successors')
                succ = key
                if succ.m_state < UVM_PHASE_SCHEDULED:
                    state_chg.m_prev_state = succ.m_state
                    state_chg.m_phase = succ
                    succ.set_state(UVM_PHASE_SCHEDULED)
                    uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', succ, state_chg)
                    await uvm_zero_delay()  # LET ANY WAITERS WAKE UP
                    if not UVMPhase.m_phase_hopper.try_put(succ):
                        raise Exception('Failed try_put(succ). Should not ever fail')
                    if UVMPhase.m_phase_trace:
                         UVM_PH_TRACE("PH/TRC/SCHEDULED", ("Scheduled from phase "
                             + self.get_full_name()), succ, UVM_LOW)
        uvm_debug(self, 'execute_phase', 'End of task reached. Yay!')
        #endtask


    async def _wait_all_predecessors_done(self):
        nn = self.get_name()
        if self.has_predecessors():
            uvm_debug(self, '_wait_all_predecessors_done', nn + '| has predecessors() OK')
            events = []
            for pred in self.m_predecessors:
                uvm_debug(self, '_wait_all_predecessors_done', 'pred is now ' + str(pred))
                #wait (pred.m_state == UVM_PHASE_DONE)
                #events.append(pred.get_phase_done_event())
                events.append(pred.get_phase_done_event().wait())

            uvm_debug(self, '_wait_all_predecessors_done', nn + "| Before combining events")
            await Combine(*events)  # Combine expects *args, not list
            uvm_debug(self, '_wait_all_predecessors_done', nn + "| After combining events")
        else:
            uvm_debug(self, '_wait_all_predecessors_done', nn + '| before yield Timer(0)')
            await uvm_zero_delay()
            uvm_debug(self, '_wait_all_predecessors_done', nn + '| after yield Timer(0)')


    async def _wait_phases_synced(self):
        events = []
        for phase in self.m_sync:
            if (phase.m_state < UVM_PHASE_SYNCING):
                events.append(phase.get_phase_synced_event())
        await Combine(*events)

    def has_predecessors(self):
        return len(self.m_predecessors) > 0

    #  extern local function void m_terminate_phase()
    #  extern local function void m_print_termination_state()

    #//---------------------------------
    #// Implementation - Overall Control
    #//---------------------------------

    #// This task loops until this phase instance and all its siblings, either
    #// sync'd or sharing a common successor, have all objections dropped.
    async def wait_for_self_and_siblings_to_drop(self):
        need_to_check_all = True
        top = None
        cs = None
        siblings = {}  # bit siblings[uvm_phase]
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        top = cs.get_root()

        self.get_predecessors_for_successors(siblings)
        for ss in self.m_sync:
            siblings[ss] = 1
        await uvm_zero_delay()

        while need_to_check_all is True:
            need_to_check_all = False  # if all are dropped, we won't need to do this again

            # wait for own objections to drop
            if ((self.phase_done is not None) and
                    (self.phase_done.get_objection_total(top) != 0)):
                self.set_state(UVM_PHASE_EXECUTING)
                await self.phase_done.wait_for(UVM_ALL_DROPPED, top)
                need_to_check_all = True

            # now wait for siblings to drop
            #foreach(siblings[sib]) begin
            for sib in siblings:
                # sibling must be at least executing
                await sib.wait_for_state(UVM_PHASE_EXECUTING, UVM_GTE)
                if ((sib.phase_done is not None) and
                        (sib.phase_done.get_objection_total(top) != 0)):
                    self.set_state(UVM_PHASE_EXECUTING)
                    # sibling must drop any objection
                    await sib.phase_done.wait_for(UVM_ALL_DROPPED, top)
                    need_to_check_all = True
        #endtask

    #  extern function void kill()
    #  extern function void kill_successors()


    def convert2string(self):
        #return $sformatf("PHASE %s = %p",get_name(),this)
        par_str = 'null'
        if self.m_parent is not None:
            par_str = self.get_schedule_name()
        pred_str = str(self.m_predecessors)
        succ_str = str(self.m_successors)
        s = "phase: {} parent={}  pred={}  succ={}".format(
            self.get_name(), par_str, pred_str, succ_str)
        return s

    #  local function string m_aa2string(bit aa[uvm_phase]); // TBD tidy
    #    string s
    #    int i
    #    s = "'{ "
    #    foreach (aa[ph]) begin
    #      uvm_phase n = ph
    #      s = {s, (n == null) ? "null" : n.get_name(),
    #        (i == aa.num()-1) ? "" : ", "}
    #      i++
    #    end
    #    s = {s, " }"}
    #    return s
    #  endfunction
    #
    #  function bit is_domain()
    #    return (self.m_phase_type == UVM_PHASE_DOMAIN)
    #  endfunction
    #
    #  virtual function void m_get_transitive_children(ref uvm_phase phases[$])
    #    foreach (self.m_successors[succ])
    #    begin
    #        phases.push_back(succ)
    #        succ.m_get_transitive_children(phases)
    #    end
    #  endfunction
    #endclass
    #uvm_object_utils(UVMPhase)
    #uvm_register_cb(UVMPhase, UVMPhaseCb)


    async def wait_for_criterion_for_end_phase(self, state_chg):
        await self._wait_for_all_dropped(state_chg)


    async def _wait_for_all_dropped(self, state_chg):
        cs = get_cs()
        top = cs.get_root()
        # WAIT_FOR_ALL_DROPPED
        do_ready_to_end = False  # bit used for ready_to_end iterations
        # OVM semantic: don't end until objection raised or stop request
        if (self.phase_done.get_objection_total(top) or (UVMPhase.m_use_ovm_run_semantic
                and self.m_imp.get_name() == "run")):
            if not self.phase_done.m_top_all_dropped:
                await self.phase_done.wait_for(UVM_ALL_DROPPED, top)
            UVM_PH_TRACE("PH/TRC/EXE/ALLDROP","PHASE EXIT ALL_DROPPED",self,UVM_MEDIUM)
        else:
            if (UVMPhase.m_phase_trace):
                UVM_PH_TRACE("PH/TRC/SKIP","No objections raised, skipping phase",self,UVM_LOW)

        uvm_debug(self, '_wait_for_all_dropped', self.get_name() + ' waiting siblings to drop')
        await self.wait_for_self_and_siblings_to_drop()
        uvm_debug(self, '_wait_for_all_dropped', self.get_name() + ' all siblings have dropped')
        do_ready_to_end = True

        # --------------
        #  READY_TO_END:
        # --------------
        while do_ready_to_end:
            # Let all siblings see no objections before traverse might raise another
            await uvm_wait_for_nba_region()
            UVM_PH_TRACE("PH_READY_TO_END","PHASE READY TO END",self,UVM_MEDIUM)
            self.m_ready_to_end_count += 1
            if (UVMPhase.m_phase_trace):
                UVM_PH_TRACE("PH_READY_TO_END_CB","CALLING READY_TO_END CB",self,UVM_MEDIUM)
            state_chg.m_prev_state = self.m_state
            self.set_state(UVM_PHASE_READY_TO_END)
            uvm_do_callbacks(self, UVMPhaseCb, 'phase_state_change', self, state_chg)
            if self.m_imp is not None:
                if self.m_imp.is_task_phase():
                    await self.m_imp.traverse(top, self, UVM_PHASE_READY_TO_END)
                else:
                    self.m_imp.traverse(top, self, UVM_PHASE_READY_TO_END)

            await uvm_wait_for_nba_region()  # Give traverse targets a chance to object
            await self.wait_for_self_and_siblings_to_drop()
            do_ready_to_end = ((self.m_state == UVM_PHASE_EXECUTING) and (self.m_ready_to_end_count
                < self.max_ready_to_end_iter))  # when we don't wait in task above, we drop out of while loop


#------------------------------------------------------------------------------
#
# Class: uvm_phase_cb
#
#------------------------------------------------------------------------------
#
# This class defines a callback method that is invoked by the phaser
# during the execution of a specific node in the phase graph or all phase nodes.
# User-defined callback extensions can be used to integrate data types that
# are not natively phase-aware with the UVM phasing.

class UVMPhaseCb(UVMCallback):

    def __init__(self, name="unnamed-uvm_phase_cb"):
        """
        Function: new
        Constructor
        Args:
            name:
        """
        UVMCallback.__init__(self)

    def phase_state_change(self, phase, change):
        """
        Function: phase_state_change

        Called whenever a `phase` changes state.
        The `change` descriptor describes the transition that was just completed.
        The callback method is invoked immediately after the phase state has changed,
        but before the phase implementation is executed.

        An extension may interact with the phase,
        such as raising the phase objection to prolong the phase,
        in a manner that is consistent with the current phase state.

        By default, the callback method does nothing.
        Unless otherwise specified, modifying the  phase transition descriptor has
        no effect on the phasing schedule or execution.

        Args:
            phase:
            change:
        """
        pass


#------------------------------------------------------------------------------
#
# Class: uvm_phase_cb_pool
#
#------------------------------------------------------------------------------
# Convenience type for the uvm_callbacks#(uvm_phase, uvm_phase_cb) class.
#typedef uvm_callbacks#(uvm_phase, uvm_phase_cb) uvm_phase_cb_pool


    ##------------------------------------------------------------------------------
    ##                               IMPLEMENTATION
    ##------------------------------------------------------------------------------
    #
    #typedef class uvm_cmdline_processor


    #//-----------------------------
    #// Implementation - Construction
    #//-----------------------------
    #
    #// get_imp
    #// -------
    #
    #function uvm_phase uvm_phase::get_imp()
    #  return m_imp
    #endfunction
    #
    #
    #
    #
    #// m_print_successors
    #// ------------------
    #
    #function void uvm_phase::m_print_successors()
    #  uvm_phase found
    #  static string spaces = "                                                 "
    #  static int level
    #  if (self.m_phase_type == UVM_PHASE_DOMAIN)
    #    level = 0
    #  `uvm_info("UVM/PHASE/SUCC",$sformatf("%s%s (%s) id=%0d",spaces.substr(0,level*2),get_name(), self.m_phase_type.name(),get_inst_id()),UVM_NONE)
    #  level++
    #  foreach (self.m_successors[succ]) begin
    #    succ.m_print_successors()
    #  end
    #  level--
    #endfunction
    #
    #



    #function void uvm_phase::get_adjacent_predecessor_nodes(ref uvm_phase pred[])
    #   bit done
    #   bit predecessors[uvm_phase]
    #   int idx
    #
    #   // Get all predecessors (including TERMINALS, SCHEDULES, etc.)
    #   foreach (self.m_predecessors[p])
    #     predecessors[p] = 1
    #
    #   // Replace any terminal / schedule nodes with their predecessors,
    #   // recursively.
    #   do begin
    #      done = 1
    #      foreach (predecessors[p]) begin
    #         if (p.get_phase_type() != UVM_PHASE_NODE) begin
    #            predecessors.delete(p)
    #            foreach (p.m_predecessors[next_p])
    #              predecessors[next_p] = 1
    #            done = 0
    #         end
    #      end
    #   end while (!done)
    #
    #   pred = new [predecessors.size()]
    #   foreach (predecessors[p]) begin
    #      pred[idx++] = p
    #   end
    #endfunction : get_adjacent_predecessor_nodes
    #
    #
    #
    #
    #
    #
    #//---------------------------------
    #// Implementation - Synchronization
    #//---------------------------------
    #
    #
    #
    #// get_objection_count
    #// -------------------
    #
    #function int uvm_phase::get_objection_count (uvm_object obj=null)
    #   if (self.phase_done != null)
    #     return self.phase_done.get_objection_count(obj)
    #   else begin
    #      m_report_null_objection(obj, "" , 0, "get_objection_count")
    #      return 0
    #   end
    #endfunction : get_objection_count
    #
    #// sync
    #// ----
    #
    #function void uvm_phase::sync(uvm_domain target,
    #                              uvm_phase phase=null,
    #                              uvm_phase with_phase=null)
    #  if (!this.is_domain()) begin
    #    `uvm_fatal("PH_BADSYNC","sync() called from a non-domain phase schedule node")
    #  end
    #  else if (target == null) begin
    #    `uvm_fatal("PH_BADSYNC","sync() called with a null target domain")
    #  end
    #  else if (!target.is_domain()) begin
    #    `uvm_fatal("PH_BADSYNC","sync() called with a non-domain phase schedule node as target")
    #  end
    #  else if (phase == null && with_phase != null) begin
    #    `uvm_fatal("PH_BADSYNC","sync() called with null phase and non-null with phase")
    #  end
    #  else if (phase == null) begin
    #    // whole domain sync - traverse this domain schedule from begin to end node and sync each node
    #    int visited[uvm_phase]
    #    uvm_phase queue[$]
    #    queue.push_back(this)
    #    visited[this] = 1
    #    while (queue.size()) begin
    #      uvm_phase node
    #      node = queue.pop_front()
    #      if (node.m_imp != null) begin
    #        sync(target, node.m_imp)
    #      end
    #      foreach (node.m_successors[succ]) begin
    #        if (!visited.exists(succ)) begin
    #          queue.push_back(succ)
    #          visited[succ] = 1
    #        end
    #      end
    #    end
    #  end else begin
    #    // single phase sync
    #    // this is a 2-way ('with') sync and we check first in case it is already there
    #    uvm_phase from_node, to_node
    #    int found_to[$], found_from[$]
    #    if(with_phase == null) with_phase = phase
    #    from_node = find(phase)
    #    to_node = target.find(with_phase)
    #    if(from_node == null || to_node == null) return
    #    found_to = from_node.m_sync.find_index(node) with (node == to_node)
    #    found_from = to_node.m_sync.find_index(node) with (node == from_node)
    #    if (found_to.size() == 0) from_node.m_sync.push_back(to_node)
    #    if (found_from.size() == 0) to_node.m_sync.push_back(from_node)
    #  end
    #endfunction
    #
    #
    #// unsync
    #// ------
    #
    #function void uvm_phase::unsync(uvm_domain target,
    #                                uvm_phase phase=null,
    #                                uvm_phase with_phase=null)
    #  if (!this.is_domain()) begin
    #    `uvm_fatal("PH_BADSYNC","unsync() called from a non-domain phase schedule node")
    #  end else if (target == null) begin
    #    `uvm_fatal("PH_BADSYNC","unsync() called with a null target domain")
    #  end else if (!target.is_domain()) begin
    #    `uvm_fatal("PH_BADSYNC","unsync() called with a non-domain phase schedule node as target")
    #  end else if (phase == null && with_phase != null) begin
    #    `uvm_fatal("PH_BADSYNC","unsync() called with null phase and non-null with phase")
    #  end else if (phase == null) begin
    #    // whole domain unsync - traverse this domain schedule from begin to end node and unsync each node
    #    int visited[uvm_phase]
    #    uvm_phase queue[$]
    #    queue.push_back(this)
    #    visited[this] = 1
    #    while (queue.size()) begin
    #      uvm_phase node
    #      node = queue.pop_front()
    #      if (node.m_imp != null) unsync(target,node.m_imp)
    #      foreach (node.m_successors[succ]) begin
    #        if (!visited.exists(succ)) begin
    #          queue.push_back(succ)
    #          visited[succ] = 1
    #        end
    #      end
    #    end
    #  end else begin
    #    // single phase unsync
    #    // this is a 2-way ('with') sync and we check first in case it is already there
    #    uvm_phase from_node, to_node
    #    int found_to[$], found_from[$]
    #    if(with_phase == null) with_phase = phase
    #    from_node = find(phase)
    #    to_node = target.find(with_phase)
    #    if(from_node == null || to_node == null) return
    #    found_to = from_node.m_sync.find_index(node) with (node == to_node)
    #    found_from = to_node.m_sync.find_index(node) with (node == from_node)
    #    if (found_to.size()) from_node.m_sync.delete(found_to[0])
    #    if (found_from.size()) to_node.m_sync.delete(found_from[0])
    #  end
    #endfunction
    #
    #
    #
    #//-------------------------
    #// Implementation - Jumping
    #//-------------------------
    #
    #// set_jump_phase
    #// ----
    #//
    #// Specify a phase to transition to when phase is complete.
    #
    #function void uvm_phase::set_jump_phase(uvm_phase phase)
    #  uvm_phase d
    #
    #  if ((self.m_state <  UVM_PHASE_STARTED) ||
    #      (self.m_state >  UVM_PHASE_ENDED) )
    #  begin
    #   `uvm_error("JMPPHIDL", { "Attempting to jump from phase \"",
    #      get_name(), "\" which is not currently active (current state is ",
    #      self.m_state.name(), "). The jump will not happen until the phase becomes ",
    #      "active."})
    #  end
    #
    #
    #
    #  // A jump can be either forward or backwards in the phase graph.
    #  // If the specified phase (name) is found in the set of predecessors
    #  // then we are jumping backwards.  If, on the other hand, the phase is in the set
    #  // of successors then we are jumping forwards.  If neither, then we
    #  // have an error.
    #  //
    #  // If the phase is non-existant and thus we don't know where to jump
    #  // we have a situation where the only thing to do is to uvm_fatal
    #  // and terminate_phase.  By calling this function the intent was to
    #  // jump to some other phase. So, continuing in the current phase doesn't
    #  // make any sense.  And we don't have a valid phase to jump to.  So we're done.
    #
    #  d = m_find_predecessor(phase,0)
    #  if (d == null) begin
    #    d = m_find_successor(phase,0)
    #    if (d == null) begin
    #      string msg
    #      $sformat(msg,{"phase %s is neither a predecessor or successor of ",
    #                    "phase %s or is non-existant, so we cannot jump to it.  ",
    #                    "Phase control flow is now undefined so the simulation ",
    #                    "must terminate"}, phase.get_name(), get_name())
    #      `uvm_fatal("PH_BADJUMP", msg)
    #    end
    #    else begin
    #      m_jump_fwd = 1
    #      `uvm_info("PH_JUMPF",$sformatf("jumping forward to phase %s", phase.get_name()),
    #                UVM_DEBUG)
    #    end
    #  end
    #  else begin
    #    m_jump_bkwd = 1
    #    `uvm_info("PH_JUMPB",$sformatf("jumping backward to phase %s", phase.get_name()),
    #              UVM_DEBUG)
    #  end
    #
    #  m_jump_phase = d
    #endfunction
    #
    #
    #// jump
    #// ----
    #//
    #// Note that this function does not directly alter flow of control.
    #// That is, the new phase is not initiated in this function.
    #// Rather, flags are set which execute_phase() uses to determine
    #// that a jump has been requested and performs the jump.
    #
    #function void uvm_phase::jump(uvm_phase phase)
    #   set_jump_phase(phase)
    #   end_prematurely()
    #endfunction
    #
    #
    #// jump_all
    #// --------
    #function void uvm_phase::jump_all(uvm_phase phase)
    #    `uvm_warning("NOTIMPL","uvm_phase::jump_all is not implemented and has been replaced by uvm_domain::jump_all")
    #endfunction
    #
    #

    #
    #// kill
    #// ----
    #
    #function void uvm_phase::kill()
    #
    #  `uvm_info("PH_KILL", {"killing phase '", get_name(),"'"}, UVM_DEBUG)
    #
    #  if (self.m_phase_proc != null) begin
    #    self.m_phase_proc.kill()
    #    self.m_phase_proc = null
    #  end
    #
    #endfunction
    #
    #
    #// kill_successors
    #// ---------------
    #
    #// Using a depth-first traversal, kill all the successor phases of the
    #// current phase.
    #function void uvm_phase::kill_successors()
    #  foreach (self.m_successors[succ])
    #    succ.kill_successors()
    #  kill()
    #endfunction
    #
    #
    #
    #
    #// terminate_phase
    #// ---------------
    #
    #function void uvm_phase::m_terminate_phase()
    #  if (self.phase_done != null)
    #    self.phase_done.clear(this)
    #endfunction
    #
    #
    #// print_termination_state
    #// -----------------------
    #
    #function void uvm_phase::m_print_termination_state()
    #  uvm_root top
    #  uvm_coreservice_t cs
    #  cs = uvm_coreservice_t::get()
    #  top = cs.get_root()
    #  if (self.phase_done != null) begin
    #    `uvm_info("PH_TERMSTATE",
    #              $sformatf("phase %s outstanding objections = %0d",
    #                        get_name(), self.phase_done.get_objection_total(top)),
    #              UVM_DEBUG)
    #  end
    #  else begin
    #    `uvm_info("PH_TERMSTATE",
    #              $sformatf("phase %s has no outstanding objections",
    #                        get_name()),
    #              UVM_DEBUG)
    #  end


