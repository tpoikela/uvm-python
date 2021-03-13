#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019-2020 Tuomas Poikela
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

import cocotb

from ..base.uvm_globals import uvm_check_output_args
from ..tlm1.uvm_tlm_imps import add_base_class, UVM_IMP_COMMON
from ..base.uvm_port_base import UVMPortBase


def uvm_check_ref_arg(func_name, req_arg):
    if not hasattr(req_arg, 'append'):
        raise Exception("In python-uvm, ref args not supported. Variables "
                + " need to be passed as empty lists to obtain the output "
                + "values. Function: " + func_name)

#----------------------------------------------------------------------------
#
# Title: TLM Implementation Port Declaration Macros
#
# The TLM implementation declaration macros provide a way for components
# to provide multiple implementation ports of the same implementation
# interface. When an implementation port is defined using the built-in
# set of imps, there must be exactly one implementation of the interface.
#
# For example, if a component needs to provide a put implementation then
# it would have an implementation port defined like:
#
#| class mycomp extends uvm_component;
#|   uvm_put_imp#(data_type, mycomp) put_imp;
#|   ...
#|   virtual task put (data_type t);
#|     ...
#|   endtask
#| endclass
#
# There are times, however, when you need more than one implementation
# for an interface. This set of declarations allow you to easily create
# a new implementation class to allow for multiple implementations. Although
# the new implementation class is a different class, it can be bound to
# the same types of exports and ports as the original class. Extending
# the put example above, let's say that mycomp needs to provide two put
# implementation ports. In that case, you would do something like:
#
#| //Define two new put interfaces which are compatible with uvm_put_ports
#| //and uvm_put_exports.
#|
#| `uvm_put_imp_decl(_1)
#| `uvm_put_imp_decl(_2)
#|
#| class my_put_imp#(type T=int) extends uvm_component;
#|    uvm_put_imp_1#(T,my_put_imp#(T)) put_imp1;
#|    uvm_put_imp_2#(T,my_put_imp#(T)) put_imp2;
#|    ...
#|    function void put_1 (input T t);
#|      //puts coming into put_imp1
#|      ...
#|    endfunction
#|    function void put_2(input T t);
#|      //puts coming into put_imp2
#|      ...
#|    endfunction
#| endclass
#
# The important thing to note is that each `uvm_<interface>_imp_decl creates a
# new class of type uvm_<interface>_imp<suffix>, where suffix is the input
# argument to the macro. For this reason, you will typically want to put
# these macros in a separate package to avoid collisions and to allow
# sharing of the definitions.
#-----------------------------------------------------------------------------

# MACRO: `uvm_blocking_put_imp_decl
#
#| `uvm_blocking_put_imp_decl(SFX)
#
# Define the class uvm_blocking_put_impSFX for providing blocking put
# implementations.  ~SFX~ is the suffix for the new class type.
#
#`define uvm_blocking_put_imp_decl(SFX) \
#class uvm_blocking_put_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_BLOCKING_PUT_MASK,`"uvm_blocking_put_imp``SFX`",IMP) \
#  `UVM_BLOCKING_PUT_IMP_SFX(SFX, m_imp, T, t) \
#endclass


