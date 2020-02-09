#//----------------------------------------------------------------------
#//   Copyright 2010 Mentor Graphics Corporation
#//   Copyright 2010-2011 Synopsys, Inc
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
#

from uvm import UVMComponent, uvm_component_utils
from uvm.macros import *

from initiator import initiator
from target import target

class tb_env(UVMComponent):

    def __init__(self, name="tb_env", parent=None):
        super().__init__(name, parent)
        self.master = None
        self.slave = None

    def build_phase(self, phase):
        self.master = initiator.type_id.create("master", self)
        self.slave  = target.type_id.create("slave", self)

    def connect_phase(self, phase):
        self.master.sock.connect(self.slave.sock)

    def check_phase(self, phase):
        if self.slave.num_transport == 0:
            uvm_fatal("ERR_NUM_TRANSPORT", "Got zero items!")

uvm_component_utils(tb_env)
