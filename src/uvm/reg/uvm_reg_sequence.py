#//
#// -------------------------------------------------------------
#//    Copyright 2004-2009 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2010-2011 Cadence Design Systems, Inc.
#//    Copyright 2019 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//

import cocotb
from cocotb.triggers import Timer
from ..seq.uvm_sequence import UVMSequence
from ..macros import uvm_object_utils, uvm_fatal, uvm_warning, uvm_info
from ..base import UVM_LOW, UVM_HIGH
from ..base.uvm_globals import uvm_zero_delay
from .uvm_reg_model import UVM_WRITE

#//------------------------------------------------------------------------------
#// TITLE: Register Sequence Classes
#//------------------------------------------------------------------------------
#//
#// This section defines the base classes used for register stimulus generation.
#//------------------------------------------------------------------------------

LOCAL = 0
UPSTREAM = 1

#//------------------------------------------------------------------------------
#//
#// CLASS: UVMRegSequence
#//
#// This class provides base functionality for both user-defined RegModel test
#// sequences and "register translation sequences".
#//
#// - When used as a base for user-defined RegModel test sequences, this class
#//   provides convenience methods for reading and writing registers and
#//   memories. Users implement the body() method to interact directly with
#//   the RegModel model (held in the <model> property) or indirectly via the
#//   delegation methods in this class.
#//
#// - When used as a translation sequence, objects of this class are
#//   executed directly on a bus sequencer which are used in support of a layered sequencer
#//   use model, a pre-defined convert-and-execute algorithm is provided.
#//
#// Register operations do not require extending this class if none of the above
#// services are needed. Register test sequences can be extend from the base
#// <uvm_sequence #(REQ,RSP)> base class or even from outside a sequence.
#//
#// Note- The convenience API not yet implemented.
#//------------------------------------------------------------------------------
#class UVMRegSequence #(type BASE=uvm_sequence #(uvm_reg_item)) extends BASE;


