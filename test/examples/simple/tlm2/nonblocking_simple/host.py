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

from uvm import (UVMComponent, sv, wait)
from uvm.macros import uvm_info, uvm_component_utils
from uvm.tlm2 import *

from usb_xfer import (usb_xfer, USB_TLM_TOKEN,
    USB_TLM_DATA,  USB_TLM_HANDSHAKE)


class host(UVMComponent):


    def __init__(self, name="host", parent=None):
        super().__init__(name, parent)
        #   uvm_tlm_nb_initiator_socket#(host, usb_xfer, usb_tlm_phase) sock
        self.sock = UVMTLMNbInitiatorSocket("sock", self)
        self.xfer = None  # usb_xfer
        self.ph = None  # usb_tlm_phase
        self.delay = UVMTLMTime()
        self.sync = 0  # uvm_tlm_sync_e

    #   // Backward path
    def nb_transport_bw(self, xfer, ph, delay):
        uvm_info("USB/HST/BWD", sv.sformatf("%s @%0d: %s",
            self.ph.name(), self.delay.get_realtime(1, "ns"),
            xfer.convert2string()), UVM_LOW)

        assert(xfer == self.xfer)
        self.ph    = ph
        self.delay = delay

        if xfer.kind == usb_xfer.OUT:
            assert(ph == USB_TLM_HANDSHAKE)
            self.sync = uvm_tlm_sync_e.UVM_TLM_COMPLETED
            return uvm_tlm_sync_e.UVM_TLM_COMPLETED
        elif xfer.kind == usb_xfer.IN:
            assert(ph == USB_TLM_DATA)
            # Could do an early completion too
            return uvm_tlm_sync_e.UVM_TLM_ACCEPTED
        return uvm_tlm_sync_e.UVM_TLM_COMPLETED


    #   //
    #   // Execute an OUT followed by an IN bulk transfer
    #   //
    async def run_phase(self, phase):
        phase.raise_objection(self)
        self.xfer = usb_xfer.type_id.create("xfer",None, self.get_full_name())

        # OUT bulk transfer

        done = False
        while not done:
            self.xfer.kind = usb_xfer.OUT
            self.xfer.addr = 0x7A
            self.xfer.endp = 0x5

            self.ph = USB_TLM_TOKEN
            self.sync = await self.sock.nb_transport_fw(self.xfer, self.ph, self.delay)
            print("self.sync is " + self.sync.name)
            if self.sync == uvm_tlm_sync_e.UVM_TLM_COMPLETED:
                uvm_info("USB/HST/OUT/REFUSED", "Device refused the transfer",
                    UVM_LOW)
                break

            self.ph = USB_TLM_DATA
            tdata = [0xDE, 0xAD, 0xBE, 0xEF]
            self.xfer.data = tdata
            self.sync = await self.sock.nb_transport_fw(self.xfer, self.ph, self.delay)
            if self.sync == uvm_tlm_sync_e.UVM_TLM_COMPLETED:
                uvm_info("USB/HST/OUT/EARLY", "Device completed OUT transfer early",
                         UVM_LOW)
                break

            # Wait for the device to reply
            # TODO
            # wait(self.sync == uvm_tlm_sync_e.UVM_TLM_COMPLETED)
            uvm_info("USB/HST/OUT/NORMAL", "OUT Transfer completed normally",
                UVM_LOW)
            done = True


        uvm_info("USB/HST/OUT/DONE", self.xfer.convert2string(), UVM_NONE)

        # IN bulk transfer
        done = False
        while not done:
            # Ok to reuse the same XFER instance
            self.xfer.kind = usb_xfer.IN
            self.xfer.addr = 0x7A
            self.xfer.endp = 0x5
            self.xfer.data = []

            self.ph = USB_TLM_TOKEN
            self.sync = await self.sock.nb_transport_fw(self.xfer, self.ph, self.delay)
            if self.sync == uvm_tlm_sync_e.UVM_TLM_COMPLETED:
                uvm_info("USB/HST/IN/REFUSED", "Device refused the transfer",
                        UVM_LOW)
                break
            if self.sync == uvm_tlm_sync_e.UVM_TLM_UPDATED:
                uvm_info("USB/HST/IN/EARLY", "Device returned bulk data early",
                        UVM_LOW)
            else:
                # Wait for the device to reply
                # TODO wait(ph == USB_TLM_DATA)
                uvm_info("USB/HST/IN/NORMAL", "IN data returned normally",
                        UVM_LOW)

            self.ph = USB_TLM_HANDSHAKE
            self.xfer.status = usb_xfer.ACK
            self.sync = await self.sock.nb_transport_fw(self.xfer, self.ph, self.delay)
            assert(self.sync == uvm_tlm_sync_e.UVM_TLM_COMPLETED)
            done = True

        uvm_info("USB/HST/IN/DONE", self.xfer.convert2string(), UVM_NONE)
        phase.drop_objection(self)


uvm_component_utils(host)
