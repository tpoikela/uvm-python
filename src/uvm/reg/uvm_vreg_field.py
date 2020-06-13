#//
#// -------------------------------------------------------------
#//    Copyright 2004-2009 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
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
"""
#//------------------------------------------------------------------------------
#// Title: Virtual Register Field Classes
#//
#// This section defines the virtual field and callback classes.
#//
#// A virtual field is set of contiguous bits in one or more memory locations.
#// The semantics and layout of virtual fields comes from
#// an agreement between the software and the hardware,
#// not any physical structures in the DUT.
#//
#//------------------------------------------------------------------------------
"""

#typedef class uvm_vreg_field_cbs

#import cocotb

from ..base import (UVMObject, sv)
from ..macros import (uvm_error, uvm_object_utils, UVM_REG_DATA_WIDTH)
from ..base.uvm_callback import *
#from .uvm_reg_model import (UVM_REG_DATA_WIDTH)


class UVMVRegField(UVMObject):
    """
     Class: UVMVRegField

     Virtual field abstraction class

     A virtual field represents a set of adjacent bits that are
     logically implemented in consecutive memory locations.
    """


    #   `uvm_register_cb(UVMVRegField, uvm_vreg_field_cbs)

    #   //
    #   // Function: new
    #   // Create a new virtual field instance
    #   //
    #   // This method should not be used directly.
    #   // The UVMVRegField::type_id::create() method should be used instead.
    #   //
    def __init__(self, name="UVMVRegField"):
        super().__init__(name)
        self.parent = None  # UVMVReg
        self.lsb = 0
        self.size = 0
        self.fname = 0
        self.lineno = 0
        self.read_in_progress = False
        self.write_in_progress = False


    #   //
    #   // Function: configure
    #   // Instance-specific configuration
    #   //
    #   // Specify the ~parent~ virtual register of this virtual field, its
    #   // ~size~ in bits, and the position of its least-significant bit
    #   // within the virtual register relative to the least-significant bit
    #   // of the virtual register.
    #   //
    #   extern function void configure(uvm_vreg parent,
    #                                  int unsigned size,
    #                                  int unsigned lsb_pos)
    def configure(self, parent, size: int, lsb_pos: int):
        self.parent = parent
        if size == 0:
            uvm_error("RegModel", sv.sformatf("Virtual field '%s' cannot have 0 bits", self.get_full_name()))
            size = 1

        if size > UVM_REG_DATA_WIDTH:
            uvm_error("RegModel", sv.sformatf("Virtual field '%s' cannot have more than %0d bits",
                self.get_full_name(),
                UVM_REG_DATA_WIDTH))
            size = UVM_REG_DATA_WIDTH

        self.size = size
        self.lsb = lsb_pos
        self.parent.add_field(self)


    #   //
    #   // Group: Introspection
    #   //

    #   //
    #   // Function: get_name
    #   // Get the simple name
    #   //
    #   // Return the simple object name of this virtual field
    #   //

    #   // Function: get_full_name
    #   // Get the hierarchical name
    #   //
    #   // Return the hierarchal name of this virtual field
    #   // The base of the hierarchical name is the root block.
    #   //
    #   extern def string        get_full_name(self):
    def get_full_name(self) -> str:
        return (self.parent.get_full_name() + "." + self.get_name())


    #   //
    #   // FUNCTION: get_parent
    #   // Get the parent virtual register
    #   //
    #   extern def get_parent(self):
    def get_parent(self):
        return self.parent

    #   extern def get_register(self):
    def get_register(self):
        return self.parent

    #   //
    #   // FUNCTION: get_lsb_pos_in_register
    #   // Return the position of the virtual field
    #   ///
    #   // Returns the index of the least significant bit of the virtual field
    #   // in the virtual register that instantiates it.
    #   // An offset of 0 indicates a field that is aligned with the
    #   // least-significant bit of the register.
    #   //
    #   extern def int unsigned get_lsb_pos_in_register(self):
    def get_lsb_pos_in_register(self):
        return self.lsb

    #   //
    #   // FUNCTION: get_n_bits
    #   // Returns the width, in bits, of the virtual field.
    #   //
    #   extern def int unsigned get_n_bits(self):
    def get_n_bits(self):
        return self.size

    #   //
    #   // FUNCTION: get_access
    #   // Returns the access policy of the virtual field register
    #   // when written and read via an address map.
    #   //
    #   // If the memory implementing the virtual field
    #   // is mapped in more than one address map,
    #   // an address ~map~ must be specified.
    #   // If access restrictions are present when accessing a memory
    #   // through the specified address map, the access mode returned
    #   // takes the access restrictions into account.
    #   // For example, a read-write memory accessed
    #   // through an address map with read-only restrictions would return "RO".
    #   //
    #   extern def get_access(self,uvm_reg_map map = None):


    #   //
    #   // Group: HDL Access
    #   //

    #   //
    #   // TASK: write
    #   // Write the specified value in a virtual field
    #   //
    #   // Write ~value~ in the DUT memory location(s) that implements
    #   // the virtual field that corresponds to this
    #   // abstraction class instance using the specified access
    #   // ~path~.
    #   //
    #   // If the memory implementing the virtual register array
    #   // containing this virtual field
    #   // is mapped in more than one address map,
    #   // an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   //
    #   // The operation is eventually mapped into
    #   // memory read-modify-write operations at the location
    #   // where the virtual register
    #   // specified by ~idx~ in the virtual register array is implemented.
    #   // If a backdoor is available for the memory implementing the
    #   // virtual field, it will be used for the memory-read operation.
    #   //
    #   extern def write(self,input  longint unsigned   idx,
    #                             output uvm_status_e  status,
    #                             input  uvm_reg_data_t     value,
    #                             input  uvm_path_e    path = UVM_DEFAULT_PATH,
    #                             input  uvm_reg_map        map = None,
    #                             input  uvm_sequence_base  parent = None,
    #                             input  uvm_object         extension = None,
    #                             input  string             fname = "",
    #                             input  int                lineno = 0)

    #   //
    #   // TASK: read
    #   // Read the current value from a virtual field
    #   //
    #   // Read from the DUT memory location(s) that implements
    #   // the virtual field that corresponds to this
    #   // abstraction class instance using the specified access
    #   // ~path~, and return the readback ~value~.
    #   //
    #   // If the memory implementing the virtual register array
    #   // containing this virtual field
    #   // is mapped in more than one address map,
    #   // an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   //
    #   // The operation is eventually mapped into
    #   // memory read operations at the location(s)
    #   // where the virtual register
    #   // specified by ~idx~ in the virtual register array is implemented.
    #   //
    #   extern def read(self,input  longint unsigned    idx,
    #                            output uvm_status_e   status,
    #                            output uvm_reg_data_t      value,
    #                            input  uvm_path_e     path = UVM_DEFAULT_PATH,
    #                            input  uvm_reg_map         map = None,
    #                            input  uvm_sequence_base   parent = None,
    #                            input  uvm_object          extension = None,
    #                            input  string              fname = "",
    #                            input  int                 lineno = 0)


    #   //
    #   // TASK: poke
    #   // Deposit the specified value in a virtual field
    #   //
    #   // Deposit ~value~ in the DUT memory location(s) that implements
    #   // the virtual field that corresponds to this
    #   // abstraction class instance using the specified access
    #   // ~path~.
    #   //
    #   // The operation is eventually mapped into
    #   // memory peek-modify-poke operations at the location
    #   // where the virtual register
    #   // specified by ~idx~ in the virtual register array is implemented.
    #   //
    #   extern def poke(self,input  longint unsigned    idx,
    #                            output uvm_status_e   status,
    #                            input  uvm_reg_data_t      value,
    #                            input  uvm_sequence_base   parent = None,
    #                            input  uvm_object          extension = None,
    #                            input  string              fname = "",
    #                            input  int                 lineno = 0)

    #   //
    #   // TASK: peek
    #   // Sample the current value from a virtual field
    #   //
    #   // Sample from the DUT memory location(s) that implements
    #   // the virtual field that corresponds to this
    #   // abstraction class instance using the specified access
    #   // ~path~, and return the readback ~value~.
    #   //
    #   // If the memory implementing the virtual register array
    #   // containing this virtual field
    #   // is mapped in more than one address map,
    #   // an address ~map~ must be
    #   // specified if a physical access is used (front-door access).
    #   //
    #   // The operation is eventually mapped into
    #   // memory peek operations at the location(s)
    #   // where the virtual register
    #   // specified by ~idx~ in the virtual register array is implemented.
    #   //
    #   extern def peek(self,input  longint unsigned    idx,
    #                            output uvm_status_e   status,
    #                            output uvm_reg_data_t      value,
    #                            input  uvm_sequence_base   parent = None,
    #                            input  uvm_object          extension = None,
    #                            input  string              fname = "",
    #                            input  int                 lineno = 0)

    #   //
    #   // Group: Callbacks
    #   //


    #   //
    #   // TASK: pre_write
    #   // Called before virtual field write.
    #   //
    #   // If the specified data value, access ~path~ or address ~map~ are modified,
    #   // the updated data value, access path or address map will be used
    #   // to perform the virtual register operation.
    #   //
    #   // The virtual field callback methods are invoked before the callback methods
    #   // on the containing virtual register.
    #   // The registered callback methods are invoked after the invocation
    #   // of this method.
    #   // The pre-write virtual register and field callbacks are executed
    #   // before the corresponding pre-write memory callbacks
    #   //
    #async def pre_write(self,longint unsigned     idx,
    #                          ref uvm_reg_data_t   wdat,
    #                          ref uvm_path_e  path,
    #                          ref uvm_reg_map   map)
    #   endtask: pre_write

    #   //
    #   // TASK: post_write
    #   // Called after virtual field write
    #   //
    #   // If the specified ~status~ is modified,
    #   // the updated status will be
    #   // returned by the virtual register operation.
    #   //
    #   // The virtual field callback methods are invoked after the callback methods
    #   // on the containing virtual register.
    #   // The registered callback methods are invoked before the invocation
    #   // of this method.
    #   // The post-write virtual register and field callbacks are executed
    #   // after the corresponding post-write memory callbacks
    #   //
    #async   def post_write(self,longint unsigned       idx,
    #                           uvm_reg_data_t         wdat,
    #                           uvm_path_e        path,
    #                           uvm_reg_map         map,
    #                           ref uvm_status_e  status)
    #   endtask: post_write

    #   //
    #   // TASK: pre_read
    #   // Called before virtual field read.
    #   //
    #   // If the specified access ~path~ or address ~map~ are modified,
    #   // the updated access path or address map will be used to perform
    #   // the virtual register operation.
    #   //
    #   // The virtual field callback methods are invoked after the callback methods
    #   // on the containing virtual register.
    #   // The registered callback methods are invoked after the invocation
    #   // of this method.
    #   // The pre-read virtual register and field callbacks are executed
    #   // before the corresponding pre-read memory callbacks
    #   //
    #async   def pre_read(self,longint unsigned      idx,
    #                         ref uvm_path_e   path,
    #                         ref uvm_reg_map    map)
    #   endtask: pre_read

    #   //
    #   // TASK: post_read
    #   // Called after virtual field read.
    #   //
    #   // If the specified readback data ~rdat~ or ~status~ is modified,
    #   // the updated readback data or status will be
    #   // returned by the virtual register operation.
    #   //
    #   // The virtual field callback methods are invoked after the callback methods
    #   // on the containing virtual register.
    #   // The registered callback methods are invoked before the invocation
    #   // of this method.
    #   // The post-read virtual register and field callbacks are executed
    #   // after the corresponding post-read memory callbacks
    #   //
    #async   def post_read(self,longint unsigned       idx,
    #                          ref uvm_reg_data_t     rdat,
    #                          uvm_path_e        path,
    #                          uvm_reg_map         map,
    #                          ref uvm_status_e  status)
    #   endtask: post_read


    #   extern def do_print(self,uvm_printer printer):
    #   extern virtual function string convert2string
    #   extern def clone(self):
    #   extern def do_copy(self,uvm_object rhs):
    #   extern virtual function bit do_compare (uvm_object  rhs,
    #                                          uvm_comparer comparer)
    #   extern def do_pack(self,uvm_packer packer):
    #   extern def do_unpack(self,uvm_packer packer):


