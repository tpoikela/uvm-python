#// 
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#// 
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use self file except in
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
#
#
#typedef class dut_reset_seq
#class cmdline_test(uvm_test):
    #
    #   `uvm_component_utils(cmdline_test)
    #
    #   def __init__(self, name, parent)
    #      super().__init__(name, parent)
    #   endfunction
    #
    #@cocotb.coroutine
    #   def run_phase(self,uvm_phase phase); uvm_coreservice_t cs_ = uvm_coreservice_t::get()
    #
    #      tb_env env
    #
    #      phase.raise_objection(self)
    #
    #      sv.cast(env, uvm_top.find("env"))
    #
    #      begin
    #         dut_reset_seq rst_seq
    #         rst_seq = dut_reset_seq.type_id.create("rst_seq", self)
    #         rst_seq.start(None)
    #      end
    #      env.model.reset()
    #
    #      begin
    #         uvm_cmdline_processor opts = uvm_cmdline_processor::get_inst()
    #
    #         uvm_reg_sequence  seq
    #         string            seq_name
    #	 uvm_factory factory
    #
    #	 factory = cs_.get_factory()
    #         void'(opts.get_arg_value("+UVM_REG_SEQ=", seq_name))
    #         
    #         if (!sv.cast(seq, factory.create_object_by_name(seq_name,
    #                                                       get_full_name(),
    #                                                       "seq"))
    #              or  seq is None):
    #            `uvm_fatal("TEST/CMD/BADSEQ", {"Sequence ", seq_name,
    #                                           " is not a known sequence"})
    #         end
    #         seq.model = env.model
    #         seq.start(None)
    #      end
    #
    #      phase.drop_objection(self)
    #   endtask : run_phase
    #
    #endclass : cmdline_test
#
#
from uvm.comps.uvm_test import *
from uvm.macros import *
import cocotb
#
