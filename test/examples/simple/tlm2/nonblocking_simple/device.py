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

from uvm.base.uvm_component import *
from uvm.macros import *
from usb_xfer import usb_xfer
from uvm.tlm2 import UVMTLMNbTargetSocket


class device(UVMComponent):
    #
    #   uvm_tlm_nb_target_socket#(device, usb_xfer, usb_tlm_phase) sock
    #
    #
    def __init__(self, name="device", parent=None):
        super().__init__(name, parent)
        self.sock = UVMTLMNbTargetSocket("sock", self)
        self.data = []


    #   // Forward path
    async def nb_transport_fw(self, xfer, ph, delay):
        uvm_info("USB/DEV/FWD", sv.sformatf("%s @%0d: %s",
            int(ph), delay.get_realtime(1, "NS"),
            xfer.convert2string()), UVM_LOW)
        # This device?
        if xfer.addr != 0x7A:
            return UVM_TLM_COMPLETED
        
        # Valid endpoint in the device?
        if xfer.endp != 0x5:
            return UVM_TLM_COMPLETED

        if xfer.kind == usb_xfer.OUT:
            pass
            #          case (ph)
            #           USB_TLM_TOKEN: begin
            #              return UVM_TLM_ACCEPTED
            #           end
            #
            #           USB_TLM_DATA: begin
            #              data = xfer.data
            #
            #              // Could complete transfer early here
            #              fork: out_ack
            #                 automatic usb_xfer     xf = xfer
            #                 automatic uvm_tlm_time dl = delay
            #                 begin
            #                    usb_tlm_phase ph = USB_TLM_HANDSHAKE
            #                    yield Timer(100, )
            #                    xf.status = usb_xfer::ACK
            #                    assert(sock.nb_transport_bw(xf, ph, dl) ==
            #                           UVM_TLM_COMPLETED)
            #
            #                    uvm_info("USB/DEV/OUT/DONE", xf.convert2string(),
            #                              UVM_NONE)
            #                    
            #                 end
            #              join_none
            #
            #              return UVM_TLM_ACCEPTED
            #           end
            #           
            #          endcase
            #       end
        elif xfer.kind == usb_xfer.IN:
            pass
            #          case (ph)
            #           USB_TLM_TOKEN: begin
            #              // Could return the data early here
            #              fork: in_data
            #                 automatic usb_xfer     xf = xfer
            #                 automatic uvm_tlm_time dl = delay
            #                 begin
            #                    usb_tlm_phase ph = USB_TLM_DATA
            #                    yield Timer(150, )
            #		    begin
            #			byte tdata[2]='{ 0xAB,  0xCD}
            #                    	xf.data = tdata
            #		    end
            #                    sock.nb_transport_bw(xf, ph, dl)  # cast to 'void' removed
            #                 end
            #              join_none
            #
            #              return UVM_TLM_ACCEPTED
            #           end
            #
            #           USB_TLM_HANDSHAKE: begin
            #              uvm_info("USB/DEV/IN/DONE", xfer.convert2string(),
            #                        UVM_NONE)
            #              
            #              return UVM_TLM_COMPLETED
            #           end
            #           
            #          endcase
            #       end
            #      endcase

        return UVM_TLM_COMPLETED
        #   endfunction
    #
uvm_component_utils(device)
