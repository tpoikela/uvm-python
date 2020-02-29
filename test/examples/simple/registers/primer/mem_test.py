
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
from cocotb.triggers import Timer
from uvm.macros import *
from uvm.base import UVMConfigDb
from uvm.reg import UVMRegSequence
from uvm.reg.uvm_reg_backdoor import UVMRegBackdoor
from uvm.reg.uvm_reg_model import (UVM_IS_OK, UVM_BACKDOOR)


class mem_backdoor(UVMRegBackdoor):

    def __init__(self, name="mem_backdoor"):
        super().__init__(name)
        self.dut = None
        self.mem_name = "DMA"

    
    async def write(self, rw):  # task
        await self.do_pre_write(rw)  # Required, as stated in uvm_reg_backdoor
        #uvm_fatal("RegModel", "UVMRegBackdoor::write() method has not been overloaded")
        print("rw.offset is " + str(rw.offset))
        self.dut.DMA[rw.offset] <= rw.value[0]
        rw.status = UVM_IS_OK
        await self.do_post_write(rw)  # Required, as stated in uvm_reg_backdoor


    def read_func(self, rw):
        # uvm_fatal("RegModel", "UVMRegBackdoor::read_func() method has not been overloaded")
        data = 0
        rw.status = UVM_IS_OK
        offset = rw.offset
        data = self.dut.DMA[offset]
        rw.value[0] = data
        #endfunction



class mem_test_seq(UVMRegSequence):

    def __init__(self, name="user_test_seq"):
        super().__init__(name)
        self.addr = None  # type: int
        self.data = None  # type: int
        self.dut = None

    
    async def body(self):
        arr = []
        if UVMConfigDb.get(None, "", "dut", arr):
            self.dut = arr[0]
        else:
            uvm_fatal("NO_DUT", "Could not find DUT from config_db")
        model = self.model
        dma_ram = model.DMA_RAM
        bkd = mem_backdoor("backdoor")
        dma_ram.set_backdoor(bkd)
        bkd.dut = self.dut

        for i in range(10):

            status = []
            data = 0x1234
            offset = i * 4
            await dma_ram.write(status, offset, data)
            await Timer(100, "NS")

            status = []
            data = []
            offset = i * 4
            await dma_ram.read(status, offset, data)
            exp = data[0]
            await Timer(100, "NS")
            status = []
            data = []
            await dma_ram.read(status, offset, data, path=UVM_BACKDOOR)
            if exp != data[0]:
                uvm_error("MEM_READ_ERR", "Exp: {}, Got: {}".format(exp, data[0]))

            # Test backdoor access with write/read operation
            ref_data = 0xBEEFFACE
            status = []
            await Timer(100, "NS")
            await dma_ram.write(status, offset, ref_data, path=UVM_BACKDOOR)
            status = []
            data = []
            await Timer(100, "NS")
            await dma_ram.read(status, offset, data, path=UVM_BACKDOOR)
            if data[0] != ref_data:
                uvm_fatal("MEM_DATA_ERR", "Exp: {}, Got: {}".format(ref_data, data[0]))
        await Timer(100, "NS")


uvm_object_utils(mem_test_seq)
