
#// -------------------------------------------------------------
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
from uvm.reg import UVMRegSequence


class mem_test_seq(UVMRegSequence):

    def __init__(self, name="user_test_seq"):
        super().__init__(name)
        self.addr = None  # type: int
        self.data = None  # type: int

    @cocotb.coroutine
    def body(self):
        model = self.model
        dma_ram = model.DMA_RAM

        for i in range(10):
            status = []
            data = [0x1]
            offset = i * 1 << 4
            yield dma_ram.write(status, offset, data)
            status = []
            data = []
            yield dma_ram.read(status, offset, data)


uvm_object_utils(mem_test_seq)
