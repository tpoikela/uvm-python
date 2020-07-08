#//----------------------------------------------------------------------
#// Copyright 2010-2011 Mentor Graphics Corporation
#// Copyright 2010 Synopsys, Inc.
#// Copyright 2010-2018 Cadence Design Systems, Inc.
#// Copyright 2015 NVIDIA Corporation
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

from uvm.base.uvm_port_base import UVMPortBase
from uvm.tlm1.uvm_tlm_imps import UVM_EXPORT_COMMON
from uvm.tlm2.uvm_tlm2_defines import UVM_TLM_B_MASK, UVM_TLM_NB_FW_MASK,\
    UVM_TLM_NB_BW_MASK
from uvm.tlm2.uvm_tlm2_imps import UVM_TLM_B_TRANSPORT_IMP,\
    UVM_TLM_NB_TRANSPORT_FW_IMP, UVM_TLM_NB_TRANSPORT_BW_IMP
#
#//----------------------------------------------------------------------
#// Title -- NODOCS -- TLM2 Export Classes
#//
#// This section defines the export classes for connecting TLM2
#// interfaces.
#//----------------------------------------------------------------------
#
#
#// Class -- NODOCS -- uvm_tlm_b_transport_export
#//
#// Blocking transport export class.

class UVMTLMBTransportExport(UVMPortBase):
    pass

UVMTLMBTransportExport = UVM_EXPORT_COMMON(UVMTLMBTransportExport, UVM_TLM_B_MASK, "uvm_tlm_b_transport_export")
UVM_TLM_B_TRANSPORT_IMP('m_if', UVMTLMBTransportExport)



#// Class: uvm_tlm_nb_transport_fw_export
#//
#// Non-blocking forward transport export class

class UVMTLMNbTransportFwExport(UVMPortBase):
    pass

UVMTLMNbTransportFwExport = UVM_EXPORT_COMMON(UVMTLMNbTransportFwExport, UVM_TLM_NB_FW_MASK,
        "uvm_tlm_nb_transport_fw_export")
UVM_TLM_NB_TRANSPORT_FW_IMP('m_if', UVMTLMNbTransportFwExport)



#// Class: uvm_tlm_nb_transport_bw_export
#//
#// Non-blocking backward transport export class

class UVMTLMNbTransportBwExport(UVMPortBase):
    pass

UVMTLMNbTransportBwExport = UVM_EXPORT_COMMON(UVMTLMNbTransportBwExport, UVM_TLM_NB_BW_MASK,
        "uvm_tlm_nb_transport_bw_export")
UVM_TLM_NB_TRANSPORT_BW_IMP('m_if', UVMTLMNbTransportBwExport)

