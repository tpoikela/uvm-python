#
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


from ..base.uvm_object_globals import UVM_EXPORT, UVM_IMPLEMENTATION, UVM_PORT

# These IMP macros define implementations of the uvm_*_port, uvm_*_export,
# and uvm_*_imp ports.

#---------------------------------------------------------------
# Macros for implementations of UVM ports and exports
#
#/*
#`define UVM_BLOCKING_PUT_IMP(imp, TYPE, arg) \
#  task put (TYPE arg); \
#    if (m_imp_list.size()) == 0) begin \
#      uvm_report_error("Port Not Bound","Blocking put to unbound port will wait forever.", UVM_NONE);
#      @imp;
#    end
#    if (bcast_mode) begin \
#      if (m_imp_list.size()) > 1) \
#        fork
#          begin
#            foreach (m_imp_list[index]) \
#              fork \
#                automatic int i = index; \
#                begin m_imp_list[i].put(arg); end \
#              join_none \
#            wait fork; \
#          end \
#        join \
#      else \
#        m_imp_list[0].put(arg); \
#    end \
#    else  \
#      if (imp != null) \
#        imp.put(arg); \
#  endtask \
#
#`define UVM_NONBLOCKING_PUT_IMP(imp, TYPE, arg) \
#  function bit try_put(input TYPE arg); \
#    if (bcast_mode) begin \
#      if (!can_put()) \
#        return 0; \
#      foreach (m_imp_list[index]) \
#        void'(m_imp_list[index].try_put(arg)); \
#      return 1; \
#    end  \
#    if (imp != null) \
#      return imp.try_put(arg)); \
#    return 0; \
#  endfunction \
#  \
#  function bit can_put(); \
#    if (bcast_mode) begin \
#      if (m_imp_list.size()) begin \
#        foreach (m_imp_list[index]) begin \
#          if (!m_imp_list[index].can_put() \
#            return 0; \
#        end \
#        return 1; \
#      end \
#      return 0; \
#    end \
#    if (imp != null) \
#      return imp.can_put(); \
#    return 0; \
#  endfunction
#
#*/

#-----------------------------------------------------------------------
# TLM imp implementations
#
#`define UVM_BLOCKING_PUT_IMP(imp, TYPE, arg) \
def UVM_BLOCKING_PUT_IMP(imp, T):
    
    async def put(self, t):
        if not hasattr(self, imp):
            raise Exception('Tried calling put() for attr {}'.format(imp))
        port_imp = getattr(self, imp)
        await port_imp.put(t)
    #endtask
    setattr(T, 'put', put)

#`define UVM_NONBLOCKING_PUT_IMP(imp, TYPE, arg) \
#  function bit try_put (TYPE arg); \
#    return imp.try_put(arg); \
#  endfunction \
#  function bit can_put(); \
#    return imp.can_put(); \
#  endfunction
def UVM_NONBLOCKING_PUT_IMP(imp, T):
    def try_put(self, arg):
        return getattr(self, imp).try_put(arg)
    setattr(T, 'try_put', try_put)

    def can_put(self):
        return getattr(self, imp).can_put()
    setattr(T, 'can_put', can_put)

#`define UVM_BLOCKING_GET_IMP(imp, TYPE, arg) \
#  task get (output TYPE arg); \
#    imp.get(arg); \
#  endtask
def UVM_BLOCKING_GET_IMP(imp, T):
    
    async def get(self, arg):
        await getattr(self, imp).get(arg)
    setattr(T, 'get', get)

#`define UVM_NONBLOCKING_GET_IMP(imp, TYPE, arg) \
#  function bit try_get (output TYPE arg); \
#    return imp.try_get(arg); \
#  endfunction \
#  function bit can_get(); \
#    return imp.can_get(); \
#  endfunction
def UVM_NONBLOCKING_GET_IMP(imp, T):
    def try_get(self, arg):
        return getattr(self, imp).try_get(arg)
    setattr(T, 'try_get', try_get)

    def can_get(self):
        return getattr(self, imp).can_get()
    setattr(T, 'can_get', can_get)

#`define UVM_BLOCKING_PEEK_IMP(imp, TYPE, arg) \
#  task peek (output TYPE arg); \
#    imp.peek(arg); \
def UVM_BLOCKING_PEEK_IMP(imp, T):
    
    async def peek(self, arg):
        await getattr(self, imp).peek(arg)
    setattr(T, 'peek', peek)

#`define UVM_NONBLOCKING_PEEK_IMP(imp, TYPE, arg) \
#  function bit try_peek (output TYPE arg); \
#    return imp.try_peek(arg); \
#  function bit can_peek(); \
#    return imp.can_peek(); \

