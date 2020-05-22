#//----------------------------------------------------------------------
#// Copyright 2010-2011 Mentor Graphics Corporation
#// Copyright 2014 Semifore
#// Copyright 2010 Synopsys, Inc.
#// Copyright 2010-2018 Cadence Design Systems, Inc.
#// Copyright 2014-2015 NVIDIA Corporation
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
from uvm.base.uvm_port_base import UVMPortBase
from ..macros.uvm_message_defines import (uvm_error)

#//----------------------------------------------------------------------
#// Title -- NODOCS -- TLM2 imps (interface implementations)
#//
#// This section defines the implementation classes for connecting TLM2
#// interfaces.
#//
#// TLM imps bind a TLM interface with the object that contains the
#// interface implementation.
#// In addition to the transaction type and the phase type, the imps
#// are parameterized with the type of the object that will provide the
#// implementation. Most often this will be the type of the component
#// where the imp resides. The constructor of the imp takes as an argument
#// an object of type IMP and installs it as the implementation object.
#// Most often the imp constructor argument is "this".
#//----------------------------------------------------------------------

#//--------------------------
#// Group -- NODOCS -- IMP binding macros
#//--------------------------

from uvm.tlm2.uvm_tlm2_ifs import uvm_tlm_sync_e
from uvm.base.uvm_port_base import UVMPortBase
from uvm.tlm1.uvm_tlm_imps import UVM_IMP_COMMON
from uvm.tlm2.uvm_tlm2_defines import UVM_TLM_NB_FW_MASK, UVM_TLM_B_MASK,\
    UVM_TLM_NB_BW_MASK
from uvm.macros.uvm_message_defines import uvm_error
from uvm.base.sv import cat
import cocotb

#// The macro wraps the forward path call function nb_transport_fw()
#//
#// The first call to this method for a transaction marks the initial timing point.
#// Every call to this method may mark a timing point in the execution of the
#// transaction. The timing annotation argument allows the timing points
#// to be offset from the simulation times at which the forward path is used.
#// The final timing point of a transaction may be marked by a call
#// to nb_transport_bw() within <`UVM_TLM_NB_TRANSPORT_BW_IMP> or a return from this
#// or subsequent call to nb_transport_fw().
#//
#// See <TLM2 Interfaces, Ports, Exports and Transport Interfaces Subset>
#// for more details on the semantics and rules of the nonblocking
#// transport interface.
def UVM_TLM_NB_TRANSPORT_FW_IMP(imp, T):
    def nb_transport_fw(self, t, p, delay):
        if delay is None:
            uvm_error("UVM/TLM/NULLDELAY",
                cat(self.get_full_name(),
                   ".nb_transport_fw() called with 'null' delay"))
            return uvm_tlm_sync_e.UVM_TLM_COMPLETED

        return getattr(self, imp).nb_transport_fw(t, p, delay)
    setattr(T, "nb_transport_fw", nb_transport_fw)


#// Implementation of the backward path.
#// The macro wraps the function called nb_transport_bw().
#// This function MUST be implemented in the INITIATOR component class.
#//
#// Every call to this method may mark a timing point, including the final
#// timing point, in the execution of the transaction.
#// The timing annotation argument allows the timing point
#// to be offset from the simulation times at which the backward path is used.
#// The final timing point of a transaction may be marked by a call
#// to nb_transport_fw() within <`UVM_TLM_NB_TRANSPORT_FW_IMP> or a return from
#// this or subsequent call to nb_transport_bw().
#//
#// See <TLM2 Interfaces, Ports, Exports and Transport Interfaces Subset>
#// for more details on the semantics and rules of the nonblocking
#// transport interface.
#//
#// Example:
#//
#//| class master extends uvm_component;
#//|    uvm_tlm_nb_initiator_socket
#//|          #(trans, uvm_tlm_phase_e, this_t) initiator_socket;
#//|
#//|    function void build_phase(uvm_phase phase);
#//|       initiator_socket = new("initiator_socket", this, this);
#//|    endfunction
#//|
#//|    function uvm_tlm_sync_e nb_transport_bw(trans t,
#//|                                   ref uvm_tlm_phase_e p,
#//|                                   input uvm_tlm_time delay);
#//|        transaction = t;
#//|        state = p;
#//|        return UVM_TLM_ACCEPTED;
#//|    endfunction
#//|
#//|    ...
#//| endclass
def UVM_TLM_NB_TRANSPORT_BW_IMP(imp, T):
    def nb_transport_bw(self, t, p, delay):
        if delay is None:
            uvm_error("UVM/TLM/NULLDELAY",
                cat(self.get_full_name(),
                   ".nb_transport_bw() called with 'null' delay"))
            return uvm_tlm_sync_e.UVM_TLM_COMPLETED
        return getattr(self, imp).nb_transport_bw(t, p, delay)

    setattr(T, "nb_transport_bw", nb_transport_bw)


#// The macro wraps the function b_transport()
#// Execute a blocking transaction. Once this method returns,
#// the transaction is assumed to have been executed. Whether
#// that execution is successful or not must be indicated by the
#// transaction itself.
#//
#// The callee may modify or update the transaction object, subject
#// to any constraints imposed by the transaction class. The
#// initiator may re-use a transaction object from one call to
#// the next and across calls to b_transport().
#//
#// The call to b_transport shall mark the first timing point of the
#// transaction. The return from b_transport() shall mark the final
#// timing point of the transaction. The timing annotation argument
#// allows the timing points to be offset from the simulation times
#// at which the task call and return are executed.
def UVM_TLM_B_TRANSPORT_IMP(imp, T):

    async def b_transport(self, t, delay):
        if delay == None:
            uvm_error("UVM/TLM/NULLDELAY",
                  cat(self.get_full_name(),
                   ".b_transport() called with 'null' delay"))
            return
        await getattr(self, imp).b_transport(t, delay)
    setattr(T, "b_transport", b_transport)


#//---------------------------
#// Group -- NODOCS -- IMP binding classes
#//---------------------------

#//
#// Used like exports, except an additional class parameter specifies
#// the type of the implementation object.  When the
#// imp is instantiated the implementation object is bound.
class UVMTLMBTransportImp(UVMPortBase):
    pass

UVMTLMBTransportImp = UVM_IMP_COMMON(UVMTLMBTransportImp,  # type: ignore
        UVM_TLM_B_MASK, "uvm_tlm_b_transport_imp")
UVM_TLM_B_TRANSPORT_IMP('m_imp', UVMTLMBTransportImp)


#// Used like exports, except an additional class parameter specifies
#// the type of the implementation object.  When the
#// imp is instantiated the implementation object is bound.
class UVMTLMNbTransportFwImp(UVMPortBase):
    pass

UVMTLMNbTransportFwImp = UVM_IMP_COMMON(UVMTLMNbTransportFwImp,  # type: ignore
        UVM_TLM_NB_FW_MASK, "uvm_tlm_nb_transport_fw_imp")
UVM_TLM_NB_TRANSPORT_FW_IMP('m_imp', UVMTLMNbTransportFwImp)


#// Used like exports, except an additional class parameter specifies
#// the type of the implementation object.  When the
#// imp is instantiated the implementation object is bound.
class UVMTLMNbTransportBwImp(UVMPortBase):
    pass

UVMTLMNbTransportBwImp = UVM_IMP_COMMON(UVMTLMNbTransportBwImp,  # type: ignore
        UVM_TLM_NB_BW_MASK, "uvm_tlm_nb_transport_bw_imp")
UVM_TLM_NB_TRANSPORT_BW_IMP('m_imp', UVMTLMNbTransportBwImp)