# MACRO: `uvm_nonblocking_put_imp_decl
#
#| `uvm_nonblocking_put_imp_decl(SFX)
#
# Define the class uvm_nonblocking_put_impSFX for providing non-blocking
# put implementations.  ~SFX~ is the suffix for the new class type.
#
#`define uvm_nonblocking_put_imp_decl(SFX) \
#class uvm_nonblocking_put_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_NONBLOCKING_PUT_MASK,`"uvm_nonblocking_put_imp``SFX`",IMP) \
#  `UVM_NONBLOCKING_PUT_IMP_SFX( SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_put_imp_decl
#
#| `uvm_put_imp_decl(SFX)
#
# Define the class uvm_put_impSFX for providing both blocking and
# non-blocking put implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_put_imp_decl(SFX) \
#class uvm_put_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_PUT_MASK,`"uvm_put_imp``SFX`",IMP) \
#  `UVM_BLOCKING_PUT_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_NONBLOCKING_PUT_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_blocking_get_imp_decl
#
#| `uvm_blocking_get_imp_decl(SFX)
#
# Define the class uvm_blocking_get_impSFX for providing blocking get
# implementations.  ~SFX~ is the suffix for the new class type.
#
#`define uvm_blocking_get_imp_decl(SFX) \
#class uvm_blocking_get_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_BLOCKING_GET_MASK,`"uvm_blocking_get_imp``SFX`",IMP) \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_nonblocking_get_imp_decl
#
#| `uvm_nonblocking_get_imp_decl(SFX)
#
# Define the class uvm_nonblocking_get_impSFX for providing non-blocking
# get implementations.  ~SFX~ is the suffix for the new class type.
#
#`define uvm_nonblocking_get_imp_decl(SFX) \
#class uvm_nonblocking_get_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_NONBLOCKING_GET_MASK,`"uvm_nonblocking_get_imp``SFX`",IMP) \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_get_imp_decl
#
#| `uvm_get_imp_decl(SFX)
#
# Define the class uvm_get_impSFX for providing both blocking and
# non-blocking get implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_get_imp_decl(SFX) \
#class uvm_get_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_GET_MASK,`"uvm_get_imp``SFX`",IMP) \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_blocking_peek_imp_decl
#
#| `uvm_blocking_peek_imp_decl(SFX)
#
# Define the class uvm_blocking_peek_impSFX for providing blocking peek
# implementations.  ~SFX~ is the suffix for the new class type.
#
#`define uvm_blocking_peek_imp_decl(SFX) \
#class uvm_blocking_peek_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_BLOCKING_PEEK_MASK,`"uvm_blocking_peek_imp``SFX`",IMP) \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_nonblocking_peek_imp_decl
#
#| `uvm_nonblocking_peek_imp_decl(SFX)
#
# Define the class uvm_nonblocking_peek_impSFX for providing non-blocking
# peek implementations.  ~SFX~ is the suffix for the new class type.
#
#`define uvm_nonblocking_peek_imp_decl(SFX) \
#class uvm_nonblocking_peek_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_NONBLOCKING_PEEK_MASK,`"uvm_nonblocking_peek_imp``SFX`",IMP) \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_peek_imp_decl
#
#| `uvm_peek_imp_decl(SFX)
#
# Define the class uvm_peek_impSFX for providing both blocking and
# non-blocking peek implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_peek_imp_decl(SFX) \
#class uvm_peek_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_PEEK_MASK,`"uvm_peek_imp``SFX`",IMP) \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_blocking_get_peek_imp_decl
#
#| `uvm_blocking_get_peek_imp_decl(SFX)
#
# Define the class uvm_blocking_get_peek_impSFX for providing the
# blocking get_peek implementation.
#
#`define uvm_blocking_get_peek_imp_decl(SFX) \
#class uvm_blocking_get_peek_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_BLOCKING_GET_PEEK_MASK,`"uvm_blocking_get_peek_imp``SFX`",IMP) \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_nonblocking_get_peek_imp_decl
#
#| `uvm_nonblocking_get_peek_imp_decl(SFX)
#
# Define the class uvm_nonblocking_get_peek_impSFX for providing non-blocking
# get_peek implementation.
#
#`define uvm_nonblocking_get_peek_imp_decl(SFX) \
#class uvm_nonblocking_get_peek_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_NONBLOCKING_GET_PEEK_MASK,`"uvm_nonblocking_get_peek_imp``SFX`",IMP) \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_get_peek_imp_decl
#
#| `uvm_get_peek_imp_decl(SFX)
#
# Define the class uvm_get_peek_impSFX for providing both blocking and
# non-blocking get_peek implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_get_peek_imp_decl(SFX) \
#class uvm_get_peek_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_GET_PEEK_MASK,`"uvm_get_peek_imp``SFX`",IMP) \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_imp, T, t) \
#endclass

