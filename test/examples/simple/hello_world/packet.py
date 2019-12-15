#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela (tpoikela)
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

from uvm.base import UVMTransaction
from uvm.macros import uvm_object_utils

class packet(UVMTransaction):

    #`ifndef NO_RAND
    #  rand
    #`endif
    #  int addr;

    #  constraint c { addr >= 0 && addr < 'h100; }

    def __init__(self, name):
        UVMTransaction.__init__(self, name)
        self.addr = 0

uvm_object_utils(packet)
#uvm_field_int(addr, UVM_ALL_ON)
