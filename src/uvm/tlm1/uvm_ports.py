# type: ignore
#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#----------------------------------------------------------------------

from .uvm_tlm_imps import (UVM_BLOCKING_GET_IMP, UVM_BLOCKING_GET_PEEK_IMP, UVM_BLOCKING_PEEK_IMP,
   UVM_BLOCKING_PUT_IMP, UVM_BLOCKING_TRANSPORT_IMP, UVM_GET_IMP,
   UVM_GET_PEEK_IMP, UVM_NONBLOCKING_GET_IMP, UVM_NONBLOCKING_GET_PEEK_IMP,
   UVM_NONBLOCKING_PEEK_IMP, UVM_NONBLOCKING_PUT_IMP,
   UVM_NONBLOCKING_TRANSPORT_IMP, UVM_PEEK_IMP, UVM_PORT_COMMON,
   UVM_PUT_IMP, UVM_TRANSPORT_IMP)

from ..macros.uvm_tlm_defines import (UVM_TLM_BLOCKING_GET_MASK, UVM_TLM_BLOCKING_GET_PEEK_MASK,
    UVM_TLM_BLOCKING_MASTER_MASK, UVM_TLM_BLOCKING_PEEK_MASK,
    UVM_TLM_BLOCKING_PUT_MASK, UVM_TLM_BLOCKING_SLAVE_MASK,
    UVM_TLM_BLOCKING_TRANSPORT_MASK, UVM_TLM_GET_MASK,
    UVM_TLM_GET_PEEK_MASK, UVM_TLM_MASTER_MASK,
    UVM_TLM_NONBLOCKING_GET_MASK,
    UVM_TLM_NONBLOCKING_GET_PEEK_MASK,
    UVM_TLM_NONBLOCKING_MASTER_MASK,
    UVM_TLM_NONBLOCKING_PEEK_MASK, UVM_TLM_NONBLOCKING_PUT_MASK,
    UVM_TLM_NONBLOCKING_SLAVE_MASK,
    UVM_TLM_NONBLOCKING_TRANSPORT_MASK, UVM_TLM_PEEK_MASK,
    UVM_TLM_PUT_MASK, UVM_TLM_SLAVE_MASK, UVM_TLM_TRANSPORT_MASK)

#------------------------------------------------------------------------------
# Title: TLM Port Classes
#------------------------------------------------------------------------------
# The following classes define the TLM port classes.
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
#
# Class: uvm_*_port #(T)
#
# These unidirectional ports are instantiated by components that ~require~,
# or ~use~, the associated interface to convey transactions. A port can
# be connected to any compatible port, export, or imp port. Unless its
# ~min_size~ is 0, a port ~must~ be connected to at least one implementation
# of its associated interface.
#
# The asterisk in ~uvm_*_port~ is any of the following
#
#|  blocking_put
#|  nonblocking_put
#|  put
#|
#|  blocking_get
#|  nonblocking_get
#|  get
#|
#|  blocking_peek
#|  nonblocking_peek
#|  peek
#|
#|  blocking_get_peek
#|  nonblocking_get_peek
#|  get_peek
#
# Type parameters
#
# T - The type of transaction to be communicated by the export. The type T is not restricted
# to class handles and may be a value type such as int,enum,struct or similar.
#
# Ports are connected to interface implementations directly via
# <uvm_*_imp #(T,IMP)> ports or indirectly via hierarchical connections
# to <uvm_*_port #(T)> and <uvm_*_export #(T)> ports.
#
#------------------------------------------------------------------------------

# Function: new
#
# The ~name~ and ~parent~ are the standard <uvm_component> constructor arguments.
# The ~min_size~ and ~max_size~ specify the minimum and maximum number of
# interfaces that must have been connected to this port by the end of elaboration.
#
#|  function new (string name,
#|                uvm_component parent,
#|                int min_size=1,
#|                int max_size=1)

class UVMBlockingPutPort():
    # extends uvm_port_base #(uvm_tlm_if_base #(T,T));
    pass
UVMBlockingPutPort = UVM_PORT_COMMON(UVMBlockingPutPort, UVM_TLM_BLOCKING_PUT_MASK, "uvm_blocking_put_port")
UVM_BLOCKING_PUT_IMP('m_if', UVMBlockingPutPort)
#endclass

#class uvm_nonblocking_put_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_PUT_MASK,"uvm_nonblocking_put_port")
#  `UVM_NONBLOCKING_PUT_IMP(this.m_if, T, t)
#endclass
class UVMNonBlockingPutPort():
    pass