# MACRO: `uvm_blocking_master_imp_decl
#
#| `uvm_blocking_master_imp_decl(SFX)
#
# Define the class uvm_blocking_master_impSFX for providing the
# blocking master implementation.
#
#`define uvm_blocking_master_imp_decl(SFX) \
#class uvm_blocking_master_imp``SFX #(type REQ=int, type RSP=int, type IMP=int, \
#                                     type REQ_IMP=IMP, type RSP_IMP=IMP) \
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP)); \
#  typedef IMP     this_imp_type; \
#  typedef REQ_IMP this_req_type; \
#  typedef RSP_IMP this_rsp_type; \
#  `UVM_MS_IMP_COMMON(`UVM_TLM_BLOCKING_MASTER_MASK,`"uvm_blocking_master_imp``SFX`") \
#  \
#  `UVM_BLOCKING_PUT_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  \
#endclass

# MACRO: `uvm_nonblocking_master_imp_decl
#
#| `uvm_nonblocking_master_imp_decl(SFX)
#
# Define the class uvm_nonblocking_master_impSFX for providing the
# non-blocking master implementation.
#
#`define uvm_nonblocking_master_imp_decl(SFX) \
#class uvm_nonblocking_master_imp``SFX #(type REQ=int, type RSP=int, type IMP=int, \
#                                   type REQ_IMP=IMP, type RSP_IMP=IMP) \
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP)); \
#  typedef IMP     this_imp_type; \
#  typedef REQ_IMP this_req_type; \
#  typedef RSP_IMP this_rsp_type; \
#  `UVM_MS_IMP_COMMON(`UVM_TLM_NONBLOCKING_MASTER_MASK,`"uvm_nonblocking_master_imp``SFX`") \
#  \
#  `UVM_NONBLOCKING_PUT_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  \
#endclass

# MACRO: `uvm_master_imp_decl
#
#| `uvm_master_imp_decl(SFX)
#
# Define the class uvm_master_impSFX for providing both blocking and
# non-blocking master implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_master_imp_decl(SFX) \
#class uvm_master_imp``SFX #(type REQ=int, type RSP=int, type IMP=int, \
#                            type REQ_IMP=IMP, type RSP_IMP=IMP) \
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP)); \
#  typedef IMP     this_imp_type; \
#  typedef REQ_IMP this_req_type; \
#  typedef RSP_IMP this_rsp_type; \
#  `UVM_MS_IMP_COMMON(`UVM_TLM_MASTER_MASK,`"uvm_master_imp``SFX`") \
#  \
#  `UVM_BLOCKING_PUT_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  `UVM_NONBLOCKING_PUT_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  \
#endclass

# MACRO: `uvm_blocking_slave_imp_decl
#
#| `uvm_blocking_slave_imp_decl(SFX)
#
# Define the class uvm_blocking_slave_impSFX for providing the
# blocking slave implementation.
#
#`define uvm_blocking_slave_imp_decl(SFX) \
#class uvm_blocking_slave_imp``SFX #(type REQ=int, type RSP=int, type IMP=int, \
#                                    type REQ_IMP=IMP, type RSP_IMP=IMP) \
#  extends uvm_port_base #(uvm_tlm_if_base #(RSP, REQ)); \
#  typedef IMP     this_imp_type; \
#  typedef REQ_IMP this_req_type; \
#  typedef RSP_IMP this_rsp_type; \
#  `UVM_MS_IMP_COMMON(`UVM_TLM_BLOCKING_SLAVE_MASK,`"uvm_blocking_slave_imp``SFX`") \
#  \
#  `UVM_BLOCKING_PUT_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  \
#endclass

# MACRO: `uvm_nonblocking_slave_imp_decl
#
#| `uvm_nonblocking_slave_imp_decl(SFX)
#
# Define the class uvm_nonblocking_slave_impSFX for providing the
# non-blocking slave implementation.
#
#`define uvm_nonblocking_slave_imp_decl(SFX) \
#class uvm_nonblocking_slave_imp``SFX #(type REQ=int, type RSP=int, type IMP=int, \
#                                       type REQ_IMP=IMP, type RSP_IMP=IMP) \
#  extends uvm_port_base #(uvm_tlm_if_base #(RSP, REQ)); \
#  typedef IMP     this_imp_type; \
#  typedef REQ_IMP this_req_type; \
#  typedef RSP_IMP this_rsp_type; \
#  `UVM_MS_IMP_COMMON(`UVM_TLM_NONBLOCKING_SLAVE_MASK,`"uvm_nonblocking_slave_imp``SFX`") \
#  \
#  `UVM_NONBLOCKING_PUT_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  \
#endclass

