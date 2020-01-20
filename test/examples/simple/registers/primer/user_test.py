#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
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

import cocotb
from uvm.macros import *
from uvm.reg import uvm_reg_sequence
from uvm.base import sv


class user_test_seq(uvm_reg_sequence):

    def __init__(self, name="user_test_seq"):
        super().__init__(name)
        self.addr = None  # type: int
        self.data = None  # type: int

    #   rand bit   [31:0] addr
    #   rand logic [31:0] data

    @cocotb.coroutine
    def body(self):
        #reg_block_slave model

        #sv.cast(model, self.model)
        model = self.model

        # Randomize the content of 10 random indexed registers
        for i in range(10):
            idx = sv.urandom_range(0, 255)
            data = sv.urandom()
            status = []
            default_map = model.TABLES[idx].get_default_map()
            yield model.TABLES[idx].write(status, data, _map=default_map, parent=self)

        # Find which indexed registers are non-zero
        for i in range(len(model.TABLES)):
            data = 0
            status = []

            yield model.TABLES[i].read(status, data)
            if data != 0:
                print(sv.sformatf("TABLES[%0d] is 0x%h...", i, data))


uvm_object_utils(user_test_seq)
