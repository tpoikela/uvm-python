#//
#// -------------------------------------------------------------
#//    Copyright 2010-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2019 Tuomas Poikela (tpoikela)
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

from uvm.macros import uvm_object_utils
from uvm.reg import *
from uvm.base import *

#//
#// This example demonstrates how to include a user-defined register
#// in a register model.
#//

#//
#// The user_acp_reg has a user-defined behavior
#//
#// It increments by 1 after every write
#//

class user_acp_incr_on_write_cbs(UVMRegCbs):

    def __init__(self, name="write_cbs"):
        UVMRegCbs.__init__(self, name)
        self.num_called = 0


    def post_predict(self, fld, previous, value, kind, path, _map):
        if (kind != UVM_PREDICT_WRITE):
            return
        if (path != UVM_FRONTDOOR):
            return
        value.push(previous + 1)
        self.num_called += 1


class user_acp_reg(UVMReg):
    #
    #   local UVMRegField value;
    #
    #
    def __init__(self, name="user_acp_reg"):
        UVMReg.__init__(self, name,16,UVM_NO_COVERAGE)

    def build(self):
        self.value = UVMRegField.type_id.create("value", None, self.get_full_name())
        self.value.configure(self, 16, 0, "RW", 0, 0x0000, 1, 0, 0);
        self.value.set_compare(UVM_NO_CHECK);

        UVMResourceDb.set("REG::" + self.get_full_name(),
                "NO_REG_BIT_BASH_TEST", 1)
        UVMResourceDb.set("REG::" + self.get_full_name(),
                "NO_REG_ACCESS_TEST", 1);
        self.cb = user_acp_incr_on_write_cbs()
        UVMRegFieldCb.add(self.value, self.cb)
        #   endfunction: build


    
    async def pre_write(self, rw):
        m_data = 0
        rg = None

        #assert($cast(rg,rw.element));
        rg = rw.element

        # Predict the value that will be in the register
        m_data = rg.get() + 1

        # If a backdoor write is used, replace the value written
        # with the incremented value to emulate the front-door
        if (rw.path == UVM_BACKDOOR):
            rw.value[0] = m_data
        await Timer(5, "NS")
        #   endtask: pre_write
    #
    #endclass : user_acp_reg

uvm_object_utils(user_acp_reg)


class block_B(UVMRegBlock):
    #   user_acp_reg user_acp;

    def __init__(self, name="B"):
        UVMRegBlock.__init__(self, name, UVM_NO_COVERAGE)

    def build(self):
        self.default_map = self.create_map("", 0, 1, UVM_BIG_ENDIAN)
        self.user_acp = user_acp_reg.type_id.create("user_acp", None, self.get_full_name())
        self.user_acp.configure(self, None, "acp")
        self.user_acp.build()
    
        self.default_map.add_reg(self.user_acp, 0x0000, "RW")
        self.lock_model()

    #endclass : block_B
uvm_object_utils(block_B)