# MACRO: `uvm_slave_imp_decl
#
#| `uvm_slave_imp_decl(SFX)
#
# Define the class uvm_slave_impSFX for providing both blocking and
# non-blocking slave implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_slave_imp_decl(SFX) \
#class uvm_slave_imp``SFX #(type REQ=int, type RSP=int, type IMP=int, \
#                           type REQ_IMP=IMP, type RSP_IMP=IMP) \
#  extends uvm_port_base #(uvm_tlm_if_base #(RSP, REQ)); \
#  typedef IMP     this_imp_type; \
#  typedef REQ_IMP this_req_type; \
#  typedef RSP_IMP this_rsp_type; \
#  `UVM_MS_IMP_COMMON(`UVM_TLM_SLAVE_MASK,`"uvm_slave_imp``SFX`") \
#  \
#  `UVM_BLOCKING_PUT_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  `UVM_NONBLOCKING_PUT_IMP_SFX(SFX, m_rsp_imp, RSP, t) // rsp \
#  \
#  `UVM_BLOCKING_GET_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  `UVM_BLOCKING_PEEK_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  `UVM_NONBLOCKING_GET_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  `UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, m_req_imp, REQ, t) // req \
#  \
#endclass

# MACRO: `uvm_blocking_transport_imp_decl
#
#| `uvm_blocking_transport_imp_decl(SFX)
#
# Define the class uvm_blocking_transport_impSFX for providing the
# blocking transport implementation.
#
#`define uvm_blocking_transport_imp_decl(SFX) \
#class uvm_blocking_transport_imp``SFX #(type REQ=int, type RSP=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP)); \
#  `UVM_IMP_COMMON(`UVM_TLM_BLOCKING_TRANSPORT_MASK,`"uvm_blocking_transport_imp``SFX`",IMP) \
#  `UVM_BLOCKING_TRANSPORT_IMP_SFX(SFX, m_imp, REQ, RSP, req, rsp) \
#endclass
#
# MACRO: `uvm_nonblocking_transport_imp_decl
#
#| `uvm_nonblocking_transport_imp_decl(SFX)
#
# Define the class uvm_nonblocking_transport_impSFX for providing the
# non-blocking transport implementation.
#
#`define uvm_nonblocking_transport_imp_decl(SFX) \
#class uvm_nonblocking_transport_imp``SFX #(type REQ=int, type RSP=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP)); \
#  `UVM_IMP_COMMON(`UVM_TLM_NONBLOCKING_TRANSPORT_MASK,`"uvm_nonblocking_transport_imp``SFX`",IMP) \
#  `UVM_NONBLOCKING_TRANSPORT_IMP_SFX(SFX, m_imp, REQ, RSP, req, rsp) \
#endclass
#
#`define uvm_non_blocking_transport_imp_decl(SFX) \
#  `uvm_nonblocking_transport_imp_decl(SFX)

# MACRO: `uvm_transport_imp_decl
#
#| `uvm_transport_imp_decl(SFX)
#
# Define the class uvm_transport_impSFX for providing both blocking and
# non-blocking transport implementations.  ~SFX~ is the suffix for the new class
# type.
#
#`define uvm_transport_imp_decl(SFX) \
#class uvm_transport_imp``SFX #(type REQ=int, type RSP=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(REQ, RSP)); \
#  `UVM_IMP_COMMON(`UVM_TLM_TRANSPORT_MASK,`"uvm_transport_imp``SFX`",IMP) \
#  `UVM_BLOCKING_TRANSPORT_IMP_SFX(SFX, m_imp, REQ, RSP, req, rsp) \
#  `UVM_NONBLOCKING_TRANSPORT_IMP_SFX(SFX, m_imp, REQ, RSP, req, rsp) \
#endclass