UVMNonBlockingPutPort = UVM_PORT_COMMON(UVMNonBlockingPutPort, UVM_TLM_NONBLOCKING_PUT_MASK, "uvm_nonblocking_put_port")
UVM_NONBLOCKING_PUT_IMP('m_if', UVMNonBlockingPutPort)

#class uvm_put_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_PUT_MASK,"uvm_put_port")
#  `UVM_PUT_IMP(this.m_if, T, t)
#endclass
class UVMPutPort():
    pass
UVMPutPort = UVM_PORT_COMMON(UVMPutPort, UVM_TLM_PUT_MASK,"uvm_put_port")
UVM_PUT_IMP('m_if', UVMPutPort)

#class uvm_blocking_get_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_BLOCKING_GET_MASK,"uvm_blocking_get_port")
#  `UVM_BLOCKING_GET_IMP(this.m_if, T, t)
#endclass
class UVMBlockingGetPort():
    pass
UVMBlockingGetPort = UVM_PORT_COMMON(UVMBlockingGetPort, UVM_TLM_BLOCKING_GET_MASK,"uvm_blocking_get_port")
UVM_BLOCKING_GET_IMP('m_if', UVMBlockingGetPort)

#class uvm_nonblocking_get_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_GET_MASK,"uvm_nonblocking_get_port")
#  `UVM_NONBLOCKING_GET_IMP(this.m_if, T, t)
#endclass
class UVMNonBlockingGetPort():
    pass
UVMNonBlockingGetPort = UVM_PORT_COMMON(UVMNonBlockingGetPort, UVM_TLM_NONBLOCKING_GET_MASK,"uvm_nonblocking_get_port")
UVM_NONBLOCKING_GET_IMP('m_if', UVMNonBlockingGetPort)

#class uvm_get_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_GET_MASK,"uvm_get_port")
#  `UVM_GET_IMP(this.m_if, T, t)
#endclass
class UVMGetPort():
    pass
UVMGetPort = UVM_PORT_COMMON(UVMGetPort, UVM_TLM_GET_MASK, "uvm_get_port")
UVM_GET_IMP('m_if', UVMGetPort)

#class uvm_blocking_peek_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_BLOCKING_PEEK_MASK,"uvm_blocking_peek_port")
#  `UVM_BLOCKING_PEEK_IMP(this.m_if, T, t)
#endclass
class UVMBlockingPeekPort():
    pass
UVMBlockingPeekPort = UVM_PORT_COMMON(UVMBlockingPeekPort,
        UVM_TLM_BLOCKING_PEEK_MASK, "uvm_blocking_peek_port")
UVM_BLOCKING_PEEK_IMP('m_if', UVMBlockingPeekPort)

#class uvm_nonblocking_peek_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_PEEK_MASK,"uvm_nonblocking_peek_port")
#  `UVM_NONBLOCKING_PEEK_IMP(this.m_if, T, t)
#endclass
class UVMNonBlockingPeekPort():
    pass
UVMNonBlockingPeekPort = UVM_PORT_COMMON(UVMNonBlockingPeekPort,
    UVM_TLM_NONBLOCKING_PEEK_MASK,"uvm_nonblocking_peek_port")
UVM_NONBLOCKING_PEEK_IMP('m_if', UVMNonBlockingPeekPort)

#class uvm_peek_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_PEEK_MASK,"uvm_peek_port")
#  `UVM_PEEK_IMP(this.m_if, T, t)
#endclass
class UVMPeekPort():
    pass
UVMPeekPort = UVM_PORT_COMMON(UVMPeekPort, UVM_TLM_PEEK_MASK,"uvm_peek_port")
UVM_PEEK_IMP('m_if', UVMPeekPort)

#class uvm_blocking_get_peek_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_BLOCKING_GET_PEEK_MASK,"uvm_blocking_get_peek_port")
#  `UVM_BLOCKING_GET_PEEK_IMP(this.m_if, T, t)
#endclass
class UVMBlockingGetPeekPort():
    pass
UVMBlockingGetPeekPort = UVM_PORT_COMMON(UVMBlockingGetPeekPort,
    UVM_TLM_BLOCKING_GET_PEEK_MASK,"uvm_blocking_get_peek_port")
UVM_BLOCKING_GET_PEEK_IMP('m_if', UVMBlockingGetPeekPort)

#class uvm_nonblocking_get_peek_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_GET_PEEK_MASK,"uvm_nonblocking_get_peek_port")
#  `UVM_NONBLOCKING_GET_PEEK_IMP(this.m_if, T, t)
#endclass
class UVMNonBlockingGetPeekPort():
    pass
UVMNonBlockingGetPeekPort = UVM_PORT_COMMON(UVMNonBlockingGetPeekPort,
        UVM_TLM_NONBLOCKING_GET_PEEK_MASK,"uvm_nonblocking_get_peek_port")
