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

#typedef enum {USB_TLM_TOKEN, USB_TLM_DATA, USB_TLM_HANDSHAKE} usb_tlm_phase
USB_TLM_TOKEN = 0
USB_TLM_DATA = 1
USB_TLM_HANDSHAKE = 2


class usb_xfer(UVMSequenceItem):

    #   typedef enum {IN, OUT} kind_e
    #   typedef enum {ACK, NAK, STALL, NYET} status_e

    IN = 10
    OUT = 20

    ACK = 0
    NAK = 1
    STALL = 2
    NYET = 3

    #   rand bit [6:0] addr
    #   rand bit [3:0] endp
    #   rand kind_e   kind;  
    #   rand byte      data[]
    #   rand status_e  status


    def __init__(self, name="usb_xfer"):
        super().__init__(name)
        self.addr = 0
        self.endp = 0x0
        self.kind = usb_xfer.IN
        self.data = []
        self.status = usb_xfer.ACK

    def convert2string(self):
        convert2string = sv.sformatf("dev=%h.%h kind=%s hndsk=%s data=h",
            self.addr, self.endp, int(self.kind), int(self.status))

        #      case (data.size())
        #       0: return {convert2string, "[]"}
        #       1: return sv.sformatf("%s0x%h", convert2string, data[0])
        #       2: return sv.sformatf("%s0x%h 0x%h", convert2string, data[0], data[1])
        #       3: return sv.sformatf("%s0x%h 0x%h 0x%h", convert2string,
        #                           data[0], data[1], data[2])
        #
        #       default:
        #          return sv.sformatf("%s0x%h 0x%h .. 0x%h (%0d bytes)", convert2string,
        #                           data[0], data[1], data[data.size()-1],
        #                           data.size())
        #      endcase
        return convert2string


uvm_object_utils_begin(usb_xfer)
#     `uvm_field_enum(kind_e, kind, UVM_ALL_ON | UVM_NOPACK)
#     `uvm_field_array_int(data, UVM_ALL_ON | UVM_NOPACK)
#     `uvm_field_enum(status_e, status, UVM_ALL_ON | UVM_NOPACK)
uvm_object_utils_end(usb_xfer)
