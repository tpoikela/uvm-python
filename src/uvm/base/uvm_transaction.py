#
#-----------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela
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
#-----------------------------------------------------------------------------

from .sv import sv
from .uvm_recorder import UVMRecorder
from .uvm_object import UVMObject
from .uvm_pool import UVMEventPool


class UVMTransaction(UVMObject):
    """
    The `UVMTransaction` class is the root base class for UVM transactions.
    Inheriting all the methods of `UVMObject`, `UVMTransaction` adds a timing and
    recording interface.

    This class provides timestamp properties, notification events, and transaction
    recording support.

    Use of this class as a base for user-defined transactions
    is deprecated. Its subtype, `uvm_sequence_item`, shall be used as the
    base class for all user-defined transaction types.

    The intended use of this API is via a `uvm_driver` to call `accept_tr`,
    `begin_tr`, and `end_tr` during the course of
    sequence item execution. These methods in the component base class will
    call into the corresponding methods in this class to set the corresponding
    timestamps (`accept_time`, `begin_time`, and `end_time`), trigger the
    corresponding event (`begin_event` and `end_event`, and, if enabled,
    record the transaction contents to a vendor-specific transaction database.

    Note that get_next_item/item_done when called on a `uvm_seq_item_pull_port`
    will automatically trigger the `begin_event` and `end_event` via calls to `begin_tr` and `end_tr`.
    While convenient, it is generally the responsibility of drivers to mark a
    transaction's progress during execution.  To allow the driver or layering sequence
    to control sequence item timestamps, events, and recording, you must call
    `UVM_SEQ_ITEM_PULL_IMP.disable_auto_item_recording` at the beginning
    of the driver's `run_phase` task.

    Users may also use the transaction's event pool, `events`,
    to define custom events for the driver to trigger and the sequences to wait on. Any
    in-between events such as marking the beginning of the address and data
    phases of transaction execution could be implemented via the
    `events` pool.

    In pipelined protocols, the driver may release a sequence (return from
    `finish_item` or it's `uvm_do` macro) before the item has been completed.
    If the driver uses the `begin_tr`/`end_tr` API in `UVMComponent`, the sequence can
    wait on the item's `end_event` to block until the item was fully executed,
    as in the following example.

    .. code-block:: systemverilog

        task uvm_execute(item, ...)
            // can use the `uvm_do macros as well
            start_item(item)
            item.randomize()
            finish_item(item)
            item.self.end_event.wait_on()
            // get_response(rsp, item.get_transaction_id()); //if needed
        endtask


    A simple two-stage pipeline driver that can execute address and
    data phases concurrently might be implemented as follows:

    .. code-block:: systemverilog

        task run()

            // this driver supports a two-deep pipeline
            fork
              do_item()
              do_item()
            join
        endtask


        task do_item()

          forever begin
            mbus_item req

            lock.get()

            seq_item_port.get(req); // Completes the sequencer-driver handshake

            accept_tr(req)

              // request bus, wait for grant, etc.

            begin_tr(req)

              // execute address phase

            // allows next transaction to begin address phase
            lock.put()

              // execute data phase
              // (may trigger custom "data_phase" event here)

            end_tr(req)

          end

        endtask: do_item
    """

    #  // Variable: events
    #  //
    #  // The event pool instance for this transaction. This pool is used to track
    #  // various milestones: by default, begin, accept, and end
    #
    #  const uvm_event_pool events = new
    #
    #
    #  // Variable: self.begin_event
    #  //
    #  // A ~uvm_event#(uvm_object)~ that is triggered when this transaction's actual execution on the
    #  // bus begins, typically as a result of a driver calling <uvm_component::begin_tr>.
    #  // Processes that wait on this event will block until the transaction has
    #  // begun.
    #  //
    #  // For more information, see the general discussion for <uvm_transaction>.
    #  // See <uvm_event#(T)> for details on the event API.
    #  //
    #  uvm_event#(uvm_object) self.begin_event
    #
    #  // Variable: self.end_event
    #  //
    #  // A ~uvm_event#(uvm_object)~ that is triggered when this transaction's actual execution on
    #  // the bus ends, typically as a result of a driver calling <uvm_component::end_tr>.
    #  // Processes that wait on this event will block until the transaction has
    #  // ended.
    #  //
    #  // For more information, see the general discussion for <uvm_transaction>.
    #  // See <uvm_event#(T)> for details on the event API.
    #  //
    #  //| virtual task my_sequence::body()
    #  //|  ...
    #  //|  start_item(item);    \
    #  //|  item.randomize();     } `uvm_do(item)
    #  //|  finish_item(item);   /
    #  //|  // return from finish item does not always mean item is completed
    #  //|  item.self.end_event.wait_on()
    #  //|  ...
    #  //
    #  uvm_event#(uvm_object) self.end_event

    # Function: new
    #
    # Creates a new transaction object. The name is the instance name of the
    # transaction. If not supplied, then the object is unnamed.
    #
    def __init__(self, name="", initiator=None):
        UVMObject.__init__(self, name)
        self.initiator = initiator
        self.m_transaction_id = -1
        self.events = UVMEventPool()
        self.begin_event = self.events.get("begin")
        self.end_event = self.events.get("end")
        self.stream_handle = None  # For recording
        self.tr_recorder = None

        self.begin_time = -1
        self.end_time = -1
        self.accept_time = -1


    #  // Function: accept_tr
    #  //
    #  // Calling ~accept_tr~ indicates that the transaction item has been received by
    #  // a consumer component. Typically a <uvm_driver #(REQ,RSP)> would call <uvm_component::accept_tr>,
    #  // which calls this method-- upon return from a ~get_next_item()~, ~get()~, or ~peek()~
    #  // call on its sequencer port, <uvm_driver#(REQ,RSP)::seq_item_port>.
    #  //
    #  // With some
    #  // protocols, the received item may not be started immediately after it is
    #  // accepted. For example, a bus driver, having accepted a request transaction,
    #  // may still have to wait for a bus grant before beginning to execute
    #  // the request.
    #  //
    #  // This function performs the following actions:
    #  //
    #  // - The transaction's internal accept time is set to the current simulation
    #  //   time, or to accept_time if provided and non-zero. The ~accept_time~ may be
    #  //   any time, past or future.
    #  //
    #  // - The transaction's internal accept event is triggered. Any processes
    #  //   waiting on the this event will resume in the next delta cycle.
    #  //
    #  // - The <do_accept_tr> method is called to allow for any post-accept
    #  //   action in derived classes.
    #
    #  extern function void accept_tr (time accept_time = 0)
    def accept_tr(self, accept_time=0):
        e = None
        if accept_time != 0:
            self.accept_time = accept_time
        else:
            self.accept_time = sv.realtime()

        self.do_accept_tr()
        e = self.events.get("accept")
        if e is not None:
            e.trigger()


    #  // Function: do_accept_tr
    #  //
    #  // This user-definable callback is called by <accept_tr> just before the accept
    #  // event is triggered. Implementations should call ~super.do_accept_tr~ to
    #  // ensure correct operation.
    #
    #  extern virtual protected function void do_accept_tr ()
    def do_accept_tr(self):
        return

    #
    #  // Function: begin_tr
    #  //
    #  // This function indicates that the transaction has been started and is not
    #  // the child of another transaction. Generally, a consumer component begins
    #  // execution of a transactions it receives.
    #  //
    #  // Typically a <uvm_driver #(REQ,RSP)> would call <uvm_component::begin_tr>, which
    #  // calls this method, before actual execution of a sequence item transaction.
    #  // Sequence items received by a driver are always a child of a parent sequence.
    #  // In this case, begin_tr obtains the parent handle and delegates to <begin_child_tr>.
    #  //
    #  // See <accept_tr> for more information on how the
    #  // begin-time might differ from when the transaction item was received.
    #  //
    #  // This function performs the following actions:
    #  //
    #  // - The transaction's internal start time is set to the current simulation
    #  //   time, or to begin_time if provided and non-zero. The begin_time may be
    #  //   any time, past or future, but should not be less than the accept time.
    #  //
    #  // - If recording is enabled, then a new database-transaction is started with
    #  //   the same begin time as above.
    #  //
    #  // - The <do_begin_tr> method is called to allow for any post-begin action in
    #  //   derived classes.
    #  //
    #  // - The transaction's internal begin event is triggered. Any processes
    #  //   waiting on this event will resume in the next delta cycle.
    #  //
    #  // The return value is a transaction handle, which is valid (non-zero) only if
    #  // recording is enabled. The meaning of the handle is implementation specific.
    #
    #
    #  extern function integer begin_tr (time begin_time = 0)
    def begin_tr(self, begin_time=0):
        return self.m_begin_tr(begin_time)

    #
    #  // Function: begin_child_tr
    #  //
    #  // This function indicates that the transaction has been started as a child of
    #  // a parent transaction given by ~parent_handle~. Generally, a consumer
    #  // component calls this method via <uvm_component::begin_child_tr> to indicate
    #  // the actual start of execution of this transaction.
    #  //
    #  // The parent handle is obtained by a previous call to begin_tr or
    #  // begin_child_tr. If the parent_handle is invalid (=0), then this function
    #  // behaves the same as <begin_tr>.
    #  //
    #  // This function performs the following actions:
    #  //
    #  // - The transaction's internal start time is set to the current simulation
    #  //   time, or to begin_time if provided and non-zero. The begin_time may be
    #  //   any time, past or future, but should not be less than the accept time.
    #  //
    #  // - If recording is enabled, then a new database-transaction is started with
    #  //   the same begin time as above. The inherited <uvm_object::record> method
    #  //   is then called, which records the current property values to this new
    #  //   transaction. Finally, the newly started transaction is linked to the
    #  //   parent transaction given by parent_handle.
    #  //
    #  // - The <do_begin_tr> method is called to allow for any post-begin
    #  //   action in derived classes.
    #  //
    #  // - The transaction's internal begin event is triggered. Any processes
    #  //   waiting on this event will resume in the next delta cycle.
    #  //
    #  // The return value is a transaction handle, which is valid (non-zero) only if
    #  // recording is enabled. The meaning of the handle is implementation specific.
    #
    #  extern function integer begin_child_tr (time begin_time = 0,
    #                                               integer parent_handle = 0)
    #Use a parent handle of zero to link to the parent after begin
    def begin_child_tr(self, begin_time=0, parent_handle=0):
        return self.m_begin_tr(begin_time, parent_handle)

    #
    #
    #  // Function: do_begin_tr
    #  //
    #  // This user-definable callback is called by <begin_tr> and <begin_child_tr> just
    #  // before the begin event is triggered. Implementations should call
    #  // ~super.do_begin_tr~ to ensure correct operation.
    #
    #  extern virtual protected function void do_begin_tr ()
    def do_begin_tr(self):
        pass


    #  // Function: end_tr
    #  //
    #  // This function indicates that the transaction execution has ended.
    #  // Generally, a consumer component ends execution of the transactions it
    #  // receives.
    #  //
    #  // You must have previously called <begin_tr> or <begin_child_tr> for this
    #  // call to be successful.
    #  //
    #  // Typically a <uvm_driver #(REQ,RSP)> would call <uvm_component::end_tr>, which
    #  // calls this method, upon completion of a sequence item transaction.
    #  // Sequence items received by a driver are always a child of a parent sequence.
    #  // In this case, begin_tr obtain the parent handle and delegate to <begin_child_tr>.
    #  //
    #  // This function performs the following actions:
    #  //
    #  // - The transaction's internal end time is set to the current simulation
    #  //   time, or to ~end_time~ if provided and non-zero. The ~end_time~ may be any
    #  //   time, past or future, but should not be less than the begin time.
    #  //
    #  // - If recording is enabled and a database-transaction is currently active,
    #  //   then the record method inherited from uvm_object is called, which records
    #  //   the final property values. The transaction is then ended. If ~free_handle~
    #  //   is set, the transaction is released and can no longer be linked to (if
    #  //   supported by the implementation).
    #  //
    #  // - The <do_end_tr> method is called to allow for any post-end
    #  //   action in derived classes.
    #  //
    #  // - The transaction's internal end event is triggered. Any processes waiting
    #  //   on this event will resume in the next delta cycle.
    #
    #  extern function void end_tr (time end_time=0, bit free_handle=1)
    def end_tr(self, end_time=0, free_handle=1):
        self.end_time = end_time
        if end_time == 0:
            self.end_time = sv.realtime()
        self.do_end_tr()  # Callback prior to actual ending of transaction

        if(self.is_recording_enabled() and (self.tr_recorder is not None)):
            self.record(self.tr_recorder)
            self.tr_recorder.close(self.end_time)

            if free_handle:
                # once freed, can no longer link to
                self.tr_recorder.free()
        self.tr_recorder = None

        self.end_event.trigger()


    #  // Function: do_end_tr
    #  //
    #  // This user-definable callback is called by <end_tr> just before the end event
    #  // is triggered. Implementations should call ~super.do_end_tr~ to ensure correct
    #  // operation.
    #
    #  extern virtual protected function void do_end_tr ()
    def do_end_tr(self):
        return


    #  // Function: get_tr_handle
    #  //
    #  // Returns the handle associated with the transaction, as set by a previous
    #  // call to <begin_child_tr> or `begin_tr` with transaction recording enabled.
    #
    #  extern function integer get_tr_handle ()
    def get_tr_handle (self):
        if self.tr_recorder is not None:
            return self.tr_recorder.get_handle()
        else:
            return 0


    #  // Function: disable_recording
    #  //
    #  // Turns off recording for the transaction stream. This method does not
    #  // effect a <uvm_component>'s recording streams.
    def disable_recording(self):
        self.stream_handle = None


    #  // Function: enable_recording
    #  // Turns on recording to the ~stream~ specified.
    #  //
    #  // If transaction recording is on, then a call to ~record~ is made when the
    #  // transaction is ended.
    def enable_recording(self, stream):
        self.stream_handle = stream


    #  // Function: is_recording_enabled
    #  //
    #  // Returns 1 if recording is currently on, 0 otherwise.
    #
    #  extern function bit is_recording_enabled()
    def is_recording_enabled(self):
        return self.stream_handle is not None

    #  // Function: is_active
    #  //
    #  // Returns 1 if the transaction has been started but has not yet been ended.
    #  // Returns 0 if the transaction has not been started.
    #
    #  extern function bit is_active ()
    def is_active(self):
        return self.end_time == -1


    #  // Function: get_event_pool
    #  //
    #  // Returns the event pool associated with this transaction.
    #  //
    #  // By default, the event pool contains the events: begin, accept, and end.
    #  // Events can also be added by derivative objects. An event pool is a
    #  // specialization of <uvm_pool#(KEY,T)>, e.g. a ~uvm_pool#(uvm_event)~.
    #
    #  extern function uvm_event_pool get_event_pool ()
    def get_event_pool(self):
        return self.events


    #  // Function: set_initiator
    #  //
    #  // Sets initiator as the initiator of this transaction.
    #  //
    #  // The initiator can be the component that produces the transaction. It can
    #  // also be the component that started the transaction. This or any other
    #  // usage is up to the transaction designer.
    #
    #  extern function void set_initiator (uvm_component initiator)
    def set_initiator(self, initiator):
        self.initiator = initiator


    #  // Function: get_initiator
    #  //
    #  // Returns the component that produced or started the transaction, as set by
    #  // a previous call to set_initiator.
    #  extern function uvm_component get_initiator ()


    #  // Function: get_accept_time
    #
    def get_accept_time(self):
        return self.accept_time

    #  // Function: get_begin_time
    #
    def get_begin_time(self):
        return self.begin_time


    #  // Function: get_end_time
    #  //
    #  // Returns the time at which this transaction was accepted, begun, or ended,
    #  // as by a previous call to <accept_tr>, <begin_tr>, <begin_child_tr>, or <end_tr>.
    #
    #  extern function time   get_end_time       ()
    def get_end_time(self):
        return self.end_time


    #  // Function: set_transaction_id
    #  //
    #  // Sets this transaction's numeric identifier to id. If not set via this
    #  // method, the transaction ID defaults to -1.
    #  //
    #  // When using sequences to generate stimulus, the transaction ID is used along
    #  // with the sequence ID to route responses in sequencers and to correlate
    #  // responses to requests.
    def set_transaction_id(self, id):
        self.m_transaction_id = id

    #  // Function: get_transaction_id
    #  //
    #  // Returns this transaction's numeric identifier, which is -1 if not set
    #  // explicitly by ~set_transaction_id~.
    #  //
    #  // When using a <uvm_sequence #(REQ,RSP)> to generate stimulus, the transaction
    #  // ID is used along
    #  // with the sequence ID to route responses in sequencers and to correlate
    #  // responses to requests.
    def get_transaction_id(self):
        return self.m_transaction_id

    #  //----------------------------------------------------------------------------
    #  //
    #  // Internal methods properties; do not use directly
    #  //
    #  //----------------------------------------------------------------------------

    #  //Override data control methods for internal properties
    #  extern virtual function void do_print  (uvm_printer printer)

    #  extern virtual function void do_record (uvm_recorder recorder)

    #  extern virtual function void do_copy   (uvm_object rhs)

    #  extern protected function integer m_begin_tr (time    begin_time=0,
    #                                                integer parent_handle=0)
    def m_begin_tr(self, begin_time=0, parent_handle=0):
        m_begin_tr = 0
        tmp_time = begin_time
        if begin_time == 0:
            tmp_time = sv.realtime()
        parent_recorder = None

        if parent_handle != 0:
            parent_recorder = UVMRecorder.get_recorder_from_handle(parent_handle)

        # If we haven't ended the previous record, end it.
        if self.tr_recorder is not None:
            # Don't free the handle, someone else may be using it...
            self.end_tr(tmp_time)

        # May want to establish predecessor/successor relation
        # (don't free handle until then)
        if self.is_recording_enabled():
            db = self.stream_handle.get_db()
            self.end_time = -1
            self.begin_time = tmp_time

            if (parent_recorder is None):
                self.tr_recorder = self.stream_handle.open_recorder(self.get_type_name(),
                        self.begin_time,
                        "Begin_No_Parent, Link")
            else:
                self.tr_recorder = self.stream_handle.open_recorder(self.get_type_name(),
                        self.begin_time,
                        "Begin_End, Link")

                if (self.tr_recorder is not None):
                    pass
                    #link = uvm_parent_child_link::get_link(parent_recorder, self.tr_recorder)
                    # TODO
                    #db.establish_link(link)

            if (self.tr_recorder is not None):
                m_begin_tr = self.tr_recorder.get_handle()
            else:
                m_begin_tr = 0
        else:
            self.tr_recorder = None
            self.end_time = -1
            self.begin_time = tmp_time
            m_begin_tr = 0

        self.do_begin_tr()  # execute callback before event trigger
        self.begin_event.trigger()
        return m_begin_tr

        #endfunction

    #
    #endclass

