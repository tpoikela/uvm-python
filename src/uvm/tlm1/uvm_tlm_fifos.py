#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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
#------------------------------------------------------------------------------

import cocotb

from .uvm_tlm_fifo_base import *
from ..base.uvm_mailbox import UVMMailbox

#------------------------------------------------------------------------------
#
# Title: TLM FIFO Classes
#
# This section defines TLM-based FIFO classes.
#
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#
# Class: uvm_tlm_fifo#(T)
#
# This class provides storage of transactions between two independently running
# processes. Transactions are put into the FIFO via the ~put_export~.
# transactions are fetched from the FIFO in the order they arrived via the
# ~get_peek_export~. The ~put_export~ and ~get_peek_export~ are inherited from
# the <uvm_tlm_fifo_base #(T)> super class, and the interface methods provided by
# these exports are defined by the <uvm_tlm_if_base #(T1,T2)> class.
#
#------------------------------------------------------------------------------


class UVMTLMFIFO(UVMTLMFIFOBase):
    type_name = "uvm_tlm_fifo #(T)"

    #  // Function: new
    #  //
    #  // The ~name~ and ~parent~ are the normal uvm_component constructor arguments.
    #  // The ~parent~ should be ~null~ if the <uvm_tlm_fifo#(T)> is going to be used in a
    #  // statically elaborated construct (e.g., a module). The ~size~ indicates the
    #  // maximum size of the FIFO; a value of zero indicates no upper bound.
    #
    def __init__(self, name, parent=None, size=1):
        UVMTLMFIFOBase.__init__(self, name, parent)
        self.m = UVMMailbox(size)
        self.m_size = size
        self.m_pending_blocked_gets = 0

    def get_type_name(self):
        return UVMTLMFIFO.type_name

    #  // Function: size
    #  //
    #  // Returns the capacity of the FIFO-- that is, the number of entries
    #  // the FIFO is capable of holding. A return value of 0 indicates the
    #  // FIFO capacity has no limit.
    def size(self):
        return self.m_size

    #  // Function: used
    #  //
    #  // Returns the number of entries put into the FIFO.
    def used(self):
        return self.m.num()

    #  // Function: is_empty
    #  //
    #  // Returns 1 when there are no entries in the FIFO, 0 otherwise.
    def is_empty(self):
        return (self.m.num() == 0)

    #  // Function: is_full
    #  //
    #  // Returns 1 when the number of entries in the FIFO is equal to its <size>,
    #  // 0 otherwise.
    #
    def is_full(self):
        return (self.m_size != 0) and (self.m.num() == self.m_size)

    @cocotb.coroutine
    def put(self, t):
        yield self.m.put(t)
        self.put_ap.write(t)

    @cocotb.coroutine
    def get(self, t):
        self.m_pending_blocked_gets += 1
        yield self.m.get(t)
        self.m_pending_blocked_gets -= 1
        self.get_ap.write(t)

    @cocotb.coroutine
    def peek(self, t):
        yield self.m.peek(t)

    def try_get(self, t):
        if not self.m.try_get(t):
            return False
        self.get_ap.write(t[0])
        return True

    def try_peek(self, t):
        return self.m.try_peek(t)

    def try_put(self, t):
        if not self.m.try_put(t):
            return False
        self.put_ap.write(t)
        return True

    def can_put(self):
        return self.m_size == 0 or self.m.num() < self.m_size

    def can_get(self):
        return self.m.num() > 0 and self.m_pending_blocked_gets == 0

    def can_peek(self):
        return self.m.num() > 0

    #  // Function: flush
    #  //
    #  // Removes all entries from the FIFO, after which <used> returns 0
    #  // and <is_empty> returns 1.
    #
    def flush(self):
        t = []
        r = 1
        while r:
            r = self.try_get(t)

        if self.m.num() > 0 and self.m_pending_blocked_gets != 0:
            uvm_report_error("flush failed" ,
                "there are blocked gets preventing the flush", UVM_NONE)
    #endclass


#------------------------------------------------------------------------------
#
# Class: uvm_tlm_analysis_fifo#(T)
#
# An analysis_fifo is a <uvm_tlm_fifo#(T)> with an unbounded size and a write interface.
# It can be used any place a <uvm_analysis_imp> is used. Typical usage is
# as a buffer between a <uvm_analysis_port> in an initiator component
# and TLM1 target component.
#
#------------------------------------------------------------------------------

class UVMTLMAnalysisFIFO(UVMTLMFIFO):
    type_name = "uvm_tlm_analysis_fifo #(T)"
    #
    #  // Port: analysis_export #(T)
    #  //
    #  // The analysis_export provides the write method to all connected analysis
    #  // ports and parent exports:
    #  //
    #  //|  function void write (T t)
    #  //
    #  // Access via ports bound to this export is the normal mechanism for writing
    #  // to an analysis FIFO.
    #  // See write method of <uvm_tlm_if_base #(T1,T2)> for more information.
    #
    #  uvm_analysis_imp #(T, uvm_tlm_analysis_fifo #(T)) analysis_export
    #
    #
    #  // Function: new
    #  //
    #  // This is the standard uvm_component constructor. ~name~ is the local name
    #  // of this component. The ~parent~ should be left unspecified when this
    #  // component is instantiated in statically elaborated constructs and must be
    #  // specified when this component is a child of another UVM component.
    #
    def __init__(self, name, parent=None):
        UVMTLMFIFO.__init__(self, name, parent, 0)  # // analysis fifo must be unbounded
        self.analysis_export = UVMAnalysisImp("analysis_export", self)

    def get_type_name(self):
        return UVMTLMAnalysisFIFO.type_name

    def write(self, t):
        self.try_put(t)  # unbounded => must succeed
    #endclass
