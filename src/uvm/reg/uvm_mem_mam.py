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

import cocotb
from ..macros import uvm_error, uvm_info
from ..base import sv, UVM_MEDIUM

#//------------------------------------------------------------------------------
#//
#// Title: Memory Allocation Manager
#//
#// Manages the exclusive allocation of consecutive memory locations
#// called ~regions~.
#// The regions can subsequently be accessed like little memories of
#// their own, without knowing in which memory or offset they are
#// actually located.
#//
#// The memory allocation manager should be used by any
#// application-level process
#// that requires reserved space in the memory,
#// such as DMA buffers.
#//
#// A region will remain reserved until it is explicitly released.
#//
#//------------------------------------------------------------------------------


#//------------------------------------------------------------------------------
#// CLASS: UVMMemMam
#//------------------------------------------------------------------------------
#// Memory allocation manager
#//
#// Memory allocation management utility class similar to C's malloc()
#// and free().
#// A single instance of this class is used to manage a single,
#// contiguous address space.
#//------------------------------------------------------------------------------


class UVMMemMam:

    #   //----------------------
    #   // Group: Initialization
    #   //----------------------


    #   // Type: alloc_mode_e
    #   //
    #   // Memory allocation mode
    #   //
    #   // Specifies how to allocate a memory region
    #   //
    #   // GREEDY   - Consume new, previously unallocated memory
    #   // THRIFTY  - Reused previously released memory as much as possible (not yet implemented)
    #   //
    #   typedef enum {GREEDY, THRIFTY} alloc_mode_e
    GREEDY = 0
    THRIFTY = 1



    #   // Type: locality_e
    #   //
    #   // Location of memory regions
    #   //
    #   // Specifies where to locate new memory regions
    #   //
    #   // BROAD    - Locate new regions randomly throughout the address space
    #   // NEARBY   - Locate new regions adjacent to existing regions
    #
    #   typedef enum {BROAD, NEARBY}   locality_e
    BROAD = 0
    NEARBY = 1

    def __init__(self, name, cfg, mem=None):
        """         
           Function: new
          
           Create a new manager instance
          
           Create an instance of a memory allocation manager
           with the specified name and configuration.
           This instance manages all memory region allocation within
           the address range specified in the configuration descriptor.
          
           If a reference to a memory abstraction class is provided, the memory
           locations within the regions can be accessed through the region
           descriptor, using the <UVMMemRegion::read()> and
           <UVMMemRegion::write()> methods.
          
          extern def __init__(self, name,
                              UVMMemMamCfg cfg,
                              uvm_mem mem=None)
        Args:
            name: 
            cfg: 
            mem: 
        """
        self.cfg           = cfg
        self.memory        = mem
        self.in_use = []  # UVMMemRegion
        self.for_each_idx = -1  # type: int
        self.fname = ""  # type: str
        self.lineno = 0  # type: int
        #   // Variable: default_alloc
        #   //
        #   // Region allocation policy
        #   //
        #   // This object is repeatedly randomized when allocating new regions.
        self.default_alloc = UVMMemMamPolicy()
        #    self.len = None  # type: unsigned
        #    self.n_bytes = None  # type: unsigned
        #    self.parent = None  # type: UVMMemMam
        #    self.fname =   # type: string
        #    self.lineno = 0  # type: int
        #    self.XvregX = None  # type: uvm_vreg
        #    self.len = None  # type: unsigned
        #    self.start_offset = None  # type: bit
        #    self.min_offset = None  # type: bit
        #    self.max_offset = None  # type: bit
        #    self.in_use = None  # type: UVMMemRegion
        #    self.t = None  # type: min_offse
        #    self.n_bytes = None  # type: unsigned
        #    self.start_offset = None  # type: bit
        #    self.end_offset = None  # type: bit
        #    self.mode = None  # type: alloc_mode_e
        #    self.locality = None  # type: ity_e
        #    self.t = None  # type: start_offse
        #    self.4 = None  # type: 6
    #endfunction: new

    #   // Function: reconfigure
    #   //
    #   // Reconfigure the manager
    #   //
    #   // Modify the maximum and minimum addresses of the address space managed by
    #   // the allocation manager, allocation mode, or locality.
    #   // The number of bytes per memory location cannot be modified
    #   // once an allocation manager has been constructed.
    #   // All currently allocated regions must fall within the new address space.
    #   //
    #   // Returns the previous configuration.
    #   //
    #   // if no new configuration is specified, simply returns the current
    #   // configuration.
    #   //
    #   extern def UVMMemMamCfg reconfigure(self,UVMMemMamCfg cfg = None):

    #   //-------------------------
    #   // Group: Memory Management
    #   //-------------------------

    #   // Function: reserve_region
    #   //
    #   // Reserve a specific memory region
    #   //
    #   // Reserve a memory region of the specified number of bytes
    #   // starting at the specified offset.
    #   // A descriptor of the reserved region is returned.
    #   // If the specified region cannot be reserved, ~None~ is returned.
    #   //
    #   // It may not be possible to reserve a region because
    #   // it overlaps with an already-allocated region or
    #   // it lies outside the address range managed
    #   // by the memory manager.
    #   //
    #   // Regions can be reserved to create "holes" in the managed address space.
    #   //
    #   extern function UVMMemRegion reserve_region(bit [63:0]   start_offset,
    #                                                 int unsigned n_bytes,
    #                                                 string       fname = "",
    #                                                 int          lineno = 0)
    def reserve_region(self, start_offset, n_bytes, fname = "", lineno=0):
        end_offset = 0
        self.fname = fname
        self.lineno = lineno
        if n_bytes == 0:
            uvm_error("RegModel", "Cannot reserve 0 bytes")
            return None

        if start_offset < self.cfg.start_offset:
            uvm_error("RegModel", sv.sformatf(
                "Cannot reserve before start of memory space: 'h%h < 'h%h",
                start_offset, self.cfg.start_offset))
            return None

        end_offset = start_offset + int((n_bytes-1) / self.cfg.n_bytes)
        n_bytes = (end_offset - start_offset + 1) * self.cfg.n_bytes

        if end_offset > self.cfg.end_offset:
            uvm_error("RegModel", sv.sformatf("Cannot reserve past end of memory space: 'h%h > 'h%h",
                end_offset, self.cfg.end_offset))
            return None

        uvm_info("RegModel",sv.sformatf("Attempting to reserve ['h%h:'h%h]...",
            start_offset, end_offset),UVM_MEDIUM)

        for i in range(len(self.in_use)):
            if (start_offset <= self.in_use[i].get_end_offset()  and
                    end_offset >= self.in_use[i].get_start_offset()):
               # Overlap!
               uvm_error("RegModel", sv.sformatf(
                   "Cannot reserve ['h%h:'h%h] because it overlaps with %s",
                   start_offset, end_offset,
                   self.in_use[i].convert2string()))
               return None

        
            # Regions are stored in increasing start offset
            if start_offset > self.in_use[i].get_start_offset():
                reserve_region = UVMMemRegion(start_offset, end_offset,
                        end_offset - start_offset + 1, n_bytes, self)
                self.in_use.insert(i, reserve_region)
                return reserve_region
        
        reserve_region = UVMMemRegion(start_offset, end_offset,
                end_offset - start_offset + 1, n_bytes, self)
        self.in_use.append(reserve_region)
        return reserve_region
        #endfunction: reserve_region
    

    #   // Function: request_region
    #   //
    #   // Request and reserve a memory region
    #   //
    #   // Request and reserve a memory region of the specified number
    #   // of bytes starting at a random location.
    #   // If an policy is specified, it is randomized to determine
    #   // the start offset of the region.
    #   // If no policy is specified, the policy found in
    #   // the <UVMMemMam::default_alloc> class property is randomized.
    #   //
    #   // A descriptor of the allocated region is returned.
    #   // If no region can be allocated, ~None~ is returned.
    #   //
    #   // It may not be possible to allocate a region because
    #   // there is no area in the memory with enough consecutive locations
    #   // to meet the size requirements or
    #   // because there is another contradiction when randomizing
    #   // the policy.
    #   //
    #   // If the memory allocation is configured to ~THRIFTY~ or ~NEARBY~,
    #   // a suitable region is first sought procedurally.
    #   //
    #   extern function UVMMemRegion request_region(int unsigned   n_bytes,
    #                                                 UVMMemMamPolicy alloc = None,
    #                                                 string         fname = "",
    #                                                 int            lineno = 0)
    #
    #
    #   // Function: release_region
    #   //
    #   // Release the specified region
    #   //
    #   // Release a previously allocated memory region.
    #   // An error is issued if the
    #   // specified region has not been previously allocated or
    #   // is no longer allocated.
    #   //
    #   extern def void release_region(self,UVMMemRegion region):

    #
    #
    #   // Function: release_all_regions
    #   //
    #   // Forcibly release all allocated memory regions.
    #   //
    #   extern def void release_all_regions(self):

    #
    #
    #   //---------------------
    #   // Group: Introspection
    #   //---------------------
    #
    #   // Function: convert2string
    #   //
    #   // Image of the state of the manager
    #   //
    #   // Create a human-readable description of the state of
    #   // the memory manager and the currently allocated regions.
    #   //
    #   extern def string convert2string(self):

    #
    #
    #   // Function: for_each
    #   //
    #   // Iterate over all currently allocated regions
    #   //
    #   // If reset is ~TRUE~, reset the iterator
    #   // and return the first allocated region.
    #   // Returns ~None~ when there are no additional allocated
    #   // regions to iterate on.
    #   //
    #   extern def UVMMemRegion for_each(self,bit reset = 0):

    #
    #
    #   // Function: get_memory
    #   //
    #   // Get the managed memory implementation
    #   //
    #   // Return the reference to the memory abstraction class
    #   // for the memory implementing
    #   // the locations managed by self instance of the allocation manager.
    #   // Returns ~None~ if no
    #   // memory abstraction class was specified at construction time.
    #   //
    #   extern def uvm_mem get_memory(self):

    #endclass: UVMMemMam