def UVM_NONBLOCKING_PEEK_IMP(imp, T):
    def try_peek(self, arg):
        return getattr(self, imp).try_peek(arg)
    setattr(T, 'try_peek', try_peek)

    def can_peek(self):
        return getattr(self, imp).can_peek()
    setattr(T, 'can_peek', can_peek)

#`define UVM_BLOCKING_TRANSPORT_IMP(imp, REQ, RSP, req_arg, rsp_arg) \
#  task transport (REQ req_arg, output RSP rsp_arg); \
#    imp.transport(req_arg, rsp_arg); \
def UVM_BLOCKING_TRANSPORT_IMP(imp, T):
    
    async def transport (self, req_arg, rsp_arg):
        await getattr(self, imp).transport(req_arg, rsp_arg)
    setattr(T, 'transport', transport)

#`define UVM_NONBLOCKING_TRANSPORT_IMP(imp, REQ, RSP, req_arg, rsp_arg) \
#  function bit nb_transport (REQ req_arg, output RSP rsp_arg); \
#    return imp.nb_transport(req_arg, rsp_arg); \
def UVM_NONBLOCKING_TRANSPORT_IMP(imp, T):
    def nb_transport(self, req_arg, rsp_arg):
        return getattr(self, imp).nb_transport(req_arg, rsp_arg)
    setattr(T, 'nb_transport', nb_transport)

def UVM_PUT_IMP(imp, T):
    UVM_BLOCKING_PUT_IMP(imp, T)
    UVM_NONBLOCKING_PUT_IMP(imp, T)

def UVM_GET_IMP(imp, T):
    UVM_BLOCKING_GET_IMP(imp, T)
    UVM_NONBLOCKING_GET_IMP(imp, T)

#`define UVM_PEEK_IMP(imp, TYPE, arg) \
#  `UVM_BLOCKING_PEEK_IMP(imp, TYPE, arg) \
#  `UVM_NONBLOCKING_PEEK_IMP(imp, TYPE, arg)
def UVM_PEEK_IMP(imp, T):
    UVM_BLOCKING_PEEK_IMP(imp, T)
    UVM_NONBLOCKING_PEEK_IMP(imp, T)

#`define UVM_BLOCKING_GET_PEEK_IMP(imp, TYPE, arg) \
#  `UVM_BLOCKING_GET_IMP(imp, TYPE, arg) \
#  `UVM_BLOCKING_PEEK_IMP(imp, TYPE, arg)
def UVM_BLOCKING_GET_PEEK_IMP(imp, T):
    UVM_BLOCKING_GET_IMP(imp, T)
    UVM_BLOCKING_PEEK_IMP(imp, T)

#`define UVM_NONBLOCKING_GET_PEEK_IMP(imp, TYPE, arg) \
#  `UVM_NONBLOCKING_GET_IMP(imp, TYPE, arg) \
#  `UVM_NONBLOCKING_PEEK_IMP(imp, TYPE, arg)
def UVM_NONBLOCKING_GET_PEEK_IMP(imp, T):
    UVM_NONBLOCKING_GET_IMP(imp, T)
    UVM_NONBLOCKING_PEEK_IMP(imp, T)

#`define UVM_GET_PEEK_IMP(imp, TYPE, arg) \
#  `UVM_BLOCKING_GET_PEEK_IMP(imp, TYPE, arg) \
#  `UVM_NONBLOCKING_GET_PEEK_IMP(imp, TYPE, arg)
def UVM_GET_PEEK_IMP(imp, T):
    UVM_BLOCKING_GET_PEEK_IMP(imp, T)
    UVM_NONBLOCKING_GET_PEEK_IMP(imp, T)

#`define UVM_TRANSPORT_IMP(imp, REQ, RSP, req_arg, rsp_arg) \
#  `UVM_BLOCKING_TRANSPORT_IMP(imp, REQ, RSP, req_arg, rsp_arg) \
#  `UVM_NONBLOCKING_TRANSPORT_IMP(imp, REQ, RSP, req_arg, rsp_arg)
def UVM_TRANSPORT_IMP(imp, T):
    UVM_BLOCKING_TRANSPORT_IMP(imp, T)
    UVM_NONBLOCKING_TRANSPORT_IMP(imp, T)

def UVM_TLM_GET_TYPE_NAME(T):
    Ts = T.__name__

    def get_type_name(self):
        return Ts
    setattr(T, 'get_type_name', get_type_name)
#