uvm_object_utils(UVMVRegField)


#//------------------------------------------------------------------------------
#// Class: uvm_vreg_field_cbs
#//
#// Pre/post read/write callback facade class
#//
#//------------------------------------------------------------------------------

#class uvm_vreg_field_cbs(uvm_callback):
    #   string fname
    #   int    lineno
    #
    #   def __init__(self, name = "uvm_vreg_field_cbs")
    #      super().__init__(name)
    #   endfunction
    #
    #
    #   //
    #   // Task: pre_write
    #   // Callback called before a write operation.
    #   //
    #   // The registered callback methods are invoked before the invocation
    #   // of the virtual register pre-write callbacks and
    #   // after the invocation of the <UVMVRegField::pre_write()> method.
    #   //
    #   // The written value ~wdat~, access ~path~ and address ~map~,
    #   // if modified, modifies the actual value, access path or address map
    #   // used in the register operation.
    #   //
    #@cocotb.coroutine
    #   def pre_write(self,UVMVRegField       field,
    #                          longint unsigned     idx,
    #                          ref uvm_reg_data_t   wdat,
    #                          ref uvm_path_e  path,
    #                          ref uvm_reg_map   map)
    #   endtask: pre_write
    #
    #
    #   //
    #   // TASK: post_write
    #   // Called after a write operation
    #   //
    #   // The registered callback methods are invoked after the invocation
    #   // of the virtual register post-write callbacks and
    #   // before the invocation of the <UVMVRegField::post_write()> method.
    #   //
    #   // The ~status~ of the operation,
    #   // if modified, modifies the actual returned status.
    #   //
    #@cocotb.coroutine
    #   def post_write(self,UVMVRegField        field,
    #                           longint unsigned      idx,
    #                           uvm_reg_data_t        wdat,
    #                           uvm_path_e       path,
    #                           uvm_reg_map        map,
    #                           ref uvm_status_e status)
    #   endtask: post_write
    #
    #
    #   //
    #   // TASK: pre_read
    #   // Called before a virtual field read.
    #   //
    #   // The registered callback methods are invoked after the invocation
    #   // of the virtual register pre-read callbacks and
    #   // after the invocation of the <UVMVRegField::pre_read()> method.
    #   //
    #   // The access ~path~ and address ~map~,
    #   // if modified, modifies the actual access path or address map
    #   // used in the register operation.
    #   //
    #@cocotb.coroutine
    #   def pre_read(self,UVMVRegField        field,
    #                         longint unsigned      idx,
    #                         ref uvm_path_e   path,
    #                         ref uvm_reg_map    map)
    #   endtask: pre_read
    #
    #
    #   //
    #   // TASK: post_read
    #   // Called after a virtual field read.
    #   //
    #   // The registered callback methods are invoked after the invocation
    #   // of the virtual register post-read callbacks and
    #   // before the invocation of the <UVMVRegField::post_read()> method.
    #   //
    #   // The readback value ~rdat~ and the ~status~ of the operation,
    #   // if modified, modifies the actual returned readback value and status.
    #   //
    #@cocotb.coroutine
    #   def post_read(self,UVMVRegField         field,
    #                          longint unsigned       idx,
    #                          ref uvm_reg_data_t     rdat,
    #                          uvm_path_e        path,
    #                          uvm_reg_map         map,
    #                          ref uvm_status_e  status)
    #   endtask: post_read
    #endclass: uvm_vreg_field_cbs