#//------------------------------------------------------------------------------
#// CLASS: UVMMemRegion
#//------------------------------------------------------------------------------
#// Allocated memory region descriptor
#//
#// Each instance of this class describes an allocated memory region.
#// Instances of this class are created only by
#// the memory manager, and returned by the
#// <UVMMemMam::reserve_region()> and <UVMMemMam::request_region()>
#// methods.
#//------------------------------------------------------------------------------


class UVMMemRegion:
    #
    #   /*local*/ bit [63:0] Xstart_offsetX;  // Can't be local since function
    #   /*local*/ bit [63:0] Xend_offsetX;    // calls not supported in constraints
    #
    #   local int unsigned len
    #   local int unsigned n_bytes
    #   local UVMMemMam  parent
    #   local string       fname
    #   local int          lineno
    #
    #   /*local*/ uvm_vreg XvregX
    #

    def __init__(self, start_offset, end_offset, _len, n_bytes, parent):
        """         
          extern /*local*/ function new(bit [63:0]   start_offset,
                                        bit [63:0]   end_offset,
                                        int unsigned len,
                                        int unsigned n_bytes,
                                        UVMMemMam      parent)
        Args:
            start_offset: 
            end_offset: 
            _len: 
            n_bytes: 
            parent: 
        """
        self.Xstart_offsetX = start_offset
        self.Xend_offsetX   = end_offset
        self.len            = _len
        self.n_bytes        = n_bytes
        self.parent         = parent
        self.fname = ""
        self.lineno = 0
        self.XvregX         = None
        #endfunction: new

    #
    #   // Function: get_start_offset
    #   //
    #   // Get the start offset of the region
    #   //
    #   // Return the address offset, within the memory,
    #   // where self memory region starts.
    #   //
    #   extern def bit [63:0] get_start_offset(self):
    #
    #
    #   // Function: get_end_offset
    #   //
    #   // Get the end offset of the region
    #   //
    #   // Return the address offset, within the memory,
    #   // where self memory region ends.
    #   //
    #   extern def bit [63:0] get_end_offset(self):
    #
    #
    #   // Function: get_len
    #   //
    #   // Size of the memory region
    #   //
    #   // Return the number of consecutive memory locations
    #   // (not necessarily bytes) in the allocated region.
    #   //
    #   extern def int unsigned get_len(self):
    #
    #
    #   // Function: get_n_bytes
    #   //
    #   // Number of bytes in the region
    #   //
    #   // Return the number of consecutive bytes in the allocated region.
    #   // If the managed memory contains more than one byte per address,
    #   // the number of bytes in an allocated region may
    #   // be greater than the number of requested or reserved bytes.
    #   //
    #   extern def int unsigned get_n_bytes(self):
    #
    #
    #   // Function: release_region
    #   //
    #   // Release self region
    #   //
    #   extern def void release_region(self):
    #
    #
    #   // Function: get_memory
    #   //
    #   // Get the memory where the region resides
    #   //
    #   // Return a reference to the memory abstraction class
    #   // for the memory implementing self allocated memory region.
    #   // Returns ~None~ if no memory abstraction class was specified
    #   // for the allocation manager that allocated self region.
    #   //
    #   extern def uvm_mem get_memory(self):
    #
    #
    #   // Function: get_virtual_registers
    #   //
    #   // Get the virtual register array in self region
    #   //
    #   // Return a reference to the virtual register array abstraction class
    #   // implemented in self region.
    #   // Returns ~None~ if the memory region is
    #   // not known to implement virtual registers.
    #   //
    #   extern def uvm_vreg get_virtual_registers(self):
    #
    #
    #   // Task: write
    #   //
    #   // Write to a memory location in the region.
    #   //
    #   // Write to the memory location that corresponds to the
    #   // specified ~offset~ within self region.
    #   // Requires that the memory abstraction class be associated with
    #   // the memory allocation manager that allocated self region.
    #   //
    #   // See <uvm_mem::write()> for more details.
    #   //
    #   extern def write(self,output uvm_status_e       status,
    #                     input  uvm_reg_addr_t     offset,
    #                     input  uvm_reg_data_t     value,
    #                     input  uvm_path_e         path   = UVM_DEFAULT_PATH,
    #                     input  uvm_reg_map        map    = None,
    #                     input  uvm_sequence_base  parent = None,
    #                     input  int                prior = -1,
    #                     input  uvm_object         extension = None,
    #                     input  string             fname = "",
    #                     input  int                lineno = 0)
    #
    #
    #   // Task: read
    #   //
    #   // Read from a memory location in the region.
    #   //
    #   // Read from the memory location that corresponds to the
    #   // specified ~offset~ within self region.
    #   // Requires that the memory abstraction class be associated with
    #   // the memory allocation manager that allocated self region.
    #   //
    #   // See <uvm_mem::read()> for more details.
    #   //
    #   extern def read(self,output uvm_status_e       status,
    #                    input  uvm_reg_addr_t     offset,
    #                    output uvm_reg_data_t     value,
    #                    input  uvm_path_e         path   = UVM_DEFAULT_PATH,
    #                    input  uvm_reg_map        map    = None,
    #                    input  uvm_sequence_base  parent = None,
    #                    input  int                prior = -1,
    #                    input  uvm_object         extension = None,
    #                    input  string             fname = "",
    #                    input  int                lineno = 0)
    #
    #
    #   // Task: burst_write
    #   //
    #   // Write to a set of memory location in the region.
    #   //
    #   // Write to the memory locations that corresponds to the
    #   // specified ~burst~ within self region.
    #   // Requires that the memory abstraction class be associated with
    #   // the memory allocation manager that allocated self region.
    #   //
    #   // See <uvm_mem::burst_write()> for more details.
    #   //
    #   extern def burst_write(self,output uvm_status_e       status,
    #                           input  uvm_reg_addr_t     offset,
    #                           input  uvm_reg_data_t     value[],
    #                           input  uvm_path_e         path   = UVM_DEFAULT_PATH,
    #                           input  uvm_reg_map        map    = None,
    #                           input  uvm_sequence_base  parent = None,
    #                           input  int                prior  = -1,
    #                           input  uvm_object         extension = None,
    #                           input  string             fname  = "",
    #                           input  int                lineno = 0)
    #
    #
    #   // Task: burst_read
    #   //
    #   // Read from a set of memory location in the region.
    #   //
    #   // Read from the memory locations that corresponds to the
    #   // specified ~burst~ within self region.
    #   // Requires that the memory abstraction class be associated with
    #   // the memory allocation manager that allocated self region.
    #   //
    #   // See <uvm_mem::burst_read()> for more details.
    #   //
    #   extern def burst_read(self,output uvm_status_e       status,
    #                          input  uvm_reg_addr_t     offset,
    #                          output uvm_reg_data_t     value[],
    #                          input  uvm_path_e         path   = UVM_DEFAULT_PATH,
    #                          input  uvm_reg_map        map    = None,
    #                          input  uvm_sequence_base  parent = None,
    #                          input  int                prior  = -1,
    #                          input  uvm_object         extension = None,
    #                          input  string             fname  = "",
    #                          input  int                lineno = 0)
    #
    #
    #   // Task: poke
    #   //
    #   // Deposit in a memory location in the region.
    #   //
    #   // Deposit the specified value in the memory location
    #   // that corresponds to the
    #   // specified ~offset~ within self region.
    #   // Requires that the memory abstraction class be associated with
    #   // the memory allocation manager that allocated self region.
    #   //
    #   // See <uvm_mem::poke()> for more details.
    #   //
    #   extern def poke(self,output uvm_status_e       status,
    #                    input  uvm_reg_addr_t     offset,
    #                    input  uvm_reg_data_t     value,
    #                    input  uvm_sequence_base  parent = None,
    #                    input  uvm_object         extension = None,
    #                    input  string             fname = "",
    #                    input  int                lineno = 0)
    #
    #
    #   // Task: peek
    #   //
    #   // Sample a memory location in the region.
    #   //
    #   // Sample the memory location that corresponds to the
    #   // specified ~offset~ within self region.
    #   // Requires that the memory abstraction class be associated with
    #   // the memory allocation manager that allocated self region.
    #   //
    #   // See <uvm_mem::peek()> for more details.
    #   //
    #   extern def peek(self,output uvm_status_e       status,
    #                    input  uvm_reg_addr_t     offset,
    #                    output uvm_reg_data_t     value,
    #                    input  uvm_sequence_base  parent = None,
    #                    input  uvm_object         extension = None,
    #                    input  string             fname = "",
    #                    input  int                lineno = 0)
    #
    #
    #   extern def string convert2string(self):
    #
    #endclass



