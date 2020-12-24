#//
#// -------------------------------------------------------------
#//    Copyright 2004-2009 Synopsys, Inc.
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
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

import cocotb
from uvm.base.uvm_object import UVMObject
from uvm.base.uvm_callback import UVMCallbackIter
from uvm.macros import (uvm_object_utils, uvm_fatal, uvm_do_obj_callbacks)
from uvm.reg.uvm_reg_model import UVM_NOT_OK
from uvm.base.uvm_globals import uvm_zero_delay
from .uvm_reg_cbs import UVMRegCbs

#//------------------------------------------------------------------------------
#// Class: UVMRegBackdoor
#//
#// Base class for user-defined back-door register and memory access.
#//
#// This class can be extended by users to provide user-specific back-door access
#// to registers and memories that are not implemented in pure SystemVerilog
#// or that are not accessible using the default DPI backdoor mechanism.
#//------------------------------------------------------------------------------


class UVMRegBackdoor(UVMObject):

    def __init__(self, name=""):
        """         
           Function: new
          
           Create an instance of self class
          
           Create an instance of the user-defined backdoor class
           for the specified register or memory
          
        Args:
            name: 
        """
        super().__init__(name)
        self.fname = ""
        self.lineno = 0

    async def do_pre_read(self, rw):
        """         

           Task: do_pre_read
          
           Execute the pre-read callbacks
          
           This method `must` be called as the first statement in
           a user extension of the <read()> method.
          
        Args:
            rw: 
        """
        await self.pre_read(rw)
        uvm_do_obj_callbacks(self, UVMRegCbs, 'pre_read', self, rw)

    async def do_post_read(self, rw):
        """         

           Task: do_post_read
          
           Execute the post-read callbacks
          
           This method `must` be called as the last statement in
           a user extension of the <read()> method.
          
        Args:
            rw: 
        """
        iter = UVMCallbackIter(self)
        # for(uvm_reg_cbs cb = iter.last(); cb is not None; cb=iter.prev())
        #     cb.decode(rw.value)
        cb = iter.first()
        while cb is not None:
            cb.decode(rw.value)
            cb = iter.next()
        uvm_do_obj_callbacks(self, UVMRegCbs,'post_read',self,rw)
        await self.post_read(rw)


    async def do_pre_write(self, rw):
        """         
           Task: do_pre_write
          
           Execute the pre-write callbacks
          
           This method `must` be called as the first statement in
           a user extension of the <write()> method.
          
        Args:
            rw: 
        """
        #uvm_callback_iter#(UVMRegBackdoor, uvm_reg_cbs) iter = new(self)
        iter = UVMCallbackIter(self)
        await self.pre_write(rw)
        uvm_do_obj_callbacks(self, UVMRegCbs,'pre_write',self,rw)
        #      for(uvm_reg_cbs cb = iter.first(); cb is not None; cb = iter.next())
        #         cb.encode(rw.value)
        cb = iter.first()
        while cb is not None:
            cb.decode(rw.value)
            cb = iter.next()


    async def do_post_write(self, rw):
        """         
           Task: do_post_write
          
           Execute the post-write callbacks
          
           This method `must` be called as the last statement in
           a user extension of the <write()> method.
        Args:
            rw: 
        """
        uvm_do_obj_callbacks(self, UVMRegCbs, 'post_write', self, rw)
        await self.post_write(rw)



    async def write(self, rw):  # task
        """         
           Task: write
          
           User-defined backdoor write operation.
          
           Call <do_pre_write()>.
           Deposit the specified value in the specified register HDL implementation.
           Call <do_post_write()>.
           Returns an indication of the success of the operation.
          
          extern def write(self,uvm_reg_item rw)
        Args:
            rw: 
        """
        uvm_fatal("RegModel", "UVMRegBackdoor::write() method has not been overloaded")


    async def read(self, rw):  # task:
        """         
           Task: read
          
           User-defined backdoor read operation.
          
           Overload self method only if the backdoor requires the use of task.
          
           Call <do_pre_read()>.
           Peek the current value of the specified HDL implementation.
           Call <do_post_read()>.
           Returns the current value and an indication of the success of
           the operation.
          
           By default, calls <read_func()>.
          
        Args:
            rw: 
        """
        await self.do_pre_read(rw)
        self.read_func(rw)
        await self.do_post_read(rw)


    def read_func(self, rw):
        """         
           Function: read_func
          
           User-defined backdoor read operation.
          
           Peek the current value in the HDL implementation.
           Returns the current value and an indication of the success of
           the operation.
          
          extern virtual def void read_func(self,uvm_reg_item rw):
        Args:
            rw: 
        """
        uvm_fatal("RegModel", "UVMRegBackdoor::read_func() method has not been overloaded")
        rw.status = UVM_NOT_OK
        #endfunction


    def is_auto_updated(self, field):
        """         
           Function: is_auto_updated
          
           Indicates if wait_for_change() method is implemented
          
           Implement to return TRUE if and only if
           <wait_for_change()> is implemented to watch for changes
           in the HDL implementation of the specified field
          
          extern virtual def bit is_auto_updated(self,uvm_reg_field field):
        Args:
            field: 
        Returns:
        """
        return False

    async def wait_for_change(self, element):  # task
        """         
           Task: wait_for_change
          
           Wait for a change in the value of the register or memory
           element in the DUT.
          
           When self method returns, the mirror value for the register
           corresponding to self instance of the backdoor class will be updated
           via a backdoor read operation.
          
        Args:
            element: 
        """
        uvm_fatal("RegModel", "UVMRegBackdoor::wait_for_change() method has not been overloaded")


    # tpoikela: Unsure if these are really needed anywhere?
    #   /*local*/ extern def void start_update_thread(self,uvm_object element):
    #   /*local*/ extern def void kill_update_thread(self,uvm_object element):
    #   /*local*/ extern def bit has_update_threads(self):


    async def pre_read(self, rw):
        """         
           Task: pre_read
          
           Called before user-defined backdoor register read.
          
           The registered callback methods are invoked after the invocation
           of self method.
          
        Args:
            rw: 
        """
        await uvm_zero_delay()


    async def post_read(self, rw):
        """         
           Task: post_read
          
           Called after user-defined backdoor register read.
          
           The registered callback methods are invoked before the invocation
           of self method.
        Args:
            rw: 
        """
        await uvm_zero_delay()


    async def pre_write(self, rw):
        """         
           Task: pre_write
          
           Called before user-defined backdoor register write.
          
           The registered callback methods are invoked after the invocation
           of self method.
          
           The written value, if modified, modifies the actual value that
           will be written.
        Args:
            rw: 
        """
        await uvm_zero_delay()


    async def post_write(self, rw):
        """         
           Task: post_write
          
           Called after user-defined backdoor register write.
          
           The registered callback methods are invoked before the invocation
           of self method.
        Args:
            rw: 
        """
        await uvm_zero_delay()


    #`ifdef UVM_USE_PROCESS_CONTAINER
    #   local process_container_c m_update_thread[uvm_object]
    #`else
    #   local process m_update_thread[uvm_object]
    #`endif