UVM_NONBLOCKING_GET_PEEK_IMP('m_if',  UVMNonBlockingGetPeekPort)

#class uvm_get_peek_port #(type T=int)
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T));
#  `UVM_PORT_COMMON(`UVM_TLM_GET_PEEK_MASK,"uvm_get_peek_port")
#  `UVM_GET_PEEK_IMP(this.m_if, T, t)
#endclass
class UVMGetPeekPort():
    pass
UVMGetPeekPort = UVM_PORT_COMMON(UVMGetPeekPort, UVM_TLM_GET_PEEK_MASK,"uvm_get_peek_port")
UVM_GET_PEEK_IMP('m_if',  UVMGetPeekPort)

#------------------------------------------------------------------------------
#
# Class: uvm_*_port #(REQ,RSP)
#
# These bidirectional ports are instantiated by components that ~require~,
# or ~use~, the associated interface to convey transactions. A port can
# be connected to any compatible port, export, or imp port. Unless its
# ~min_size~ is 0, a port ~must~ be connected to at least one implementation
# of its associated interface.
#
# The asterisk in ~uvm_*_port~ is any of the following
#
#|  blocking_transport
#|  nonblocking_transport
#|  transport
#|
#|  blocking_master
#|  nonblocking_master
#|  master
#|
#|  blocking_slave
#|  nonblocking_slave
#|  slave
#
# Ports are connected to interface implementations directly via
# <uvm_*_imp #(REQ,RSP,IMP,REQ_IMP,RSP_IMP)> ports or indirectly via
# hierarchical connections to <uvm_*_port #(REQ,RSP)> and
# <uvm_*_export #(REQ,RSP)> ports.
#
# Type parameters
#
# REQ - The type of request transaction to be communicated by the export
#
# RSP - The type of response transaction to be communicated by the export
#
#------------------------------------------------------------------------------
#
# Function: new
#
# The ~name~ and ~parent~ are the standard <uvm_component> constructor arguments.
# The ~min_size~ and ~max_size~ specify the minimum and maximum number of
# interfaces that must have been supplied to this port by the end of elaboration.
#
#   function new (string name,
#                 uvm_component parent,
#                 int min_size=1,
#                 int max_size=1)
#
#
#class uvm_blocking_master_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP));
#  `UVM_PORT_COMMON(`UVM_TLM_BLOCKING_MASTER_MASK,"uvm_blocking_master_port")
#  `UVM_BLOCKING_PUT_IMP(this.m_if, REQ, t)
#  `UVM_BLOCKING_GET_PEEK_IMP(this.m_if, RSP, t)
#endclass
class UVMBlockingMasterPort():  #(type REQ=int, type RSP=REQ)
    pass
UVMBlockingMasterPort = UVM_PORT_COMMON(UVMBlockingMasterPort,
        UVM_TLM_BLOCKING_MASTER_MASK,"uvm_blocking_master_port")
UVM_BLOCKING_PUT_IMP('m_if',  UVMBlockingMasterPort)
UVM_BLOCKING_GET_PEEK_IMP('m_if', UVMBlockingMasterPort)

#class uvm_nonblocking_master_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_MASTER_MASK,"uvm_nonblocking_master_port")
#  `UVM_NONBLOCKING_PUT_IMP(this.m_if, REQ, t)
#  `UVM_NONBLOCKING_GET_PEEK_IMP(this.m_if, RSP, t)
#endclass
class UVMNonBlockingMasterPort():   #(type REQ=int, type RSP=REQ)
    pass
UVMNonBlockingMasterPort = UVM_PORT_COMMON(UVMNonBlockingMasterPort,
        UVM_TLM_NONBLOCKING_MASTER_MASK,"uvm_nonblocking_master_port")
UVM_NONBLOCKING_PUT_IMP('m_if',  UVMNonBlockingMasterPort)
UVM_NONBLOCKING_GET_PEEK_IMP('m_if', UVMNonBlockingMasterPort)

#class uvm_master_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP));
#  `UVM_PORT_COMMON(`UVM_TLM_MASTER_MASK,"uvm_master_port")
#  `UVM_PUT_IMP(this.m_if, REQ, t)
#  `UVM_GET_PEEK_IMP(this.m_if, RSP, t)
#endclass
class UVMMasterPort():  # (type REQ=int, type RSP=REQ)
    pass
UVMMasterPort = UVM_PORT_COMMON(UVMMasterPort,
        UVM_TLM_MASTER_MASK,"uvm_master_port")
UVM_PUT_IMP('m_if',  UVMMasterPort)
UVM_GET_PEEK_IMP('m_if', UVMMasterPort)

