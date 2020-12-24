#//
#// -------------------------------------------------------------
#//    Copyright 2004-2009 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
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

from ..base.uvm_callback import UVMCallback, UVMCallbackIter, UVMCallbacks
from ..base.uvm_globals import uvm_zero_delay
from ..macros import uvm_object_utils

#//------------------------------------------------------------------------------
#// Title: Register Callbacks
#//
#// This section defines the base class used for all register callback
#// extensions. It also includes pre-defined callback extensions for use on
#// read-only and write-only registers.
#//------------------------------------------------------------------------------

#//------------------------------------------------------------------------------
#// Class: uvm_reg_cbs
#//
#// Facade class for field, register, memory and backdoor
#// access callback methods.
#//------------------------------------------------------------------------------


class UVMRegCbs(UVMCallback):

    def __init__(self, name="uvm_reg_cbs"):
        UVMCallback.__init__(self, name)

    async def pre_write(self, rw):
        """
           Task: pre_write

           Called before a write operation.

           All registered `pre_write` callback methods are invoked after the
           invocation of the `pre_write` method of associated object (`uvm_reg`,
           `uvm_reg_field`, `uvm_mem`, or `uvm_reg_backdoor`). If the element being
           written is a `uvm_reg`, all `pre_write` callback methods are invoked
           before the contained `uvm_reg_fields`.

           Backdoor - <uvm_reg_backdoor::pre_write>,
                      <uvm_reg_cbs::pre_write> cbs for backdoor.

           Register - <uvm_reg::pre_write>,
                      <uvm_reg_cbs::pre_write> cbs for reg,
                      then foreach field:
                        <uvm_reg_field::pre_write>,
                        <uvm_reg_cbs::pre_write> cbs for field

           RegField - <uvm_reg_field::pre_write>,
                      <uvm_reg_cbs::pre_write> cbs for field

           Memory   - <uvm_mem::pre_write>,
                      <uvm_reg_cbs::pre_write> cbs for mem

           The `rw` argument holds information about the operation.

           - Modifying the `value` modifies the actual value written.

           - For memories, modifying the `offset` modifies the offset
             used in the operation.

           - For non-backdoor operations, modifying the access `path` or
             address `map` modifies the actual path or map used in the
             operation.

           If the ~rw.status~ is modified to anything other than `UVM_IS_OK`,
           the operation is aborted.

           See `uvm_reg_item` for details on `rw` information.

          virtual task pre_write(uvm_reg_item rw); endtask
        Args:
            rw:
        """
        await uvm_zero_delay()

    async def post_write(self, rw):
        """
           Task: post_write

           Called after a write operation.

           All registered `post_write` callback methods are invoked before the
           invocation of the `post_write` method of the associated object (`uvm_reg`,
           `uvm_reg_field`, `uvm_mem`, or `uvm_reg_backdoor`). If the element being
           written is a `uvm_reg`, all `post_write` callback methods are invoked
           before the contained `uvm_reg_fields`.

           Summary of callback order:

           Backdoor - <uvm_reg_cbs::post_write> cbs for backdoor,
                      <uvm_reg_backdoor::post_write>

           Register - <uvm_reg_cbs::post_write> cbs for reg,
                      <uvm_reg::post_write>,
                      then foreach field:
                        <uvm_reg_cbs::post_write> cbs for field,
                        <uvm_reg_field::post_read>

           RegField - <uvm_reg_cbs::post_write> cbs for field,
                      <uvm_reg_field::post_write>

           Memory   - <uvm_reg_cbs::post_write> cbs for mem,
                      <uvm_mem::post_write>

           The `rw` argument holds information about the operation.

           - Modifying the `status` member modifies the returned status.

           - Modifying the `value` or `offset` members has no effect, as
             the operation has already completed.

           See `uvm_reg_item` for details on `rw` information.

          virtual task post_write(uvm_reg_item rw); endtask
        Args:
            rw:
        """
        await uvm_zero_delay()

    async def pre_read(self, rw):
        """
           Task: pre_read

           Callback called before a read operation.

           All registered `pre_read` callback methods are invoked after the
           invocation of the `pre_read` method of associated object (`uvm_reg`,
           `uvm_reg_field`, `uvm_mem`, or `uvm_reg_backdoor`). If the element being
           read is a `uvm_reg`, all `pre_read` callback methods are invoked before
           the contained `uvm_reg_fields`.

           Backdoor - <uvm_reg_backdoor::pre_read>,
                      <uvm_reg_cbs::pre_read> cbs for backdoor

           Register - <uvm_reg::pre_read>,
                      <uvm_reg_cbs::pre_read> cbs for reg,
                      then foreach field:
                        <uvm_reg_field::pre_read>,
                        <uvm_reg_cbs::pre_read> cbs for field

           RegField - <uvm_reg_field::pre_read>,
                      <uvm_reg_cbs::pre_read> cbs for field

           Memory   - <uvm_mem::pre_read>,
                      <uvm_reg_cbs::pre_read> cbs for mem

           The `rw` argument holds information about the operation.

           - The `value` member of `rw` is not used has no effect if modified.

           - For memories, modifying the `offset` modifies the offset
             used in the operation.

           - For non-backdoor operations, modifying the access `path` or
             address `map` modifies the actual path or map used in the
             operation.

           If the ~rw.status~ is modified to anything other than `UVM_IS_OK`,
           the operation is aborted.

           See `uvm_reg_item` for details on `rw` information.

          virtual task pre_read(uvm_reg_item rw); endtask
        Args:
            rw:
        """
        await uvm_zero_delay()


    def post_read(self, rw):
        """
           Task: post_read

           Callback called after a read operation.

           All registered `post_read` callback methods are invoked before the
           invocation of the `post_read` method of the associated object (`uvm_reg`,
           `uvm_reg_field`, `uvm_mem`, or `uvm_reg_backdoor`). If the element being read
           is a `uvm_reg`, all `post_read` callback methods are invoked before the
           contained `uvm_reg_fields`.

           Backdoor - <uvm_reg_cbs::post_read> cbs for backdoor,
                      <uvm_reg_backdoor::post_read>

           Register - <uvm_reg_cbs::post_read> cbs for reg,
                      <uvm_reg::post_read>,
                      then foreach field:
                        <uvm_reg_cbs::post_read> cbs for field,
                        <uvm_reg_field::post_read>

           RegField - <uvm_reg_cbs::post_read> cbs for field,
                      <uvm_reg_field::post_read>

           Memory   - <uvm_reg_cbs::post_read> cbs for mem,
                      <uvm_mem::post_read>

           The `rw` argument holds information about the operation.

           - Modifying the readback `value` or `status` modifies the actual
             returned value and status.

           - Modifying the `value` or `offset` members has no effect, as
             the operation has already completed.

           See `uvm_reg_item` for details on `rw` information.

          virtual task post_read(uvm_reg_item rw); endtask
        Args:
            rw:
        """
        pass


    #   // Task: post_predict
    #   //
    #   // Called by the <uvm_reg_field::predict()> method
    #   // after a successful UVM_PREDICT_READ or UVM_PREDICT_WRITE prediction.
    #   //
    #   // ~previous~ is the previous value in the mirror and
    #   // ~value~ is the latest predicted value. Any change to ~value~ will
    #   // modify the predicted mirror value.
    #   //
    #   virtual function void post_predict(input uvm_reg_field  fld,
    #                                      input uvm_reg_data_t previous,
    #                                      inout uvm_reg_data_t value,
    #                                      input uvm_predict_e  kind,
    #                                      input uvm_path_e     path,
    #                                      input uvm_reg_map    map)
    #   endfunction


    def encode(self, data):
        """
           Function: encode

           Data encoder

           The registered callback methods are invoked in order of registration
           after all the `pre_write` methods have been called.
           The encoded data is passed through each invocation in sequence.
           This allows the `pre_write` methods to deal with clear-text data.

           By default, the data is not modified.

        Args:
            data:
        """
        pass


    def decode(self, data):
        """
           Function: decode

           Data decode

           The registered callback methods are invoked in ~reverse order~
           of registration before all the `post_read` methods are called.
           The decoded data is passed through each invocation in sequence.
           This allows the `post_read` methods to deal with clear-text data.

           The reversal of the invocation order is to allow the decoding
           of the data to be performed in the opposite order of the encoding
           with both operations specified in the same callback extension.

           By default, the data is not modified.

        Args:
            data:
        """
        pass