#------------------------------------------------------------------------------
# IMPLEMENTATION
#------------------------------------------------------------------------------

# get_initiator
# ------------
#
#function uvm_component uvm_transaction::get_initiator()
#  return initiator
#endfunction
#
#
#
# do_print
# --------
#
#function void uvm_transaction::do_print (uvm_printer printer)
#  string str
#  uvm_component tmp_initiator; //work around $swrite bug
#  super.do_print(printer)
#  if(accept_time != -1)
#    printer.print_time("accept_time", accept_time)
#  if(begin_time != -1)
#    printer.print_time("begin_time", begin_time)
#  if(end_time != -1)
#    printer.print_time("end_time", end_time)
#  if(initiator is not None):
#    tmp_initiator = initiator
#    $swrite(str,"@%0d", tmp_initiator.get_inst_id())
#    printer.print_generic("initiator", initiator.get_type_name(), -1, str)
#  end
#endfunction
#
#function void uvm_transaction::do_copy (uvm_object rhs)
#  uvm_transaction txn
#  super.do_copy(rhs)
#  if(rhs is None) return
#  if(!$cast(txn, rhs) ) return
#
#  accept_time = txn.accept_time
#  begin_time = txn.begin_time
#  end_time = txn.end_time
#  initiator = txn.initiator
#  stream_handle = txn.stream_handle
#  self.tr_recorder = txn.self.tr_recorder
#endfunction
#
# do_record
# ---------
#
#function void uvm_transaction::do_record (uvm_recorder recorder)
#  string s
#  super.do_record(recorder)
#  if(accept_time != -1)
#     recorder.record_field("accept_time", accept_time, $bits(accept_time), UVM_TIME)
#  if(initiator is not None):
#    uvm_recursion_policy_enum p = recorder.policy
#    recorder.policy = UVM_REFERENCE
#    recorder.record_object("initiator", initiator)
#    recorder.policy = p
#  end
#endfunction
#