uvm_object_utils(UVMRegBackdoor)
#TODO   `uvm_register_cb(UVMRegBackdoor, uvm_reg_cbs)



#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#// start_update_thread
#
#def void UVMRegBackdoor::start_update_thread(self,uvm_object element):
#   uvm_reg rg
#   if (self.m_update_thread.exists(element)):
#      self.kill_update_thread(element)
#   end
#   if (!sv.cast(rg,element))
#     return; // only regs supported at self time
#
#   fork
#      begin
#         uvm_reg_field fields[$]
#
#`ifdef UVM_USE_PROCESS_CONTAINER
#         self.m_update_thread[element] = new(process::self())
#`else
#         self.m_update_thread[element] = process::self()
#`endif
#
#         rg.get_fields(fields)
#         while True:
#            uvm_status_e status
#            uvm_reg_data_t  val
#            uvm_reg_item r_item = new("bd_r_item")
#            r_item.element = rg
#            r_item.element_kind = UVM_REG
#            self.read(r_item)
#            val = r_item.value[0]
#            if (r_item.status != UVM_IS_OK):
#               `uvm_error("RegModel", sv.sformatf("Backdoor read of register '%s' failed.",
#                          rg.get_name()))
#            end
#            foreach (fields[i]):
#               if (self.is_auto_updated(fields[i])):
#                  r_item.value[0] = (val >> fields[i].get_lsb_pos()) &
#                                    ((1 << fields[i].get_n_bits())-1)
#                  fields[i].do_predict(r_item)
#                end
#            end
#            self.wait_for_change(element)
#         end
#      end
#   join_none
#endfunction
#
#
#// kill_update_thread
#
#def void UVMRegBackdoor::kill_update_thread(self,uvm_object element):
#   if (self.m_update_thread.exists(element)):
#
#`ifdef UVM_USE_PROCESS_CONTAINER
#      self.m_update_thread[element].p.kill()
#`else
#      self.m_update_thread[element].kill()
#`endif
#
#      self.m_update_thread.delete(element)
#   end
#endfunction
#
#
#// has_update_threads
#
#def bit UVMRegBackdoor::has_update_threads(self):
#   return self.m_update_thread.num() > 0
#endfunction
