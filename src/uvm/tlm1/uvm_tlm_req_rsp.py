#//
#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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

from ..base.uvm_component import UVMComponent
from ..base.uvm_object_globals import UVM_NO_ACTION
from ..tlm1 import (UVMAnalysisPort, UVMGetPeekExport, UVMMasterImp,
    UVMPutExport, UVMSlaveImp, UVMTLMFIFO)
from ..base.uvm_port_base import (s_connection_error_id)

#//------------------------------------------------------------------------------
#// Title: TLM Channel Classes
#//------------------------------------------------------------------------------
#// This section defines built-in TLM channel classes.
#//------------------------------------------------------------------------------

#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_tlm_req_rsp_channel #(REQ,RSP)
#//
#// The uvm_tlm_req_rsp_channel contains a request FIFO of type ~REQ~ and a response
#// FIFO of type ~RSP~. These FIFOs can be of any size. This channel is
#// particularly useful for dealing with pipelined protocols where the request
#// and response are not tightly coupled.
#//
#// Type parameters:
#//
#// REQ - Type of the request transactions conveyed by self channel.
#// RSP - Type of the response transactions conveyed by self channel.
#//
#//------------------------------------------------------------------------------


class UVMTLMReqRspChannel(UVMComponent):


    #  typedef uvm_tlm_req_rsp_channel #(REQ, RSP) this_type
    #
    #  const static string type_name = "uvm_tlm_req_rsp_channel #(REQ,RSP)"
    type_name = "uvm_tlm_req_rsp_channel #(REQ,RSP)"

    #  // Port: put_request_export
    #  //
    #  // The put_export provides both the blocking and non-blocking put interface
    #  // methods to the request FIFO:
    #  //
    #  //|  def put(self,input T t)
    #  //|  def bit can_put (self):
    #  //|  def bit try_put (self,input T t):
    #  //
    #  // Any put port variant can connect and send transactions to the request FIFO
    #  // via self export, provided the transaction types match.
    #
    #  uvm_put_export #(REQ) put_request_export
    #
    #
    #  // Port: get_peek_response_export
    #  //
    #  // The get_peek_response_export provides all the blocking and non-blocking get
    #  // and peek interface methods to the response FIFO:
    #  //
    #  //|  def get(self,output T t)
    #  //|  def bit can_get (self):
    #  //|  def bit try_get (self,output T t):
    #  //|  def peek(self,output T t)
    #  //|  def bit can_peek (self):
    #  //|  def bit try_peek (self,output T t):
    #  //
    #  // Any get or peek port variant can connect to and retrieve transactions from
    #  // the response FIFO via self export, provided the transaction types match.
    #
    #  uvm_get_peek_export #(RSP) get_peek_response_export
    #
    #
    #  // Port: get_peek_request_export
    #  //
    #  // The get_peek_export provides all the blocking and non-blocking get and peek
    #  // interface methods to the response FIFO:
    #  //
    #  //|  def get(self,output T t)
    #  //|  def bit can_get (self):
    #  //|  def bit try_get (self,output T t):
    #  //|  def peek(self,output T t)
    #  //|  def bit can_peek (self):
    #  //|  def bit try_peek (self,output T t):
    #  //
    #  // Any get or peek port variant can connect to and retrieve transactions from
    #  // the response FIFO via self export, provided the transaction types match.
    #
    #
    #  uvm_get_peek_export #(REQ) get_peek_request_export
    #
    #
    #  // Port: put_response_export
    #  //
    #  // The put_export provides both the blocking and non-blocking put interface
    #  // methods to the response FIFO:
    #  //
    #  //|  def put(self,input T t)
    #  //|  def bit can_put (self):
    #  //|  def bit try_put (self,input T t):
    #  //
    #  // Any put port variant can connect and send transactions to the response FIFO
    #  // via self export, provided the transaction types match.
    #
    #  uvm_put_export #(RSP) put_response_export
    #
    #
    #  // Port: request_ap
    #  //
    #  // Transactions passed via ~put~ or ~try_put~ (via any port connected to the
    #  // put_request_export) are sent out self port via its write method.
    #  //
    #  //|  def void write (self,T t):
    #  //
    #  // All connected analysis exports and imps will receive these transactions.
    #
    #  uvm_analysis_port #(REQ) request_ap
    #
    #
    #  // Port: response_ap
    #  //
    #  // Transactions passed via ~put~ or ~try_put~ (via any port connected to the
    #  // put_response_export) are sent out self port via its write method.
    #  //
    #  //|  def void write (self,T t):
    #  //
    #  // All connected analysis exports and imps will receive these transactions.
    #
    #  uvm_analysis_port   #(RSP) response_ap
    #
    #
    #  // Port: master_export
    #  //
    #  // Exports a single interface that allows a master to put requests and get or
    #  // peek responses. It is a combination of the put_request_export and
    #  // get_peek_response_export.
    #
    #  uvm_master_imp #(REQ, RSP, this_type, uvm_tlm_fifo #(REQ), uvm_tlm_fifo #(RSP)) master_export
    #
    #
    #  // Port: slave_export
    #  //
    #  // Exports a single interface that allows a slave to get or peek requests and
    #  // to put responses. It is a combination of the get_peek_request_export
    #  // and put_response_export.
    #
    #  uvm_slave_imp  #(REQ, RSP, this_type, uvm_tlm_fifo #(REQ), uvm_tlm_fifo #(RSP)) slave_export
    #
    #  // port aliases for backward compatibility
    #  uvm_put_export      #(REQ) blocking_put_request_export,
    #                             nonblocking_put_request_export
    #  uvm_get_peek_export #(REQ) get_request_export,
    #                             blocking_get_request_export,
    #                             nonblocking_get_request_export,
    #                             peek_request_export,
    #                             blocking_peek_request_export,
    #                             nonblocking_peek_request_export,
    #                             blocking_get_peek_request_export,
    #                             nonblocking_get_peek_request_export
    #
    #  uvm_put_export      #(RSP) blocking_put_response_export,
    #                             nonblocking_put_response_export
    #  uvm_get_peek_export #(RSP) get_response_export,
    #                             blocking_get_response_export,
    #                             nonblocking_get_response_export,
    #                             peek_response_export,
    #                             blocking_peek_response_export,
    #                             nonblocking_peek_response_export,
    #                             blocking_get_peek_response_export,
    #                             nonblocking_get_peek_response_export
    #
    #  uvm_master_imp #(REQ, RSP, this_type, uvm_tlm_fifo #(REQ), uvm_tlm_fifo #(RSP))
    #                             blocking_master_export,
    #                             nonblocking_master_export
    #
    #  uvm_slave_imp  #(REQ, RSP, this_type, uvm_tlm_fifo #(REQ), uvm_tlm_fifo #(RSP))
    #                             blocking_slave_export,
    #                             nonblocking_slave_export


    #  // Function: new
    #  //
    #  // The ~name~ and ~parent~ are the standard <uvm_component> constructor arguments.
    #  // The ~parent~ must be ~None~ if self component is defined within a static
    #  // component such as a module, program block, or interface. The last two
    #  // arguments specify the request and response FIFO sizes, which have default
    #  // values of 1.
    def __init__(self, name, parent=None, request_fifo_size=1,
            response_fifo_size=1):
        super().__init__(name, parent)

        self.m_request_fifo  = UVMTLMFIFO("request_fifo", self, request_fifo_size)
        self.m_response_fifo = UVMTLMFIFO("response_fifo", self, response_fifo_size)
        self.request_ap      = UVMAnalysisPort("request_ap", self)
        self.response_ap     = UVMAnalysisPort("response_ap", self)

        self.put_request_export       = UVMPutExport("put_request_export", self)
        self.get_peek_request_export  = UVMGetPeekExport("get_peek_request_export", self)
        self.put_response_export      = UVMPutExport("put_response_export", self)
        self.get_peek_response_export = UVMGetPeekExport("get_peek_response_export", self)

        self.master_export   = UVMMasterImp("master_export", self, self.m_request_fifo,
                self.m_response_fifo)
        self.slave_export    = UVMSlaveImp("slave_export", self, self.m_request_fifo,
                self.m_response_fifo)
        self.create_aliased_exports()
        self.set_report_id_action_hier(s_connection_error_id, UVM_NO_ACTION)

    def connect_phase(self, phase):
        self.put_request_export.connect(self.m_request_fifo.put_export)
        self.get_peek_request_export.connect(self.m_request_fifo.get_peek_export)
        self.m_request_fifo.put_ap.connect(self.request_ap)
        self.put_response_export.connect(self.m_response_fifo.put_export)
        self.get_peek_response_export.connect(self.m_response_fifo.get_peek_export)
        self.m_response_fifo.put_ap.connect(self.response_ap)


    def create_aliased_exports(self):
        # request
        self.blocking_put_request_export         = self.put_request_export
        self.nonblocking_put_request_export      = self.put_request_export
        self.get_request_export                  = self.get_peek_request_export
        self.blocking_get_request_export         = self.get_peek_request_export
        self.nonblocking_get_request_export      = self.get_peek_request_export
        self.peek_request_export                 = self.get_peek_request_export
        self.blocking_peek_request_export        = self.get_peek_request_export
        self.nonblocking_peek_request_export     = self.get_peek_request_export
        self.blocking_get_peek_request_export    = self.get_peek_request_export
        self.nonblocking_get_peek_request_export = self.get_peek_request_export

        # response
        self.blocking_put_response_export         = self.put_response_export
        self.nonblocking_put_response_export      = self.put_response_export
        self.get_response_export                  = self.get_peek_response_export
        self.blocking_get_response_export         = self.get_peek_response_export
        self.nonblocking_get_response_export      = self.get_peek_response_export
        self.peek_response_export                 = self.get_peek_response_export
        self.blocking_peek_response_export        = self.get_peek_response_export
        self.nonblocking_peek_response_export     = self.get_peek_response_export
        self.blocking_get_peek_response_export    = self.get_peek_response_export
        self.nonblocking_get_peek_response_export = self.get_peek_response_export

        # master/slave
        self.blocking_master_export    = self.master_export
        self.nonblocking_master_export = self.master_export
        self.blocking_slave_export     = self.slave_export
        self.nonblocking_slave_export  = self.slave_export

    #  // get_type_name
    #  // -------------
    def get_type_name(self):
        return UVMTLMReqRspChannel.type_name

    #  // create
    #  // ------

    def create(self, name=""):
        return UVMTLMReqRspChannel(name)

