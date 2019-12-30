#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2013-2014 NVIDIA Corporation
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

import cocotb
from cocotb.triggers import Timer, Event

from ..base.sv import sv, process
from ..base.uvm_component import UVMComponent
from ..base.uvm_event import UVMEvent
from ..base.uvm_resource import UVMResourcePool
from ..base.uvm_config_db import UVMConfigDb
from ..macros import uvm_info
from ..base.uvm_object_globals import *
from ..base.uvm_pool import UVMPool
from ..base.uvm_queue import UVMQueue
from ..base.uvm_globals import uvm_wait_for_nba_region

SEQ_ERR1_MSG = ("The task responsible for requesting a lock on sequencer '%s' "
    + " for sequence '%s' has been killed, to avoid a deadlock the sequence will "
    + "be removed from the arbitration queues")

SEQ_ERR2_MSG = ("The task responsible for requesting a wait_for_grant on sequencer "
        + "'%s' for sequence '%s' has been killed, to avoid a deadlock the sequence "
        + "will be removed from the arbitration queues")

SEQ_ERR3_MSG = ("Parent sequence '%s' should not finish before all items from itself "
        + "and items from descendent sequences are processed.  The item request from " +
        "the sequence '%s' is being removed.")

SEQ_ERR4_MSG = ("Parent sequence '%s' should not finish before locks from itself "
        + "and descedent sequences are removed.  The lock held by the child "
        + "sequence '%s' is being removed.")

SEQ_FATAL1_MSG = (
    "Zero time loop detected, passed wait_for_relevant %0d times without time advancing")

#typedef uvm_config_db#(uvm_sequence_base) uvm_config_seq
#typedef class uvm_sequence_request

#// Utility class for tracking default_sequences


class uvm_sequence_process_wrapper:
    # process pid
    # uvm_sequence_base seq
    def __init__(self):
        self.pid = 0
        self.seq = None
    #endclass : uvm_sequence_process_wrapper

#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_sequencer_base
#//
#// Controls the flow of sequences, which generate the stimulus (sequence item
#// transactions) that is passed on to drivers for execution.
#//
#//------------------------------------------------------------------------------

#  typedef enum {SEQ_TYPE_REQ,
#                SEQ_TYPE_LOCK,
#                SEQ_TYPE_GRAB} seq_req_t; // FIXME SEQ_TYPE_GRAB is unused

SEQ_TYPE_REQ = 0
SEQ_TYPE_LOCK = 1
SEQ_TYPE_GRAB = 2

