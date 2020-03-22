#//
#// -------------------------------------------------------------
#//    Copyright 2010 Mentor Graphics Corporation
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


from uvm.reg.uvm_reg_fifo import UVMRegFIFO
from uvm.macros import uvm_object_utils
from uvm.reg.uvm_reg_block import UVMRegBlock
from uvm.reg.uvm_reg_model import UVM_NO_COVERAGE, UVM_LITTLE_ENDIAN

FIFO_SIZE = 8


class fifo_reg(UVMRegFIFO):

    def __init__(self, name="fifo_reg"):
        super().__init__(name, FIFO_SIZE, 32, UVM_NO_COVERAGE)


uvm_object_utils(fifo_reg)


class reg_block_B(UVMRegBlock):

    #    rand fifo_reg FIFO

    def __init__(self, name="B"):
        super().__init__(name, UVM_NO_COVERAGE)


    def build(self):
        self.FIFO = fifo_reg.type_id.create("FIFO")
        self.FIFO.configure(self, None)
        self.FIFO.build()

        self.default_map = self.create_map("default_map_fifo", 0x0, 4, UVM_LITTLE_ENDIAN)
        self.default_map.add_reg(self.FIFO, 0x0, "RW")


uvm_object_utils(reg_block_B)