#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_tlm_transport_channel #(REQ,RSP)
#//
#// A uvm_tlm_transport_channel is a <uvm_tlm_req_rsp_channel #(REQ,RSP)> that implements
#// the transport interface. It is useful when modeling a non-pipelined bus at
#// the transaction level. Because the requests and responses have a tightly
#// coupled one-to-one relationship, the request and response FIFO sizes are both
#// set to one.
#//
#//------------------------------------------------------------------------------
#
#class uvm_tlm_transport_channel #(type REQ=int, type RSP=REQ)
    #                                     extends uvm_tlm_req_rsp_channel #(REQ, RSP)
    #
    #  typedef uvm_tlm_transport_channel #(REQ, RSP) this_type
    #
    #  // Port: transport_export
    #  //
    #  // The put_export provides both the blocking and non-blocking transport
    #  // interface methods to the response FIFO:
    #  //
    #  //|  def transport(self,REQ request, output RSP response)
    #  //|  def bit nb_transport(self,REQ request, output RSP response):
    #  //
    #  // Any transport port variant can connect to and send requests and retrieve
    #  // responses via self export, provided the transaction types match. Upon
    #  // return, the response argument carries the response to the request.
    #
    #  uvm_transport_imp #(REQ, RSP, this_type) transport_export
    #
    #
    #  // Function: new
    #  //
    #  // The ~name~ and ~parent~ are the standard <uvm_component> constructor
    #  // arguments. The ~parent~ must be ~None~ if self component is defined within a
    #  // statically elaborated construct such as a module, program block, or
    #  // interface.
    #
    #  def __init__(self, name, parent=None)
    #    super().__init__(name, parent, 1, 1)
    #    transport_export = new("transport_export", self)
    #    self.e = None  # type: this_typ
    #    self.type_name =  "uvm_tlm_req_rsp_channel #(REQ,RSP)"  # type: string
    #    self.t = None  # type: put_request_expor
    #    self.t = None  # type: get_peek_response_expor
    #    self.t = None  # type: get_peek_request_expor
    #    self.t = None  # type: put_response_expor
    #    self.p = None  # type: request_a
    #    self.p = None  # type: response_a
    #    self.t = None  # type: master_expor
    #    self.t = None  # type: slave_expor
    #    self.t = None  # type: nonblocking_put_request_expor
    #    self.t = None  # type: nonblocking_get_peek_request_expor
    #    self.t = None  # type: nonblocking_put_response_expor
    #    self.t = None  # type: nonblocking_get_peek_response_expor
    #    self.t = None  # type: nonblocking_master_expor
    #    self.t = None  # type: nonblocking_slave_expor
    #    self.o = None  # type: m_request_fif
    #    self.o = None  # type: m_response_fif
    #    self.e = None  # type: this_typ
    #    self.t = None  # type: transport_expor
    #  endfunction
    #
    #@cocotb.coroutine
    #  def transport(self,REQ request, output RSP response )
    #    self.m_request_fifo.put( request )
    #    self.m_response_fifo.get( response )
    #  endtask
    #
    #  def bit nb_transport (self,REQ req, output RSP rsp ):
    #    if(self.m_request_fifo.try_put(req))
    #      return self.m_response_fifo.try_get(rsp)
    #    else
    #      return 0
    #  endfunction
    #
    #endclass