# MACRO: `uvm_analysis_imp_decl
#
#| `uvm_analysis_imp_decl(SFX)
#
# Define the class uvm_analysis_impSFX for providing an analysis
# implementation. ~SFX~ is the suffix for the new class type. The analysis
# implementation is the write function. The `uvm_analysis_imp_decl allows
# for a scoreboard (or other analysis component) to support input from many
# places. For example:
#
#| `uvm_analysis_imp_decl(_ingress)
#| `uvm_analysis_imp_decl(_egress)
#|
#| class myscoreboard extends uvm_component;
#|   uvm_analysis_imp_ingress#(mydata, myscoreboard) ingress;
#|   uvm_analysis_imp_egress#(mydata, myscoreboard) egress;
#|   mydata ingress_list[$];
#|   ...
#|
#|   function new(string name, uvm_component parent);
#|     super.new(name,parent);
#|     ingress = new("ingress", this);
#|     egress = new("egress", this);
#|   endfunction
#|
#|   function void write_ingress(mydata t);
#|     ingress_list.push_back(t);
#|   endfunction
#|
#|   function void write_egress(mydata t);
#|     find_match_in_ingress_list(t);
#|   endfunction
#|
#|   function void find_match_in_ingress_list(mydata t);
#|     //implement scoreboarding for this particular dut
#|     ...
#|   endfunction
#| endclass

#`define uvm_analysis_imp_decl(SFX) \
#class uvm_analysis_imp``SFX #(type T=int, type IMP=int) \
#  extends uvm_port_base #(uvm_tlm_if_base #(T,T)); \
#  `UVM_IMP_COMMON(`UVM_TLM_ANALYSIS_MASK,`"uvm_analysis_imp``SFX`",IMP) \
#  function void write( input T t); \
#    m_imp.write``SFX( t); \
#  endfunction \
#  \
#endclass
def uvm_analysis_imp_decl(SFX):
    TT = type("UVMAnalysisImp" + SFX, (), {})
    T = add_base_class(TT, UVMPortBase)
    T = UVM_IMP_COMMON(T, UVM_TLM_ANALYSIS_MASK, "UVMAnalysisImp" + SFX)
    def write(self, t):
        getattr(self.m_imp, "write" + SFX)(t)
    setattr(T, "write", write)
    return T


# These imps are used in uvm_*_port, uvm_*_export and uvm_*_imp, using suffixes

#`define UVM_BLOCKING_PUT_IMP_SFX(SFX, imp, TYPE, arg) \
#  task put( input TYPE arg); imp.put``SFX( arg); endtask
#
#`define UVM_BLOCKING_GET_IMP_SFX(SFX, imp, TYPE, arg) \
#  task get( output TYPE arg); imp.get``SFX( arg); endtask
#
#`define UVM_BLOCKING_PEEK_IMP_SFX(SFX, imp, TYPE, arg) \
#  task peek( output TYPE arg);imp.peek``SFX( arg); endtask

#`define UVM_NONBLOCKING_PUT_IMP_SFX(SFX, imp, TYPE, arg) \
#  function bit try_put( input TYPE arg); \
#    if( !imp.try_put``SFX( arg)) return 0; \
#    return 1; \
#  endfunction \
#  function bit can_put(); return imp.can_put``SFX(); endfunction

#`define UVM_NONBLOCKING_GET_IMP_SFX(SFX, imp, TYPE, arg) \
#  function bit try_get( output TYPE arg); \
#    if( !imp.try_get``SFX( arg)) return 0; \
#    return 1; \
#  endfunction \
#  function bit can_get(); return imp.can_get``SFX(); endfunction

#`define UVM_NONBLOCKING_PEEK_IMP_SFX(SFX, imp, TYPE, arg) \
#  function bit try_peek( output TYPE arg); \
#    if( !imp.try_peek``SFX( arg)) return 0; \
#    return 1; \
#  endfunction \
#  function bit can_peek(); return imp.can_peek``SFX(); endfunction

#`define UVM_BLOCKING_TRANSPORT_IMP_SFX(SFX, imp, REQ, RSP, req_arg, rsp_arg) \
#  task transport( input REQ req_arg, output RSP rsp_arg); \
#    imp.transport``SFX(req_arg, rsp_arg); \
#  endtask

