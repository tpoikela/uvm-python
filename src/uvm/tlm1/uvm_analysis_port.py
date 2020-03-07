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

from ..base.uvm_port_base import *
from .uvm_tlm_imps import *

"""
Analysis Ports

This section defines the port, export, and imp classes used for transaction
analysis.
"""


class UVMAnalysisPort(UVMPortBase):
    """
    Broadcasts a value to all subscribers implementing a <uvm_analysis_imp>.

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
        Method: write
        Send specified value to all connected interface
        Args:
            t: Transaction to broadcast.
        """
        for i in range(0, self.size()):
            tif = self.get_if(i)
            if tif is None:
                uvm_report_fatal("NTCONN", ("No uvm_tlm interface is connected to ",
                  + self.get_full_name() + " for executing write()"), UVM_NONE)
            tif.write(t)

    #endclass


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
            t: Transaction to write.
        """
        self.m_imp.write(t)

UVMAnalysisImp = UVM_IMP_COMMON(UVMAnalysisImp, UVM_TLM_ANALYSIS_MASK, "uvm_analysis_imp")

#------------------------------------------------------------------------------
# Class: uvm_analysis_export
#
# Exports a lower-level <uvm_analysis_imp> to its parent.
#------------------------------------------------------------------------------

class UVMAnalysisExport(UVMPortBase):

    def __init__(self, name, parent=None):
        """
        Instantiate the export.
        Args:
            name: Name of the export.
            parent: Parent component.
        """
        UVMPortBase.__init__(self, name, parent, UVM_EXPORT, 1, UVM_UNBOUNDED_CONNECTIONS)
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
                uvm_report_fatal("NTCONN", ("No uvm_tlm interface is connected to "
                    + self.get_full_name() + " for executing write()"), UVM_NONE)
            tif.write(t)


import unittest

class TestUVMAnalysisPort(unittest.TestCase):

    def test_ports(self):
        from ..base.uvm_domain import UVMDomain
        from ..base.uvm_component import UVMComponent
        domains = UVMDomain.get_common_domain()

        class MyComp(UVMComponent):
            def build(self):
                self.analysis_imp = UVMAnalysisImp('ap', self)

            def write(self, t):
                self.written = True
                self.t = t

        imp = UVMComponent("port_parent", None)
        analysis_port = UVMAnalysisPort('aport', None)
        analysis_export = UVMAnalysisExport('my_export_in_test1', imp)
        targetComp = MyComp('my_comp', None)
        targetComp.build()
        analysis_port.connect(analysis_export)
        analysis_export.connect(targetComp.analysis_imp)
        #analysis_port.connect(targetComp.analysis_imp)
        analysis_port.resolve_bindings()

        analysis_port.write(12345)
        self.assertEqual(targetComp.written, True)
        self.assertEqual(targetComp.t, 12345)

if __name__ == '__main__':
    unittest.main()