#//------------------
#// Section: Typedefs
#//------------------


#// Type: uvm_reg_cb
#//
#// Convenience callback type declaration for registers
#//
#// Use this declaration to register the register callbacks rather than
#// the more verbose parameterized class
#//
#typedef uvm_callbacks#(uvm_reg, uvm_reg_cbs) uvm_reg_cb
UVMRegCb = UVMCallbacks

#// Type: uvm_reg_cb_iter
#//
#// Convenience callback iterator type declaration for registers
#//
#// Use this declaration to iterate over registered register callbacks
#// rather than the more verbose parameterized class
#//
#typedef uvm_callback_iter#(uvm_reg, uvm_reg_cbs) uvm_reg_cb_iter
UVMRegCbIter = UVMCallbackIter



#// Type: uvm_reg_bd_cb
#//
#// Convenience callback type declaration for backdoor
#//
#// Use this declaration to register register backdoor callbacks rather than
#// the more verbose parameterized class
#//
#typedef uvm_callbacks#(uvm_reg_backdoor, uvm_reg_cbs) uvm_reg_bd_cb


#// Type: uvm_reg_bd_cb_iter
#// Convenience callback iterator type declaration for backdoor
#//
#// Use this declaration to iterate over registered register backdoor callbacks
#// rather than the more verbose parameterized class
#//
#typedef uvm_callback_iter#(uvm_reg_backdoor, uvm_reg_cbs) uvm_reg_bd_cb_iter


