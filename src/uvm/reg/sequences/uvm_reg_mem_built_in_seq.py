#//
#// -------------------------------------------------------------
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Synopsys, Inc.
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

#//------------------------------------------------------------------------------
#// Class: UVMRegMemBuiltInSeq
#//
#// Sequence that executes a user-defined selection
#// of pre-defined register and memory test sequences.
#//
#//------------------------------------------------------------------------------

import cocotb
from ..uvm_reg_sequence import UVMRegSequence
from ...macros import uvm_object_utils, uvm_error, uvm_info
from ...base.uvm_resource_db import UVMResourceDb
from ..uvm_reg_model import *


class UVMRegMemBuiltInSeq(UVMRegSequence):  # (uvm_sequence #(uvm_reg_item))


    def __init__(self, name="UVMRegMemBuiltInSeq"):
        super().__init__(name)
        #   // Variable: model
        #   //
        #   // The block to be tested. Declared in the base class.
        #   //
        self.model = None  # uvm_reg_block

        #   // Variable: tests
        #   //
        #   // The pre-defined test sequences to be executed.
        #   //
        self.tests = UVM_DO_ALL_REG_MEM_TESTS

    #   // Task: body
    #   //
    #   // Executes any or all the built-in register and memory sequences.
    #   // Do not call directly. Use seq.start() instead.
    #
    @cocotb.coroutine
    def body(self):  # task

        if self.model is None:
            uvm_error("UVMRegMemBuiltInSeq", "Not block or system specified to run sequence on")
            return


        uvm_info("START_SEQ","\n\nStarting " + self.get_name() + " sequence...\n",UVM_LOW)

    #      if (tests & UVM_DO_REG_HW_RESET  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_HW_RESET_TEST", 0) is None ):
    #        uvm_reg_hw_reset_seq seq = uvm_reg_hw_reset_seq.type_id.create("reg_hw_reset_seq")
    #        seq.model = model
    #        seq.start(None,self)
    #        uvm_info("FINISH_SEQ",{"Finished ",seq.get_name()," sequence."},UVM_LOW)
    #      end
    #
    #      if (tests & UVM_DO_REG_BIT_BASH  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_BIT_BASH_TEST", 0) is None ):
    #        uvm_reg_bit_bash_seq seq = uvm_reg_bit_bash_seq.type_id.create("reg_bit_bash_seq")
    #        seq.model = model
    #        seq.start(None,self)
    #        uvm_info("FINISH_SEQ",{"Finished ",seq.get_name()," sequence."},UVM_LOW)
    #      end
    #
    #      if (tests & UVM_DO_REG_ACCESS  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_ACCESS_TEST", 0) is None ):
    #        uvm_reg_access_seq seq = uvm_reg_access_seq.type_id.create("reg_access_seq")
    #        seq.model = model
    #        seq.start(None,self)
    #        uvm_info("FINISH_SEQ",{"Finished ",seq.get_name()," sequence."},UVM_LOW)
    #      end
    #
    #      if (tests & UVM_DO_MEM_ACCESS  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_MEM_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_MEM_ACCESS_TEST", 0) is None ):
    #        uvm_mem_access_seq seq = uvm_mem_access_seq.type_id.create("mem_access_seq")
    #        seq.model = model
    #        seq.start(None,self)
    #        uvm_info("FINISH_SEQ",{"Finished ",seq.get_name()," sequence."},UVM_LOW)
    #      end
    #
    #      if (tests & UVM_DO_SHARED_ACCESS  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_SHARED_ACCESS_TEST", 0) is None ):
    #        uvm_reg_mem_shared_access_seq seq = uvm_reg_mem_shared_access_seq.type_id.create("shared_access_seq")
    #        seq.model = model
    #        seq.start(None,self)
    #        uvm_info("FINISH_SEQ",{"Finished ",seq.get_name()," sequence."},UVM_LOW)
    #      end
    #
    #      if (tests & UVM_DO_MEM_WALK  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_REG_TESTS", 0) is None  and
    #          UVMResourceDb.get_by_name({"REG::",model.get_full_name()},
    #                                             "NO_MEM_WALK_TEST", 0) is None ):
    #        uvm_mem_walk_seq seq = uvm_mem_walk_seq.type_id.create("mem_walk_seq")
    #        seq.model = model
    #        seq.start(None,self)
    #        uvm_info("FINISH_SEQ",{"Finished ",seq.get_name()," sequence."},UVM_LOW)
    #      end
    #
    #   endtask: body
    #
    #endclass: UVMRegMemBuiltInSeq

uvm_object_utils(UVMRegMemBuiltInSeq)
