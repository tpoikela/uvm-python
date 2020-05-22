#//----------------------------------------------------------------------
#// Copyright 2010-2011 Mentor Graphics Corporation
#// Copyright 2010 Synopsys, Inc.
#// Copyright 2010-2018 Cadence Design Systems, Inc.
#// Copyright 2015 NVIDIA Corporation
#// Copyright 2014 Cisco Systems, Inc.
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

#//----------------------------------------------------------------------
#// Title -- NODOCS -- TLM2 ports
#//
#// The following defines TLM2 port classes.
#//
#//----------------------------------------------------------------------

#//
#// Class providing the blocking transport port.
#// The port can be bound to one export.
#// There is no backward path for the blocking transport.
from uvm.base.uvm_port_base import UVMPortBase
from uvm.tlm1.uvm_tlm_imps import UVM_PORT_COMMON
from uvm.tlm2.uvm_tlm2_defines import UVM_TLM_B_MASK, UVM_TLM_NB_FW_MASK,\
    UVM_TLM_NB_BW_MASK
from uvm.tlm2.uvm_tlm2_imps import UVM_TLM_B_TRANSPORT_IMP,\
    UVM_TLM_NB_TRANSPORT_FW_IMP, UVM_TLM_NB_TRANSPORT_BW_IMP

class UVMTLMBTransportPort(UVMPortBase):
    pass

UVMTLMBTransportPort = UVM_PORT_COMMON(UVMTLMBTransportPort,  # type: ignore
        UVM_TLM_B_MASK, "uvm_tlm_b_transport_port")
UVM_TLM_B_TRANSPORT_IMP('m_if', UVMTLMBTransportPort)

#
#// class -- NODOCS -- uvm_tlm_nb_transport_fw_port
#//
#// Class providing the non-blocking backward transport port.
#// Transactions received from the producer, on the forward path, are
#// sent back to the producer on the backward path using this
#// non-blocking transport port.
#// The port can be bound to one export.
#//
class UVMTLMNbTransportFwPort(UVMPortBase):
    pass

UVMTLMNbTransportFwPort = UVM_PORT_COMMON(UVMTLMNbTransportFwPort,  # type: ignore
        UVM_TLM_NB_FW_MASK, "uvm_tlm_nb_transport_fw_port")
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTLMNbTransportFwPort)

#// class: uvm_tlm_nb_transport_bw_port
#//
#// Class providing the non-blocking backward transport port.
#// Transactions received from the producer, on the forward path, are
#// sent back to the producer on the backward path using this
#// non-blocking transport port
#// The port can be bound to one export.
#//

class UVMTLMNbTransportBwPort(UVMPortBase):
    pass

UVMTLMNbTransportBwPort = UVM_PORT_COMMON(UVMTLMNbTransportBwPort,  # type: ignore
        UVM_TLM_NB_BW_MASK, "uvm_tlm_nb_transport_bw_port")
UVM_TLM_NB_TRANSPORT_BW_IMP('m_if', UVMTLMNbTransportBwPort)