class UVMRegSequence(UVMSequence):
    #
    #
    #  // Parameter: BASE
    #  //
    #  // Specifies the sequence type to extend from.
    #  //
    #  // When used as a translation sequence running on a bus sequencer, ~BASE~ must
    #  // be compatible with the sequence type expected by the bus sequencer.
    #  //
    #  // When used as a test sequence running on a particular sequencer, ~BASE~
    #  // must be compatible with the sequence type expected by that sequencer.
    #  //
    #  // When used as a virtual test sequence without a sequencer, ~BASE~ does
    #  // not need to be specified, i.e. the default specialization is adequate.
    #  //
    #  // To maximize opportunities for reuse, user-defined RegModel sequences should
    #  // "promote" the BASE parameter.
    #  //
    #  // | class my_reg_sequence #(type BASE=uvm_sequence #(uvm_reg_item))
    #  // |                               extends UVMRegSequence #(BASE);
    #  //
    #  // This way, the RegModel sequence can be extended from
    #  // user-defined base sequences.

    #
    #
    #  // Variable: model
    #  //
    #  // Block abstraction this sequence executes on, defined only when this
    #  // sequence is a user-defined test sequence.
    #  //
    #  uvm_reg_block model;

    #  // Variable: adapter
    #  //
    #  // Adapter to use for translating between abstract register transactions
    #  // and physical bus transactions, defined only when this sequence is a
    #  // translation sequence.
    #  //
    #  uvm_reg_adapter adapter;


    #  // Variable: reg_seqr
    #  //
    #  // Layered upstream "register" sequencer.
    #  //
    #  // Specifies the upstream sequencer between abstract register transactions
    #  // and physical bus transactions. Defined only when this sequence is a
    #  // translation sequence, and we want to "pull" from an upstream sequencer.
    #  //
    #  uvm_sequencer #(uvm_reg_item) reg_seqr;

    def __init__(self, name="uvm_reg_sequence_inst"):
        """         
          Function: new
         
          Create a new instance, giving it the optional `name`.
         
        Args:
            name: 
        """
        super().__init__(name)
        self.reg_seqr = None
        self.adapter = None
        self.model = None
        self.parent_select = LOCAL
        self.upstream_parent = None

    async def body(self):
        """         
          Task: body
         
          Continually gets a register transaction from the configured upstream
          sequencer, `reg_seqr`, and executes the corresponding bus transaction
          via `do_reg_item`.
         
          User-defined RegModel test sequences must override body() and not call
          super.body(), else a warning will be issued and the calling process
          not return.
         
        """
        if self.m_sequencer is None:
            uvm_fatal("NO_SEQR", "Sequence executing as translation sequence, " +
               "but is not associated with a sequencer (m_sequencer == null)")

        if self.reg_seqr is None:
            uvm_warning("REG_XLATE_NO_SEQR",
               "Executing RegModel translation sequence on sequencer " +
               self.m_sequencer.get_full_name() + "' does not have an upstream sequencer defined. "
               + "Execution of register items available only via direct calls to 'do_reg_item'")
            #wait(0);
            await uvm_zero_delay()
        uvm_info("REG_XLATE_SEQ_START",
           "Starting RegModel translation sequence on sequencer " +
           self.m_sequencer.get_full_name() + "'", UVM_LOW)
        while True:
            reg_item = []  # uvm_reg_item reg_item;
            await self.reg_seqr.peek(reg_item)
            await self.do_reg_item(reg_item[0])
            await self.reg_seqr.get(reg_item)
            #0;
            await uvm_zero_delay()


    async def do_reg_item(self, rw):
        """         
          Function: do_reg_item
         
          Executes the given register transaction, `rw`, via the sequencer on
          which this sequence was started (i.e. m_sequencer). Uses the configured
          `adapter` to convert the register transaction into the type expected by
          this sequencer.
         
         virtual task do_reg_item(uvm_reg_item rw);
        Args:
            rw: 
        """
        rws = rw.convert2string()
        if self.m_sequencer is None:
            uvm_fatal("REG/DO_ITEM/NULL","do_reg_item: m_sequencer is null")
        if self.adapter is None:
            uvm_fatal("REG/DO_ITEM/NULL","do_reg_item: adapter handle is null")

        uvm_info("DO_RW_ACCESS","Doing transaction: " + rws, UVM_HIGH)
        #
        if (self.parent_select == LOCAL):
            self.upstream_parent = rw.parent
            rw.parent = self

        if (rw.kind == UVM_WRITE):
            await rw.local_map.do_bus_write(rw, self.m_sequencer, self.adapter)
        else:
            await rw.local_map.do_bus_read(rw, self.m_sequencer, self.adapter)

        if (self.parent_select == LOCAL):
            rw.parent = self.upstream_parent


    #   //----------------------------------
    #   // Group: Convenience Write/Read API
    #   //----------------------------------
    #   //
    #   // The following methods delegate to the corresponding method in the
    #   // register or memory element. They allow a sequence ~body()~ to do
    #   // reads and writes without having to explicitly supply itself to
    #   // ~parent~ sequence argument. Thus, a register write
    #   //
    #   //| model.regA.write(status, value, .parent(this));
    #   //
    #   // can be written instead as
    #   //
    #   //| write_reg(model.regA, status, value);
    #   //


    #   // Task: write_reg
    #   //
    #   // Writes the given register ~rg~ using <uvm_reg::write>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| write_reg(model.regA, status, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.write(status, value, .parent(this));
    #   //
    #   virtual task write_reg(input  uvm_reg           rg,
    #                          output uvm_status_e      status,
    #                          input  uvm_reg_data_t    value,
    #                          input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                          input  uvm_reg_map       map = null,
    #                          input  int               prior = -1,
    #                          input  uvm_object        extension = null,
    #                          input  string            fname = "",
    #                          input  int               lineno = 0);
    #      if (rg == null)
    #        `uvm_error("NO_REG","Register argument is null")
    #      else
    #        rg.write(status,value,path,map,this,prior,extension,fname,lineno);
    #   endtask


    #   // Task: read_reg
    #   //
    #   // Reads the given register ~rg~ using <uvm_reg::read>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| read_reg(model.regA, status, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.read(status, value, .parent(this));
    #   //
    #   //
    #   virtual task read_reg(input  uvm_reg           rg,
    #                         output uvm_status_e      status,
    #                         output uvm_reg_data_t    value,
    #                         input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                         input  uvm_reg_map       map = null,
    #                         input  int               prior = -1,
    #                         input  uvm_object        extension = null,
    #                         input  string            fname = "",
    #                         input  int               lineno = 0);
    #      if (rg == null)
    #        `uvm_error("NO_REG","Register argument is null")
    #      else
    #        rg.read(status,value,path,map,this,prior,extension,fname,lineno);
    #   endtask

    #   // Task: poke_reg
    #   //
    #   // Pokes the given register ~rg~ using <uvm_reg::poke>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| poke_reg(model.regA, status, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.poke(status, value, .parent(this));
    #   //
    #   //
    #   virtual task poke_reg(input  uvm_reg           rg,
    #                         output uvm_status_e      status,
    #                         input  uvm_reg_data_t    value,
    #                         input  string            kind = "",
    #                         input  uvm_object        extension = null,
    #                         input  string            fname = "",
    #                         input  int               lineno = 0);
    #      if (rg == null)
    #        `uvm_error("NO_REG","Register argument is null")
    #      else
    #        rg.poke(status,value,kind,this,extension,fname,lineno);
    #   endtask

    #   // Task: peek_reg
    #   //
    #   // Peeks the given register ~rg~ using <uvm_reg::peek>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| peek_reg(model.regA, status, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.peek(status, value, .parent(this));
    #   //
    #   virtual task peek_reg(input  uvm_reg           rg,
    #                         output uvm_status_e      status,
    #                         output uvm_reg_data_t    value,
    #                         input  string            kind = "",
    #                         input  uvm_object        extension = null,
    #                         input  string            fname = "",
    #                         input  int               lineno = 0);
    #      if (rg == null)
    #        `uvm_error("NO_REG","Register argument is null")
    #      else
    #        rg.peek(status,value,kind,this,extension,fname,lineno);
    #   endtask

    #   // Task: update_reg
    #   //
    #   // Updates the given register ~rg~ using <uvm_reg::update>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| update_reg(model.regA, status, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.update(status, value, .parent(this));
    #   //
    #   virtual task update_reg(input  uvm_reg           rg,
    #                           output uvm_status_e      status,
    #                           input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                           input  uvm_reg_map       map = null,
    #                           input  int               prior = -1,
    #                           input  uvm_object        extension = null,
    #                           input  string            fname = "",
    #                           input  int               lineno = 0);
    #      if (rg == null)
    #        `uvm_error("NO_REG","Register argument is null")
    #      else
    #        rg.update(status,path,map,this,prior,extension,fname,lineno);
    #   endtask


    #   // Task: mirror_reg
    #   //
    #   // Mirrors the given register ~rg~ using <uvm_reg::mirror>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| mirror_reg(model.regA, status, UVM_CHECK);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.mirror(status, UVM_CHECK, .parent(this));
    #   //
    #   virtual task mirror_reg(input  uvm_reg       rg,
    #                           output uvm_status_e  status,
    #                           input  uvm_check_e   check  = UVM_NO_CHECK,
    #                           input  uvm_path_e    path = UVM_DEFAULT_PATH,
    #                           input  uvm_reg_map   map = null,
    #                           input  int           prior = -1,
    #                           input  uvm_object    extension = null,
    #                           input  string        fname = "",
    #                           input  int           lineno = 0);
    #      if (rg == null)
    #        `uvm_error("NO_REG","Register argument is null")
    #      else
    #        rg.mirror(status,check,path,map,this,prior,extension,fname,lineno);
    #   endtask

    #   // Task: write_mem
    #   //
    #   // Writes the given memory ~mem~ using <uvm_mem::write>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| write_mem(model.regA, status, offset, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.write(status, offset, value, .parent(this));
    #   //
    #   virtual task write_mem(input  uvm_mem           mem,
    #                          output uvm_status_e      status,
    #                          input  uvm_reg_addr_t    offset,
    #                          input  uvm_reg_data_t    value,
    #                          input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                          input  uvm_reg_map       map = null,
    #                          input  int               prior = -1,
    #                          input  uvm_object        extension = null,
    #                          input  string            fname = "",
    #                          input  int               lineno = 0);
    #      if (mem == null)
    #        `uvm_error("NO_MEM","Memory argument is null")
    #      else
    #        mem.write(status,offset,value,path,map,this,prior,extension,fname,lineno);
    #   endtask

    #   // Task: read_mem
    #   //
    #   // Reads the given memory ~mem~ using <uvm_mem::read>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| read_mem(model.regA, status, offset, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.read(status, offset, value, .parent(this));
    #   //
    #   //
    #   virtual task read_mem(input  uvm_mem           mem,
    #                         output uvm_status_e      status,
    #                         input  uvm_reg_addr_t    offset,
    #                         output uvm_reg_data_t    value,
    #                         input  uvm_path_e        path = UVM_DEFAULT_PATH,
    #                         input  uvm_reg_map       map = null,
    #                         input  int               prior = -1,
    #                         input  uvm_object        extension = null,
    #                         input  string            fname = "",
    #                         input  int               lineno = 0);
    #      if (mem == null)
    #        `uvm_error("NO_MEM","Memory argument is null")
    #      else
    #        mem.read(status,offset,value,path,map,this,prior,extension,fname,lineno);
    #   endtask

    #   // Task: poke_mem
    #   //
    #   // Pokes the given memory ~mem~ using <uvm_mem::poke>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| poke_mem(model.regA, status, offset, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.poke(status, offset, value, .parent(this));
    #   //
    #   //
    #   virtual task poke_mem(input  uvm_mem           mem,
    #                         output uvm_status_e      status,
    #                         input  uvm_reg_addr_t    offset,
    #                         input  uvm_reg_data_t    value,
    #                         input  string            kind = "",
    #                         input  uvm_object        extension = null,
    #                         input  string            fname = "",
    #                         input  int               lineno = 0);
    #      if (mem == null)
    #        `uvm_error("NO_MEM","Memory argument is null")
    #      else
    #        mem.poke(status,offset,value,kind,this,extension,fname,lineno);
    #   endtask

    #   // Task: peek_mem
    #   //
    #   // Peeks the given memory ~mem~ using <uvm_mem::peek>, supplying 'this' as
    #   // the ~parent~ argument. Thus,
    #   //
    #   //| peek_mem(model.regA, status, offset, value);
    #   //
    #   // is equivalent to
    #   //
    #   //| model.regA.peek(status, offset, value, .parent(this));
    #   //
    #   virtual task peek_mem(input  uvm_mem           mem,
    #                         output uvm_status_e      status,
    #                         input  uvm_reg_addr_t    offset,
    #                         output uvm_reg_data_t    value,
    #                         input  string            kind = "",
    #                         input  uvm_object        extension = null,
    #                         input  string            fname = "",
    #                         input  int               lineno = 0);
    #      if (mem == null)
    #        `uvm_error("NO_MEM","Memory argument is null")
    #      else
    #        mem.peek(status,offset,value,kind,this,extension,fname,lineno);
    #   endtask

    #  // Function- put_response
    #  //
    #  // not user visible. Needed to populate this sequence's response
    #  // queue with any bus item type.
    #  //
    #  virtual function void put_response(uvm_sequence_item response_item);
    #    put_base_response(response_item);
    #  endfunction
    #
    #endclass
