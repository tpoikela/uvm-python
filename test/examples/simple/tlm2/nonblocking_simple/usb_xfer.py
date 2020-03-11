#// 
#// -------------------------------------------------------------
#//    Copyright 2010-2011 Synopsys, Inc.
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

from uvm.seq.uvm_sequence_item import *
from uvm.macros import *
from uvm.base import sv
from enum import Enum, auto

#typedef enum {USB_TLM_TOKEN, USB_TLM_DATA, USB_TLM_HANDSHAKE} usb_tlm_phase
USB_TLM_TOKEN = 0
USB_TLM_DATA = 1
USB_TLM_HANDSHAKE = 2


class status_e(Enum):
    ACK = auto()
    NAK = auto()
    STALL = auto()
    NYET = auto()


class usb_xfer(UVMSequenceItem):

    IN = 10
    OUT = 20

    ACK = status_e.ACK
    NAK = status_e.NAK
    STALL = status_e.STALL
    NYET = status_e.NYET

    #   rand kind_e   kind;  
    #   rand byte      data[]
    #   rand status_e  status


    def __init__(self, name="usb_xfer"):
        super().__init__(name)
        self.addr = 0
        self.rand('addr', range(0, (1 << 7) - 1))
        self.endp = 0x0
        self.rand('endp', range(0, (1 << 4) - 1))
        self.kind = usb_xfer.IN
        self.rand('kind', [usb_xfer.IN, usb_xfer.OUT])
        self.data = []
        self.status = usb_xfer.ACK

    def convert2string(self):
        convert2string = sv.sformatf("dev=%h.%h kind=%s hndsk=%s data=h",
            self.addr, self.endp, int(self.kind), self.status.name)
        ndata = len(self.data)

        if ndata == 0:
            return convert2string + "[]"
        if ndata == 1:
            return sv.sformatf("%s0x%h", convert2string, self.data[0])
        if ndata == 2:
            return sv.sformatf("%s0x%h 0x%h", convert2string, self.data[0],
                    self.data[1])
        if ndata == 3:
            return sv.sformatf("%s0x%h 0x%h 0x%h", convert2string,
                self.data[0], self.data[1], self.data[2])

        return sv.sformatf("%s0x%h 0x%h .. 0x%h (%0d bytes)", convert2string,
            self.data[0], self.data[1], self.data[-1],
            len(self.data))

uvm_object_utils_begin(usb_xfer)
#     `uvm_field_enum(kind_e, kind, UVM_ALL_ON | UVM_NOPACK)
#     `uvm_field_array_int(data, UVM_ALL_ON | UVM_NOPACK)
#     `uvm_field_enum(status_e, status, UVM_ALL_ON | UVM_NOPACK)
uvm_object_utils_end(usb_xfer)