#class uvm_blocking_slave_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(RSP, REQ));
#  `UVM_PORT_COMMON(`UVM_TLM_BLOCKING_SLAVE_MASK,"uvm_blocking_slave_port")
#  `UVM_BLOCKING_PUT_IMP(this.m_if, RSP, t)
#  `UVM_BLOCKING_GET_PEEK_IMP(this.m_if, REQ, t)
#endclass
class UVMBlockingSlavePort():  #(type REQ=int, type RSP=REQ)
    pass
UVMBlockingSlavePort = UVM_PORT_COMMON(UVMBlockingSlavePort,
        UVM_TLM_BLOCKING_SLAVE_MASK,"uvm_blocking_slave_port")
UVM_BLOCKING_PUT_IMP('m_if',  UVMBlockingSlavePort)
UVM_BLOCKING_GET_PEEK_IMP('m_if', UVMBlockingSlavePort)

#class uvm_nonblocking_slave_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(RSP, REQ));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_SLAVE_MASK,"uvm_nonblocking_slave_port")
#  `UVM_NONBLOCKING_PUT_IMP(this.m_if, RSP, t)
#  `UVM_NONBLOCKING_GET_PEEK_IMP(this.m_if, REQ, t)
#endclass
class UVMNonBlockingSlavePort():  # (type REQ=int, type RSP=REQ)
    pass
UVMNonBlockingSlavePort = UVM_PORT_COMMON(UVMNonBlockingSlavePort,
        UVM_TLM_NONBLOCKING_SLAVE_MASK,"uvm_nonblocking_slave_port")
UVM_NONBLOCKING_PUT_IMP('m_if',  UVMNonBlockingSlavePort)
UVM_NONBLOCKING_GET_PEEK_IMP('m_if', UVMNonBlockingSlavePort)

#class uvm_slave_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(RSP, REQ));
#  `UVM_PORT_COMMON(`UVM_TLM_SLAVE_MASK,"uvm_slave_port")
#  `UVM_PUT_IMP(this.m_if, RSP, t)
#  `UVM_GET_PEEK_IMP(this.m_if, REQ, t)
#endclass
class UVMSlavePort():  # (type REQ=int, type RSP=REQ)
    pass
UVMSlavePort = UVM_PORT_COMMON(UVMSlavePort,
        UVM_TLM_SLAVE_MASK,"uvm_slave_port")
UVM_PUT_IMP('m_if',  UVMSlavePort)
UVM_GET_PEEK_IMP('m_if', UVMSlavePort)

#class uvm_blocking_transport_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP));
#  `UVM_PORT_COMMON(`UVM_TLM_BLOCKING_TRANSPORT_MASK,"uvm_blocking_transport_port")
#  `UVM_BLOCKING_TRANSPORT_IMP(this.m_if, REQ, RSP, req, rsp)
#endclass
class UVMBlockingTransportPort():   # (type REQ=int, type RSP=REQ)
    pass
UVMBlockingTransportPort = UVM_PORT_COMMON(UVMBlockingTransportPort,
    UVM_TLM_BLOCKING_TRANSPORT_MASK,"uvm_blocking_transport_port")
UVM_BLOCKING_TRANSPORT_IMP('m_if', UVMBlockingTransportPort)

#class uvm_nonblocking_transport_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP));
#  `UVM_PORT_COMMON(`UVM_TLM_NONBLOCKING_TRANSPORT_MASK,"uvm_nonblocking_transport_port")
#  `UVM_NONBLOCKING_TRANSPORT_IMP(this.m_if, REQ, RSP, req, rsp)
#endclass
class UVMNonBlockingTransportPort():   # (type REQ=int, type RSP=REQ)
    pass
UVMNonBlockingTransportPort =  UVM_PORT_COMMON(UVMNonBlockingTransportPort,
    UVM_TLM_NONBLOCKING_TRANSPORT_MASK,"uvm_nonblocking_transport_port")
UVM_NONBLOCKING_TRANSPORT_IMP('m_if', UVMNonBlockingTransportPort)


#class uvm_transport_port #(type REQ=int, type RSP=REQ)
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP));
#  `UVM_PORT_COMMON(`UVM_TLM_TRANSPORT_MASK,"uvm_transport_port")
#  `UVM_TRANSPORT_IMP(this.m_if, REQ, RSP, req, rsp)
#endclass
class UVMTransportPort():  # (type REQ=int, type RSP=REQ)
    pass
UVMTransportPort = UVM_PORT_COMMON(UVMTransportPort,
    UVM_TLM_TRANSPORT_MASK,"uvm_transport_port")
UVM_TRANSPORT_IMP('m_if', UVMTransportPort)