#class uvm_sequencer_base extends uvm_component
class UVMSequencerBase(UVMComponent):

    g_request_id = 0
    g_sequence_id = 1
    g_sequencer_id = 1

    #  // Function: new
    #  //
    #  // Creates and initializes an instance of this class using the normal
    #  // constructor arguments for uvm_component: name is the name of the
    #  // instance, and parent is the handle to the hierarchical parent.
    #  extern function new (string name, uvm_component parent)
    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.m_sequencer_id = UVMSequencerBase.g_sequencer_id
        UVMSequencerBase.g_sequencer_id += 1
        self.m_lock_arb_size = -1
        # Hidden array, keeps track of running default sequences
        self.m_default_sequences = UVMPool()  # uvm_sequence_process_wrapper[uvm_phase]

        # queue of sequences waiting for arbitration
        self.arb_sequence_q = UVMQueue()  # uvm_sequence_request [$]
        self.lock_list = UVMQueue()  # uvm_sequence_base lock_list[$]

        self.m_arbitration = UVM_SEQ_ARB_FIFO  # uvm_sequencer_arb_mode
        self.m_lock_arb_size = 0  # used for waiting processes
        self.m_arb_size = 0  # used for waiting processes

        # self.m_event_value_changed = UVMEvent("event_value_changed")
        self.m_event_value_changed = Event("event_value_changed")

        self.reg_sequences = UVMPool()  # uvm_sequence_base   reg_sequences[int]
        self.arb_completed = UVMPool()

        self.m_auto_item_recording = False
        self.m_is_relevant_completed = 0

        self.m_wait_for_item_sequence_id = 0
        self.m_wait_for_item_transaction_id = 0

        self.m_wait_relevant_count = 0
        self.m_max_zero_time_wait_relevant_count = 10
        self.m_last_wait_relevant_time = 0

    #  // Function: is_child
    #  //
    #  // Returns 1 if the child sequence is a child of the parent sequence,
    #  // 0 otherwise.
    #  //
    #  extern function bit is_child (uvm_sequence_base parent, uvm_sequence_base child)
    def is_child(self, parent, child):
        child_parent = None  # uvm_sequence_base

        if child is None:
            self.uvm_report_fatal("uvm_sequencer", "is_child passed None child", UVM_NONE)

        if parent is None:
            self.uvm_report_fatal("uvm_sequencer", "is_child passed None parent", UVM_NONE)

        child_parent = child.get_parent_sequence()
        while child_parent is not None:
            if (child_parent.get_inst_id() == parent.get_inst_id()):
                return True
            child_parent = child_parent.get_parent_sequence()
        return False
    #endfunction

    #
    #  // Function: user_priority_arbitration
    #  //
    #  // When the sequencer arbitration mode is set to UVM_SEQ_ARB_USER (via the
    #  // <set_arbitration> method), the sequencer will call this function each
    #  // time that it needs to arbitrate among sequences.
    #  //
    #  // Derived sequencers may override this method to perform a custom arbitration
    #  // policy. The override must return one of the entries from the
    #  // avail_sequences queue, which are indexes into an internal queue,
    #  // self.arb_sequence_q.
    #  //
    #  // The default implementation behaves like UVM_SEQ_ARB_FIFO, which returns the
    #  // entry at avail_sequences[0].
    #  //
    #  extern virtual function integer user_priority_arbitration(integer avail_sequences[$])
    #
    #
    #  // Task: execute_item
    #  //
    #  // Executes the given transaction ~item~ directly on this sequencer. A temporary
    #  // parent sequence is automatically created for the ~item~.  There is no capability to
    #  // retrieve responses. If the driver returns responses, they will accumulate in the
    #  // sequencer, eventually causing response overflow unless
    #  // <uvm_sequence_base::set_response_queue_error_report_disabled> is called.
    #
    #  extern virtual task execute_item(uvm_sequence_item item)
    #
    #

    #  // Function: start_phase_sequence
    #  //
    #  // Start the default sequence for this phase, if any.
    #  // The default sequence is configured via resources using
    #  // either a sequence instance or sequence type (object wrapper).
    #  // If both are used,
    #  // the sequence instance takes precedence. When attempting to override
    #  // a previous default sequence setting, you must override both
    #  // the instance and type (wrapper) resources, else your override may not
    #  // take effect.
    #  //
    #  // When setting the resource using ~set~, the 1st argument specifies the
    #  // context pointer, usually ~this~ for components or ~None~ when executed from
    #  // outside the component hierarchy (i.e. in module).
    #  // The 2nd argument is the instance string, which is a path name to the
    #  // target sequencer, relative to the context pointer.  The path must include
    #  // the name of the phase with a "_phase" suffix. The 3rd argument is the
    #  // resource name, which is "default_sequence". The 4th argument is either
    #  // an object wrapper for the sequence type, or an instance of a sequence.
    #  //
    #  // Configuration by instances
    #  // allows pre-initialization, setting rand_mode, use of inline
    #  // constraints, etc.
    #  //
    #  //| myseq_t myseq = new("myseq")
    #  //| myseq.randomize() with { ... }
    #  //| uvm_config_db #(uvm_sequence_base)::set(None, "top.agent.myseqr.main_phase",
    #  //|                                         "default_sequence",
    #  //|                                         myseq)
    #  //
    #  // Configuration by type is shorter and can be substituted via
    #  // the factory.
    #  //
    #  //| uvm_config_db #(uvm_object_wrapper)::set(None, "top.agent.myseqr.main_phase",
    #  //|                                          "default_sequence",
    #  //|                                          myseq_type::type_id::get())
    #  //
    #  // The uvm_resource_db can similarly be used.
    #  //
    #  //| myseq_t myseq = new("myseq")
    #  //| myseq.randomize() with { ... }
    #  //| uvm_resource_db #(uvm_sequence_base)::set({get_full_name(), ".myseqr.main_phase",
    #  //|                                           "default_sequence",
    #  //|                                           myseq, this)
    #  //
    #  //| uvm_resource_db #(uvm_object_wrapper)::set({get_full_name(), ".myseqr.main_phase",
    #  //|                                            "default_sequence",
    #  //|                                            myseq_t::type_id::get(),
    #  //|                                            this )
    #  //
    #  //
    #
    #  extern virtual function void start_phase_sequence(uvm_phase phase)
    @cocotb.coroutine
    def start_phase_sequence(self, phase):
        rp = UVMResourcePool.get()  # uvm_resource_pool
        rq = []  # uvm_resource_types::rsrc_q_t
        seq = None  # uvm_sequence_base
        from ..base.uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        f = cs.get_factory()  # uvm_factory

        # Has a default sequence been specified?
        rq = rp.lookup_name(self.get_full_name() + "." + phase.get_name() + "_phase",
                "default_sequence", None, 0)
        rq = UVMResourcePool.sort_by_precedence(rq)

        # Look for the first one if the appropriate type
        #for (int i = 0; seq is None && i < rq.size(); i++):
        for i in range(len(rq)):
            if seq is not None:
                break
            rsrc = rq.get(i)  # uvm_resource_base
            sbr = []  # uvm_resource#(uvm_sequence_base)
            owr = []  # uvm_resource#(uvm_object_wrapper)

            # uvm_config_db#(uvm_sequence_base)?
            # Priority is given to uvm_sequence_base because it is a specific sequence instance
            # and thus more specific than one that is dynamically created via the
            # factory and the object wrapper.
            if (sv.cast(sbr, rsrc, UVMConfigDb) and sbr[0] is not None):
                seq = sbr.read(self)
                if seq is None:
                    uvm_info("UVM/SQR/PH/DEF/SB/None", "Default phase sequence for phase '"
                            + phase.get_name() + "' explicitly disabled", UVM_FULL)
                    yield Timer(0, "NS")
                    return

            # uvm_config_db#(uvm_object_wrapper)?
            elif (sv.cast(owr, rsrc, UVMConfigDb) and owr is not None):
                wrapper = None  # uvm_object_wrapper
                wrapper = owr.read(self)
                if wrapper is None:
                    uvm_info("UVM/SQR/PH/DEF/OW/None", "Default phase sequence for phase '"
                            + phase.get_name() + "' explicitly disabled", UVM_FULL)
                    yield Timer(0, "NS")
                    return

                new_obj = f.create_object_by_type(wrapper, self.get_full_name(),
                        wrapper.get_type_name())
                seq_arr = []
                if not(sv.cast(seq_arr, new_obj, UVMSequence) or seq_arr[0] is None):
                    uvm_warning("PHASESEQ", "Default sequence for phase '" +
                            phase.get_name() + "' %s is not a sequence type")
                    yield Timer(0, "NS")
                    return
                else:
                    seq = seq_arr[0]

        if seq is None:
            uvm_info("PHASESEQ", "No default phase sequence for phase '"
                    + phase.get_name() + "'", UVM_FULL)
            yield Timer(0, "NS")
            return

        uvm_info("PHASESEQ", "Starting default sequence '" + seq.get_type_name()
                + "' for phase '" + phase.get_name() + "'", UVM_FULL)

        seq.print_sequence_info = 1
        seq.set_sequencer(self)
        seq.reseed()
        seq.set_starting_phase(phase)

        if (seq.do_not_randomize is False and seq.randomize() is False):
            uvm_warning("STRDEFSEQ", "Randomization failed for default sequence '"
                    + seq.get_type_name() + "' for phase '" + phase.get_name() + "'")
            yield Timer(0, "NS")
            return

        cocotb.fork(self.c_seq_fork_proc(seq, phase))
        #endfunction

    @cocotb.coroutine
    def _seq_fork_proc(self, seq, phase):
        #fork begin TODO this section incomplete
        w = uvm_sequence_process_wrapper()
        # reseed this process for random stability
        # w.pid = process::self()
        w.seq = seq
        # w.pid.srandom(uvm_create_random_seed(seq.get_type_name(), self.get_full_name()))
        self.m_default_sequences[phase] = w
        # this will either complete naturally, or be killed later
        yield seq.start(self)
        self.m_default_sequences.delete(phase)
        #join_none


    #
    #  // Function: stop_phase_sequence
    #  //
    #  // Stop the default sequence for this phase, if any exists, and it
    #  // is still executing.
    #
    #function void uvm_sequencer_base::stop_phase_sequence(uvm_phase phase)
    def stop_phase_sequence(self, phase):
        if self.m_default_sequences.exists(phase):
            uvm_info("PHASESEQ",
                      ("Killing default sequence '" +
                      self.m_default_sequences[phase].seq.get_type_name() +
                       "' for phase '" + phase.get_name() + "'"), UVM_FULL)
            self.m_default_sequences[phase].seq.kill()
        else:
            uvm_info("PHASESEQ", ("No default sequence to kill for phase '" + phase.get_name() + "'"),
                UVM_FULL)



    #  // Task: wait_for_grant
    #  //
    #  // This task issues a request for the specified sequence.  If item_priority
    #  // is not specified, then the current sequence priority will be used by the
    #  // arbiter.  If a lock_request is made, then the  sequencer will issue a lock
    #  // immediately before granting the sequence.  (Note that the lock may be
    #  // granted without the sequence being granted if is_relevant is not asserted).
    #  //
    #  // When this method returns, the sequencer has granted the sequence, and the
    #  // sequence must call send_request without inserting any simulation delay
    #  // other than delta cycles.  The driver is currently waiting for the next
    #  // item to be sent via the send_request call.
    #
    #  extern virtual task wait_for_grant(uvm_sequence_base sequence_ptr,
    #                                     int item_priority = -1,
    #                                     bit lock_request = 0)
    @cocotb.coroutine
    def wait_for_grant(self, sequence_ptr, item_priority=-1, lock_request=0):
        req_s = None  # uvm_sequence_request
        my_seq_id = 0

        if sequence_ptr is None:
            self.uvm_report_fatal("uvm_sequencer",
                "wait_for_grant passed None sequence_ptr", UVM_NONE)

        my_seq_id = self.m_register_sequence(sequence_ptr)

        # If lock_request is asserted, then issue a lock.  Don't wait for the response, since
        # there is a request immediately following the lock request
        if (lock_request == 1):
            req_s = uvm_sequence_request()
            req_s.grant = 0
            req_s.sequence_id = my_seq_id
            req_s.request = SEQ_TYPE_LOCK
            req_s.sequence_ptr = sequence_ptr
            req_s.request_id = UVMSequencerBase.g_request_id
            UVMSequencerBase.g_request_id += 1
            # TODO req_s.process_id = process::self()
            self.arb_sequence_q.push_back(req_s)

        # Push the request onto the queue
        req_s = uvm_sequence_request()
        req_s.grant = 0
        req_s.request = SEQ_TYPE_REQ
        req_s.sequence_id = my_seq_id
        req_s.item_priority = item_priority
        req_s.sequence_ptr = sequence_ptr
        req_s.request_id = UVMSequencerBase.g_request_id
        UVMSequencerBase.g_request_id += 1
        # TODO req_s.process_id = process::self()
        self.arb_sequence_q.push_back(req_s)
        self.m_update_lists()

        # Wait until this entry is granted
        # Continue to point to the element, since location in queue will change
        yield self.m_wait_for_arbitration_completed(req_s.request_id)

        # The wait_for_grant_semaphore is used only to check that send_request
        # is only called after wait_for_grant.  This is not a complete check, since
        # requests might be done in parallel, but it will catch basic errors
        req_s.sequence_ptr.m_wait_for_grant_semaphore += 1
        #endtask

    #
    #  // Task: wait_for_item_done
    #  //
    #  // A sequence may optionally call wait_for_item_done.  This task will block
    #  // until the driver calls item_done() or put() on a transaction issued by the
    #  // specified sequence.  If no transaction_id parameter is specified, then the
    #  // call will return the next time that the driver calls item_done() or put().
    #  // If a specific transaction_id is specified, then the call will only return
    #  // when the driver indicates that it has completed that specific item.
    #  //
    #  // Note that if a specific transaction_id has been specified, and the driver
    #  // has already issued an item_done or put for that transaction, then the call
    #  // will hang waiting for that specific transaction_id.
    #  //
    #  extern virtual task wait_for_item_done(uvm_sequence_base sequence_ptr,
    #                                         int transaction_id)
    @cocotb.coroutine
    def wait_for_item_done(self, sequence_ptr, transaction_id):
        sequence_id = sequence_ptr.m_get_sqr_sequence_id(self.m_sequencer_id, 1)
        self.m_wait_for_item_sequence_id = -1
        self.m_wait_for_item_transaction_id = -1

        if (transaction_id == -1):
            #wait (m_wait_for_item_sequence_id == sequence_id)
            while True:
                self.m_event_value_changed.clear()
                yield self.m_event_value_changed.wait()
                if self.m_wait_for_item_sequence_id == sequence_id:
                    break
        else:
            # wait ((m_wait_for_item_sequence_id == sequence_id &&
            #        m_wait_for_item_transaction_id == transaction_id))
            while True:
                self.m_event_value_changed.clear()
                yield self.m_event_value_changed.wait()
                if ((self.m_wait_for_item_sequence_id == sequence_id and
                    self.m_wait_for_item_transaction_id == transaction_id)):
                    break

    #  // Function: is_blocked
    #  //
    #  // Returns 1 if the sequence referred to by sequence_ptr is currently locked
    #  // out of the sequencer.  It will return 0 if the sequence is currently
    #  // allowed to issue operations.
    #  //
    #  // Note that even when a sequence is not blocked, it is possible for another
    #  // sequence to issue a lock before this sequence is able to issue a request
    #  // or lock.
    #  //
    #  extern function bit is_blocked(uvm_sequence_base sequence_ptr)
    def is_blocked(self, sequence_ptr):
        if sequence_ptr is None:
            uvm_report_fatal("uvm_sequence_controller",
                           "self.is_blocked passed None sequence_ptr", UVM_NONE)

        #foreach (self.lock_list[i]):
        for i in range(len(self.lock_list)):
            if ((self.lock_list[i].get_inst_id() !=
                 sequence_ptr.get_inst_id()) and
                 (self.is_child(self.lock_list[i], sequence_ptr) == 0)):
                return 1
        return 0
        #endfunction

    #  // Function: has_lock
    #  //
    #  // Returns 1 if the sequence referred to in the parameter currently has a lock
    #  // on this sequencer, 0 otherwise.
    #  //
    #  // Note that even if this sequence has a lock, a child sequence may also have
    #  // a lock, in which case the sequence is still blocked from issuing
    #  // operations on the sequencer
    #  //
    #  extern function bit has_lock(uvm_sequence_base sequence_ptr)
    #
    #
    #  // Task: lock
    #  //
    #  // Requests a lock for the sequence specified by sequence_ptr.
    #  //
    #  // A lock request will be arbitrated the same as any other request. A lock is
    #  // granted after all earlier requests are completed and no other locks or
    #  // grabs are blocking this sequence.
    #  //
    #  // The lock call will return when the lock has been granted.
    #  //
    #  extern virtual task lock(uvm_sequence_base sequence_ptr)
    #
    #
    #  // Task: grab
    #  //
    #  // Requests a lock for the sequence specified by sequence_ptr.
    #  //
    #  // A grab request is put in front of the arbitration queue. It will be
    #  // arbitrated before any other requests. A grab is granted when no other
    #  // grabs or locks are blocking this sequence.
    #  //
    #  // The grab call will return when the grab has been granted.
    #  //
    #  extern virtual task grab(uvm_sequence_base sequence_ptr)
    #
    #
    #  // Function: unlock
    #  //
    #  // Removes any locks and grabs obtained by the specified sequence_ptr.
    #  //
    #  extern virtual function void unlock(uvm_sequence_base sequence_ptr)
    #
    #
    #  // Function: ungrab
    #  //
    #  // Removes any locks and grabs obtained by the specified sequence_ptr.
    #  //
    #  extern virtual function void  ungrab(uvm_sequence_base sequence_ptr)
    #
    #
    #  // Function: stop_sequences
    #  //
    #  // Tells the sequencer to kill all sequences and child sequences currently
    #  // operating on the sequencer, and remove all requests, locks and responses
    #  // that are currently queued.  This essentially resets the sequencer to an
    #  // idle state.
    #  //
    #  extern virtual function void stop_sequences()
    #
    #
    #  // Function: is_grabbed
    #  //
    #  // Returns 1 if any sequence currently has a lock or grab on this sequencer,
    #  // 0 otherwise.
    #  //
    #  extern virtual function bit is_grabbed()
    #
    #
    #  // Function: current_grabber
    #  //
    #  // Returns a reference to the sequence that currently has a lock or grab on
    #  // the sequence.  If multiple hierarchical sequences have a lock, it returns
    #  // the child that is currently allowed to perform operations on the sequencer.
    #  //
    #  extern virtual function uvm_sequence_base current_grabber()
    #
    #
    #  // Function: has_do_available
    #  //
    #  // Returns 1 if any sequence running on this sequencer is ready to supply a
    #  // transaction, 0 otherwise. A sequence is ready if it is not blocked (via
    #  // ~grab~ or ~lock~ and ~is_relevant~ returns 1.
    #  //
    #  extern virtual function bit has_do_available()
    #
    #
    #  // Function: set_arbitration
    #  //
    #  // Specifies the arbitration mode for the sequencer. It is one of
    #  //
    #  // UVM_SEQ_ARB_FIFO          - Requests are granted in FIFO order (default)
    #  // UVM_SEQ_ARB_WEIGHTED      - Requests are granted randomly by weight
    #  // UVM_SEQ_ARB_RANDOM        - Requests are granted randomly
    #  // UVM_SEQ_ARB_STRICT_FIFO   - Requests at highest priority granted in FIFO order
    #  // UVM_SEQ_ARB_STRICT_RANDOM - Requests at highest priority granted in randomly
    #  // UVM_SEQ_ARB_USER          - Arbitration is delegated to the user-defined
    #  //                             function, user_priority_arbitration. That function
    #  //                             will specify the next sequence to grant.
    #  //
    #  // The default user function specifies FIFO order.
    #  //
    #  extern function void set_arbitration(UVM_SEQ_ARB_TYPE val)
    #
    #
    #  // Function: get_arbitration
    #  //
    #  // Return the current arbitration mode set for this sequencer. See
    #  // <set_arbitration> for a list of possible modes.
    #  //
    #  extern function UVM_SEQ_ARB_TYPE get_arbitration()

    #  // Task: wait_for_sequences
    #  //
    #  // Waits for a sequence to have a new item available. Uses
    #  // <uvm_wait_for_nba_region> to give a sequence as much time as
    #  // possible to deliver an item before advancing time.
    #
    #  extern virtual task wait_for_sequences()
    #// ------------------
    @cocotb.coroutine
    def wait_for_sequences(self):
        yield uvm_wait_for_nba_region()

    #  // Function: send_request
    #  //
    #  // Derived classes implement this function to send a request item to the
    #  // sequencer, which will forward it to the driver.  If the rerandomize bit
    #  // is set, the item will be randomized before being sent to the driver.
    #  //
    #  // This function may only be called after a <wait_for_grant> call.
    #
    #  extern virtual function void send_request(uvm_sequence_base sequence_ptr,
    #                                            uvm_sequence_item t,
    #                                            bit rerandomize = 0)
    #
    #  // Function: set_max_zero_time_wait_relevant_count
    #  //
    #  // Can be called at any time to change the maximum number of times
    #  // wait_for_relevant() can be called by the sequencer in zero time before
    #  // an error is declared.  The default maximum is 10.
    #  extern virtual function void set_max_zero_time_wait_relevant_count(int new_val)
    #
    #
    #  //----------------------------------------------------------------------------
    #  // INTERNAL METHODS - DO NOT CALL DIRECTLY, ONLY OVERLOAD IF VIRTUAL
    #  //----------------------------------------------------------------------------

    #  extern protected function void grant_queued_locks()
    #// ------------------
    #// Any lock or grab requests that are at the front of the queue will be
    #// granted at the earliest possible time.  This function grants any queues
    #// at the front that are not locked out
    #
    def grant_queued_locks(self):
        #  first remove sequences with dead lock control process
        q = []  # uvm_sequence_request q[$]
        def find_with_func(item):
            return (item.request == SEQ_TYPE_LOCK and
                    item.process_id.status == process.KILLED or
                    item.process_id.status == process.FINISHED)
        q = self.arb_sequence_q.find_with(find_with_func)
                #item, [{request: SEQ_TYPE_LOCK}, {'process_id.status':
                #    [process::KILLED, process::FINISHED])
        for idx in range(len(q)):
            uvm_error("SEQLCKZMB", sv.sformatf(SEQ_ERR1_MSG, self.get_full_name(),
                q[idx].sequence_ptr.get_full_name()))
            self.remove_sequence_from_queues(q[idx].sequence_ptr)

        # now move all self.is_blocked() into self.lock_list
        # uvm_sequence_request leading_lock_reqs[$],blocked_seqs[$],not_blocked_seqs[$];
        leading_lock_reqs = UVMQueue()
        blocked_seqs = UVMQueue()
        not_blocked_seqs = UVMQueue()

        # Dodgy region, original code very confusing
        b: int = self.arb_sequence_q.size()  # index for first non-LOCK request
        def find_func(item):
            return item.request != SEQ_TYPE_LOCK
        idx = self.arb_sequence_q.find_first_index(find_func)
        if idx >= 0:
            b = idx

        if b != 0:  # at least one lock
            # set of locks; arb_sequence[b] is the first req!=SEQ_TYPE_LOCK
            leading_lock_reqs = self.arb_sequence_q[0:b-1]
            # split into blocked/not-blocked requests
            for i in range(len(leading_lock_reqs)):
                item: uvm_sequence_request = leading_lock_reqs[i]
                if self.is_blocked(item.sequence_ptr) != 0:
                    blocked_seqs.push_back(item)
                else:
                    not_blocked_seqs.push_back(item)

            if b > (self.arb_sequence_q.size()-1):
                self.arb_sequence_q = blocked_seqs
            else:
                self.arb_sequence_q = {blocked_seqs,self.arb_sequence_q[b:self.arb_sequence_q.size()-1]}

            for idx in range(len(not_blocked_seqs)):
                self.lock_list.push_back(not_blocked_seqs[idx].sequence_ptr);
                self.m_set_arbitration_completed(not_blocked_seqs[idx].request_id)

            # trigger listeners if lock list has changed
            if(not_blocked_seqs.size()):
                self.m_update_lists()

    #  extern protected task          m_select_sequence()
    @cocotb.coroutine
    def m_select_sequence(self):
        selected_sequence = 0

        # Select a sequence
        while True:
            yield self.wait_for_sequences()
            selected_sequence = self.m_choose_next_request()
            if selected_sequence == -1:
                yield self.m_wait_for_available_sequence()
            if selected_sequence != -1:
                break
            #end while (selected_sequence == -1)

        # issue grant
        if selected_sequence >= 0:
            self.m_set_arbitration_completed(self.arb_sequence_q[selected_sequence].request_id)
            self.arb_sequence_q.delete(selected_sequence)
            self.m_update_lists()
    #endtask
    #

    #  extern protected function int  m_choose_next_request()
    #// When a driver requests an operation, this function must find the next
    #// available, unlocked, relevant sequence.
    #//
    #// This function returns -1 if no sequences are available or the entry into
    #// self.arb_sequence_q for the chosen sequence
    def m_choose_next_request(self) -> int:
        i = 0  #  int i, temp
        temp = 0
        avail_sequence_count: int = 0  # int avail_sequence_count
        sum_priority_val: int = 0  # int sum_priority_val
        avail_sequences: UVMQueue = UVMQueue()  # integer [$]
        highest_sequences:UVMQueue = UVMQueue()  # integer [$]
        highest_pri: int = 0  # int highest_pri
        s: str = ""  # string s

        self.grant_queued_locks()
        i = 0
        while i < self.arb_sequence_q.size():
            if ((self.arb_sequence_q[i].process_id.status == process.KILLED) or
                    (self.arb_sequence_q[i].process_id.status == process.FINISHED)):
                uvm_error("SEQREQZMB", sv.sformatf(SEQ_ERR2_MSG, self.get_full_name(),
                   self.arb_sequence_q[i].sequence_ptr.get_full_name()))
                self.remove_sequence_from_queues(self.arb_sequence_q[i].sequence_ptr)
                continue

            if i < self.arb_sequence_q.size():
                if self.arb_sequence_q[i].request == SEQ_TYPE_REQ:
                    if (self.is_blocked(self.arb_sequence_q[i].sequence_ptr) == 0):
                        if self.arb_sequence_q[i].sequence_ptr.is_relevant() == 1:
                            if (self.m_arbitration == UVM_SEQ_ARB_FIFO):
                                return i
                            else:
                                avail_sequences.push_back(i)
            i += 1

        # Return immediately if there are 0 or 1 available sequences
        if (self.m_arbitration == UVM_SEQ_ARB_FIFO):
            return -1
        if (avail_sequences.size() < 1):
            return -1

        if (avail_sequences.size() == 1):
            return avail_sequences[0]

        # If any locks are in place, then the available queue must
        # be checked to see if a lock prevents any sequence from proceeding
        if (self.lock_list.size() > 0):
            for i in range(len(avail_sequences)):
                if self.is_blocked(self.arb_sequence_q[avail_sequences[i]].sequence_ptr) != 0:
                    avail_sequences.delete(i)
                    i -= 1
            if (avail_sequences.size() < 1):
                return -1
            if (avail_sequences.size() == 1):
                return avail_sequences[0]

    #
    #  //  Weighted Priority Distribution
    #  // Pick an available sequence based on weighted priorities of available sequences
    #  if (self.m_arbitration == UVM_SEQ_ARB_WEIGHTED):
    #    sum_priority_val = 0
    #    for (i = 0; i < avail_sequences.size(); i++):
    #      sum_priority_val += m_get_seq_item_priority(self.arb_sequence_q[avail_sequences[i]])
    #    end
    #
    #    temp = $urandom_range(sum_priority_val-1, 0)
    #
    #    sum_priority_val = 0
    #    for (i = 0; i < avail_sequences.size(); i++):
    #      if ((m_get_seq_item_priority(self.arb_sequence_q[avail_sequences[i]]) +
    #           sum_priority_val) > temp):
    #        return avail_sequences[i]
    #      end
    #      sum_priority_val += m_get_seq_item_priority(self.arb_sequence_q[avail_sequences[i]])
    #    end
    #    uvm_report_fatal("Sequencer", "UVM Internal error in weighted arbitration code", UVM_NONE)
    #  end
    #
    #  //  Random Distribution
    #  if (self.m_arbitration == UVM_SEQ_ARB_RANDOM):
    #    i = $urandom_range(avail_sequences.size()-1, 0)
    #    return avail_sequences[i]
    #  end
    #
    #  //  Strict Fifo
    #  if ((self.m_arbitration == UVM_SEQ_ARB_STRICT_FIFO) || self.m_arbitration == UVM_SEQ_ARB_STRICT_RANDOM):
    #    highest_pri = 0
    #    // Build a list of sequences at the highest priority
    #    for (i = 0; i < avail_sequences.size(); i++):
    #      if (m_get_seq_item_priority(self.arb_sequence_q[avail_sequences[i]]) > highest_pri):
    #        // New highest priority, so start new list
    #        highest_sequences.delete()
    #        highest_sequences.push_back(avail_sequences[i])
    #        highest_pri = m_get_seq_item_priority(self.arb_sequence_q[avail_sequences[i]])
    #      end
    #      else if (m_get_seq_item_priority(self.arb_sequence_q[avail_sequences[i]]) == highest_pri):
    #        highest_sequences.push_back(avail_sequences[i])
    #      end
    #    end
    #
    #    // Now choose one based on arbitration type
    #    if (self.m_arbitration == UVM_SEQ_ARB_STRICT_FIFO):
    #      return(highest_sequences[0])
    #    end
    #
    #    i = $urandom_range(highest_sequences.size()-1, 0)
    #    return highest_sequences[i]
    #  end
    #
    #  if (self.m_arbitration == UVM_SEQ_ARB_USER):
    #    i = user_priority_arbitration( avail_sequences)
    #
    #    // Check that the returned sequence is in the list of available sequences.  Failure to
    #    // use an available sequence will cause highly unpredictable results.
    #    highest_sequences = avail_sequences.find with (item == i)
    #    if (highest_sequences.size() == 0):
    #      uvm_report_fatal("Sequencer",
    #          $sformatf("Error in User arbitration, sequence %0d not available\n%s",
    #                    i, convert2string()), UVM_NONE)
    #    end
    #    return(i)
    #  end
    #
    #  uvm_report_fatal("Sequencer", "Internal error: Failed to choose sequence", UVM_NONE)
    #
    #endfunction

    #  extern           task          m_wait_for_arbitration_completed(int request_id)
    @cocotb.coroutine
    def m_wait_for_arbitration_completed(self, request_id):
        lock_arb_size = 0

        # Search the list of arb_wait_q, see if this item is done
        while True:
            lock_arb_size  = self.m_lock_arb_size

            if self.arb_completed.exists(request_id):
                self.arb_completed.delete(request_id)
                return
            self.m_event_value_changed.clear()
            evt = self.m_event_value_changed.wait()
            yield evt
            if lock_arb_size != self.m_lock_arb_size:
                break
        #endtask
        #

    #  extern           function void m_set_arbitration_completed(int request_id)
    def m_set_arbitration_completed(self, request_id):
        self.arb_completed[request_id] = 1

    #
    #
    #  extern local task m_lock_req(uvm_sequence_base sequence_ptr, bit lock)
    #
    #
    #  // Task- m_unlock_req
    #  //
    #  // Called by a sequence to request an unlock.  This
    #  // will remove a lock for this sequence if it exists
    #
    #  extern function void m_unlock_req(uvm_sequence_base sequence_ptr)
    #
    #

    #  extern local function void remove_sequence_from_queues(uvm_sequence_base sequence_ptr)
    def remove_sequence_from_queues(self, sequence_ptr):
        i = 0
        seq_id = sequence_ptr.m_get_sqr_sequence_id(self.m_sequencer_id, 0)

        # Remove all queued items for this sequence and any child sequences
        while (True):
            if (self.arb_sequence_q.size() > i):
                if ((self.arb_sequence_q[i].sequence_id == seq_id) or
                      (self.is_child(sequence_ptr, self.arb_sequence_q[i].sequence_ptr))):
                    if (sequence_ptr.get_sequence_state() == UVM_FINISHED):
                        uvm_error("SEQFINERR", sv.sformatf(SEQ_ERR3_MSG, sequence_ptr.get_full_name(),
                            self.arb_sequence_q[i].sequence_ptr.get_full_name()))
                    self.arb_sequence_q.delete(i)
                    self.m_update_lists()
                else:
                  i += 1
            if not (i < self.arb_sequence_q.size()):
                break

        # remove locks for this sequence, and any child sequences
        i = 0
        while (True):
            if self.lock_list.size() > i:
                if ((self.lock_list[i].get_inst_id() == sequence_ptr.get_inst_id()) or
                        (self.is_child(sequence_ptr, self.lock_list[i]))):
                    if (sequence_ptr.get_sequence_state() == UVM_FINISHED):
                        uvm_error("SEQFINERR", sv.sformatf(SEQ_ERR4_MSG,sequence_ptr.get_full_name(),
                            self.lock_list[i].get_full_name()))
                    self.lock_list.delete(i)
                    self.m_update_lists()
                else:
                  i += 1
            if not (i < self.lock_list.size()):
                break

        # Unregister the sequence_id, so that any returning data is dropped
        self.m_unregister_sequence(sequence_ptr.m_get_sqr_sequence_id(self.m_sequencer_id, 1))

    #  extern function void m_sequence_exiting(uvm_sequence_base sequence_ptr)
    def m_sequence_exiting(self, sequence_ptr):
        self.remove_sequence_from_queues(sequence_ptr)

    #  extern function void kill_sequence(uvm_sequence_base sequence_ptr)
    #
    #  extern virtual function void analysis_write(uvm_sequence_item t)
    #
    #
    #  extern virtual   function void   build()
    #  extern virtual   function void   build_phase(uvm_phase phase)
    def build(self):
        dummy = 0
        UVMComponent.build(self)

    #  extern           function void   do_print (uvm_printer printer)
    #
    #

    #  extern virtual   function int    m_register_sequence(uvm_sequence_base sequence_ptr)
    def m_register_sequence(self, sequence_ptr):
        if sequence_ptr.m_get_sqr_sequence_id(self.m_sequencer_id, 1) > 0:
            return sequence_ptr.get_sequence_id()

        sequence_ptr.m_set_sqr_sequence_id(self.m_sequencer_id, UVMSequencerBase.g_sequence_id)
        UVMSequencerBase.g_sequence_id += 1
        self.reg_sequences[sequence_ptr.get_sequence_id()] = sequence_ptr
        return sequence_ptr.get_sequence_id()
    #endfunction

    # virtual function void   m_unregister_sequence(int sequence_id)
    def m_unregister_sequence(self, sequence_id):
        if not (self.reg_sequences.exists(sequence_id)):
            return
        self.reg_sequences.delete(sequence_id)

    # function uvm_sequence_base m_find_sequence(int sequence_id)
    def m_find_sequence(self, sequence_id):
        #seq_ptr = None  # #  uvm_sequence_base

        # When sequence_id is -1, return the first available sequence.  This is used
        # when deleting all sequences
        if (sequence_id == -1):
            if self.reg_sequences.has_first():
                return self.reg_sequences.first()
            return None

        if not self.reg_sequences.exists(sequence_id):
            return None
        return self.reg_sequences[sequence_id]

    #  extern protected function void   self.m_update_lists()
    def m_update_lists(self):
        self.set_value('m_lock_arb_size', self.m_lock_arb_size + 1)

    #  extern           function string convert2string()
    #  extern protected
    #           virtual function int    m_find_number_driver_connections()

    def set_value(self, key, value):
        setattr(self, key, value)
        self.m_event_value_changed.set()

    #  extern protected task            m_wait_arb_not_equal()
    @cocotb.coroutine
    def m_wait_arb_not_equal(self):
        while (True):
            self.m_event_value_changed.clear()
            yield self.m_event_value_changed.wait()
            if self.m_arb_size != self.m_lock_arb_size:
                break

    #  extern protected task            m_wait_for_available_sequence()
    @cocotb.coroutine
    def m_wait_for_available_sequence(self):
        i = 0
        is_relevant_entries: List[int] = []  # int[$]

        # This routine will wait for a change in the request list, or for
        # wait_for_relevant to return on any non-relevant, non-blocked sequence
        self.set_value('m_arb_size', self.m_lock_arb_size)

        for i in range(len(self.arb_sequence_q)):
            if (self.arb_sequence_q[i].request == SEQ_TYPE_REQ):
                if (self.is_blocked(self.arb_sequence_q[i].sequence_ptr) == 0):
                    if (self.arb_sequence_q[i].sequence_ptr.is_relevant() == 0):
                        is_relevant_entries.append(i)

        # Typical path - don't need fork if all queued entries are relevant
        if (len(is_relevant_entries) == 0):
            yield self.m_wait_arb_not_equal()
            return

        #fork // isolate inner fork block for disabling
        fork_first = cocotb.fork(self._fork_first_proc(is_relevant_entries))
        yield fork_first
        #join

    @cocotb.coroutine
    def _rel_entry_fork_proc(self, i, is_relevant_entries):
        k = i
        yield self.arb_sequence_q[is_relevant_entries[k]].sequence_ptr.wait_for_relevant()
        if sv.realtime() != self.m_last_wait_relevant_time:
            self.m_last_wait_relevant_time = sv.realtime()
            self.m_wait_relevant_count = 0
        else:
            self.m_wait_relevant_count += 1
            if self.m_wait_relevant_count > self.m_max_zero_time_wait_relevant_count:
                uvm_fatal("SEQRELEVANTLOOP",sv.sformatf(SEQ_FATAL1_MSG, self.m_wait_relevant_count))
        #self.m_is_relevant_completed = 1
        self.set_value('m_is_relevant_completed', True)

    @cocotb.coroutine
    def _fork_first_proc(self, is_relevant_entries):
        started_forks = []
        #fork
        forked_proc1 = cocotb.fork(self._fork_first_proc_sub_fork1(is_relevant_entries))
        started_forks.append(forked_proc1)
        # The other path in the fork is for any queue entry to change
        forked_proc2 = self.m_wait_arb_not_equal()
        started_forks.append(forked_proc2)
        yield started_forks  # join_any
        # disable fork
        for p in started_forks:
            p.kill()

    @cocotb.coroutine
    def _fork_first_proc_sub_fork1(self, is_relevant_entries):
        # One path in fork is for any wait_for_relevant to return
        fork_procs_join_none = []
        self.set_value('m_is_relevant_completed', False)
        for i in range(len(is_relevant_entries)):
            #fork
            forked_proc = cocotb.fork(self._rel_entry_fork_proc(i, is_relevant_entries))
            fork_procs_join_none.append(forked_proc)
            #join_none
        yield self.wait_is_relevant_completed()

    @cocotb.coroutine
    def wait_is_relevant_completed(self):
        yield Timer(0)
        # TODO
        while True:
            self.m_event_value_changed.clear()
            yield self.m_event_value_changed.wait()
            if self.m_is_relevant_completed > 0:
                break

    #  extern protected function int    m_get_seq_item_priority(uvm_sequence_request seq_q_entry)
    #
    #  int m_is_relevant_completed
    #
    #
    #`ifdef UVM_DISABLE_AUTO_ITEM_RECORDING
    #  local bit m_auto_item_recording = 0
    #`else
    #  local bit m_auto_item_recording = 1
    #`endif
    #
    #
    #  // Access to following internal methods provided via seq_item_export
    #
    #  virtual function void disable_auto_item_recording()
    #    m_auto_item_recording = 0
    #  endfunction

    def is_auto_item_recording_enabled(self):
        return self.m_auto_item_recording

    #  //----------------------------------------------------------------------------
    #  // DEPRECATED - DO NOT USE IN NEW DESIGNS - NOT PART OF UVM STANDARD
    #  //----------------------------------------------------------------------------
    #
    #`ifndef UVM_NO_DEPRECATED
    #  // Variable- count
    #  //
    #  // Sets the number of items to execute.
    #  //
    #  // Supercedes the max_random_count variable for uvm_random_sequence class
    #  // for backward compatibility.
    #
    #  int count = -1
    #
    #  int m_random_count
    #  int m_exhaustive_count
    #  int m_simple_count
    #
    #  int unsigned max_random_count = 10
    #  int unsigned max_random_depth = 4
    #
    #  protected string default_sequence = "uvm_random_sequence"
    #  protected bit m_default_seq_set
    #
    #
    #  string sequences[$]
    #  protected int sequence_ids[string]
    #  protected rand int seq_kind
    #
    #  extern function void              add_sequence(string type_name)
    #  extern function void              remove_sequence(string type_name)
    #  extern function void              set_sequences_queue(ref string sequencer_sequence_lib[$])
    #  extern virtual task               start_default_sequence()
    #  extern function int               get_seq_kind(string type_name)
    #  extern function uvm_sequence_base get_sequence(int req_kind)
    #  extern function int               num_sequences()
    #  extern virtual function void      m_add_builtin_seqs(bit add_simple = 1)
    #  extern virtual task               run_phase(uvm_phase phase)
    #`endif
    #
    #endclass
