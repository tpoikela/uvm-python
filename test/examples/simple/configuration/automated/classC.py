#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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

from uvm import (UVMComponent, sv, UVM_DEFAULT)
from uvm.macros import *


class C(UVMComponent):


    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.v = 0  # type: int
        self.s = 0  # type: int
        self.myaa = {}  # type: str
        self.my_conf_obj = None
        self.tag = ''


    def build_phase(self, phase):
        super().build_phase(phase)
        sv.display("%s: In Build: v = %0d  s = %0d", self.get_full_name(),
            self.v, self.s)


    #endclass


uvm_component_utils_begin(C)
uvm_field_int('v', UVM_DEFAULT)
uvm_field_int('s', UVM_DEFAULT)
uvm_field_object('my_conf_obj', UVM_DEFAULT)
uvm_field_string('tag', UVM_DEFAULT)
#uvm_field_aa_string_string('myaa', UVM_DEFAULT)
uvm_component_utils_end(C)