#//------------------------------------------------------------------------------
#// Class: UVMMemMamPolicy
#//------------------------------------------------------------------------------
#//
#// An instance of this class is randomized to determine
#// the starting offset of a randomly allocated memory region.
#// This class can be extended to provide additional constraints
#// on the starting offset, such as word alignment or
#// location of the region within a memory page.
#// If a procedural region allocation policy is required,
#// it can be implemented in the pre/post_randomize() method.
#//------------------------------------------------------------------------------

class UVMMemMamPolicy:
    #   // variable: len
    #   // Number of addresses required
    #   int unsigned len
    #
    #   // variable: start_offset
    #   // The starting offset of the region
    #   rand bit [63:0] start_offset
    #
    #   // variable: min_offset
    #   // Minimum address offset in the managed address space
    #   bit [63:0] min_offset
    #
    #   // variable: max_offset
    #   // Maximum address offset in the managed address space
    #   bit [63:0] max_offset
    #
    #   // variable: in_use
    #   // Regions already allocated in the managed address space
    #   UVMMemRegion in_use[$]
    #
    #   constraint uvm_mem_mam_policy_valid {
    #      start_offset >= min_offset
    #      start_offset <= max_offset - len + 1
    #   }
    #
    #   constraint uvm_mem_mam_policy_no_overlap {
    #      foreach (in_use[i]) {
    #         !(start_offset <= in_use[i].Xend_offsetX  and
    #           start_offset + len - 1 >= in_use[i].Xstart_offsetX)
    #      }
    #   }

    def __init__(self):
        """         
        Constructor
        """
        self.len = 0
        self.start_offset = 0
        self.min_offset = 0
        self.max_offset = 0
        self.in_use = []


