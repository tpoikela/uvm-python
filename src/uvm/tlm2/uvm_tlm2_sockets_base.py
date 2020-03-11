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
from uvm.tlm2.uvm_tlm2_ports import UVMTLMNbTransportBwPort
from uvm.tlm2.uvm_tlm2_exports import UVMTLMNbTransportBwExport

class UVMTLMBTargetSocketBase(UVMPortBase):

    def __init__(self, name, parent):
        super().__init__(name, parent, UVM_IMPLEMENTATION, 1, 1)
        self.m_if_mask = UVM_TLM_B_MASK

UVM_TLM_GET_TYPE_NAME(UVMTLMBTargetSocketBase)
    
#
#//----------------------------------------------------------------------
#// Class: uvm_tlm_b_initiator_socket_base
#//
#// IS-A forward port; has no backward path except via the payload
#// contents
#//----------------------------------------------------------------------
class UVMTLMBInitiatorSocketBase(UVMPortBase):
    pass

UVMTLMBInitiatorSocketBase = UVM_PORT_COMMON(UVMTLMBInitiatorSocketBase, UVM_TLM_B_MASK, "UVMTLMBInitiatorSocketBase")
UVM_TLM_B_TRANSPORT_IMP("m_if", UVMTLMBInitiatorSocketBase)

#
#//----------------------------------------------------------------------
#// Class: uvm_tlm_nb_target_socket_base
#//
#// IS-A forward imp; HAS-A backward port
#//----------------------------------------------------------------------
class UVMTLMNbTargetSocketBase(UVMPortBase):

    def __init__(self, name, parent):
        super().__init__(name, parent, UVM_IMPLEMENTATION, 1, 1)
        self.m_if_mask = UVM_TLM_NB_FW_MASK
#        self.bw_port = UVMTLMNbTransportBwPort(name, parent, port_type, min_size, max_size)None # TODO: uvm_tlm_nb_transport_bw_port

UVM_TLM_GET_TYPE_NAME(UVMTLMNbTargetSocketBase)
UVM_TLM_NB_TRANSPORT_BW_IMP('bw_port', UVMTLMNbTargetSocketBase)


#//----------------------------------------------------------------------
#// Class: uvm_tlm_nb_initiator_socket_base
#//
#// IS-A forward port; HAS-A backward imp
#//----------------------------------------------------------------------
class UVMTLMNbInitiatorSocketBase(UVMPortBase):
    
    def __init__(self, name, parent):
        super().__init__(name, parent, UVM_PORT, 1, 1)
        self.m_if_mask = UVM_TLM_NB_FW_MASK

UVM_TLM_GET_TYPE_NAME(UVMTLMNbInitiatorSocketBase)
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTLMNbInitiatorSocketBase)

#//----------------------------------------------------------------------
#// Class -- NODOCS -- uvm_tlm_nb_passthrough_initiator_socket_base
#//
#// IS-A forward port; HAS-A backward export
#//----------------------------------------------------------------------
class UVMTLMNbPassthroughInitiatorSocketBase(UVMPortBase):

    def __init__(self, name, parent, min_size=1, max_size=1):
        super().__init__(name, parent, UVM_PORT, min_size, max_size)
        self.m_if_mask = UVM_TLM_NB_FW_MASK
        self.bw_export = UVMTLMNbTransportBwExport("bw_export", self.get_comp())

UVM_TLM_GET_TYPE_NAME(UVMTLMNbPassthroughInitiatorSocketBase)
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTLMNbPassthroughInitiatorSocketBase)
UVM_TLM_NB_TRANSPORT_BW_IMP('bw_export', UVMTLMNbPassthroughInitiatorSocketBase)

#//----------------------------------------------------------------------
#// Class: uvm_tlm_nb_passthrough_target_socket_base
#//
#// IS-A forward export; HAS-A backward port
#//----------------------------------------------------------------------
class UVMTLMNbPassthroughTargetSocketBase(UVMPortBase):

    def __init__(self, name, parent, min_size=1, max_size=1):
        super().__init__(name, parent, UVM_EXPORT, min_size, max_size)
        self.m_if_mask = UVM_TLM_NB_FW_MASK
        self.bw_port = UVMTLMNbTransportBwPort("bw_port", self.get_comp())

UVM_TLM_GET_TYPE_NAME(UVMTLMNbPassthroughTargetSocketBase)
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTLMNbPassthroughTargetSocketBase)
UVM_TLM_NB_TRANSPORT_BW_IMP('bw_port', UVMTLMNbPassthroughTargetSocketBase)

#//----------------------------------------------------------------------
#// Class: uvm_tlm_b_passthrough_initiator_socket_base
#//
#// IS-A forward port
#//----------------------------------------------------------------------
class UVMTLMBPassthroughInitiatorSocketBase(UVMPortBase):
    pass

UVMTLMBPassthroughInitiatorSocketBase = UVM_PORT_COMMON(UVMTLMBPassthroughInitiatorSocketBase, UVM_TLM_B_MASK, "uvm_tlm_b_passthrough_initiator_socket")
UVM_TLM_B_TRANSPORT_IMP('m_if', UVMTLMBPassthroughInitiatorSocketBase)

#//----------------------------------------------------------------------
#// Class -- NODOCS -- uvm_tlm_b_passthrough_target_socket_base
#//
#// IS-A forward export
#//----------------------------------------------------------------------
class UVMTLMBPassthroughTargetSocketBase(UVMPortBase):
    pass

UVMTLMBPassthroughTargetSocketBase = UVM_EXPORT_COMMON(UVMTLMBPassthroughTargetSocketBase, UVM_TLM_B_MASK, "uvm_tlm_b_passthrough_target_socket")
UVM_TLM_B_TRANSPORT_IMP('m_if', UVMTLMBPassthroughTargetSocketBase)

