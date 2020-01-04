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

#------------------------------------------------------------------------------
# Title: Analysis Ports
#------------------------------------------------------------------------------
#
# This section defines the port, export, and imp classes used for transaction
# analysis.
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Class: uvm_analysis_port
#
# Broadcasts a value to all subscribers implementing a <uvm_analysis_imp>.
#
#| class mon extends uvm_component
#|   uvm_analysis_port#(trans) ap
#|
#|   function new(string name = "sb", uvm_component parent = null)
#|      super.new(name, parent)
#|      ap = new("ap", this)
#|   endfunction
#|
#|   task run_phase(uvm_phase phase)
#|       trans t
#|       ...
#|       ap.write(t)
#|       ...
#|   endfunction
#| endclass
#------------------------------------------------------------------------------

class UVMAnalysisPort(UVMPortBase):

    def __init__(self, name, parent):
        UVMPortBase.__init__(self, name, parent, UVM_PORT, 0, UVM_UNBOUNDED_CONNECTIONS)
        self.m_if_mask = UVM_TLM_ANALYSIS_MASK

    def get_type_name(self):
        return "uvm_analysis_port"

    # Method: write
    # Send specified value to all connected interface
    def write(self, t):
        for i in range(0, self.size()):
            tif = self.get_if(i)
            if tif is None:
                uvm_report_fatal("NTCONN", ("No uvm_tlm interface is connected to ",
                  + self.get_full_name() + " for executing write()"), UVM_NONE)
            tif.write(t)

    #endclass

#------------------------------------------------------------------------------
# Class: uvm_analysis_imp
#
# Receives all transactions broadcasted by a <uvm_analysis_port>. It serves as
# the termination point of an analysis port/export/imp connection. The component
# attached to the ~imp~ class--called a ~subscriber~-- implements the analysis
# interface.
#
# Will invoke the ~write(T)~ method in the parent component.
# The implementation of the ~write(T)~ method must not modify
# the value passed to it.
#
#| class sb extends uvm_component
#|   uvm_analysis_imp#(trans, sb) ap
#|
#|   function new(string name = "sb", uvm_component parent = null)
#|      super.new(name, parent)
#|      ap = new("ap", this)
#|   endfunction
#|
#|   function void write(trans t)
#|       ...
#|   endfunction
#| endclass
#------------------------------------------------------------------------------

class UVMAnalysisImp:
    #`UVM_IMP_COMMON(`UVM_TLM_ANALYSIS_MASK,"uvm_analysis_imp",IMP)
    def write (self, t):
        self.m_imp.write (t)
    #endclass
UVMAnalysisImp = UVM_IMP_COMMON(UVMAnalysisImp, UVM_TLM_ANALYSIS_MASK, "uvm_analysis_imp")

#------------------------------------------------------------------------------
# Class: uvm_analysis_export
#
# Exports a lower-level <uvm_analysis_imp> to its parent.
#------------------------------------------------------------------------------

class UVMAnalysisExport(UVMPortBase):

    # Function: new
    # Instantiate the export.
    def __init__(self, name, parent=None):
        UVMPortBase.__init__(self, name, parent, UVM_EXPORT, 1, UVM_UNBOUNDED_CONNECTIONS)
        self.m_if_mask = UVM_TLM_ANALYSIS_MASK

    def get_type_name(self):
        return "uvm_analysis_export"

    # analysis port differs from other ports in that it broadcasts
    # to all connected interfaces. Ports only send to the interface
    # at the index specified in a call to set_if (0 by default).
    def write(self, t):
        for i in range(0, self.size()):
            tif = self.get_if(i)
            if tif is None:
                uvm_report_fatal("NTCONN", ("No uvm_tlm interface is connected to "
                    + self.get_full_name() + " for executing write()"), UVM_NONE)
            tif.write(t)

    #endclass

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
