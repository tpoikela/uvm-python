#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
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


from cocotb.triggers import Event

from .uvm_imps import UVMGetPeekImp, UVMPutImp
from .uvm_analysis_port import UVMAnalysisPort
from ..base.uvm_component import UVMComponent
from ..base.uvm_object_globals import UVM_NONE
from ..base.uvm_globals import uvm_report_error

UVM_TLM_FIFO_TASK_ERROR = "fifo channel task not implemented"
UVM_TLM_FIFO_FUNCTION_ERROR = "fifo channel function not implemented"


class UVMTLMEvent:
    def __init__(self):
        self.event = Event()


class UVMTLMFIFOBase(UVMComponent):
    """
    This class is the base for `UVMTLMFIFO`. It defines the TLM exports
    through which all transaction-based FIFO operations occur. It also defines
    default implementations for each interface method provided by these exports.

    The interface methods provided by the `put_export` and the `get_peek_export`
    are defined and described by `UVMTLMIfBase`.  See the TLM Overview
    section for a general discussion of TLM interface definition and usage.

    :ivar UVMPutImp put_export:

     The `put_export` provides both the blocking and non-blocking put interface
     methods to any attached port:

     Example:

     .. code-block:: python

        task put (input T t)
        function bit can_put ()
        function bit try_put (input T t)

    Any `put` port variant can connect and send transactions to the FIFO via this
    export, provided the transaction types match. See `UVMTLMIfBase`
    for more information on each of the above interface methods.

    :ivar UVMGetPeekImp get_peek_export:

    The `get_peek_export` provides all the blocking and non-blocking get and peek
    interface methods:

    .. code-block:: python
        task get (output T t)
        function bit can_get ()
        function bit try_get (output T t)
        task peek (output T t)
        function bit can_peek ()
        function bit try_peek (output T t)

    Any `get` or `peek` port variant can connect to and retrieve transactions from
    the FIFO via this export, provided the transaction types match. See
    <uvm_tlm_if_base #(T1,T2)> for more information on each of the above interface
    methods.

    :ivar UVMAnalysisPort put_ap:

    Transactions passed via `put` or `try_put` (via any port connected to the
    <put_export>) are sent out this port via its `write` method.

    .. code-block:: python
        def write (T t)

    All connected analysis exports and imps will receive put transactions.
    See <uvm_tlm_if_base #(T1,T2)> for more information on the `write` interface
    method.

    :ivar UVMAnalysisPort get_ap:

    Transactions passed via `get`, `try_get`, `peek`, or `try_peek` (via any
    port connected to the <get_peek_export>) are sent out this port via its
    `write` method.

    .. code-block:: python
        def write (T t)

    All connected analysis exports and imps will receive get transactions.
    See <uvm_tlm_if_base #(T1,T2)> for more information on the `write` method.

    The following are aliases to the above put_export.

    :ivar UVMPutImp blocking_put_export:
    :ivar UVMPutImp nonblocking_put_export:

    The following are all aliased to the above get_peek_export, which provides
    the superset of these interfaces.

    :ivar `UVMGetPeekImp` blocking_get_export:
    :ivar `UVMGetPeekImp` nonblocking_get_export:
    :ivar `UVMGetPeekImp` get_export:
    :ivar `UVMGetPeekImp` blocking_peek_export:
    :ivar `UVMGetPeekImp` nonblocking_peek_export:
    :ivar `UVMGetPeekImp` peek_export:
    :ivar `UVMGetPeekImp` blocking_get_peek_export:
    :ivar `UVMGetPeekImp` nonblocking_get_peek_export:
    """

    def __init__(self, name, parent=None):
        """
          The `name` and `parent` are the normal `UVMComponent` constructor arguments.
          The `parent` should be `None` if the `UVMTLMFIFO` is going to be used in a
          statically elaborated construct (e.g., a module). The `size` indicates the
          maximum size of the FIFO. A value of zero indicates no upper bound.

        Args:
            name (str): Name of the component
            parent (UVMComponent): Parent component.
        """
        UVMComponent.__init__(self, name, parent)
        self.put_export = UVMPutImp("put_export", self)
        self.blocking_put_export = self.put_export
        self.nonblocking_put_export = self.put_export

        get_peek_export = UVMGetPeekImp("get_peek_export", self)
        self.get_peek_export = get_peek_export
        self.blocking_get_peek_export = get_peek_export
        self.nonblocking_get_peek_export = get_peek_export
        self.blocking_get_export = get_peek_export
        self.nonblocking_get_export = get_peek_export
        self.get_export = get_peek_export
        self.blocking_peek_export = get_peek_export
        self.nonblocking_peek_export = get_peek_export
        self.peek_export = get_peek_export
        self.put_ap = UVMAnalysisPort("put_ap", self)
        self.get_ap = UVMAnalysisPort("get_ap", self)

    def build_phase(self, phase):
        """
        Args:
            phase (UVMPhase):
        """
        self.build()  # for backward compat, won't cause auto-config


    def flush(self):
        uvm_report_error("flush", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)

    def size(self):
        uvm_report_error("size", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0


    async def put(self, t):
        uvm_report_error("put", UVM_TLM_FIFO_TASK_ERROR, UVM_NONE)


    async def get(self,t):
        uvm_report_error("get", UVM_TLM_FIFO_TASK_ERROR, UVM_NONE)


    async def peek(self, t):
        uvm_report_error("peek", UVM_TLM_FIFO_TASK_ERROR, UVM_NONE)

    def try_put(self, t):
        uvm_report_error("try_put", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def try_get(self, t):
        uvm_report_error("try_get", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def try_peek(self, t):
        uvm_report_error("try_peek", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def can_put(self):
        uvm_report_error("can_put", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def can_get(self):
        uvm_report_error("can_get", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def can_peek(self):
        uvm_report_error("can_peek", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def ok_to_put(self):
        uvm_report_error("ok_to_put", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return None

    def ok_to_get(self):
        uvm_report_error("ok_to_get", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return None

    def ok_to_peek(self):
        uvm_report_error("ok_to_peek", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return None

    def is_empty(self):
        uvm_report_error("is_empty", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0

    def is_full(self):
        uvm_report_error("is_full", UVM_TLM_FIFO_FUNCTION_ERROR)
        return 0

    def used(self):
        uvm_report_error("used", UVM_TLM_FIFO_FUNCTION_ERROR, UVM_NONE)
        return 0