#// CLASS: UVMMemMamCfg
#// Specifies the memory managed by an instance of a <UVMMemMam> memory
#// allocation manager class.
class UVMMemMamCfg:
    #   // variable: n_bytes
    #   // Number of bytes in each memory location
    #   rand int unsigned n_bytes
    #
    #// FIXME start_offset and end_offset should be "longint unsigned" to match the memory addr types
    #   // variable: start_offset
    #   // Lowest address of managed space
    #   rand bit [63:0] start_offset
    #
    #   // variable: end_offset
    #   // Last address of managed space
    #   rand bit [63:0] end_offset
    #
    #   // variable: mode
    #   // Region allocation mode
    #   rand UVMMemMam::alloc_mode_e mode
    #
    #   // variable: locality
    #   // Region location mode
    #   rand UVMMemMam::locality_e   locality
    #
    #   constraint uvm_mem_mam_cfg_valid {
    #      end_offset > start_offset
    #      n_bytes < 64
    #   }

    def __init__(self):
        """         
        Constructor
        """
        self.n_bytes = 0
        self.start_offset = 0
        self.end_offset = 0
        self.mode = 0
        self.locality = 0



#//------------------------------------------------------------------
#//  Implementation
#//------------------------------------------------------------------
#
#def bit [63:0] UVMMemRegion::get_start_offset(self):
#   return self.Xstart_offsetX
#endfunction: get_start_offset
#
#
#def bit [63:0] UVMMemRegion::get_end_offset(self):
#   return self.Xend_offsetX
#endfunction: get_end_offset
#
#
#def int unsigned UVMMemRegion::get_len(self):
#   return self.len
#endfunction: get_len
#
#
#def int unsigned UVMMemRegion::get_n_bytes(self):
#   return self.n_bytes
#endfunction: get_n_bytes
#
#
#def string UVMMemRegion::convert2string(self):
#   $sformat(convert2string, "['h%h:'h%h]",
#            self.Xstart_offsetX, self.Xend_offsetX)
#endfunction: convert2string
#
#
#def void UVMMemRegion::release_region(self):
#   self.parent.release_region(self)
#endfunction
#
#
#def uvm_mem UVMMemRegion::get_memory(self):
#   return self.parent.get_memory()
#endfunction: get_memory
#
#
#def uvm_vreg UVMMemRegion::get_virtual_registers(self):
#   return self.XvregX
#endfunction: get_virtual_registers
#
#
#
#
#def UVMMemMamCfg UVMMemMam::reconfigure(self,UVMMemMamCfg cfg = None):
#   uvm_root top
#   uvm_coreservice_t cs
#   if (cfg is None)
#     return self.cfg
#
#   cs = uvm_coreservice_t::get()
#   top = cs.get_root()
#
#   // Cannot reconfigure n_bytes
#   if (cfg.n_bytes != self.cfg.n_bytes):
#      top.uvm_report_error("UVMMemMam",
#                 sv.sformatf("Cannot reconfigure Memory Allocation Manager with a different number of bytes (%0d != %0d)",
#                           cfg.n_bytes, self.cfg.n_bytes), UVM_LOW)
#      return self.cfg
#   end
#
#   // All currently allocated regions must fall within the new space
#   foreach (self.in_use[i]):
#      if (self.in_use[i].get_start_offset() < cfg.start_offset  or
#          self.in_use[i].get_end_offset() > cfg.end_offset):
#         top.uvm_report_error("UVMMemMam",
#                    sv.sformatf("Cannot reconfigure Memory Allocation Manager with a currently allocated region outside of the managed address range ([%0d:%0d] outside of [%0d:%0d])",
#                              self.in_use[i].get_start_offset(),
#                              self.in_use[i].get_end_offset(),
#                              cfg.start_offset, cfg.end_offset), UVM_LOW)
#         return self.cfg
#      end
#   end
#
#   reconfigure = self.cfg
#   self.cfg = cfg
#endfunction: reconfigure
#
#
#
#
#function UVMMemRegion UVMMemMam::request_region(int unsigned      n_bytes,
#                                                UVMMemMamPolicy    alloc = None,
#                                                string            fname = "",
#                                                int               lineno = 0)
#   self.fname = fname
#   self.lineno = lineno
#   if (alloc is None) alloc = self.default_alloc
#
#   alloc.len        = (n_bytes-1) / self.cfg.n_bytes + 1
#   alloc.min_offset = self.cfg.start_offset
#   alloc.max_offset = self.cfg.end_offset
#   alloc.in_use     = self.in_use
#
#   if (!alloc.randomize()):
#      `uvm_error("RegModel", "Unable to randomize policy")
#      return None
#   end
#
#   return reserve_region(alloc.start_offset, n_bytes)
#endfunction: request_region
#
#
#def void UVMMemMam::release_region(self,UVMMemRegion region):
#
#   if (region is None) return
#
#   foreach (self.in_use[i]):
#      if (self.in_use[i] == region):
#         self.in_use.delete(i)
#         return
#      end
#   end
#   `uvm_error("RegModel", {"Attempting to release unallocated region\n",
#                      region.convert2string()})
#endfunction: release_region
#
#
#def void UVMMemMam::release_all_regions(self):
#  in_use.delete()
#endfunction: release_all_regions
#
#
#def string UVMMemMam::convert2string(self):
#   convert2string = "Allocated memory regions:\n"
#   foreach (self.in_use[i]):
#      $sformat(convert2string, "%s   %s\n", convert2string,
#               self.in_use[i].convert2string())
#   end
#endfunction: convert2string
#
#
#def UVMMemRegion UVMMemMam::for_each(self,bit reset = 0):
#   if (reset) self.for_each_idx = -1
#
#   self.for_each_idx++
#
#   if (self.for_each_idx >= self.in_use.size()):
#      return None
#   end
#
#   return self.in_use[self.for_each_idx]
#endfunction: for_each
#
#
#def uvm_mem UVMMemMam::get_memory(self):
#   return self.memory
#endfunction: get_memory
#
#
#@cocotb.coroutine
#task UVMMemRegion::write(output uvm_status_e       status,
#                           input  uvm_reg_addr_t     offset,
#                           input  uvm_reg_data_t     value,
#                           input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                           input  uvm_reg_map        map    = None,
#                           input  uvm_sequence_base  parent = None,
#                           input  int                prior = -1,
#                           input  uvm_object         extension = None,
#                           input  string             fname = "",
#                           input  int                lineno = 0)
#
#   uvm_mem mem = self.parent.get_memory()
#   self.fname = fname
#   self.lineno = lineno
#
#   if (mem is None):
#      `uvm_error("RegModel", "Cannot use UVMMemRegion::write() on a region that was allocated by a Memory Allocation Manager that was not associated with a uvm_mem instance")
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (offset > self.len):
#      `uvm_error("RegModel",
#                 sv.sformatf("Attempting to write to an offset outside of the allocated region (%0d > %0d)",
#                           offset, self.len))
#      status = UVM_NOT_OK
#      return
#   end
#
#   mem.write(status, offset + self.get_start_offset(), value,
#            path, map, parent, prior, extension)
#endtask: write
#
#
#@cocotb.coroutine
#task UVMMemRegion::read(output uvm_status_e       status,
#                          input  uvm_reg_addr_t     offset,
#                          output uvm_reg_data_t     value,
#                          input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                          input  uvm_reg_map        map    = None,
#                          input  uvm_sequence_base  parent = None,
#                          input  int                prior = -1,
#                          input  uvm_object         extension = None,
#                          input  string             fname = "",
#                          input  int                lineno = 0)
#   uvm_mem mem = self.parent.get_memory()
#   self.fname = fname
#   self.lineno = lineno
#
#   if (mem is None):
#      `uvm_error("RegModel", "Cannot use UVMMemRegion::read() on a region that was allocated by a Memory Allocation Manager that was not associated with a uvm_mem instance")
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (offset > self.len):
#      `uvm_error("RegModel",
#                 sv.sformatf("Attempting to read from an offset outside of the allocated region (%0d > %0d)",
#                           offset, self.len))
#      status = UVM_NOT_OK
#      return
#   end
#
#   mem.read(status, offset + self.get_start_offset(), value,
#            path, map, parent, prior, extension)
#endtask: read
#
#
#@cocotb.coroutine
#task UVMMemRegion::burst_write(output uvm_status_e       status,
#                                 input  uvm_reg_addr_t     offset,
#                                 input  uvm_reg_data_t     value[],
#                                 input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                                 input  uvm_reg_map        map    = None,
#                                 input  uvm_sequence_base  parent = None,
#                                 input  int                prior = -1,
#                                 input  uvm_object         extension = None,
#                                 input  string             fname = "",
#                                 input  int                lineno = 0)
#   uvm_mem mem = self.parent.get_memory()
#   self.fname = fname
#   self.lineno = lineno
#
#   if (mem is None):
#      `uvm_error("RegModel", "Cannot use UVMMemRegion::burst_write() on a region that was allocated by a Memory Allocation Manager that was not associated with a uvm_mem instance")
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (offset + value.size() > self.len):
#      `uvm_error("RegModel",
#                 sv.sformatf("Attempting to burst-write to an offset outside of the allocated region (burst to [%0d:%0d] > mem_size %0d)",
#                           offset,offset+value.size(),self.len))
#      status = UVM_NOT_OK
#      return
#   end
#
#   mem.burst_write(status, offset + get_start_offset(), value,
#                   path, map, parent, prior, extension)
#
#endtask: burst_write
#
#
#@cocotb.coroutine
#task UVMMemRegion::burst_read(output uvm_status_e       status,
#                                input  uvm_reg_addr_t     offset,
#                                output uvm_reg_data_t     value[],
#                                input  uvm_path_e         path = UVM_DEFAULT_PATH,
#                                input  uvm_reg_map        map    = None,
#                                input  uvm_sequence_base  parent = None,
#                                input  int                prior = -1,
#                                input  uvm_object         extension = None,
#                                input  string             fname = "",
#                                input  int                lineno = 0)
#   uvm_mem mem = self.parent.get_memory()
#   self.fname = fname
#   self.lineno = lineno
#
#   if (mem is None):
#      `uvm_error("RegModel", "Cannot use UVMMemRegion::burst_read() on a region that was allocated by a Memory Allocation Manager that was not associated with a uvm_mem instance")
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (offset + value.size() > self.len):
#      `uvm_error("RegModel",
#                 sv.sformatf("Attempting to burst-read to an offset outside of the allocated region (burst to [%0d:%0d] > mem_size %0d)",
#                           offset,offset+value.size(),self.len))
#      status = UVM_NOT_OK
#      return
#   end
#
#   mem.burst_read(status, offset + get_start_offset(), value,
#                  path, map, parent, prior, extension)
#
#endtask: burst_read
#
#
#@cocotb.coroutine
#task UVMMemRegion::poke(output uvm_status_e       status,
#                          input  uvm_reg_addr_t     offset,
#                          input  uvm_reg_data_t     value,
#                          input  uvm_sequence_base  parent = None,
#                          input  uvm_object         extension = None,
#                          input  string             fname = "",
#                          input  int                lineno = 0)
#   uvm_mem mem = self.parent.get_memory()
#   self.fname = fname
#   self.lineno = lineno
#
#   if (mem is None):
#      `uvm_error("RegModel", "Cannot use UVMMemRegion::poke() on a region that was allocated by a Memory Allocation Manager that was not associated with a uvm_mem instance")
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (offset > self.len):
#      `uvm_error("RegModel",
#                 sv.sformatf("Attempting to poke to an offset outside of the allocated region (%0d > %0d)",
#                           offset, self.len))
#      status = UVM_NOT_OK
#      return
#   end
#
#   mem.poke(status, offset + self.get_start_offset(), value, "", parent, extension)
#endtask: poke
#
#
#@cocotb.coroutine
#task UVMMemRegion::peek(output uvm_status_e       status,
#                          input  uvm_reg_addr_t     offset,
#                          output uvm_reg_data_t     value,
#                          input  uvm_sequence_base  parent = None,
#                          input  uvm_object         extension = None,
#                          input  string             fname = "",
#                          input  int                lineno = 0)
#   uvm_mem mem = self.parent.get_memory()
#   self.fname = fname
#   self.lineno = lineno
#
#   if (mem is None):
#      `uvm_error("RegModel", "Cannot use UVMMemRegion::peek() on a region that was allocated by a Memory Allocation Manager that was not associated with a uvm_mem instance")
#      status = UVM_NOT_OK
#      return
#   end
#
#   if (offset > self.len):
#      `uvm_error("RegModel",
#                 sv.sformatf("Attempting to peek from an offset outside of the allocated region (%0d > %0d)",
#                           offset, self.len))
#      status = UVM_NOT_OK
#      return
#   end
#
#   mem.peek(status, offset + self.get_start_offset(), value, "", parent, extension)
#endtask: peek