#
#
#
#
#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#// build_phase
#// -----------
#
#function void uvm_sequencer_base::build_phase(uvm_phase phase)
#  // For mantis 3402, the config stuff must be done in the deprecated
#  // build() phase in order for a manual build call to work. Both
#  // the manual build call and the config settings in build() are
#  // deprecated.
#  super.build_phase(phase)
#endfunction
#
#
#
#// do_print
#// --------
#
#function void uvm_sequencer_base::do_print (uvm_printer printer)
#  super.do_print(printer)
#  printer.print_array_header("arbitration_queue", self.arb_sequence_q.size())
#  foreach (self.arb_sequence_q[i])
#    printer.print_string($sformatf("[%0d]", i),
#       $sformatf("%s@seqid%0d",self.arb_sequence_q[i].request.name(),self.arb_sequence_q[i].sequence_id), "[")
#  printer.print_array_footer(self.arb_sequence_q.size())
#
#  printer.print_array_header("lock_queue", self.lock_list.size())
#  foreach(self.lock_list[i])
#    printer.print_string($sformatf("[%0d]", i),
#       $sformatf("%s@seqid%0d",self.lock_list[i].get_full_name(),self.lock_list[i].get_sequence_id()), "[")
#  printer.print_array_footer(self.lock_list.size())
#endfunction
#
#
#
#// convert2string
#// ----------------
#
#function string uvm_sequencer_base::convert2string()
#  string s
#
#  $sformat(s, "  -- arb i/id/type: ")
#  foreach (self.arb_sequence_q[i]):
#    $sformat(s, "%s %0d/%0d/%s ", s, i, self.arb_sequence_q[i].sequence_id, self.arb_sequence_q[i].request.name())
#  end
#  $sformat(s, "%s\n -- self.lock_list i/id: ", s)
#  foreach (self.lock_list[i]):
#    $sformat(s, "%s %0d/%0d",s, i, self.lock_list[i].get_sequence_id())
#  end
#  return(s)
#endfunction
#
#
#
#// m_find_number_driver_connections
#// --------------------------------
#
#function int  uvm_sequencer_base::m_find_number_driver_connections()
#  return 0
#endfunction
#
#
#
#
#
#
#
#// user_priority_arbitration
#// -------------------------
#
#function integer uvm_sequencer_base::user_priority_arbitration(integer avail_sequences[$])
#  return avail_sequences[0]
#endfunction
#
#
#// m_get_seq_item_priority
#// -----------------------
#
#function int uvm_sequencer_base::m_get_seq_item_priority(uvm_sequence_request seq_q_entry)
#  // If the priority was set on the item, then that is used
#  if (seq_q_entry.item_priority != -1):
#    if (seq_q_entry.item_priority <= 0):
#      uvm_report_fatal("SEQITEMPRI",
#                    $sformatf("Sequence item from %s has illegal priority: %0d",
#                            seq_q_entry.sequence_ptr.get_full_name(),
#                            seq_q_entry.item_priority), UVM_NONE)
#    end
#    return seq_q_entry.item_priority
#  end
#  // Otherwise, use the priority of the calling sequence
#  if (seq_q_entry.sequence_ptr.get_priority() < 0):
#    uvm_report_fatal("SEQDEFPRI",
#                    $sformatf("Sequence %s has illegal priority: %0d",
#                            seq_q_entry.sequence_ptr.get_full_name(),
#                            seq_q_entry.sequence_ptr.get_priority()), UVM_NONE)
#  end
#  return seq_q_entry.sequence_ptr.get_priority()
#endfunction
#
#
#
#
#
#
#
#// execute_item
#// ------------
#
#task uvm_sequencer_base::execute_item(uvm_sequence_item item)
#  uvm_sequence_base seq
#
#  seq = new()
#  item.set_sequencer(this)
#  item.set_parent_sequence(seq)
#  seq.set_sequencer(this)
#  seq.start_item(item)
#  seq.finish_item(item)
#endtask
#
#
#
#
#
#
#// has_lock
#// --------
#
#function bit uvm_sequencer_base::has_lock(uvm_sequence_base sequence_ptr)
#  int my_seq_id
#
#  if (sequence_ptr is None)
#    uvm_report_fatal("uvm_sequence_controller",
#                     "has_lock passed None sequence_ptr", UVM_NONE)
#  my_seq_id = m_register_sequence(sequence_ptr)
#    foreach (self.lock_list[i]):
#      if (self.lock_list[i].get_inst_id() == sequence_ptr.get_inst_id()):
#        return 1
#      end
#    end
#  return 0
#endfunction
#
#
#// m_lock_req
#// ----------
#// Internal method. Called by a sequence to request a lock.
#// Puts the lock request onto the arbitration queue.
#
#task uvm_sequencer_base::m_lock_req(uvm_sequence_base sequence_ptr, bit lock)
#  int my_seq_id
#  uvm_sequence_request new_req
#
#  if (sequence_ptr is None)
#    uvm_report_fatal("uvm_sequence_controller",
#                     "lock_req passed None sequence_ptr", UVM_NONE)
#
#  my_seq_id = m_register_sequence(sequence_ptr)
#  new_req = new()
#  new_req.grant = 0
#  new_req.sequence_id = sequence_ptr.get_sequence_id()
#  new_req.request = SEQ_TYPE_LOCK
#  new_req.sequence_ptr = sequence_ptr
#  new_req.request_id = g_request_id++
#  new_req.process_id = process::self()
#
#  if (lock == 1):
#    // Locks are arbitrated just like all other requests
#    self.arb_sequence_q.push_back(new_req)
#  end else begin
#    // Grabs are not arbitrated - they go to the front
#    // TODO:
#    // Missing: grabs get arbitrated behind other grabs
#    self.arb_sequence_q.push_front(new_req)
#    self.m_update_lists()
#  end
#
#  // If this lock can be granted immediately, then do so.
#  grant_queued_locks()
#
#  m_wait_for_arbitration_completed(new_req.request_id)
#endtask
#
#
#// m_unlock_req
#// ------------
#// Called by a sequence to request an unlock.  This
#// will remove a lock for this sequence if it exists
#
#function void uvm_sequencer_base::m_unlock_req(uvm_sequence_base sequence_ptr)
#  if (sequence_ptr is None):
#    uvm_report_fatal("uvm_sequencer",
#                     "m_unlock_req passed None sequence_ptr", UVM_NONE)
#  end
#
#  begin
#      int q[$]
#      int seqid=sequence_ptr.get_inst_id()
#      q=self.lock_list.find_first_index(item) with (item.get_inst_id() == seqid)
#      if(q.size()==1):
#          self.lock_list.delete(q[0])
#          grant_queued_locks(); // grant lock requests
#          self.m_update_lists();
#      end
#      else
#          uvm_report_warning("SQRUNL",
#           {"Sequence '", sequence_ptr.get_full_name(),
#            "' called ungrab / unlock, but didn't have lock"}, UVM_NONE);
#
#  end
#endfunction
#
#
#// lock
#// ----
#
#task uvm_sequencer_base::lock(uvm_sequence_base sequence_ptr)
#  m_lock_req(sequence_ptr, 1)
#endtask
#
#
#// grab
#// ----
#
#task uvm_sequencer_base::grab(uvm_sequence_base sequence_ptr)
#  m_lock_req(sequence_ptr, 0)
#endtask
#
#
#// unlock
#// ------
#
#function void uvm_sequencer_base::unlock(uvm_sequence_base sequence_ptr)
#  m_unlock_req(sequence_ptr)
#endfunction
#
#
#// ungrab
#// ------
#
#function void  uvm_sequencer_base::ungrab(uvm_sequence_base sequence_ptr)
#  m_unlock_req(sequence_ptr)
#endfunction
#
#
#
#
#// stop_sequences
#// --------------
#
#function void uvm_sequencer_base::stop_sequences()
#  uvm_sequence_base seq_ptr
#
#  seq_ptr = m_find_sequence(-1)
#  while (seq_ptr is not None)
#    begin
#      kill_sequence(seq_ptr)
#      seq_ptr = m_find_sequence(-1)
#    end
#endfunction
#
#
#
#// kill_sequence
#// -------------
#
#function void uvm_sequencer_base::kill_sequence(uvm_sequence_base sequence_ptr)
#  remove_sequence_from_queues(sequence_ptr)
#  sequence_ptr.m_kill()
#endfunction
#
#
#// is_grabbed
#// ----------
#
#function bit uvm_sequencer_base::is_grabbed()
#  return (self.lock_list.size() != 0)
#endfunction
#
#
#// current_grabber
#// ---------------
#
#function uvm_sequence_base uvm_sequencer_base::current_grabber()
#  if (self.lock_list.size() == 0):
#    return None
#  end
#  return self.lock_list[self.lock_list.size()-1]
#endfunction
#
#
#// has_do_available
#// ----------------
#
#function bit uvm_sequencer_base::has_do_available()
#
#  foreach (self.arb_sequence_q[i]):
#    if ((self.arb_sequence_q[i].sequence_ptr.is_relevant() == 1) &&
#        (self.is_blocked(self.arb_sequence_q[i].sequence_ptr) == 0)):
#      return 1
#    end
#  end
#  return 0
#endfunction
#
#
#// set_arbitration
#// ---------------
#
#function void uvm_sequencer_base::set_arbitration(UVM_SEQ_ARB_TYPE val)
#  self.m_arbitration = val
#endfunction
#
#
#// get_arbitration
#// ---------------
#
#function UVM_SEQ_ARB_TYPE uvm_sequencer_base::get_arbitration()
#  return self.m_arbitration
#endfunction
#
#
#// analysis_write
#// --------------
#
#function void uvm_sequencer_base::analysis_write(uvm_sequence_item t)
#  return
#endfunction
#
#
#
#// send_request
#// ------------
#
#function void uvm_sequencer_base::send_request(uvm_sequence_base sequence_ptr,
#                                               uvm_sequence_item t,
#                                               bit rerandomize = 0)
#  return
#endfunction
#
#
#// set_max_zero_time_wait_relevant_count
#// ------------
#
#function void uvm_sequencer_base::set_max_zero_time_wait_relevant_count(int new_val)
#   m_max_zero_time_wait_relevant_count = new_val
#endfunction
#
#
#
#
#
#//----------------------------------------------------------------------------
#//
#//                              *** DEPRECATED ***
#//
#//                        - DO NOT USE IN NEW DESIGNS -
#//
#//                        - NOT PART OF UVM STANDARD -
#//----------------------------------------------------------------------------
#
#`ifndef UVM_NO_DEPRECATED
#
#// add_sequence
#// ------------
#//
#// Adds a sequence of type specified in the type_name paramter to the
#// sequencer's sequence library.
#
#function void uvm_sequencer_base::add_sequence(string type_name)
#
#  `uvm_warning("UVM_DEPRECATED",{"Registering sequence '",type_name,
#     "' with sequencer '",get_full_name(),"' is deprecated. "})
#
#  //assign typename key to an int based on size
#  //used with get_seq_kind to return an int key to match a type name
#  if (!sequence_ids.exists(type_name)):
#    sequence_ids[type_name] = sequences.size()
#    //used w/ get_sequence to return a uvm_sequence factory object that
#    //matches an int id
#    sequences.push_back(type_name)
#  end
#endfunction
#
#
#// remove_sequence
#// ---------------
#
#function void uvm_sequencer_base::remove_sequence(string type_name)
#  sequence_ids.delete(type_name)
#  for (int i = 0; i < this.sequences.size(); i++):
#    if (this.sequences[i] == type_name)
#      this.sequences.delete(i)
#  end
#endfunction
#
#
#// set_sequences_queue
#// -------------------
#
#function void uvm_sequencer_base::set_sequences_queue(
#                                    ref string sequencer_sequence_lib[$])
#
#  for(int j=0; j < sequencer_sequence_lib.size(); j++):
#    sequence_ids[sequencer_sequence_lib[j]] = sequences.size()
#    this.sequences.push_back(sequencer_sequence_lib[j])
#  end
#endfunction
#
#
#// start_default_sequence
#// ----------------------
#// Called when the run phase begins, this method starts the default sequence,
#// as specified by the default_sequence member variable.
#//
#
#task uvm_sequencer_base::start_default_sequence()
#  uvm_sequence_base m_seq
#  uvm_coreservice_t cs = uvm_coreservice_t::get();
#  uvm_factory factory=cs.get_factory()
#
#  // Default sequence was cleared, or the count is zero
#  if (default_sequence == "" || count == 0 ||
#        (sequences.size() == 0 && default_sequence == "uvm_random_sequence"))
#    return
#
#  // Have run-time phases and no user setting of default sequence
#  if(this.m_default_seq_set == 0 && m_domain is not None):
#    default_sequence = ""
#    `uvm_info("NODEFSEQ", {"The \"default_sequence\" has not been set. ",
#       "Since this sequencer has a runtime phase schedule, the ",
#       "uvm_random_sequence is not being started for the run phase."}, UVM_HIGH)
#    return
#  end
#
#  // Have a user setting for both old and new default sequence mechanisms
#  if (this.m_default_seq_set == 1 &&
#     (uvm_config_db #(uvm_sequence_base)::exists(this, "run_phase", "default_sequence", 0) ||
#      uvm_config_db #(uvm_object_wrapper)::exists(this, "run_phase", "default_sequence", 0)))
#  begin
#    `uvm_warning("MULDEFSEQ", {"A default phase sequence has been set via the ",
#       "\"<phase_name>.default_sequence\" configuration option.",
#       "The deprecated \"default_sequence\" configuration option is ignored."})
#    return
#  end
#
#  // no user sequences to choose from
#  if(sequences.size() == 2 &&
#     sequences[0] == "uvm_random_sequence" &&
#     sequences[1] == "uvm_exhaustive_sequence"):
#    uvm_report_warning("NOUSERSEQ", {"No user sequence available. ",
#                       "Not starting the (deprecated) default sequence."}, UVM_HIGH)
#    return
#  end
#
#    `uvm_warning("UVM_DEPRECATED",{"Starting (deprecated) default sequence '",default_sequence,
#     "' on sequencer '",get_full_name(),
#     "'. See documentation for uvm_sequencer_base::start_phase_sequence() for information on ",
#     "starting default sequences in UVM."})
#
#    //create the sequence object
#    if (!$cast(m_seq, factory.create_object_by_name(default_sequence,
#                                            get_full_name(), default_sequence)))
#      begin
#        uvm_report_fatal("FCTSEQ",{"Default sequence set to invalid value : ",
#                                   default_sequence}, UVM_NONE)
#      end
#
#    if (m_seq is None):
#      uvm_report_fatal("STRDEFSEQ", "None m_sequencer reference", UVM_NONE)
#    end
#    m_seq.set_starting_phase(run_ph)
#    m_seq.print_sequence_info = 1
#    m_seq.set_parent_sequence(None)
#    m_seq.set_sequencer(this)
#    m_seq.reseed()
#    if (!m_seq.randomize()):
#      uvm_report_warning("STRDEFSEQ", "Failed to randomize sequence")
#    end
#    m_seq.start(this)
#endtask
#
#
#// get_seq_kind
#// ------------
#// Returns an int seq_kind correlating to the sequence of type type_name
#// in the sequencers sequence library. If the named sequence is not
#// registered a SEQNF warning is issued and -1 is returned.
#
#function int uvm_sequencer_base::get_seq_kind(string type_name)
#
#  `uvm_warning("UVM_DEPRECATED", $sformatf("%m is deprecated"))
#
#  if (sequence_ids.exists(type_name))
#    return sequence_ids[type_name]
#
#  `uvm_warning("SEQNF",
#    {"Sequence type_name '",type_name,"' not registered with this sequencer."})
#
#  return -1
#endfunction
#
#
#// get_sequence
#// ------------
#// Returns a reference to a sequence specified by the seq_kind int.
#// The seq_kind int may be obtained using the get_seq_kind() method.
#
#function uvm_sequence_base uvm_sequencer_base::get_sequence(int req_kind)
#  uvm_coreservice_t cs = uvm_coreservice_t::get();
#  uvm_factory factory = cs.get_factory()
#  uvm_sequence_base m_seq
#  string m_seq_type
#
#  `uvm_warning("UVM_DEPRECATED", $sformatf("%m is deprecated"))
#
#  if (req_kind < 0 || req_kind >= sequences.size()):
#    uvm_report_error("SEQRNG",
#      $sformatf("Kind arg '%0d' out of range. Need 0-%0d",
#      req_kind, sequences.size()-1))
#  end
#
#  m_seq_type = sequences[req_kind]
#  if (!$cast(m_seq, factory.create_object_by_name(m_seq_type,
#                                          get_full_name(),
#                                          m_seq_type)))
#  begin
#      uvm_report_fatal("FCTSEQ",
#        $sformatf("Factory cannot produce a sequence of type %0s.",
#        m_seq_type), UVM_NONE)
#  end
#
#  m_seq.print_sequence_info = 1
#  m_seq.set_sequencer (this)
#  return m_seq
#
#endfunction
#
#
#// num_sequences
#// -------------
#
#function int uvm_sequencer_base::num_sequences()
#  return sequences.size()
#endfunction
#
#
#// m_add_builtin_seqs
#// ------------------
#
#function void uvm_sequencer_base::m_add_builtin_seqs(bit add_simple=1)
#  if(!sequence_ids.exists("uvm_random_sequence"))
#    add_sequence("uvm_random_sequence")
#  if(!sequence_ids.exists("uvm_exhaustive_sequence"))
#    add_sequence("uvm_exhaustive_sequence")
#  if(add_simple == 1):
#    if(!sequence_ids.exists("uvm_simple_sequence"))
#      add_sequence("uvm_simple_sequence")
#  end
#endfunction
#
#
#// run_phase
#// ---------
#
#task uvm_sequencer_base::run_phase(uvm_phase phase)
#  super.run_phase(phase)
#  start_default_sequence()
#endtask
#
#
#`endif // UVM_NO_DEPRECATED
#
#//------------------------------------------------------------------------------
#//
#// Class- uvm_sequence_request
#//
#//------------------------------------------------------------------------------
#
#class uvm_sequence_request
#  bit        grant
#  int        sequence_id
#  int        request_id
#  int        item_priority
#  process    process_id
#  uvm_sequencer_base::seq_req_t  request
#  uvm_sequence_base sequence_ptr
#endclass

class uvm_sequence_request:
    def __init__(self):
        self.grant = False
        self.sequence_id = 0
        self.request_id = 0
        self.item_priority = 0
        #  process    process_id
        self.process_id = process()
        self.request = None  # uvm_sequencer_base::seq_req_t
        self.sequence_ptr = None  # uvm_sequence_base
        #endclass
