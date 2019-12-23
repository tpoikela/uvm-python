#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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

from uvm.seq import UVMSequencer
from uvm.tlm1 import UVMBlockingPeekPort
from uvm.macros import uvm_component_utils

#//------------------------------------------------------------------------------
#//
#// CLASS: ubus_slave_sequencer
#//
#//------------------------------------------------------------------------------
#class ubus_slave_sequencer extends uvm_sequencer #(ubus_transfer);


class ubus_slave_sequencer(UVMSequencer):

    def __init__(self, name, parent):
        UVMSequencer.__init__(self, name, parent)
        self.addr_ph_port = UVMBlockingPeekPort("addr_ph_port", self)
        #  endfunction : new

    #endclass : ubus_slave_sequencer


uvm_component_utils(ubus_slave_sequencer)
