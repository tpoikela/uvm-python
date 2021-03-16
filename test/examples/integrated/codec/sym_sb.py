#// 
#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#// 
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#// 
#//        http://www.apache.org/licenses/LICENSE-2.0
#// 
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//

from uvm import *

uvm_analysis_imp_sym_sb_expected = uvm_analysis_imp_decl("_sym_sb_expected")
uvm_analysis_imp_sym_sb_observed = uvm_analysis_imp_decl("_sym_sb_observed")

class sym_sb(UVMComponent):

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.expected = uvm_analysis_imp_sym_sb_expected("expected", self)
        self.observed = uvm_analysis_imp_sym_sb_observed("observed", self)
        self.n_obs_thresh = 10
        self.m_sb = []
        self.error = 0
        self.m_n_obs = 0

    def build_phase(self, phase):
        thr = []
        if UVMConfigDb.get(self, "", "n_obs_thresh", thr):  # cast to 'void' removed
            self.n_obs_thresh = thr[0]


    def write_sym_sb_expected(self, tr):
        uvm_info("SB/EXP", sv.sformatf("Expected: 0x%h", tr.chr), UVM_MEDIUM)
        self.m_sb.append(tr.chr)


    def write_sym_sb_observed(self, tr):
        exp = 0x00
        uvm_info("SB/OBS", sv.sformatf("Observed: 0x%h", tr.chr), UVM_MEDIUM)
        exp = self.m_sb.pop(0)
        if tr.chr != exp:
            self.error = 1
            uvm_error("SB/MISMTCH", sv.sformatf("Symbol 0x%h observed instead of expected 0x%h",
                tr.chr, exp))
        self.m_n_obs += 1

    async def reset_phase(self, phase):
        self.m_n_obs = 0
        self.m_sb = []

    async def main_phase(self, phase):
        phase.raise_objection(self, "Have not checked enough data")
        while True:
            await Timer(250, "NS")
            if self.m_n_obs > self.n_obs_thresh:
                break
        phase.drop_objection(self, "Enough data has been observed")

    def check_phase(self, phase):
        if self.m_n_obs < self.n_obs_thresh:
            uvm_error("ERR/SCB", "Not enough items were observed")
            self.error = 1

uvm_component_utils(sym_sb)
