#//----------------------------------------------------------------------
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

from uvm.base.uvm_component import UVMComponent
from uvm.macros import *

from host import host
from device import device


class tb_env(UVMComponent):


    def __init__(self, name="tb_env", parent=None):
        super().__init__(name, parent)
        self.hst = None
        self.dev = None


    def build_phase(self, phase):
        self.hst = host.type_id.create("hst", self)
        self.dev = device.type_id.create("dev", self)


    def connect_phase(self, phase):
        self.hst.sock.connect(self.dev.sock)