#// Type: uvm_mem_cb
#//
#// Convenience callback type declaration for memories
#//
#// Use this declaration to register memory callbacks rather than
#// the more verbose parameterized class
#//
#typedef uvm_callbacks#(uvm_mem, uvm_reg_cbs) uvm_mem_cb

#
#// Type: uvm_mem_cb_iter
#//
#// Convenience callback iterator type declaration for memories
#//
#// Use this declaration to iterate over registered memory callbacks
#// rather than the more verbose parameterized class
#//
#typedef uvm_callback_iter#(uvm_mem, uvm_reg_cbs) uvm_mem_cb_iter
UVMMemCbIter = UVMCallbackIter

#
#// Type: uvm_reg_field_cb
#//
#// Convenience callback type declaration for fields
#//
#// Use this declaration to register field callbacks rather than
#// the more verbose parameterized class
#//
#typedef uvm_callbacks#(uvm_reg_field, uvm_reg_cbs) uvm_reg_field_cb
UVMRegFieldCb = UVMCallbacks

#
#// Type: uvm_reg_field_cb_iter
#//
#// Convenience callback iterator type declaration for fields
#//
#// Use this declaration to iterate over registered field callbacks
#// rather than the more verbose parameterized class
#//
#typedef uvm_callback_iter#(uvm_reg_field, uvm_reg_cbs) uvm_reg_field_cb_iter
UVMRegFieldCbIter = UVMCallbackIter


#//-----------------------------
#// Group: Predefined Extensions
#//-----------------------------
#
#//------------------------------------------------------------------------------
#// Class: uvm_reg_read_only_cbs
#//
#// Pre-defined register callback method for read-only registers
#// that will issue an error if a write() operation is attempted.
#//
#//------------------------------------------------------------------------------
#