#`define UVM_PORT_COMMON(MASK,TYPE_NAME) \
#  function new (string name, uvm_component parent, \
#                int min_size=1, int max_size=1); \
#    super.new (name, parent, UVM_PORT, min_size, max_size); \
#    m_if_mask = MASK; \
#  endfunction \
#  UVM_TLM_GET_TYPE_NAME(TYPE_NAME)
def UVM_PORT_COMMON(T, MASK, TYPE_NAME):
    from ..base.uvm_port_base import UVMPortBase
    def __init__(self, name, parent, min_size=1, max_size=1):
        UVMPortBase.__init__(self, name, parent, UVM_PORT, min_size, max_size)
        self.m_if_mask = MASK
    setattr(T, '__init__', __init__)
    UVM_TLM_GET_TYPE_NAME(T)
    return add_base_class(T, UVMPortBase)

#
#`define UVM_SEQ_PORT(MASK,TYPE_NAME) \
#  function new (string name, uvm_component parent, \
#                int min_size=0, int max_size=1); \
#    super.new (name, parent, UVM_PORT, min_size, max_size); \
#    m_if_mask = MASK; \
#  endfunction \
#  UVM_TLM_GET_TYPE_NAME(TYPE_NAME)
def UVM_SEQ_PORT(T, MASK, TYPE_NAME):
    from ..base.uvm_port_base import UVMPortBase
    def __init__(self, name, parent, min_size=0, max_size=1):
        UVMPortBase.__init__(self, name, parent, UVM_PORT, min_size, max_size)
        self.m_if_mask = MASK
    setattr(T, '__init__', __init__)
    UVM_TLM_GET_TYPE_NAME(T)
    return add_base_class(T, UVMPortBase)

#`define UVM_EXPORT_COMMON(MASK,TYPE_NAME) \
#  function new (string name, uvm_component parent, \
#                int min_size=1, int max_size=1); \
#    super.new (name, parent, UVM_EXPORT, min_size, max_size); \
#    m_if_mask = MASK; \
def UVM_EXPORT_COMMON(T,MASK,TYPE_NAME):
    from ..base.uvm_port_base import UVMPortBase
    def __init__(self, name, parent, min_size=1, max_size=1):
        UVMPortBase.__init__(self, name, parent, UVM_EXPORT, min_size, max_size)
        self.m_if_mask = MASK
    setattr(T, '__init__', __init__)
    UVM_TLM_GET_TYPE_NAME(T)
    return add_base_class(T, UVMPortBase)

def UVM_EXPORT_PORT(T, MASK, TYPE_NAME):
    from ..base.uvm_port_base import UVMPortBase
    def __init__(self, name, parent, min_size=1, max_size=1):
        UVMPortBase.__init__(self, name, parent, UVM_EXPORT, min_size, max_size)
        self.m_if_mask = MASK
    setattr(T, '__init__', __init__)
    UVM_TLM_GET_TYPE_NAME(T)
    return add_base_class(T, UVMPortBase)

def UVM_IMP_COMMON(T,MASK,TYPE_NAME):
    from ..base.uvm_port_base import UVMPortBase
    def __init__(self, name, imp):
        UVMPortBase.__init__(self, name, imp, UVM_IMPLEMENTATION, 1, 1)
        self.m_imp = imp
        self.m_if_mask = MASK
    UVM_TLM_GET_TYPE_NAME(T)
    TT = add_base_class(T, UVMPortBase)
    setattr(TT, '__init__', __init__)
    return TT

def add_base_class(T, new_base, args={}):
    return type(T.__name__, (T, new_base,), args)

#`define UVM_MS_IMP_COMMON(MASK,TYPE_NAME) \
#  local this_req_type m_req_imp; \
#  local this_rsp_type m_rsp_imp; \
#  function new (string name, this_imp_type imp, \
#                this_req_type req_imp = null, this_rsp_type rsp_imp = null); \
#    super.new (name, imp, UVM_IMPLEMENTATION, 1, 1); \
#    if(req_imp==null) $cast(req_imp, imp); \
#    if(rsp_imp==null) $cast(rsp_imp, imp); \
#    m_req_imp = req_imp; \
#    m_rsp_imp = rsp_imp; \
#    m_if_mask = MASK; \
#  endfunction  \
#  UVM_TLM_GET_TYPE_NAME(TYPE_NAME)
def UVM_MS_IMP_COMMON(T, MASK, TYPE_NAME):
    from ..base.uvm_port_base import UVMPortBase
    def __init__(self, name, imp, req_imp=None, rsp_imp=None):
        UVMPortBase.__init__(self, name, imp, UVM_IMPLEMENTATION, 1, 1)
        if req_imp is None:
            req_imp = imp
        if rsp_imp is None:
            rsp_imp = imp
        self.m_req_imp = req_imp
        self.m_rsp_imp = rsp_imp
        self.m_if_mask = MASK
    setattr(T, '__init__', __init__)
    UVM_TLM_GET_TYPE_NAME(T)
    return add_base_class(T, UVMPortBase)

