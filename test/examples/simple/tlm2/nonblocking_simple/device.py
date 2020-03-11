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

import cocotb
from cocotb.triggers import Timer

from uvm.base.uvm_component import *
from uvm.macros import *
from usb_xfer import usb_xfer, USB_TLM_HANDSHAKE, USB_TLM_TOKEN, USB_TLM_DATA
from uvm.tlm2 import UVMTLMNbTargetSocket, uvm_tlm_sync_e


class device(UVMComponent):


    def __init__(self, name="device", parent=None):
        super().__init__(name, parent)
        self.sock = UVMTLMNbTargetSocket("sock", self)
        self.data = []


    async def fork_proc(self, xf, dl):
        ph = USB_TLM_HANDSHAKE
        await Timer(100, "NS")
        xf.status = usb_xfer.ACK
        assert(sock.nb_transport_bw(xf, ph, dl) == UVM_TLM_COMPLETED)
        uvm_info("USB/DEV/OUT/DONE", xf.convert2string(),
            UVM_NONE)


    #   // Forward path
    async def nb_transport_fw(self, xfer, ph, delay):
        uvm_info("USB/DEV/FWD", sv.sformatf("%s @%0d: %s",
            int(ph), delay.get_realtime(1),
            xfer.convert2string()), UVM_LOW)
        # This device?
        if xfer.addr != 0x7A:
            return uvm_tlm_sync_e.UVM_TLM_COMPLETED
        
        # Valid endpoint in the device?
        if xfer.endp != 0x5:
            return uvm_tlm_sync_e.UVM_TLM_COMPLETED

        if xfer.kind == usb_xfer.OUT:
            if ph == USB_TLM_TOKEN:
                return uvm_tlm_sync_e.UVM_TLM_ACCEPTED
            elif ph == USB_TLM_DATA:
                data = xfer.data
                xf = xfer
                dl = delay

                # Could complete transfer early here
                #fork: out_ack
                cocotb.fork(self.fork_proc(xf, dl))
                #join_none
                return uvm_tlm_sync_e.UVM_TLM_ACCEPTED

        elif xfer.kind == usb_xfer.IN:
            if ph == USB_TLM_TOKEN:
                # Could return the data early here
                #fork: in_data
                xf = xfer
                dl = delay
                cocotb.fork(self.fork_proc2(xf, dl))
                #join_none
                return uvm_tlm_sync_e.UVM_TLM_ACCEPTED
            elif ph == USB_TLM_HANDSHAKE:
                uvm_info("USB/DEV/IN/DONE", xfer.convert2string(),
                    UVM_NONE)
                return uvm_tlm_sync_e.UVM_TLM_COMPLETED

        return uvm_tlm_sync_e.UVM_TLM_COMPLETED


    async def fork_proc2(self, xf, dl):
        ph = USB_TLM_DATA
        await Timer(150, )
        tdata = [0xAB, 0xCD]
        xf.data = tdata
        self.sock.nb_transport_bw(xf, ph, dl)  # cast to 'void' removed


uvm_component_utils(device)
