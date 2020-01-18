#//
#//------------------------------------------------------------------------------
#//   Copyright 2011 Mentor Graphics Corporation
#//   Copyright 2011 Cadence Design Systems, Inc.
#//   Copyright 2011 Synopsys, Inc.
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

from uvm.reg.uvm_reg_block import *
from uvm.reg.uvm_reg_model import *
from uvm.macros import *
from reg_B import reg_block_B


class reg_sys_S(UVMRegBlock):
    #
    # rand reg_block_B B[2]

    def __init__(self, name="S"):
        super().__init__(name, UVM_NO_COVERAGE)
        self.B = [None] * 2  # reg_block_B
        self.rand("B")
        #  endfunction: new

    def build(self):

        self.default_map = self.create_map("default_map", 0x0, 1, UVM_LITTLE_ENDIAN)

        for i in range(len(self.B)):
            self.B[i] = reg_block_B.type_id.create(sv.sformatf("B[%0d]", i))
            self.B[i].configure(self)
            self.B[i].build()
            self.default_map.add_submap(self.B[i].default_map, 0x100 + i * 0x100)


uvm_object_utils(reg_sys_S)