uvm_object_utils(UVMRegSequence)


#//------------------------------------------------------------------------------
#// Class: UVMRegFrontdoor
#//
#// Facade class for register and memory frontdoor access.
#//------------------------------------------------------------------------------
#//
#// User-defined frontdoor access sequence
#//
#// Base class for user-defined access to register and memory reads and writes
#// through a physical interface.
#//
#// By default, different registers and memories are mapped to different
#// addresses in the address space and are accessed via those exclusively
#// through physical addresses.
#//
#// The frontdoor allows access using a non-linear and/or non-mapped mechanism.
#// Users can extend this class to provide the physical access to these registers.
#//


class UVMRegFrontdoor(UVMRegSequence):  # (uvm_sequence #(uvm_sequence_item));

    def __init__(self, name="reg_frontdoor_seq"):
        """         
           Function: new
          
           Constructor, new object given optional `name`.
          
        Args:
            name: 
        """
        super().__init__(name)
        #
        #   // Variable: rw_info
        #   //
        #   // Holds information about the register being read or written
        #   //
        #   uvm_reg_item rw_info;
        self.rw_info = None
        self.fname = ""
        self.lineno = 0
        #
        #   // Variable: sequencer
        #   //
        #   // Sequencer executing the operation
        #   //
        #   uvm_sequencer_base sequencer;
        self.sequencer = None