#`define UVM_NONBLOCKING_TRANSPORT_IMP_SFX(SFX, imp, REQ, RSP, req_arg, rsp_arg) \
#  function bit nb_transport( input REQ req_arg, output RSP rsp_arg); \
#    if(imp) return imp.nb_transport``SFX(req_arg, rsp_arg); \
#  endfunction

#----------------------------------------------------------------------
# imp definitions
#----------------------------------------------------------------------

#`define UVM_SEQ_ITEM_PULL_IMP(imp, REQ, RSP, req_arg, rsp_arg) \
def UVM_SEQ_ITEM_PULL_IMP(T, imp):
    def disable_auto_item_recording(self):
        getattr(self, imp).disable_auto_item_recording()
    setattr(T, 'disable_auto_item_recording', disable_auto_item_recording)

    def is_auto_item_recording_enabled(self):
        return getattr(self, imp).is_auto_item_recording_enabled()
    setattr(T, 'is_auto_item_recording_enabled', is_auto_item_recording_enabled)

    
    async def get_next_item(self, req_arg):
        uvm_check_ref_arg('get_next_item', req_arg)
        await getattr(self, imp).get_next_item(req_arg)
    setattr(T, 'get_next_item', get_next_item)

    
    async def try_next_item(self, req_arg):
        await getattr(self, imp).try_next_item(req_arg)
    setattr(T, 'try_next_item', try_next_item)

    def item_done(self, rsp_arg=None):
        getattr(self, imp).item_done(rsp_arg)
    setattr(T, 'item_done', item_done)

    
    async def wait_for_sequences(self):
        await getattr(self, imp).wait_for_sequences()
    setattr(T, 'wait_for_sequences', wait_for_sequences)

    def has_do_available(self):
        return getattr(self, imp).has_do_available()
    setattr(T, 'has_do_available', has_do_available)

    def put_response(self, rsp_arg):
        getattr(self, imp).put_response(rsp_arg)
    setattr(T, 'put_response', put_response)

    
    async def get(self, req_arg):
        uvm_check_ref_arg('get', req_arg)
        await getattr(self, imp).get(req_arg)
    setattr(T, 'get', get)

    
    async def peek(self, req_arg):
        uvm_check_ref_arg('get', req_arg)
        await getattr(self, imp).peek(req_arg)
    setattr(T, 'peek', peek)

    
    async def put(self, rsp_arg):
        await getattr(self, imp).put(rsp_arg)
    setattr(T, 'put', put)


# primitive interfaces
UVM_TLM_BLOCKING_PUT_MASK = (1 << 0)
UVM_TLM_BLOCKING_GET_MASK = (1 << 1)
UVM_TLM_BLOCKING_PEEK_MASK = (1 << 2)
UVM_TLM_BLOCKING_TRANSPORT_MASK = (2 << 3)
#
UVM_TLM_NONBLOCKING_PUT_MASK = (1 << 4)
UVM_TLM_NONBLOCKING_GET_MASK = (1 << 5)
UVM_TLM_NONBLOCKING_PEEK_MASK = (1 << 6)
UVM_TLM_NONBLOCKING_TRANSPORT_MASK = (1 << 7)
#
UVM_TLM_ANALYSIS_MASK = (1 << 8)
#
UVM_TLM_MASTER_BIT_MASK = (1 << 9)
UVM_TLM_SLAVE_BIT_MASK = (1 << 10)
# combination interfaces
UVM_TLM_PUT_MASK =(UVM_TLM_BLOCKING_PUT_MASK | UVM_TLM_NONBLOCKING_PUT_MASK)
UVM_TLM_GET_MASK = (UVM_TLM_BLOCKING_GET_MASK    | UVM_TLM_NONBLOCKING_GET_MASK)
UVM_TLM_PEEK_MASK = (UVM_TLM_BLOCKING_PEEK_MASK   | UVM_TLM_NONBLOCKING_PEEK_MASK)

UVM_TLM_BLOCKING_GET_PEEK_MASK = (UVM_TLM_BLOCKING_GET_MASK    | UVM_TLM_BLOCKING_PEEK_MASK)
UVM_TLM_BLOCKING_MASTER_MASK = (UVM_TLM_BLOCKING_PUT_MASK       | UVM_TLM_BLOCKING_GET_MASK | UVM_TLM_BLOCKING_PEEK_MASK | UVM_TLM_MASTER_BIT_MASK)
UVM_TLM_BLOCKING_SLAVE_MASK = (UVM_TLM_BLOCKING_PUT_MASK       | UVM_TLM_BLOCKING_GET_MASK | UVM_TLM_BLOCKING_PEEK_MASK | UVM_TLM_SLAVE_BIT_MASK)

