#//----------------------------------------------------------------------
#//   Copyright 2010 Mentor Graphics Corporation
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2020 Matthew Ballance
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

from uvm.base.uvm_port_base import *
from ..tlm1 import (UVM_PORT_COMMON)
from .uvm_tlm2_defines import UVM_TLM_B_MASK
from .uvm_tlm2_imps import (UVM_TLM_B_TRANSPORT_IMP)

#//----------------------------------------------------------------------
#// Title -- NODOCS -- TLM Socket Base Classes
#//
#// A collection of base classes, one for each socket type.  The reason
#// for having a base class for each socket is that all the socket (base)
#// types must be known before connect is defined.  Socket connection
#// semantics are provided in the derived classes, which are user
#// visible.
#//
#// Termination Sockets - A termination socket must be the terminus
#// of every TLM path.  A transaction originates with an initiator socket
#// and ultimately ends up in a target socket.  There may be zero or more
#// pass-through sockets between initiator and target.
#//
#// Pass-through Sockets - Pass-through initiators are ports and contain
#// exports for instance IS-A port and HAS-A export. Pass-through targets
#// are the opposite, they are exports and contain ports.
#//----------------------------------------------------------------------


#//----------------------------------------------------------------------
#// Class -- NODOCS -- uvm_tlm_b_target_socket_base
#//
#// IS-A forward imp; has no backward path except via the payload
#// contents.
#//----------------------------------------------------------------------
from uvm.base.uvm_port_base import UVMPortBase
from uvm.base.uvm_object_globals import UVM_IMPLEMENTATION, UVM_PORT, UVM_EXPORT
from uvm.tlm1.uvm_tlm_imps import UVM_TLM_GET_TYPE_NAME, UVM_PORT_COMMON,\
    UVM_EXPORT_COMMON
from uvm.tlm2.uvm_tlm2_defines import UVM_TLM_B_MASK, UVM_TLM_NB_FW_MASK
from uvm.tlm2.uvm_tlm2_imps import UVM_TLM_B_TRANSPORT_IMP,\
    UVM_TLM_NB_TRANSPORT_BW_IMP, UVM_TLM_NB_TRANSPORT_FW_IMP
from uvm.tlm2.uvm_tlm2_ports import UVMTlmNbTransportBwPort
from uvm.tlm2.uvm_tlm2_exports import UVMTlmNbTransportBwExport

class UVMTlmBTargetSocketBase(UVMPortBase):

    def __init__(self, name, parent):
        super().__init__(name, parent, UVM_IMPLEMENTATION, 1, 1)
        self.m_if_mask = UVM_TLM_B_MASK

UVM_TLM_GET_TYPE_NAME(UVMTlmBTargetSocketBase)
    
#
#//----------------------------------------------------------------------
#// Class: uvm_tlm_b_initiator_socket_base
#//
#// IS-A forward port; has no backward path except via the payload
#// contents
#//----------------------------------------------------------------------
class UVMTlmBInitiatorSocketBase(UVMPortBase):
    pass

UVM_PORT_COMMON(UVMTlmBInitiatorSocketBase, UVM_TLM_B_MASK, "UVMTlmBInitiatorSocketBase")
UVM_TLM_B_TRANSPORT_IMP("m_if", UVMTlmBInitiatorSocketBase)

#
#//----------------------------------------------------------------------
#// Class: uvm_tlm_nb_target_socket_base
#//
#// IS-A forward imp; HAS-A backward port
#//----------------------------------------------------------------------
class UVMTlmNbTargetSocketBase(UVMPortBase):

    def __init__(self, name, parent):
        super().__init__(name, parent, UVM_IMPLEMENTATION, 1, 1)
        self.m_if_mask = UVM_TLM_NB_FW_MASK
#        self.bw_port = UVMTlmNbTransportBwPort(name, parent, port_type, min_size, max_size)None # TODO: uvm_tlm_nb_transport_bw_port

UVM_TLM_GET_TYPE_NAME(UVMTlmNbTargetSocketBase)
UVM_TLM_NB_TRANSPORT_BW_IMP('bw_port', UVMTlmNbTargetSocketBase)


#//----------------------------------------------------------------------
#// Class: uvm_tlm_nb_initiator_socket_base
#//
#// IS-A forward port; HAS-A backward imp
#//----------------------------------------------------------------------
class UVMTlmNbInitiatorSocketBase(UVMPortBase):
    
    def __init__(self, name, parent):
        super().__init__(name, parent, UVM_PORT, 1, 1)
        self.m_if_mask = UVM_TLM_NB_FW_MASK

UVM_TLM_GET_TYPE_NAME(UVMTlmNbInitiatorSocketBase)
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTlmNbInitiatorSocketBase)

#//----------------------------------------------------------------------
#// Class -- NODOCS -- uvm_tlm_nb_passthrough_initiator_socket_base
#//
#// IS-A forward port; HAS-A backward export
#//----------------------------------------------------------------------
class UVMTlmNbPassthroughInitiatorSocketBase(UVMPortBase):

    def __init__(self, name, parent, min_size=1, max_size=1):
        super().__init__(name, parent, UVM_PORT, min_size, max_size)
        self.m_if_mask = UVM_TLM_NB_FW_MASK
        self.bw_export = UVMTlmNbTransportBwExport("bw_export", self.get_comp())

UVM_TLM_GET_TYPE_NAME(UVMTlmNbPassthroughInitiatorSocketBase)
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTlmNbPassthroughInitiatorSocketBase)
UVM_TLM_NB_TRANSPORT_BW_IMP('bw_export', UVMTlmNbPassthroughInitiatorSocketBase)

#//----------------------------------------------------------------------
#// Class: uvm_tlm_nb_passthrough_target_socket_base
#//
#// IS-A forward export; HAS-A backward port
#//----------------------------------------------------------------------
class UVMTlmNbPassthroughTargetSocketBase(UVMPortBase):

    def __init__(self, name, parent, min_size=1, max_size=1):
        super().__init__(name, parent, UVM_EXPORT, min_size, max_size)
        self.m_if_mask = UVM_TLM_NB_FW_MASK
        self.bw_port = UVMTlmNbTransportBwPort("bw_port", self.get_comp())

UVM_TLM_GET_TYPE_NAME(UVMTlmNbPassthroughTargetSocketBase)
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTlmNbPassthroughTargetSocketBase)
UVM_TLM_NB_TRANSPORT_BW_IMP('bw_port', UVMTlmNbPassthroughTargetSocketBase)

#//----------------------------------------------------------------------
#// Class: uvm_tlm_b_passthrough_initiator_socket_base
#//
#// IS-A forward port
#//----------------------------------------------------------------------
class UVMTlmBPassthroughInitiatorSocketBase(UVMPortBase):
    pass

UVM_PORT_COMMON(UVMTlmBPassthroughInitiatorSocketBase, UVM_TLM_B_MASK, "uvm_tlm_b_passthrough_initiator_socket")
UVM_TLM_B_TRANSPORT_IMP('m_if', UVMTlmBPassthroughInitiatorSocketBase)

#//----------------------------------------------------------------------
#// Class -- NODOCS -- uvm_tlm_b_passthrough_target_socket_base
#//
#// IS-A forward export
#//----------------------------------------------------------------------
class UVMTlmBPassthroughTargetSocketBase(UVMPortBase):
    pass

UVM_EXPORT_COMMON(UVMTlmBPassthroughTargetSocketBase, UVM_TLM_B_MASK, "uvm_tlm_b_passthrough_target_socket")
UVM_TLM_B_TRANSPORT_IMP('m_if', UVMTlmBPassthroughTargetSocketBase)