#class uvm_reg_read_only_cbs extends uvm_reg_cbs
class UVMRegReadOnlyCbs(UVMRegCbs):

    def __init__(self, name="uvm_reg_read_only_cbs"):
        UVMRegCbs.__init__(self, name)

    #
    #
    #   // Function: pre_write
    #   //
    #   // Produces an error message and sets status to <UVM_NOT_OK>.
    #   //
    #   virtual task pre_write(uvm_reg_item rw)
    #      string name = rw.element.get_full_name()
    #
    #      if (rw.status != UVM_IS_OK)
    #         return
    #
    #      if (rw.element_kind == UVM_FIELD) begin
    #         uvm_reg_field fld
    #         uvm_reg rg
    #         $cast(fld, rw.element)
    #         rg = fld.get_parent()
    #         name = rg.get_full_name()
    #      end
    #
    #      `uvm_error("UVM/REG/READONLY",
    #                 {name, " is read-only. Cannot call write() method."})
    #
    #      rw.status = UVM_NOT_OK
    #   endtask
    #

    m_me = None
    @classmethod
    def get(cls):
        if cls.m_me is None:
            cls.m_me = UVMRegReadOnlyCbs()
        return cls.m_me


    #   // Function: add
    #   //
    #   // Add this callback to the specified register and its contained fields.
    #   //
    @classmethod
    def add(cls, rg):
        flds = []  # uvm_reg_field [$]
        UVMRegCb.add(rg, cls.get())
        rg.get_fields(flds)
        for i in range(len(flds)):
            UVMRegFieldCb.add(flds[i], cls.get())


    #   // Function: remove
    #   //
    #   // Remove this callback from the specified register and its contained fields.
    #   //
    #   static function void remove(uvm_reg rg)
    #      uvm_reg_cb_iter cbs = new(rg)
    #      uvm_reg_field flds[$]
    #
    #      void'(cbs.first())
    #      while (cbs.get_cb() != get()) begin
    #         if (cbs.get_cb() == null)
    #            return
    #         void'(cbs.next())
    #      end
    #      uvm_reg_cb::delete(rg, get())
    #      rg.get_fields(flds)
    #      foreach (flds[i]) begin
    #         uvm_reg_field_cb::delete(flds[i], get())
    #      end
    #   endfunction
    #endclass
uvm_object_utils(UVMRegReadOnlyCbs)

#//------------------------------------------------------------------------------
#// Class: UVMRegWriteOnlyCbs
#//
#// Pre-defined register callback method for write-only registers
#// that will issue an error if a read() operation is attempted.
#//
#//------------------------------------------------------------------------------


class UVMRegWriteOnlyCbs(UVMRegCbs):

    def __init__(self, name="UVMRegWriteOnlyCbs"):
        super().__init__(name)


    #   // Function: pre_read
    #   //
    #   // Produces an error message and sets status to <UVM_NOT_OK>.
    #   //
    #   virtual task pre_read(uvm_reg_item rw)
    #      string name = rw.element.get_full_name()
    #
    #      if (rw.status != UVM_IS_OK)
    #         return
    #
    #      if (rw.element_kind == UVM_FIELD) begin
    #         uvm_reg_field fld
    #         uvm_reg rg
    #         $cast(fld, rw.element)
    #         rg = fld.get_parent()
    #         name = rg.get_full_name()
    #      end
    #
    #      `uvm_error("UVM/REG/WRTEONLY",
    #                 {name, " is write-only. Cannot call read() method."})
    #
    #      rw.status = UVM_NOT_OK
    #   endtask


    m_me = None

    @classmethod
    def get(cls):
        if cls.m_me is None:
            cls.m_me = UVMRegWriteOnlyCbs()
        return cls.m_me


    #   // Function: add
    #   //
    #   // Add this callback to the specified register and its contained fields.
    #   //
    @classmethod
    def add(cls, rg):
        flds = []  # uvm_reg_field [$]
        UVMRegCb.add(rg, cls.get())
        rg.get_fields(flds)
        for i in range(len(flds)):
            UVMRegFieldCb.add(flds[i], cls.get())


    #   // Function: remove
    #   //
    #   // Remove this callback from the specified register and its contained fields.
    #   //
    #   static function void remove(uvm_reg rg)
    #      uvm_reg_cb_iter cbs = new(rg)
    #      uvm_reg_field flds[$]
    #
    #      void'(cbs.first())
    #      while (cbs.get_cb() != get()) begin
    #         if (cbs.get_cb() == null)
    #            return
    #         void'(cbs.next())
    #      end
    #      uvm_reg_cb::delete(rg, get())
    #      rg.get_fields(flds)
    #      foreach (flds[i]) begin
    #         uvm_reg_field_cb::delete(flds[i], get())
    #      end
    #   endfunction
    #endclass

uvm_object_utils(UVMRegWriteOnlyCbs)
