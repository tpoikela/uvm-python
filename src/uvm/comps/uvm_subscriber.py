#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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
#//------------------------------------------------------------------------------

from uvm.base.uvm_component import UVMComponent
from uvm.tlm1 import UVMAnalysisImp


class UVMSubscriber(UVMComponent):  # (type T=int) extends uvm_component
    """
    This class provides an analysis export for receiving transactions from a
    connected analysis export. Making such a connection "subscribes" this
    component to any transactions emitted by the connected analysis port.

    Subtypes of this class must define the write method to process the incoming
    transactions. This class is particularly useful when designing a coverage
    collector that attaches to a monitor.

    :ivar UVMAnalysisImp analysis_export: This export provides access to the
        write method, which derived subscribers must implement.
    """


    #  // Function: new
    #  //
    #  // Creates and initializes an instance of this class using the normal
    #  // constructor arguments for <uvm_component>: ~name~ is the name of the
    #  // instance, and ~parent~ is the handle to the hierarchical parent, if any.
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.analysis_export = UVMAnalysisImp("analysis_imp", self)

    #  // Function: write
    #  //
    #  // A method that must be defined in each subclass. Access
    #  // to this method by outside components should be done via the
    #  // analysis_export.
    def write(self, t):
        raise Exception("Pure virtual function. Must be implemented")
