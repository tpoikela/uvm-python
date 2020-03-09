#//----------------------------------------------------------------------
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
#//----------------------------------------------------------------------

from ..tlm1 import (UVMTLMFIFO, UVMAnalysisImp)
from ..macros import (uvm_fatal)


class UVMSequencerAnalysisFIFO(UVMTLMFIFO):

    #  uvm_analysis_imp #(RSP, UVMSequencerAnalysisFIFO #(RSP)) analysis_export
    #  uvm_sequencer_base sequencer_ptr


    def __init__(self, name, parent=None):
        super().__init__(name, parent, 0)
        self.analysis_export = UVMAnalysisImp("analysis_export", self)
        self.sequencer_ptr = None


    def write(self, t):
        if self.sequencer_ptr is None:
            uvm_fatal("SEQRNULL", "The sequencer pointer is None when attempting a write")
        self.sequencer_ptr.analysis_write(t)
