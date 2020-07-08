#
#----------------------------------------------------------------------
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
#----------------------------------------------------------------------
"""
Analysis Ports

This section defines the port, export, and imp classes used for transaction
analysis.
"""

from ..macros.uvm_message_defines import uvm_fatal
from ..macros.uvm_tlm_defines import UVM_TLM_ANALYSIS_MASK
from ..base.uvm_port_base import UVM_UNBOUNDED_CONNECTIONS, UVMPortBase
from .uvm_tlm_imps import UVM_EXPORT, UVM_IMP_COMMON, UVM_PORT


class UVMAnalysisPort(UVMPortBase):
    """
    Broadcasts a value to all subscribers implementing a `UVMAnalysisImp`.

    .. code-block:: python
        class mon(UVMComponent):

            def __init__(self, name="sb", parent=None):
                super.new(name, parent)
                self.ap = UVMAnalysisPort("ap", self)

            async def run_phase(self, phase):
                t = None
                ...
                self.ap.write(t)
                ...
    """

    def __init__(self, name, parent):
        UVMPortBase.__init__(self, name, parent, UVM_PORT, 0, UVM_UNBOUNDED_CONNECTIONS)
        self.m_if_mask = UVM_TLM_ANALYSIS_MASK

    def get_type_name(self):
        return "uvm_analysis_port"

    def write(self, t):
        """
        Send specified value to all connected interface

        Args:
            t (any): Transaction to broadcast.
        """
        for i in range(0, self.size()):
            tif = self.get_if(i)
            if tif is None:
                uvm_fatal("NTCONN", ("No uvm_tlm interface is connected to " +
                    self.get_full_name() + " for executing write()"))
            else:
                tif.write(t)


class UVMAnalysisImp:
    """
    Receives all transactions broadcasted by a <uvm_analysis_port>. It serves as
    the termination point of an analysis port/export/imp connection. The component
    attached to the `imp` class--called a `subscriber`-- implements the analysis
    interface.

    Will invoke the ~write(T)~ method in the parent component.
    The implementation of the ~write(T)~ method must not modify
    the value passed to it.

    .. code-block:: python
      class sb(UVMComponent):
        uvm_analysis_imp#(trans, sb) ap

        def __init__(self, name="sb", parent=None):
           super().__init__(name, parent)
           self.ap = UVMAnalysisImp("ap", self)

        def write(self, t):
            ...

    """

    def write(self, t):
        """
        Args:
            t (any): Transaction to write.
        """
        self.m_imp.write(t)  # type: ignore


UVMAnalysisImp = UVM_IMP_COMMON(UVMAnalysisImp, UVM_TLM_ANALYSIS_MASK, "uvm_analysis_imp")


class UVMAnalysisExport(UVMPortBase):
    """
    Exports a lower-level `UVMAnalysisImp` to its parent. Export can be used to
    avoid long hierarchical paths like top.env.agent.monitor.
    """

    def __init__(self, name, parent=None):
        """
        Instantiate the export.

        Args:
            name (str): Name of the export.
            parent (UVMComponent): Parent component.
        """
        UVMPortBase.__init__(self, name, parent, UVM_EXPORT, 0, UVM_UNBOUNDED_CONNECTIONS)
        self.m_if_mask = UVM_TLM_ANALYSIS_MASK

    def get_type_name(self):
        return "uvm_analysis_export"

    def write(self, t):
        """
        Analysis port differs from other ports in that it broadcasts
        to all connected interfaces. Ports only send to the interface
        at the index specified in a call to set_if (0 by default).

        Args:
            t: Transaction to broadcast.
        """
        for i in range(0, self.size()):
            tif = self.get_if(i)
            if tif is None:
                uvm_fatal("NTCONN", ("No uvm_tlm interface is connected to "
                    + self.get_full_name() + " for executing write()"))
            else:
                tif.write(t)