UVM_TLM_NONBLOCKING_GET_PEEK_MASK =(UVM_TLM_NONBLOCKING_GET_MASK | UVM_TLM_NONBLOCKING_PEEK_MASK)
UVM_TLM_NONBLOCKING_MASTER_MASK = (UVM_TLM_NONBLOCKING_PUT_MASK    | UVM_TLM_NONBLOCKING_GET_MASK | UVM_TLM_NONBLOCKING_PEEK_MASK | UVM_TLM_MASTER_BIT_MASK)
UVM_TLM_NONBLOCKING_SLAVE_MASK = (UVM_TLM_NONBLOCKING_PUT_MASK    | UVM_TLM_NONBLOCKING_GET_MASK | UVM_TLM_NONBLOCKING_PEEK_MASK | UVM_TLM_SLAVE_BIT_MASK)

UVM_TLM_GET_PEEK_MASK = (UVM_TLM_GET_MASK | UVM_TLM_PEEK_MASK)
UVM_TLM_MASTER_MASK = (UVM_TLM_BLOCKING_MASTER_MASK    | UVM_TLM_NONBLOCKING_MASTER_MASK)
UVM_TLM_SLAVE_MASK = (UVM_TLM_BLOCKING_SLAVE_MASK    | UVM_TLM_NONBLOCKING_SLAVE_MASK)
UVM_TLM_TRANSPORT_MASK = (UVM_TLM_BLOCKING_TRANSPORT_MASK | UVM_TLM_NONBLOCKING_TRANSPORT_MASK)

UVM_SEQ_ITEM_GET_NEXT_ITEM_MASK = (1 << 0)
UVM_SEQ_ITEM_TRY_NEXT_ITEM_MASK = (1 << 1)
UVM_SEQ_ITEM_ITEM_DONE_MASK = (1 << 2)
UVM_SEQ_ITEM_HAS_DO_AVAILABLE_MASK = (1 << 3)
UVM_SEQ_ITEM_WAIT_FOR_SEQUENCES_MASK = (1 << 4)
UVM_SEQ_ITEM_PUT_RESPONSE_MASK = (1 << 5)
UVM_SEQ_ITEM_PUT_MASK = (1 << 6)
UVM_SEQ_ITEM_GET_MASK = (1 << 7)
UVM_SEQ_ITEM_PEEK_MASK = (1 << 8)

UVM_SEQ_ITEM_PULL_MASK = (UVM_SEQ_ITEM_GET_NEXT_ITEM_MASK |
        UVM_SEQ_ITEM_TRY_NEXT_ITEM_MASK | UVM_SEQ_ITEM_ITEM_DONE_MASK |
        UVM_SEQ_ITEM_HAS_DO_AVAILABLE_MASK | UVM_SEQ_ITEM_WAIT_FOR_SEQUENCES_MASK
        | UVM_SEQ_ITEM_PUT_RESPONSE_MASK | UVM_SEQ_ITEM_PUT_MASK |
        UVM_SEQ_ITEM_GET_MASK | UVM_SEQ_ITEM_PEEK_MASK)

UVM_SEQ_ITEM_UNI_PULL_MASK = (UVM_SEQ_ITEM_GET_NEXT_ITEM_MASK |
        UVM_SEQ_ITEM_TRY_NEXT_ITEM_MASK | UVM_SEQ_ITEM_ITEM_DONE_MASK |
        UVM_SEQ_ITEM_HAS_DO_AVAILABLE_MASK | UVM_SEQ_ITEM_WAIT_FOR_SEQUENCES_MASK
        | UVM_SEQ_ITEM_GET_MASK | UVM_SEQ_ITEM_PEEK_MASK)

UVM_SEQ_ITEM_PUSH_MASK = (UVM_SEQ_ITEM_PUT_MASK)

