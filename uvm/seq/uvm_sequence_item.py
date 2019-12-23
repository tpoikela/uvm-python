#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
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
#----------------------------------------------------------------------

#typedef class uvm_sequence_base
#typedef class uvm_sequencer_base

from ..base.uvm_transaction import UVMTransaction
from ..base.uvm_globals import *

#------------------------------------------------------------------------------
#
# CLASS: UVMSequenceItem
#
# The base class for user-defined sequence items and also the base class for
# the uvm_sequence class. The UVMSequenceItem class provides the basic
# functionality for objects, both sequence items and sequences, to operate in
# the sequence mechanism.
#
#------------------------------------------------------------------------------

class UVMSequenceItem(UVMTransaction):
    #  local      int                self.m_sequence_id = -1
    #  protected  bit                self.m_use_sequence_info
    #  protected  int                self.m_depth = -1
    #  protected  uvm_sequencer_base self.m_sequencer
    #  protected  uvm_sequence_base  self.m_parent_sequence
    #  bit        self.print_sequence_info

    #  static     bit issued1,issued2
    issued1 = False
    issued2 = False

    # Function: new
    #
    # The constructor method for UVMSequenceItem.
    #
    def __init__(self, name="UVMSequenceItem"):
        UVMTransaction.__init__(self, name)
        self.m_sequence_id = -1
        self.m_use_sequence_info = False
        self.m_depth = -1
        self.m_sequencer = None
        self.p_sequencer = None
        self.m_parent_sequence = None
        self.print_sequence_info = False
    #  endfunction

    def get_type_name(self):
        return "UVMSequenceItem"

    #  // Function- set_sequence_id
    def set_sequence_id(self, id):
        self.m_sequence_id = id

    #  // Function: get_sequence_id
    #  //
    #  // private
    #  //
    #  // Get_sequence_id is an internal method that is not intended for user code.
    #  // The sequence_id is not a simple integer.  The get_transaction_id is meant
    #  // for users to identify specific transactions.
    #  //
    #  // These methods allow access to the sequence_item sequence and transaction
    #  // IDs. get_transaction_id and set_transaction_id are methods on the
    #  // uvm_transaction base_class. These IDs are used to identify sequences to
    #  // the sequencer, to route responses back to the sequence that issued a
    #  // request, and to uniquely identify transactions.
    #  //
    #  // The sequence_id is assigned automatically by a sequencer when a sequence
    #  // initiates communication through any sequencer calls (i.e. `uvm_do_*,
    #  // wait_for_grant).  A sequence_id will remain unique for this sequence
    #  // until it ends or it is killed.  However, a single sequence may have
    #  // multiple valid sequence ids at any point in time.  Should a sequence
    #  // start again after it has ended, it will be given a new unique sequence_id.
    #  //
    #  // The transaction_id is assigned automatically by the sequence each time a
    #  // transaction is sent to the sequencer with the transaction_id in its
    #  // default (-1) value.  If the user sets the transaction_id to any non-default
    #  // value, that value will be maintained.
    #  //
    #  // Responses are routed back to this sequences based on sequence_id. The
    #  // sequence may use the transaction_id to correlate responses with their
    #  // requests.
    def get_sequence_id(self):
        return (self.m_sequence_id)
    # endfunction

    #  // Function: set_item_context
    #  //
    #  // Set the sequence and sequencer execution context for a sequence item
    #
    def set_item_context(self, parent_seq, sequencer=None):
        self.set_use_sequence_info(1)
        if parent_seq is not None:
            self.set_parent_sequence(parent_seq)
        if (sequencer is None and self.m_parent_sequence is not None):
            sequencer = self.m_parent_sequence.get_sequencer()
        self.set_sequencer(sequencer)
        if (self.m_parent_sequence is not None):
            self.set_depth(self.m_parent_sequence.get_depth() + 1)
        self.reseed()

    #  // Function: set_use_sequence_info
    #  //
    #
    def set_use_sequence_info(self, value):
        self.m_use_sequence_info = value
    #  endfunction

    #  // Function: get_use_sequence_info
    #  //
    #  // These methods are used to set and get the status of the use_sequence_info
    #  // bit. Use_sequence_info controls whether the sequence information
    #  // (sequencer, parent_sequence, sequence_id, etc.) is printed, copied, or
    #  // recorded. When use_sequence_info is the default value of 0, then the
    #  // sequence information is not used. When use_sequence_info is set to 1,
    #  // the sequence information will be used in printing and copying.

    def get_use_sequence_info(self):
        return (self.m_use_sequence_info)
    #  endfunction


    #  // Function: set_id_info
    #  //
    #  // Copies the sequence_id and transaction_id from the referenced item into
    #  // the calling item.  This routine should always be used by drivers to
    #  // initialize responses for future compatibility.
    def set_id_info(self, item):
        if item is None:
            uvm_report_fatal(self.get_full_name(), "set_id_info called with None parameter", UVM_NONE)
        self.set_transaction_id(item.get_transaction_id())
        self.set_sequence_id(item.get_sequence_id())

    #  // Function: set_sequencer
    #  //
    #  // Sets the default sequencer for the sequence to sequencer.  It will take
    #  // effect immediately, so it should not be called while the sequence is
    #  // actively communicating with the sequencer.

    def set_sequencer(self, sequencer):
        self.m_sequencer = sequencer
        self.m_set_p_sequencer()
    #  endfunction

    #  // Function: get_sequencer
    #  //
    #  // Returns a reference to the default sequencer used by this sequence.

    def get_sequencer(self):
        return self.m_sequencer
    #  endfunction


    #  // Function: set_parent_sequence
    #  //
    #  // Sets the parent sequence of this sequence_item.  This is used to identify
    #  // the source sequence of a sequence_item.

    def set_parent_sequence(self, parent):
        self.m_parent_sequence = parent
    #  endfunction


    #  // Function: get_parent_sequence
    #  //
    #  // Returns a reference to the parent sequence of any sequence on which this
    #  // method was called. If this is a parent sequence, the method returns ~None~.
    #
    def get_parent_sequence(self):
        return (self.m_parent_sequence)
    #  endfunction

    #  // Function: set_depth
    #  //
    #  // The depth of any sequence is calculated automatically.  However, the user
    #  // may use  set_depth to specify the depth of a particular sequence. This
    #  // method will override the automatically calculated depth, even if it is
    #  // incorrect.
    #
    def set_depth(self, value):
        self.m_depth = value
    #  endfunction

    #  // Function: get_depth
    #  //
    #  // Returns the depth of a sequence from its parent.  A  parent sequence will
    #  // have a depth of 1, its child will have a depth  of 2, and its grandchild
    #  // will have a depth of 3.
    #
    def get_depth(self):

        # If depth has been set or calculated, then use that
        if self.m_depth != -1:
            return (self.m_depth)

        # Calculate the depth, store it, and return the value
        if self.m_parent_sequence is None:
            self.m_depth = 1
        else:
            self.m_depth = self.m_parent_sequence.get_depth() + 1

        return self.m_depth
    #  endfunction


    #  // Function: is_item
    #  //
    #  // This function may be called on any sequence_item or sequence. It will
    #  // return 1 for items and 0 for sequences (which derive from this class).
    def is_item(self):
        return True
    #  endfunction

    #  // Function- get_full_name
    #  //
    #  // Internal method; overrides must follow same naming convention
    #
    def get_full_name(self):
        get_full_name = ""
        if self.m_parent_sequence is not None:
            get_full_name = self.m_parent_sequence.get_full_name() + "."
        elif self.m_sequencer is not None:
            get_full_name = self.m_sequencer.get_full_name() + "."
        if self.get_name() != "":
            get_full_name = get_full_name + self.get_name()
        else:
            get_full_name = get_full_name + "_item"
        return get_full_name
    #  endfunction

    #  // Function: get_root_sequence_name
    #  //
    #  // Provides the name of the root sequence (the top-most parent sequence).
    #
    def get_root_sequence_name(self):
        #uvm_sequence_base root_seq
        root_seq = self.get_root_sequence()
        if root_seq is None:
            return ""
        else:
            return root_seq.get_name()
    #  endfunction

    #  // Function- m_set_p_sequencer
    #  //
    #  // Internal method
    def m_set_p_sequencer(self):
        self.p_sequencer = self.m_sequencer

    #  // Function: get_root_sequence
    #  //
    #  // Provides a reference to the root sequence (the top-most parent sequence).
    #
    def get_root_sequence(self):
        root_seq_base = None  # UVMSequenceItem
        root_seq = None
        root_seq_base = self
        while True:
            if (root_seq_base.get_parent_sequence() is not None):
                root_seq_base = root_seq_base.get_parent_sequence()
                #$cast(root_seq, root_seq_base)
                root_seq = root_seq_base
            else:
                return root_seq
        #  endfunction

    #  // Function: get_sequence_path
    #  //
    #  // Provides a string of names of each sequence in the full hierarchical
    #  // path. A "." is used as the separator between each sequence.
    def get_sequence_path(self):
        this_item = None  # UVMSequenceItem
        seq_path = ""
        this_item = self
        seq_path = self.get_name()
        while True:
            if this_item.get_parent_sequence() is not None:
                this_item = this_item.get_parent_sequence()
                seq_path = this_item.get_name() + "." + seq_path
            else:
                return seq_path
        #  endfunction

    #  //---------------------------
    #  // Group: Reporting Interface
    #  //---------------------------
    #  //
    #  // Sequence items and sequences will use the sequencer which they are
    #  // associated with for reporting messages. If no sequencer has been se
    #  // for the item/sequence using <set_sequencer> or indirectly via
    #  // <uvm_sequence_base::start_item> or <uvm_sequence_base::start>),
    #  // then the global reporter will be used.
    #
    #  virtual function uvm_report_object uvm_get_report_object()
    #    if(self.m_sequencer == None):
    #      uvm_coreservice_t cs = uvm_coreservice_t::get()
    #       return cs.get_root()
    #    end else
    #      return self.m_sequencer
    #  endfunction
    #
    #  function int uvm_report_enabled(int verbosity,
    #    				  uvm_severity severity=UVM_INFO, string id="")
    #    uvm_report_object l_report_object = uvm_get_report_object()
    #    if (l_report_object.get_report_verbosity_level(severity, id) < verbosity)
    #      return 0
    #    return 1
    #  endfunction
    #
    #  // Function: uvm_report
    #  virtual function void uvm_report( uvm_severity severity,
    #                                    string id,
    #                                    string message,
    #                                    int verbosity = (severity == uvm_severity'(UVM_ERROR)) ? UVM_LOW :
    #                                                    (severity == uvm_severity'(UVM_FATAL)) ? UVM_NONE : UVM_MEDIUM,
    #                                    string filename = "",
    #                                    int line = 0,
    #                                    string context_name = "",
    #                                    bit report_enabled_checked = 0)
    #    uvm_report_message l_report_message
    #    if (report_enabled_checked == 0):
    #      if (!uvm_report_enabled(verbosity, severity, id))
    #        return
    #    end
    #    l_report_message = uvm_report_message::new_report_message()
    #    l_report_message.set_report_message(severity, id, message,
    #					verbosity, filename, line, context_name)
    #    uvm_process_report_message(l_report_message)
    #
    #  endfunction
    #
    #  // Function: uvm_report_info
    #
    #  virtual function void uvm_report_info( string id,
    #					 string message,
    #   					 int verbosity = UVM_MEDIUM,
    #					 string filename = "",
    #					 int line = 0,
    #   					 string context_name = "",
    #					 bit report_enabled_checked = 0)
    #
    #    this.uvm_report(UVM_INFO, id, message, verbosity, filename, line,
    #                    context_name, report_enabled_checked)
    #  endfunction
    #
    #  // Function: uvm_report_warning
    #
    #  virtual function void uvm_report_warning( string id,
    #					    string message,
    #   					    int verbosity = UVM_MEDIUM,
    #					    string filename = "",
    #					    int line = 0,
    #   					    string context_name = "",
    #					    bit report_enabled_checked = 0)
    #
    #    this.uvm_report(UVM_WARNING, id, message, verbosity, filename, line,
    #                    context_name, report_enabled_checked)
    #  endfunction
    #
    #  // Function: uvm_report_error
    #
    #  virtual function void uvm_report_error( string id,
    #					  string message,
    #   					  int verbosity = UVM_LOW,
    #					  string filename = "",
    #					  int line = 0,
    #   					  string context_name = "",
    #					  bit report_enabled_checked = 0)
    #
    #    this.uvm_report(UVM_ERROR, id, message, verbosity, filename, line,
    #                    context_name, report_enabled_checked)
    #  endfunction
    #
    #  // Function: uvm_report_fatal
    #  //
    #  // These are the primary reporting methods in the UVM. UVMSequenceItem
    #  // derived types delegate these functions to their associated sequencer
    #  // if they have one, or to the global reporter. See <uvm_report_object::Reporting>
    #  // for details on the messaging functions.
    #
    #  virtual function void uvm_report_fatal( string id,
    #					  string message,
    #   					  int verbosity = UVM_NONE,
    #					  string filename = "",
    #					  int line = 0,
    #   					  string context_name = "",
    #					  bit report_enabled_checked = 0)
    #
    #    this.uvm_report(UVM_FATAL, id, message, verbosity, filename, line,
    #                    context_name, report_enabled_checked)
    #  endfunction
    #
    #  virtual function void uvm_process_report_message (uvm_report_message report_message)
    #    uvm_report_object l_report_object = uvm_get_report_object()
    #    report_message.set_report_object(l_report_object)
    #    if (report_message.get_context() == "")
    #      report_message.set_context(get_sequence_path())
    #    l_report_object.m_rh.process_report_message(report_message)
    #  endfunction
    #
    #
    #  // Function- do_print
    #  //
    #  // Internal method
    #
    #  function void do_print (uvm_printer printer)
    #    string temp_str0, temp_str1
    #    int depth = get_depth()
    #    super.do_print(printer)
    #    if(self.print_sequence_info || self.m_use_sequence_info):
    #      printer.print_field_int("depth", depth, $bits(depth), UVM_DEC, ".", "int")
    #      if(self.m_parent_sequence != None):
    #        temp_str0 = self.m_parent_sequence.get_name()
    #        temp_str1 = self.m_parent_sequence.get_full_name()
    #      end
    #      printer.print_string("parent sequence (name)", temp_str0)
    #      printer.print_string("parent sequence (full name)", temp_str1)
    #      temp_str1 = ""
    #      if(self.m_sequencer != None):
    #        temp_str1 = self.m_sequencer.get_full_name()
    #      end
    #      printer.print_string("sequencer", temp_str1)
    #    end
    #  endfunction
    #
    #endclass

# Macro for factory creation
# uvm_object_registry(UVMSequenceItem, "UVMSequenceItem")