#
#
#//
#// Type: uvm_vreg_field_cb
#// Convenience callback type declaration
#//
#// Use this declaration to register virtual field callbacks rather than
#// the more verbose parameterized class
#//
#typedef uvm_callbacks#(UVMVRegField, uvm_vreg_field_cbs) uvm_vreg_field_cb
#
#//
#// Type: uvm_vreg_field_cb_iter
#// Convenience callback iterator type declaration
#//
#// Use this declaration to iterate over registered virtual field callbacks
#// rather than the more verbose parameterized class
#//
#typedef uvm_callback_iter#(UVMVRegField, uvm_vreg_field_cbs) uvm_vreg_field_cb_iter
#
#
#
#def string UVMVRegField::get_access(self,uvm_reg_map map = None):
#   if (self.parent.get_memory() is None):
#      uvm_error("RegModel", sv.sformatf("Cannot call UVMVRegField::get_rights() on unimplemented virtual field \"%s\"",
#                                     self.get_full_name()))
#      return "RW"
#   end
#
#   return self.parent.get_access(map)
#endfunction: get_access
#
#
#@cocotb.coroutine
#task UVMVRegField::write(input  longint unsigned    idx,
#                           output uvm_status_e   status,
#                           input  uvm_reg_data_t      value,
#                           input  uvm_path_e     path = UVM_DEFAULT_PATH,
#                           input  uvm_reg_map      map = None,
#                           input  uvm_sequence_base   parent = None,
#                           input  uvm_object          extension = None,
#                           input  string              fname = "",
#                           input  int                 lineno = 0)
#   uvm_reg_data_t  tmp
#   uvm_reg_data_t  segval
#   uvm_reg_addr_t  segoff
#   uvm_status_e st
#
#   int flsb, fmsb, rmwbits
#   int segsiz, segn
#   uvm_mem    mem
#   uvm_path_e rm_path
#
#   uvm_vreg_field_cb_iter cbs = new(self)
#
#   self.fname = fname
#   self.lineno = lineno
#
#   write_in_progress = 1'b1
#   mem = self.parent.get_memory()
#   if (mem is None):
#      uvm_error("RegModel", sv.sformatf("Cannot call UVMVRegField::write() on unimplemented virtual register \"%s\"",
#                                     self.get_full_name()))
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (path == UVM_DEFAULT_PATH):
#      uvm_reg_block blk = self.parent.get_block()
#      path = blk.get_default_path()
#   end
#
#   status = UVM_IS_OK
#
#   self.parent.XatomicX(1)
#
#   if (value >> self.size):
#      uvm_warning("RegModel", sv.sformatf("Writing value 'h%h that is greater than field \"%s\" size (%0d bits)", value, self.get_full_name(), self.get_n_bits()))
#      value &= value & ((1<<self.size)-1)
#   end
#   tmp = 0
#
#   self.pre_write(idx, value, path, map)
#   for (uvm_vreg_field_cbs cb = cbs.first(); cb is not None
#        cb = cbs.next()):
#      cb.fname = self.fname
#      cb.lineno = self.lineno
#      cb.pre_write(self, idx, value, path, map)
#   end
#
#   segsiz = mem.get_n_bytes() * 8
#   flsb    = self.get_lsb_pos_in_register()
#   segoff  = self.parent.get_offset_in_memory(idx) + (flsb / segsiz)
#
#   // Favor backdoor read to frontdoor read for the RMW operation
#   rm_path = UVM_DEFAULT_PATH
#   if (mem.get_backdoor() is not None) rm_path = UVM_BACKDOOR
#
#   // Any bits on the LSB side we need to RMW?
#   rmwbits = flsb % segsiz
#
#   // Total number of memory segment in this field
#   segn = (rmwbits + self.get_n_bits() - 1) / segsiz + 1
#
#   if (rmwbits > 0):
#      uvm_reg_addr_t  segn
#
#      mem.read(st, segoff, tmp, rm_path, map, parent, , extension, fname, lineno)
#      if (st != UVM_IS_OK  and  st != UVM_HAS_X):
#         uvm_error("RegModel",
#                    sv.sformatf("Unable to read LSB bits in %s[%0d] to for RMW cycle on virtual field %s.",
#                              mem.get_full_name(), segoff, self.get_full_name()))
#         status = UVM_NOT_OK
#         self.parent.XatomicX(0)
#         return
#      end
#
#      value = (value << rmwbits) | (tmp & ((1<<rmwbits)-1))
#   end
#
#   // Any bits on the MSB side we need to RMW?
#   fmsb = rmwbits + self.get_n_bits() - 1
#   rmwbits = (fmsb+1) % segsiz
#   if (rmwbits > 0):
#      if (segn > 0):
#         mem.read(st, segoff + segn - 1, tmp, rm_path, map, parent,, extension, fname, lineno)
#         if (st != UVM_IS_OK  and  st != UVM_HAS_X):
#            uvm_error("RegModel",
#                       sv.sformatf("Unable to read MSB bits in %s[%0d] to for RMW cycle on virtual field %s.",
#                                 mem.get_full_name(), segoff+segn-1,
#                                 self.get_full_name()))
#            status = UVM_NOT_OK
#            self.parent.XatomicX(0)
#            return
#         end
#      end
#      value |= (tmp & ~((1<<rmwbits)-1)) << ((segn-1)*segsiz)
#   end
#
#   // Now write each of the segments
#   tmp = value
#   repeat (segn):
#      mem.write(st, segoff, tmp, path, map, parent,, extension, fname, lineno)
#      if (st != UVM_IS_OK  and  st != UVM_HAS_X) status = UVM_NOT_OK
#
#      segoff++
#      tmp = tmp >> segsiz
#   end
#
#   self.post_write(idx, value, path, map, status)
#   for (uvm_vreg_field_cbs cb = cbs.first(); cb is not None
#        cb = cbs.next()):
#      cb.fname = self.fname
#      cb.lineno = self.lineno
#      cb.post_write(self, idx, value, path, map, status)
#   end
#
#   self.parent.XatomicX(0)
#
#
#   uvm_info("RegModel", sv.sformatf("Wrote virtual field \"%s\"[%0d] via %s with: 'h%h",
#                              self.get_full_name(), idx,
#                              (path == UVM_FRONTDOOR) ? "frontdoor" : "backdoor",
#                              value),UVM_MEDIUM);
#
#   write_in_progress = 1'b0
#   self.fname = ""
#   self.lineno = 0
#endtask: write
#
#
#@cocotb.coroutine
#task UVMVRegField::read(input longint unsigned     idx,
#                          output uvm_status_e   status,
#                          output uvm_reg_data_t      value,
#                          input  uvm_path_e     path = UVM_DEFAULT_PATH,
#                          input  uvm_reg_map      map = None,
#                          input  uvm_sequence_base   parent = None,
#                          input  uvm_object          extension = None,
#                          input  string              fname = "",
#                          input  int                 lineno = 0)
#   uvm_reg_data_t  tmp
#   uvm_reg_data_t  segval
#   uvm_reg_addr_t  segoff
#   uvm_status_e st
#
#   int flsb, lsb
#   int segsiz, segn
#   uvm_mem    mem
#
#   uvm_vreg_field_cb_iter cbs = new(self)
#
#   self.fname = fname
#   self.lineno = lineno
#
#   read_in_progress = 1'b1
#   mem = self.parent.get_memory()
#   if (mem is None):
#      uvm_error("RegModel", sv.sformatf("Cannot call UVMVRegField::read() on unimplemented virtual register \"%s\"",
#                                     self.get_full_name()))
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (path == UVM_DEFAULT_PATH):
#      uvm_reg_block blk = self.parent.get_block()
#      path = blk.get_default_path()
#   end
#
#   status = UVM_IS_OK
#
#   self.parent.XatomicX(1)
#
#   value = 0
#
#   self.pre_read(idx, path, map)
#   for (uvm_vreg_field_cbs cb = cbs.first(); cb is not None
#        cb = cbs.next()):
#      cb.fname = self.fname
#      cb.lineno = self.lineno
#      cb.pre_read(self, idx, path, map)
#   end
#
#   segsiz = mem.get_n_bytes() * 8
#   flsb    = self.get_lsb_pos_in_register()
#   segoff  = self.parent.get_offset_in_memory(idx) + (flsb / segsiz)
#   lsb = flsb % segsiz
#
#   // Total number of memory segment in this field
#   segn = (lsb + self.get_n_bits() - 1) / segsiz + 1
#
#   // Read each of the segments, MSB first
#   segoff += segn - 1
#   repeat (segn):
#      value = value << segsiz
#
#      mem.read(st, segoff, tmp, path, map, parent, , extension, fname, lineno)
#      if (st != UVM_IS_OK  and  st != UVM_HAS_X) status = UVM_NOT_OK
#
#      segoff--
#      value |= tmp
#   end
#
#   // Any bits on the LSB side we need to get rid of?
#   value = value >> lsb
#
#   // Any bits on the MSB side we need to get rid of?
#   value &= (1<<self.get_n_bits()) - 1
#
#   self.post_read(idx, value, path, map, status)
#   for (uvm_vreg_field_cbs cb = cbs.first(); cb is not None
#        cb = cbs.next()):
#      cb.fname = self.fname
#      cb.lineno = self.lineno
#      cb.post_read(self, idx, value, path, map, status)
#   end
#
#   self.parent.XatomicX(0)
#
#   uvm_info("RegModel", sv.sformatf("Read virtual field \"%s\"[%0d] via %s: 'h%h",
#                              self.get_full_name(), idx,
#                              (path == UVM_FRONTDOOR) ? "frontdoor" : "backdoor",
#                              value),UVM_MEDIUM)
#
#
#   read_in_progress = 1'b0
#   self.fname = ""
#   self.lineno = 0
#endtask: read
#
#
#@cocotb.coroutine
#task UVMVRegField::poke(input  longint unsigned  idx,
#                          output uvm_status_e status,
#                          input  uvm_reg_data_t    value,
#                          input  uvm_sequence_base parent = None,
#                          input  uvm_object        extension = None,
#                          input  string            fname = "",
#                          input  int               lineno = 0)
#   uvm_reg_data_t  tmp
#   uvm_reg_data_t  segval
#   uvm_reg_addr_t  segoff
#   uvm_status_e st
#
#   int flsb, fmsb, rmwbits
#   int segsiz, segn
#   uvm_mem    mem
#   uvm_path_e rm_path
#   self.fname = fname
#   self.lineno = lineno
#
#   mem = self.parent.get_memory()
#   if (mem is None):
#      uvm_error("RegModel", sv.sformatf("Cannot call UVMVRegField::poke() on unimplemented virtual register \"%s\"",
#                                     self.get_full_name()))
#      status = UVM_NOT_OK
#      return
#   end
#
#   status = UVM_IS_OK
#
#   self.parent.XatomicX(1)
#
#   if (value >> self.size):
#      uvm_warning("RegModel", sv.sformatf("Writing value 'h%h that is greater than field \"%s\" size (%0d bits)", value, self.get_full_name(), self.get_n_bits()))
#      value &= value & ((1<<self.size)-1)
#   end
#   tmp = 0
#
#   segsiz = mem.get_n_bytes() * 8
#   flsb    = self.get_lsb_pos_in_register()
#   segoff  = self.parent.get_offset_in_memory(idx) + (flsb / segsiz)
#
#   // Any bits on the LSB side we need to RMW?
#   rmwbits = flsb % segsiz
#
#   // Total number of memory segment in this field
#   segn = (rmwbits + self.get_n_bits() - 1) / segsiz + 1
#
#   if (rmwbits > 0):
#      uvm_reg_addr_t  segn
#
#      mem.peek(st, segoff, tmp, "", parent, extension, fname, lineno)
#      if (st != UVM_IS_OK  and  st != UVM_HAS_X):
#         uvm_error("RegModel",
#                    sv.sformatf("Unable to read LSB bits in %s[%0d] to for RMW cycle on virtual field %s.",
#                              mem.get_full_name(), segoff, self.get_full_name()))
#         status = UVM_NOT_OK
#         self.parent.XatomicX(0)
#         return
#      end
#
#      value = (value << rmwbits) | (tmp & ((1<<rmwbits)-1))
#   end
#
#   // Any bits on the MSB side we need to RMW?
#   fmsb = rmwbits + self.get_n_bits() - 1
#   rmwbits = (fmsb+1) % segsiz
#   if (rmwbits > 0):
#      if (segn > 0):
#         mem.peek(st, segoff + segn - 1, tmp, "", parent, extension, fname, lineno)
#         if (st != UVM_IS_OK  and  st != UVM_HAS_X):
#            uvm_error("RegModel",
#                       sv.sformatf("Unable to read MSB bits in %s[%0d] to for RMW cycle on virtual field %s.",
#                                 mem.get_full_name(), segoff+segn-1,
#                                 self.get_full_name()))
#            status = UVM_NOT_OK
#            self.parent.XatomicX(0)
#            return
#         end
#      end
#      value |= (tmp & ~((1<<rmwbits)-1)) << ((segn-1)*segsiz)
#   end
#
#   // Now write each of the segments
#   tmp = value
#   repeat (segn):
#      mem.poke(st, segoff, tmp, "", parent, extension, fname, lineno)
#      if (st != UVM_IS_OK  and  st != UVM_HAS_X) status = UVM_NOT_OK
#
#      segoff++
#      tmp = tmp >> segsiz
#   end
#
#   self.parent.XatomicX(0)
#
#   uvm_info("RegModel", sv.sformatf("Wrote virtual field \"%s\"[%0d] with: 'h%h",
#                              self.get_full_name(), idx, value),UVM_MEDIUM)
#
#   self.fname = ""
#   self.lineno = 0
#endtask: poke
#
#
#@cocotb.coroutine
#task UVMVRegField::peek(input  longint unsigned  idx,
#                          output uvm_status_e status,
#                          output uvm_reg_data_t    value,
#                          input  uvm_sequence_base parent = None,
#                          input  uvm_object        extension = None,
#                          input  string            fname = "",
#                          input  int               lineno = 0)
#   uvm_reg_data_t  tmp
#   uvm_reg_data_t  segval
#   uvm_reg_addr_t  segoff
#   uvm_status_e st
#
#   int flsb, lsb
#   int segsiz, segn
#   uvm_mem    mem
#   self.fname = fname
#   self.lineno = lineno
#
#   mem = self.parent.get_memory()
#   if (mem is None):
#      uvm_error("RegModel", sv.sformatf("Cannot call UVMVRegField::peek() on unimplemented virtual register \"%s\"",
#                                     self.get_full_name()))
#      status = UVM_NOT_OK
#      return
#   end
#
#   status = UVM_IS_OK
#
#   self.parent.XatomicX(1)
#
#   value = 0
#
#   segsiz = mem.get_n_bytes() * 8
#   flsb    = self.get_lsb_pos_in_register()
#   segoff  = self.parent.get_offset_in_memory(idx) + (flsb / segsiz)
#   lsb = flsb % segsiz
#
#   // Total number of memory segment in this field
#   segn = (lsb + self.get_n_bits() - 1) / segsiz + 1
#
#   // Read each of the segments, MSB first
#   segoff += segn - 1
#   repeat (segn):
#      value = value << segsiz
#
#      mem.peek(st, segoff, tmp, "", parent, extension, fname, lineno)
#
#      if (st != UVM_IS_OK  and  st != UVM_HAS_X) status = UVM_NOT_OK
#
#      segoff--
#      value |= tmp
#   end
#
#   // Any bits on the LSB side we need to get rid of?
#   value = value >> lsb
#
#   // Any bits on the MSB side we need to get rid of?
#   value &= (1<<self.get_n_bits()) - 1
#
#   self.parent.XatomicX(0)
#
#   uvm_info("RegModel", sv.sformatf("Peeked virtual field \"%s\"[%0d]: 'h%h", self.get_full_name(), idx, value),UVM_MEDIUM)
#
#   self.fname = ""
#   self.lineno = 0
#endtask: peek
#
#
#def void UVMVRegField::do_print (self,uvm_printer printer):
#  super().do_print(printer)
#  printer.print_generic("initiator", parent.get_type_name(), -1, convert2string())
#endfunction
#
#def string UVMVRegField::convert2string(self):
#   string res_str
#   string t_str
#   bit with_debug_info = 1'b0
#   $sformat(convert2string, {"%s[%0d-%0d]"},
#            self.get_name(),
#            self.get_lsb_pos_in_register() + self.get_n_bits() - 1,
#            self.get_lsb_pos_in_register())
#   if (read_in_progress == 1'b1):
#      if (fname != ""  and  lineno != 0)
#         $sformat(res_str, "%s:%0d ",fname, lineno)
#      convert2string = {convert2string, "\n", res_str, "currently executing read method"};
#   end
#   if ( write_in_progress == 1'b1):
#      if (fname != ""  and  lineno != 0)
#         $sformat(res_str, "%s:%0d ",fname, lineno)
#      convert2string = {convert2string, "\n", res_str, "currently executing write method"};
#   end
#
#endfunction
#
#//TODO - add fatal messages
#
#def uvm_object UVMVRegField::clone(self):
#  return None
#endfunction
#
#def void UVMVRegField::do_copy   (self,uvm_object rhs):
#endfunction
#
#function bit UVMVRegField::do_compare (uvm_object  rhs,
#                                        uvm_comparer comparer)
#  return 0
#endfunction
#
#def void UVMVRegField::do_pack (self,uvm_packer packer):
#endfunction
#
#def void UVMVRegField::do_unpack (self,uvm_packer packer):
#endfunction
