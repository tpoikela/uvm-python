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


class vip_sequence(UVMSequence):

    def __init__(self, name):
        super().__init__(name)
        self.set_automatic_phase_objection(1)


#class vip_one_char_seq(vip_sequence):
    #
    #  `uvm_object_utils(vip_one_char_seq)
    #   
    #  def __init__(self, name="vip_one_char_seq")
    #    super().__init__(name)
    #  endfunction
    #  
    #async
    #  def body(self)
    #    `uvm_do(req)
    #  endtask
    #  
    #endclass


class vip_sentence_seq(vip_sequence):

    def __init__(self, name="vip_sentence_seq"):
        super().__init__(name)

    async def body(self):
        for i in range(128):
            uvm_do(self.req)

uvm_object_utils(vip_sentence_seq)


#class vip_idle_esc_seq(vip_sequence):
    #
    #  `uvm_object_utils(vip_idle_esc_seq)
    #
    #  def __init__(self, name="vip_idle_esc_seq")
    #    super().__init__(name)
    #  endfunction
    #  
    #async
    #  def body(self)
    #     repeat (128):
    #        `uvm_do_with(req, {chr inside {8'hE7, 8'h81}; })
    #     end
    #  endtask
    #  
from uvm.seq.uvm_sequence import *
from uvm.macros import *
    #endclass
