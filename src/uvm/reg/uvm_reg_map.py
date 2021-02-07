# -------------------------------------------------------------
#    Copyright 2004-2011 Synopsys, Inc.
#    Copyright 2010-2011 Mentor Graphics Corporation
#    Copyright 2010-2011 Cadence Design Systems, Inc.
#    Copyright 2019 Tuomas Poikela
#    All Rights Reserved Worldwide
#
#    Licensed under the Apache License, Version 2.0 (the
#    "License"); you may not use this file except in
#    compliance with the License.  You may obtain a copy of
#    the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in
#    writing, software distributed under the License is
#    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#    CONDITIONS OF ANY KIND, either express or implied.  See
#    the License for the specific language governing
#    permissions and limitations under the License.
#    TODO add modifications
# -------------------------------------------------------------

from ..base.sv import sv
from ..base.uvm_debug import uvm_debug
from ..base.uvm_object import UVMObject
from ..base.uvm_globals import UVM_LOW, UVM_MEDIUM
from ..macros.uvm_message_defines import (uvm_fatal, uvm_error, uvm_warning,
    uvm_info)
from ..macros.uvm_object_defines import uvm_object_utils
from .uvm_reg_model import (UVMRegMapAddrRange, UVM_BIG_ENDIAN, UVM_BIG_FIFO, UVM_FIELD, UVM_HIER,
                            UVM_LITTLE_ENDIAN, UVM_LITTLE_FIFO, UVM_MEM, UVM_NOT_OK, UVM_NO_HIER,
                            UVM_REG)
from .uvm_reg_item import UVMRegBusOp
from ..seq import UVMSequenceBase
from .uvm_reg_cbs import UVMRegReadOnlyCbs, UVMRegWriteOnlyCbs

UVM_VERB_MEM_MAP = UVM_LOW


class UVMRegMapInfo:
    def __init__(self):
        self.offset = 0
        self.rights = ""
        self.unmapped = False
        self.addr = []  # uvm_reg_addr_t[]
        self.frontdoor = None  # uvm_reg_frontdoor
        self.mem_range = UVMRegMapAddrRange()

        # if set marks the UVMRegMapInfo as initialized,
        # prevents using an uninitialized map (for instance if the model
        # has not been locked accidently and the maps have not been computed before)
        self.is_initialized = False

    def convert2string(self):
        res = ("offset: " + str(self.offset) + ', rights: ' + self.rights
            + ', unmapped: ' + str(self.unmapped) + ', addr: ' + str(self.addr)
            + ', range: ' + self.mem_range.convert2string())
        return res


class UVMRegTransactionOrderPolicy(UVMObject):
    def __init__(self, name='policy'):
        UVMObject.__init__(self, name)

    def order(self, q):
        """
        the order() function may reorder the sequence of bus transactions
        produced by a single uvm_reg transaction (read/write).
        This can be used in scenarios when the register width differs from
        the bus width and one register access results in a series of bus transactions.
        the first item (0) of the queue will be the first bus transaction (the last($)
        will be the final transaction

        Args:
            q:
        Raises:
        """
        raise Exception("UVMRegTransactionOrderPolicy::order pure virtual function")


#------------------------------------------------------------------------------
#
# Class: uvm_reg_map
#
# :Address map abstraction class
#
# This class represents an address map.
# An address map is a collection of registers and memories
# accessible via a specific physical interface.
# Address maps can be composed into higher-level address maps.
#
# Address maps are created using the <uvm_reg_block::create_map()>
# method.
#------------------------------------------------------------------------------


class UVMRegMap(UVMObject):


    def Xinit_address_mapX(self):
        bus_width = 0
        top_map = self.get_root_map()

        if self == top_map:
            top_map.m_regs_by_offset = {}
            top_map.m_regs_by_offset_wo = {}
            top_map.m_mems_by_offset = {}

        # TODO this piece of code
        for l in self.m_submaps:
            _map = l
            _map.Xinit_address_mapX()

        for rg_ in self.m_regs_info:
            rg = rg_  # uvm_reg
            self.m_regs_info[rg].is_initialized = True
            if not self.m_regs_info[rg].unmapped:
                rg_acc = rg.Xget_fields_accessX(self)
                addrs = []
                rg_offset = self.m_regs_info[rg].offset
                bus_width = self.get_physical_addresses(rg_offset, 0, rg.get_n_bytes(), addrs)

                for i in range(len(addrs)):
                    addr = addrs[i]

                    if addr in top_map.m_regs_by_offset:
                        rg2 = top_map.m_regs_by_offset[addr]
                        rg2_acc = rg2.Xget_fields_accessX(self)

                        # If the register at the same address is RO or WO
                        # and this register is WO or RO, this is OK
                        if (rg_acc == "RO" and rg2_acc == "WO"):
                            top_map.m_regs_by_offset[addr]    = rg
                            UVMRegReadOnlyCbs.add(rg)
                            top_map.m_regs_by_offset_wo[addr] = rg2
                            UVMRegWriteOnlyCbs.add(rg2)
                        elif (rg_acc == "WO" and rg2_acc == "RO"):
                            top_map.m_regs_by_offset_wo[addr] = rg
                            UVMRegWriteOnlyCbs.add(rg)
                            UVMRegReadOnlyCbs.add(rg2)
                        else:
                            a = ""
                            a = sv.sformatf("%0h",addr)
                            uvm_warning("RegModel", ("In map '" +
                                self.get_full_name() + "' register '" + rg.get_full_name()
                                + "' maps to same address as register '"
                                + top_map.m_regs_by_offset[addr].get_full_name()
                                + "': 'h" + a))
                    else:
                        top_map.m_regs_by_offset[addr] = rg

                    #foreach (top_map.m_mems_by_offset[range]):
                    for rr in top_map.m_mems_by_offset:
                        if (addr >= rr.min and addr <= rr.max):
                            a = sv.sformatf("%0h",addr)
                            b = sv.sformatf("[%0h:%0h]", rr.min, rr.max)
                            uvm_warning("RegModel", ("In map '",
                                    self.get_full_name() + "' register '" +
                                rg.get_full_name() + "' with address " + a +
                                "maps to same address as memory '" +
                                top_map.m_mems_by_offset[rr].get_full_name()
                                + "': " + b))
                self.m_regs_info[rg].addr = addrs

        # TODO complete this
        for mem_ in self.m_mems_info:
            mem = mem_
            if not self.m_mems_info[mem].unmapped:
                addrs = []
                addrs_max = []
                min1 = 0
                max1 = 0
                min2 = 0
                max2 = 0  # uvm_reg_addr_t
                stride = 0

                mem_offset = self.m_mems_info[mem].offset

                bus_width = self.get_physical_addresses(mem_offset,0,mem.get_n_bytes(),addrs)
                if addrs[0] < addrs[len(addrs)-1]:
                    min1 = addrs[0]
                else:
                    min1 = addrs[len(addrs)-1]
                min2 = addrs[0]

                mem_offset = self.m_mems_info[mem].offset
                self.get_physical_addresses(mem_offset, mem.get_size()-1, mem.get_n_bytes(), addrs_max)
                if addrs_max[0] > addrs_max[len(addrs_max)-1]:
                    max1 = addrs_max[0]
                else:
                    max1 = addrs_max[len(addrs_max)-1]
                max2 = addrs_max[0]
                # address interval between consecutive mem offsets
                stride = int((max2 - min2)/(mem.get_size() - 1))

                for reg_addr in top_map.m_regs_by_offset:
                    if (reg_addr >= min1 and reg_addr <= max1):
                        a = ""
                        a = sv.sformatf("%0h",reg_addr)
                        reg_name = top_map.m_regs_by_offset[reg_addr].get_full_name()
                        uvm_warning("RegModel", ("In map '" + self.get_full_name()
                            + "' memory '" + mem.get_full_name() + "' maps to same address as register '"
                            + reg_name + "': 'h" + a))

                for rr in top_map.m_mems_by_offset:
                    if (min1 <= rr.max and max1 >= rr.max or
                            min1 <= rr.min and max1 >= rr.min or
                            min1 >= rr.min and max1 <= rr.max):
                        a = sv.sformatf("[%0h:%0h]",min,max)
                        uvm_warning("RegModel", ("In map '" + self.get_full_name()
                            + "' memory '" + mem.get_full_name() + "' overlaps with address range of memory '"
                            + top_map.m_mems_by_offset[rr].get_full_name()
                            + "': 'h" + a))

                addr_range = UVMRegMapAddrRange(min1, max1, stride)
                top_map.m_mems_by_offset[addr_range] = mem
                self.m_mems_info[mem].addr  = addrs
                self.m_mems_info[mem].mem_range = addr_range

        # If the block has no registers or memories,
        # bus_width won't be set
        if bus_width == 0:
            bus_width = self.m_n_bytes
        self.m_system_n_bytes = bus_width
        #endfunction

    # static local uvm_reg_map   m_backdoor;
    m_backdoor = None  # uvm_reg_map

    @classmethod
    def backdoor(cls):
        """
           Function: backdoor
           Return the backdoor pseudo-map singleton

           This pseudo-map is used to specify or configure the backdoor
           instead of a real address map.

        Returns:
        """
        if UVMRegMap.m_backdoor is None:
            UVMRegMap.m_backdoor = UVMRegMap("Backdoor")
        return UVMRegMap.m_backdoor

    #   //----------------------
    #   // Group: Initialization
    #   //----------------------

    def __init__(self, name="uvm_reg_map"):
        """
           Function: new

           Create a new instance

        Args:
            name:
        """
        n = "default_map"
        if name != "":
            n = name
        UVMObject.__init__(self, n)
        self.m_auto_predict = 0
        self.m_check_on_read = True
        # info that is valid only if top-level map
        self.m_base_addr = 0  # uvm_reg_addr_t
        self.m_n_bytes = 0  # int
        self.m_endian = 0  # uvm_endianness_e
        self.m_byte_addressing = False
        self.m_sequence_wrapper = None  # uvm_object_wrapper
        self.m_adapter = None  # uvm_reg_adapter
        self.m_sequencer = None  # uvm_sequencer_base
        self.m_parent = None  # uvm_reg_block
        self.m_system_n_bytes = 0
        #
        self.m_parent_map = None  # uvm_reg_map
        self.m_parent_maps = {}  # uvm_reg_addr_t[uvm_reg_map] // value=offset of this map at parent level
        self.m_submaps = {}  # uvm_reg_addr_t[uvm_reg_map] value=offset of submap at this level
        self.m_submap_rights = {}  # string[uvm_reg_map] # value=rights of submap at this level

        self.m_regs_info = {}  # UVMRegMapInfo[uvm_reg]
        self.m_mems_info = {}  # UVMRegMapInfo[uvm_mem]
        self.m_regs_by_offset = {}  # uvm_reg[uvm_reg_addr_t]
        # Use only in addition to above if a RO and a WO
        # register share the same address.
        self.m_regs_by_offset_wo = {}  # uvm_reg[uvm_reg_addr_t]
        self.m_mems_by_offset = {}  # uvm_mem[UVMRegMapAddrRange]
        self.policy = None  # local uvm_reg_transaction_order_policy

    def configure(self, parent, base_addr, n_bytes, endian, byte_addressing=1):
        """
           Function: configure

           Instance-specific configuration

           Configures this map with the following properties.

           parent    - the block in which this map is created and applied

           base_addr - the base address for this map. All registers, memories,
                       and sub-blocks will be at offsets to this address

           n_bytes   - the byte-width of the bus on which this map is used

           endian    - the endian format. See `uvm_endianness_e` for possible
                       values

           byte_addressing - specifies whether the address increment is on a
                       per-byte basis. For example, consecutive memory locations
                       with `n_bytes`=4 (32-bit bus) are 4 apart: 0, 4, 8, and
                       so on. Default is TRUE.

        Args:
            parent:
            base_addr:
            n_bytes:
            endian:
            byte_addressing:
        """
        self.m_parent     = parent
        self.m_n_bytes    = n_bytes
        self.m_endian     = endian
        self.m_base_addr  = base_addr
        self.m_byte_addressing = byte_addressing

    def add_reg(self, rg, offset, rights="RW", unmapped=0, frontdoor=None):
        """
           Function: add_reg

           Add a register

           Add the specified register instance `rg` to this address map.

           The register is located at the specified address `offset` from
           this maps configured base address.

           The `rights` specify the register's accessibility via this map.
           Valid values are "RW", "RO", and "WO". Whether a register field
           can be read or written depends on both the field's configured access
           policy (see <uvm_reg_field::configure> and the register's rights in
           the map being used to access the field.

           The number of consecutive physical addresses occupied by the register
           depends on the width of the register and the number of bytes in the
           physical interface corresponding to this address map.

           If `unmapped` is TRUE, the register does not occupy any
           physical addresses and the base address is ignored.
           Unmapped registers require a user-defined `frontdoor` to be specified.

           A register may be added to multiple address maps
           if it is accessible from multiple physical interfaces.
           A register may only be added to an address map whose parent block
           is the same as the register's parent block.

        Args:
            rg:
            offset:
            rights:
            unmapped:
            frontdoor:
        """
        if rg in self.m_regs_info:
            uvm_error("RegModel", ("Register '" + rg.get_name()
                      + "' has already been added to map '" + self.get_name() + "'"))
            return

        if rg.get_parent() != self.get_parent():
            uvm_error("RegModel", ("Register '" + rg.get_full_name()
                + "' may not be added to address map '"
                + self.get_full_name() + "' : they are not in the same block"))
            return

        rg.add_map(self)
        info = UVMRegMapInfo()
        info.offset   = offset
        info.rights   = rights
        info.unmapped = unmapped
        info.frontdoor = frontdoor
        self.m_regs_info[rg] = info
    #endfunction


    def add_mem(self, mem, offset, rights="RW", unmapped=0, frontdoor=None):
        """
           Function: add_mem

           Add a memory

           Add the specified memory instance to this address map.
           The memory is located at the specified base address and has the
           specified access rights ("RW", "RO" or "WO").
           The number of consecutive physical addresses occupied by the memory
           depends on the width and size of the memory and the number of bytes in the
           physical interface corresponding to this address map.

           If `unmapped` is TRUE, the memory does not occupy any
           physical addresses and the base address is ignored.
           Unmapped memories require a user-defined `frontdoor` to be specified.

           A memory may be added to multiple address maps
           if it is accessible from multiple physical interfaces.
           A memory may only be added to an address map whose parent block
           is the same as the memory's parent block.

          extern virtual function void add_mem (uvm_mem        mem,
                                                uvm_reg_addr_t offset,
                                                string         rights = "RW",
                                                bit            unmapped=0,
                                                uvm_reg_frontdoor frontdoor=None)
        Args:
            mem:
            offset:
            rights:
            unmapped:
            frontdoor:
        """
        if mem in self.m_mems_info:
            uvm_error("RegModel", "Memory '" + mem.get_name() +
                      "' has already been added to map '" + self.get_name() + "'")
            return

        if mem.get_parent() != self.get_parent():
            uvm_error("RegModel", "Memory '" + mem.get_full_name() + "' may not be added to address map '"
                + self.get_full_name() + "' : they are not in the same block")
            return

        mem.add_map(self)

        info = UVMRegMapInfo()
        info.offset   = offset
        info.rights   = rights
        info.unmapped = unmapped
        info.frontdoor = frontdoor
        self.m_mems_info[mem] = info
        #endfunction: add_mem

    def add_submap(self, child_map, offset):
        """
           Function: add_submap

           Add an address map

           Add the specified address map instance to this address map.
           The address map is located at the specified base address.
           The number of consecutive physical addresses occupied by the submap
           depends on the number of bytes in the physical interface
           that corresponds to the submap,
           the number of addresses used in the submap and
           the number of bytes in the
           physical interface corresponding to this address map.

           An address map may be added to multiple address maps
           if it is accessible from multiple physical interfaces.
           An address map may only be added to an address map
           in the grand-parent block of the address submap.

          extern virtual function void add_submap (uvm_reg_map    child_map,
                                                   uvm_reg_addr_t offset)
        Args:
            child_map:
            offset:
        """
        parent_map = None  # #   uvm_reg_map

        if child_map is None:
            uvm_error("RegModel", "Attempting to add None map to map '" +
                    self.get_full_name() + "'")
            return

        parent_map = child_map.get_parent_map()

        # Cannot have more than one parent (currently)
        if parent_map is not None:
            uvm_error("RegModel", ("Map '" + child_map.get_full_name() +
                      "' is already a child of map '" +
                      parent_map.get_full_name() +
                      "'. Cannot also be a child of map '" +
                      self.get_full_name() + "'"))
            return

        # begin : parent_block_check
        child_blk = child_map.get_parent()
        if child_blk is None:
            uvm_error("RegModel", "Cannot add submap '" +child_map.get_full_name()
                  + "' because it does not have a parent block")
            return

        while ((child_blk is not None) and (child_blk.get_parent() != self.get_parent())):
            child_blk = child_blk.get_parent()

        if child_blk is None:
            uvm_error("RegModel", ("Submap '" + child_map.get_full_name()
                + "' may not be added to this address map, '"
                + self.get_full_name(),"', as the submap's parent block, '"
                + child_blk.get_full_name()
                + "', is neither this map's parent block nor a descendent of this map's parent block, '"
                + self.m_parent.get_full_name() + "'"))
            return


        if self.m_n_bytes > child_map.get_n_bytes(UVM_NO_HIER):
            uvm_warning("RegModel",
               sv.sformatf("Adding %0d-byte submap '%s' to %0d-byte parent map '%s'",
                         child_map.get_n_bytes(UVM_NO_HIER), child_map.get_full_name(),
                         self.m_n_bytes, self.get_full_name()))


        child_map.add_parent_map(self, offset)
        self.set_submap_offset(child_map, offset)
        #endfunction: add_submap


    def set_sequencer(self, sequencer, adapter=None):
        """
           Function: set_sequencer

           Set the sequencer and adapter associated with this map. This method
           `must` be called before starting any sequences based on uvm_reg_sequence.

          extern virtual function void set_sequencer (uvm_sequencer_base sequencer,
                                                      uvm_reg_adapter    adapter=None)
        Args:
            sequencer:
            adapter:
        """
        if sequencer is None:
            uvm_error("REG_None_SQR", "None reference specified for bus sequencer")
            return

        if adapter is None:
            uvm_info("REG_NO_ADAPT", ("Adapter not specified for map '" +
                self.get_full_name() +
                "'. Accesses via this map will send abstract 'uvm_reg_item' items to sequencer '"
                + sequencer.get_full_name() + "'"), UVM_MEDIUM)

        self.m_sequencer = sequencer
        self.m_adapter = adapter
        #endfunction

    def set_submap_offset(self, submap, offset):
        """

           Function: set_submap_offset

           Set the offset of the given `submap` to `offset`.

          extern virtual function void set_submap_offset (uvm_reg_map submap,
                                                          uvm_reg_addr_t offset)
        Args:
            submap:
            offset:
        """
        if (submap is None):
            uvm_error("REG/None","set_submap_offset: submap handle is None")
            return

        self.m_submaps[submap] = offset
        if self.m_parent.is_locked():
            root_map = self.get_root_map()
            root_map.Xinit_address_mapX()


    def get_submap_offset(self, submap):
        """
           Function: get_submap_offset

           Return the offset of the given `submap`.

          extern virtual function uvm_reg_addr_t get_submap_offset (uvm_reg_map submap)
        Args:
            submap:
        Returns:
        """
        if submap is None:
            uvm_error("REG/None","set_submap_offset: submap handle is None")
            return -1

        if submap not in self.m_submaps:
            uvm_error("RegModel", "Map '" + submap.get_full_name()
                  + "' is not a submap of '" + self.get_full_name() + "'")
            return -1
        return self.m_submaps[submap]


    #   // Function: set_base_addr
    #   //
    #   // Set the base address of this map.
    #   extern virtual function void   set_base_addr (uvm_reg_addr_t  offset)


    def reset(self, kind="SOFT"):
        """
           Function: reset

           Reset the mirror for all registers in this address map.

           Sets the mirror value of all registers in this address map
           and all of its submaps
           to the reset value corresponding to the specified reset event.
           See <uvm_reg_field::reset()> for more details.
           Does not actually set the value of the registers in the design,
           only the values mirrored in their corresponding mirror.

           Note that, unlike the other reset() method, the default
           reset event for this method is "SOFT".

          extern virtual function void reset(string kind = "SOFT")
        Args:
            kind:
        """
        regs = []
        self.get_registers(regs)
        for reg in regs:
            reg.reset(kind)


    def add_parent_map(self, parent_map, offset):
        """
          /*local*/ extern virtual function void add_parent_map(uvm_reg_map  parent_map,
                                                                uvm_reg_addr_t offset)
        Args:
            parent_map:
            offset:
        """
        if (parent_map is None):
            uvm_error("RegModel",
               "Attempting to add None parent map to map '" +
               self.get_full_name() + "'")
            return

        if self.m_parent_map is not None:
            uvm_error("RegModel",
               sv.sformatf("Map \"%s\" already a submap of map \"%s\" at offset 'h%h",
                         self.get_full_name(), self.m_parent_map.get_full_name(),
                         self.m_parent_map.get_submap_offset(self)))
            return


        self.m_parent_map = parent_map
        self.m_parent_maps[parent_map] = offset  # prep for multiple parents
        parent_map.m_submaps[self] = offset
        #
        #endfunction: add_parent_map

    #   /*local*/ extern virtual function void Xverify_map_configX()


    def m_set_reg_offset(self, rg, offset, unmapped):
        """
        m_set_reg_offset
        Args:
            rg:
            offset:
            unmapped:
        """
        if not rg in self.m_regs_info:
            uvm_error("RegModel",
              ("Cannot modify offset of register '" + rg.get_full_name()
              + "' in address map '" + self.get_full_name()
              + "' : register not mapped in that address map"))
            return

        info    = self.m_regs_info[rg]
        blk     = self.get_parent()
        top_map = self.get_root_map()
        addrs = []

        if blk is None:
            uvm_fatal("RegModel", "Addr map requires parent reg_block")

        # if block is not locked, Xinit_address_mapX will resolve map when block is locked
        if blk.is_locked():

            # remove any existing cached addresses
            if info.unmapped is False:
                for addr in info.addr:
                    if addr not in top_map.m_regs_by_offset_wo:
                        del top_map.m_regs_by_offset[addr]
                    else:
                        if top_map.m_regs_by_offset[addr] == rg:
                            top_map.m_regs_by_offset[addr] = top_map.m_regs_by_offset_wo[addr]
                            #TODO UVMRegReadOnlyCbs.remove(rg)
                            #TODO UVMRegWriteOnlyCbs.remove(top_map.m_regs_by_offset[info.addr[i]])
                        else:
                            pass
                            #TODO UVMRegWriteOnlyCbs.remove(rg)
                            #TODO UVMRegReadOnlyCbs.remove(top_map.m_regs_by_offset[info.addr[i]])
                        del top_map.m_regs_by_offset_wo[addr]

            # if we are remapping...
            if not unmapped:
                rg_acc = rg.Xget_fields_accessX(self)
                # get new addresses
                self.get_physical_addresses(offset,0,rg.get_n_bytes(),addrs)

                # make sure they do not conflict with others
                for adr in addrs:
                    addr = adr

                    if addr in top_map.m_regs_by_offset:
                        rg2 = top_map.m_regs_by_offset[addr]
                        rg2_acc = rg2.Xget_fields_accessX(self)

                        # If the register at the same address is RO or WO
                        # and this register is WO or RO, this is OK
                        if (rg_acc == "RO" and rg2_acc == "WO"):
                           top_map.m_regs_by_offset[addr]    = rg
                           # TODO UVMRegReadOnlyCbs.add(rg)
                           top_map.m_regs_by_offset_wo[addr] = rg2
                           # TODO UVMRegWriteOnlyCbs.add(rg2)
                        elif (rg_acc == "WO" and rg2_acc == "RO"):
                           top_map.m_regs_by_offset_wo[addr] = rg
                           # TODO UVMRegWriteOnlyCbs.add(rg)
                           # TODO UVMRegReadOnlyCbs.add(rg2)
                        else:
                            a = "{}".format(addr)
                            uvm_warning("RegModel", ("In map '" + self.get_full_name()
                                + "' register '"+ rg.get_full_name()
                                + "' maps to same address as register '"
                                + top_map.m_regs_by_offset[addr].get_full_name()
                                + "': 'h" + a))
                    else:
                        top_map.m_regs_by_offset[addr] = rg

                    for range in top_map.m_mems_by_offset.keys():
                        if adr >= range.min and adr <= range.max:
                            a = "{}".format(adr)
                            uvm_warning("RegModel", ("In map '" + self.get_full_name()
                                + "' register '" +
                                rg.get_full_name() + "' overlaps with address range of memory '"
                                + top_map.m_mems_by_offset[range].get_full_name()
                                + "': 'h" +a))

                info.addr = addrs # cache it

        if unmapped is True:
            info.offset   = -1
            info.unmapped = 1
        else:
          info.offset   = offset
          info.unmapped = 0
    #endfunction

    #   /*local*/ extern virtual function void m_set_mem_offset(uvm_mem mem,
    #                                                           uvm_reg_addr_t offset,
    #                                                           bit unmapped)
    #


    #   //---------------------
    #   // Group: Introspection
    #   //---------------------
    #
    #   // Function: get_name
    #   //
    #   // Get the simple name
    #   //
    #   // Return the simple object name of this address map.
    #   //

    def get_full_name(self):
        """
           Function: get_full_name

           Get the hierarchical name

           Return the hierarchal name of this address map.
           The base of the hierarchical name is the root block.

          extern virtual function string get_full_name()
        Returns:
        """
        get_full_name = self.get_name()
        if self.m_parent is None:
            return get_full_name
        return self.m_parent.get_full_name() + "." + get_full_name

    def get_root_map(self):
        """
        Get the externally-visible address map

        Get the top-most address map where this address map is instantiated.
        It corresponds to the externally-visible address map that can
        be accessed by the verification environment.

        Returns:
            UVMRegMap: Root map for this address map.
        """
        if self.m_parent_map is None:
            return self
        else:
            return self.m_parent_map.get_root_map()

    def get_parent(self):
        """
           Function: get_parent

           Get the parent block

           Return the block that is the parent of this address map.

        Returns:
        """
        return self.m_parent

    def get_parent_map(self):
        """
           Function: get_parent_map
           Get the higher-level address map

           Return the address map in which this address map is mapped.
           returns `None` if this is a top-level address map.

          extern virtual function uvm_reg_map           get_parent_map()
        Returns:
        """
        return self.m_parent_map


    def get_base_addr(self, hier=UVM_HIER):
        """
           Function: get_base_addr

           Get the base offset address for this map. If this map is the
           root map, the base address is that set with the `base_addr` argument
           to <uvm_reg_block::create_map()>. If this map is a submap of a higher-level map,
           the base address is offset given this submap by the parent map.
           See `set_submap_offset`.

          extern virtual function uvm_reg_addr_t get_base_addr (uvm_hier_e hier=UVM_HIER)
        Args:
            hier:
            UVM_HIER:
        Returns:
        """
        # child = self
        if (hier == UVM_NO_HIER or self.m_parent_map is None):
            return self.m_base_addr
        get_base_addr = self.m_parent_map.get_submap_offset(self)
        get_base_addr += self.m_parent_map.get_base_addr(UVM_HIER)
        return get_base_addr


    def get_n_bytes(self, hier=UVM_HIER):
        """
           Function: get_n_bytes

           Get the width in bytes of the bus associated with this map. If `hier`
           is `UVM_HIER`, then gets the effective bus width relative to the system
           level. The effective bus width is the narrowest bus width from this
           map to the top-level root map. Each bus access will be limited to this
           bus width.

          extern virtual function int unsigned get_n_bytes (uvm_hier_e hier=UVM_HIER)
        Args:
            hier:
            UVM_HIER:
        Returns:
        """
        if hier == UVM_NO_HIER:
            return self.m_n_bytes
        return self.m_system_n_bytes


    def get_addr_unit_bytes(self):
        """
           Function: get_addr_unit_bytes

           Get the number of bytes in the smallest addressable unit in the map.
           Returns 1 if the address map was configured using byte-level addressing.
           Returns <get_n_bytes()> otherwise.

          extern virtual function int unsigned get_addr_unit_bytes()
        Returns:
        """
        if (self.m_byte_addressing):
            return 1
        else:
            return self.m_n_bytes


    def get_endian(self, hier=UVM_HIER):
        """
           Function: get_base_addr

           Gets the endianness of the bus associated with this map. If `hier` is
           set to `UVM_HIER`, gets the system-level endianness.

          extern virtual function uvm_endianness_e get_endian (uvm_hier_e hier=UVM_HIER)
        Args:
            hier:
            UVM_HIER:
        Returns:
        """
        if (hier == UVM_NO_HIER or self.m_parent_map is None):
            return self.m_endian
        return self.m_parent_map.get_endian(hier)


    def get_sequencer(self, hier=UVM_HIER):
        """
           Function: get_sequencer

           Gets the sequencer for the bus associated with this map. If `hier` is
           set to `UVM_HIER`, gets the sequencer for the bus at the system-level.
           See `set_sequencer`.

          extern virtual function uvm_sequencer_base get_sequencer (uvm_hier_e hier=UVM_HIER)
        Args:
            hier:
            UVM_HIER:
        Returns:
        """
        if (hier == UVM_NO_HIER or self.m_parent_map is None):
            return self.m_sequencer
        return self.m_parent_map.get_sequencer(hier)

    def get_adapter(self, hier=UVM_HIER):
        """
           Function: get_adapter

           Gets the bus adapter for the bus associated with this map. If `hier` is
           set to `UVM_HIER`, gets the adapter for the bus used at the system-level.
           See `set_sequencer`.

          extern virtual function uvm_reg_adapter get_adapter (uvm_hier_e hier=UVM_HIER)
        Args:
            hier:
            UVM_HIER:
        Returns:
        """
        if (hier == UVM_NO_HIER or self.m_parent_map is None):
            return self.m_adapter
        return self.m_parent_map.get_adapter(hier)
        #endfunction

    def get_submaps(self, maps, hier=UVM_HIER):
        """
           Function: get_submaps

           Get the address sub-maps

           Get the address maps instantiated in this address map.
           If `hier` is `UVM_HIER`, recursively includes the address maps,
           in the sub-maps.

          extern virtual function void  get_submaps (ref uvm_reg_map maps[$],
                                                     input uvm_hier_e hier=UVM_HIER)
        Args:
            maps:
            hier:
            UVM_HIER:
        """
        for submap in self.m_submaps:
            maps.append(submap)

        if (hier == UVM_HIER):
            for sm in self.m_submaps:
                submap = sm
                submap.get_submaps(maps)
        #endfunction

    def get_registers(self, regs, hier=UVM_HIER):
        """
           Function: get_registers

           Get the registers

           Get the registers instantiated in this address map.
           If `hier` is `UVM_HIER`, recursively includes the registers
           in the sub-maps.

          extern virtual function void  get_registers (ref uvm_reg regs[$],
                                                       input uvm_hier_e hier=UVM_HIER)
        Args:
            regs:
            hier:
            UVM_HIER:
        """
        for rg in self.m_regs_info:
            regs.append(rg)

        if hier == UVM_HIER:
            for sm in self.m_submaps:
                submap = sm
                submap.get_registers(regs)
        #endfunction

    #
    #   // Function: get_fields
    #   //
    #   // Get the fields
    #   //
    #   // Get the fields in the registers instantiated in this address map.
    #   // If ~hier~ is ~UVM_HIER~, recursively includes the fields of the registers
    #   // in the sub-maps.
    #   //
    #   extern virtual function void  get_fields (ref uvm_reg_field fields[$],
    #                                             input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_memories
    #   //
    #   // Get the memories
    #   //
    #   // Get the memories instantiated in this address map.
    #   // If ~hier~ is ~UVM_HIER~, recursively includes the memories
    #   // in the sub-maps.
    #   //
    #   extern virtual function void  get_memories (ref uvm_mem mems[$],
    #                                               input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_virtual_registers
    #   //
    #   // Get the virtual registers
    #   //
    #   // Get the virtual registers instantiated in this address map.
    #   // If ~hier~ is ~UVM_HIER~, recursively includes the virtual registers
    #   // in the sub-maps.
    #   //
    #   extern virtual function void  get_virtual_registers (ref uvm_vreg regs[$],
    #                                                        input uvm_hier_e hier=UVM_HIER)
    #
    #
    #   // Function: get_virtual_fields
    #   //
    #   // Get the virtual fields
    #   //
    #   // Get the virtual fields from the virtual registers instantiated
    #   // in this address map.
    #   // If ~hier~ is ~UVM_HIER~, recursively includes the virtual fields
    #   // in the virtual registers in the sub-maps.
    #   //
    #   extern virtual function void  get_virtual_fields (ref uvm_vreg_field fields[$],
    #                                                     input uvm_hier_e hier=UVM_HIER)
    #


    def get_reg_map_info(self, rg, error=1):
        """
        get_reg_map_info
        Args:
            rg:
            error:
        Returns:
        """
        result = None
        if rg not in self.m_regs_info:
            if error:
                uvm_error("REG_NO_MAP", ("Register '" + rg.get_name()
                    + "' not in map '" + self.get_name() + "'"))
            return None
        result = self.m_regs_info[rg]
        if not result.is_initialized:
            uvm_fatal("RegModel", ("map '" + self.get_name() +
                "' does not seem to be initialized correctly, "
                + "check that the top register model is locked()"))
        return result

    def get_mem_map_info(self, mem, error=1):
        """
          extern virtual function UVMRegMapInfo get_mem_map_info(uvm_mem mem, bit error=1)
        Args:
            mem:
            error:
        Returns:
        """
        if mem not in self.m_mems_info:
            if error:
                uvm_error("REG_NO_MAP", "Memory '" + mem.get_name() + "' not in map '"
                        + self.get_name() + "'")
            return None
        return self.m_mems_info[mem]


    #   extern virtual function int unsigned get_size()


    def get_physical_addresses(self, base_addr, mem_offset, n_bytes, addr):
        """

           Function: get_physical_addresses

           Translate a local address into external addresses

           Identify the sequence of addresses that must be accessed physically
           to access the specified number of bytes at the specified address
           within this address map.
           Returns the number of bytes of valid data in each access.

           Returns in `addr` a list of address in little endian order,
           with the granularity of the top-level address map.

           A register is specified using a base address with `mem_offset` as 0.
           A location within a memory is specified using the base address
           of the memory and the index of the location within that memory.


          extern virtual function int get_physical_addresses(uvm_reg_addr_t        base_addr,
                                                             uvm_reg_addr_t        mem_offset,
                                                             int unsigned          n_bytes,
                                                             ref uvm_reg_addr_t    addr[])
        Args:
            base_addr:
            mem_offset:
            n_bytes:
            addr:
        Returns:
        """
        bus_width = self.get_n_bytes(UVM_NO_HIER)
        up_map = None  # uvm_reg_map
        local_addr = []
        multiplier = 1
        if self.m_byte_addressing:
            multiplier = bus_width
        #addr = new [0]

        if (n_bytes <= 0):
           uvm_fatal("RegModel", sv.sformatf(
               "Cannot access %0d bytes. Must be greater than 0", n_bytes))
           return 0

        # First, identify the addresses within the block/system
        if n_bytes <= bus_width:
            local_addr.append(base_addr + (mem_offset * multiplier))
        else:
            n = 0
            n = int(((n_bytes-1) / bus_width) + 1)
            local_addr = [0] * n
            base_addr = base_addr + mem_offset * (n * multiplier)
            get_end = self.get_endian(UVM_NO_HIER)

            if get_end == UVM_LITTLE_ENDIAN:
                for i in range(len(local_addr)):
                    local_addr[i] = base_addr + (i * multiplier)
            elif get_end == UVM_BIG_ENDIAN:
                for i in range(len(local_addr)):
                    n -= 1
                    local_addr[i] = base_addr + (n * multiplier)
            elif get_end == UVM_LITTLE_FIFO:
                for i in range(len(local_addr)):
                    local_addr[i] = base_addr
            elif get_end == UVM_BIG_FIFO:
                for i in range(len(local_addr)):
                    local_addr[i] = base_addr
            else:
                uvm_error("RegModel",
                        ("Map has no specified endianness. ",
                        sv.sformatf("Cannot access %0d bytes register via its %0d byte %s interface",
                        n_bytes, bus_width, self.get_full_name())))

        up_map = self.get_parent_map()

        # Then translate these addresses in the parent's space
        if up_map is None:
            # This is the top-most system/block!
            addr.clear()
            addr.extend(local_addr)
            for i in range(len(addr)):
                addr[i] += self.m_base_addr
        else:
            sys_addr = []
            base_addr = 0
            w = 0
            k = 0

            # Scale the consecutive local address in the system's granularity
            if (bus_width < up_map.get_n_bytes(UVM_NO_HIER)):
                k = 1
            else:
                k = int((bus_width-1) / up_map.get_n_bytes(UVM_NO_HIER)) + 1

            base_addr = up_map.get_submap_offset(self)
            for i in range(len(local_addr)):
                n = len(addr)
                w = up_map.get_physical_addresses(base_addr + local_addr[i] * k,
                        0, bus_width, sys_addr)

                #addr = new [n + sys_addr.size()] (addr)
                for j in range(len(sys_addr)):
                    addr.append(sys_addr[j])
            # The width of each access is the minimum of this block or the system's width
            if (w < bus_width):
                bus_width = w

        return bus_width
        #
        #endfunction: get_physical_addresses


    def get_reg_by_offset(self, offset, read=True):
        """


           Function: get_reg_by_offset

           Get register mapped at offset

           Identify the register located at the specified offset within
           this address map for the specified type of access.
           Returns `None` if no such register is found.

           The model must be locked using <uvm_reg_block::lock_model()>
           to enable this functionality.

          extern virtual function uvm_reg get_reg_by_offset(uvm_reg_addr_t offset,
                                                            bit            read = 1)
        Args:
            offset:
            read:
        Returns:
        """
        if not(self.m_parent.is_locked()):
            uvm_error("RegModel", sv.sformatf(
                "Cannot get register by offset: Block %s is not locked.",
                self.m_parent.get_full_name()))
            return None

        if (not read and offset in self.m_regs_by_offset_wo):
            return self.m_regs_by_offset_wo[offset]

        if offset in self.m_regs_by_offset:
            return self.m_regs_by_offset[offset]

        return None


    #   //
    #   // Function: get_mem_by_offset
    #   // Get memory mapped at offset
    #   //
    #   // Identify the memory located at the specified offset within
    #   // this address map. The offset may refer to any memory location
    #   // in that memory.
    #   // Returns ~None~ if no such memory is found.
    #   //
    #   // The model must be locked using <uvm_reg_block::lock_model()>
    #   // to enable this functionality.
    #   //
    #   extern virtual function uvm_mem    get_mem_by_offset(uvm_reg_addr_t offset)


    #   //------------------
    #   // Group: Bus Access
    #   //------------------


    def set_auto_predict(self, on=True):
        """
        Sets the auto-predict mode for his map.

        When `on` is `TRUE`,
        the register model will automatically update its mirror
        (what it thinks should be in the DUT) immediately after
        any bus read or write operation via this map. Before a `UVMReg.write`
        or `UVMReg.read` operation returns, the register's `UVMReg.predict`
        method is called to update the mirrored value in the register.

        When `on` is `FALSE`, bus reads and writes via this map do not
        automatically update the mirror. For real-time updates to the mirror
        in this mode, you connect a `uvm_reg_predictor` instance to the bus
        monitor. The predictor takes observed bus transactions from the
        bus monitor, looks up the associated `UVMReg` register given
        the address, then calls that register's `UVMReg.predict` method.
        While more complex, this mode will capture all register read/write
        activity, including that not directly descendant from calls to
        `UVMReg.write` and `UVMReg.read`.

        By default, auto-prediction is turned off.

        Args:
            on:
        """
        self.m_auto_predict = on

    def get_auto_predict(self):
        """
        Gets the auto-predict mode setting for this map.

        Returns:
            bool: True if auto-predict enabled, False otherwise.
        """
        return self.m_auto_predict


    def set_check_on_read(self, on=1):
        """
        Sets the check-on-read mode for his map
        and all of its submaps.

        When `on` is `TRUE`,
        the register model will automatically check any value read back from
        a register or field against the current value in its mirror
        and report any discrepancy.
        This effectively combines the functionality of the
        <uvm_reg::read()> and ~uvm_reg::mirror(UVM_CHECK)~ method.
        This mode is useful when the register model is used passively.

        When `on` is `FALSE`, no check is made against the mirrored value.

        At the end of the read operation, the mirror value is updated based
        on the value that was read regardless of this mode setting.

        By default, auto-prediction is turned off.

        Args:
            on:
        """
        self.m_check_on_read = on
        for submap in self.m_submaps:
            submap.set_check_on_read(on)


    def get_check_on_read(self):
        """
        Gets the check-on-read mode setting for this map.

        Returns:
            bool: True if checking on read enabled, False otherwise
        """
        return self.m_check_on_read


    async def do_bus_write(self, rw, sequencer, adapter):
        """
        Perform a bus write operation.

        Args:
            rw (UVMRegItem):
            sequencer (UVMSequencer):
            adapter (UVMRegAdapter):
        """
        addrs = []
        system_map = self.get_root_map()
        bus_width = self.get_n_bytes()
        byte_en = sv.get_vector_of_ones(bus_width)
        map_info = None
        n_bits = 0
        lsb = 0
        skip = 0
        curr_byte = 0
        n_access_extra = 0
        n_access = 0
        n_bits_init = 0
        accesses = []

        [map_info, n_bits_init, lsb, skip] = self.Xget_bus_infoX(rw, map_info, n_bits_init, lsb, skip)
        #addrs = map_info.addr
        addrs = map_info.addr.copy()

        # if a memory, adjust addresses based on offset
        if rw.element_kind == UVM_MEM:
            for i in range(len(addrs)):
                addrs[i] = addrs[i] + map_info.mem_range.stride * rw.offset

        for val_idx in range(len(rw.value)):
            value = rw.value[val_idx]

            # /* calculate byte_enables */
            if rw.element_kind == UVM_FIELD:
                temp_be = 0
                idx = 0
                n_access_extra = lsb % (bus_width*8)
                n_access = n_access_extra + n_bits_init
                temp_be = n_access_extra
                value = value << n_access_extra
                while temp_be >= 8:
                    byte_en = sv.clear_bit(byte_en, idx)
                    idx += 1
                    temp_be -= 8

                temp_be += n_bits_init
                while temp_be > 0:
                    byte_en = sv.set_bit(byte_en, idx)
                    # byte_en[idx] = 1
                    idx += 1
                    temp_be -= 8
                byte_en &= (1 << idx)-1
                for i in range(skip):
                    addrs.pop_front()
                while len(addrs) > (int(n_bits_init/(bus_width*8)) + 1):
                    addrs.pop_back()
            curr_byte = 0
            n_bits = n_bits_init

            accesses = []
            for i in range(len(addrs)):
                rw_access = UVMRegBusOp()
                data = (value >> (curr_byte*8)) & ((1 << (bus_width * 8))-1)

                uvm_info(self.get_type_name(),
                   sv.sformatf("Writing 0x%0h at 0x%0h via map %s...",
                        data, addrs[i], rw.map.get_full_name()), UVM_VERB_MEM_MAP)

                if rw.element_kind == UVM_FIELD:
                    for z in range(bus_width):
                        bit_val = sv.get_bit(byte_en, curr_byte + z)
                        # rw_access.byte_en[z] = byte_en[curr_byte+z]
                        rw_access.byte_en = sv.set_bit(rw_access.byte_en, z, bit_val)

                rw_access.kind    = rw.kind
                rw_access.addr    = addrs[i]
                rw_access.data    = data
                #rw_access.n_bits  = (n_bits > bus_width*8) ? bus_width*8 : n_bits
                rw_access.n_bits = n_bits
                if (n_bits > bus_width*8):
                    rw_access.n_bits = bus_width*8
                rw_access.byte_en = byte_en

                accesses.append(rw_access)
                curr_byte += bus_width
                n_bits -= bus_width * 8

            # if set utilizy the order policy
            if (self.policy is not None):
                self.policy.order(accesses)

            # perform accesses
            # foreach(accesses[i]):
            for i in range(len(accesses)):
                rw_access = accesses[i]  # uvm_reg_bus_op
                bus_req = None  # uvm_sequence_item
                adapter.m_set_item(rw)
                bus_req = adapter.reg2bus(rw_access)
                adapter.m_set_item(None)

                if bus_req is None:
                    uvm_fatal("RegMem",
                        "adapter [" + adapter.get_name() + "] didnt return a bus transaction")

                bus_req.set_sequencer(sequencer)
                await rw.parent.start_item(bus_req, rw.prior)

                if (rw.parent is not None and i == 0):
                    rw.parent.mid_do(rw)

                await rw.parent.finish_item(bus_req)
                await bus_req.end_event.wait_on()

                if adapter.provides_responses:
                    bus_rsp = None  # uvm_sequence_item
                    op = None  # uvm_access_e
                    # TODO: need to test for right trans type, if not put back in q
                    await rw.parent.get_base_response(bus_rsp)
                    rw_access = adapter.bus2reg(bus_rsp, rw_access)
                else:
                    rw_access = adapter.bus2reg(bus_req, rw_access)
                    if rw_access is None:
                        uvm_error("ADAPTER_BUS2REG_NONE", sv.sformatf("Adapter %s"
                            + " returned None for RW item %s",
                            adapter.get_name(),
                            bus_req.convert2string())
                        )

                if (rw.parent is not None and i == len(addrs)-1):
                    rw.parent.post_do(rw)

                rw.status = rw_access.status

                uvm_info(self.get_type_name(),
                   sv.sformatf("Wrote 0x%0h at 0x%0h via map %s: %s...",
                      rw_access.data, addrs[i], rw.map.get_full_name(), rw.status), UVM_VERB_MEM_MAP)

                if rw.status == UVM_NOT_OK:
                    break

            for i in range(len(addrs)):
                addrs[i] = addrs[i] + map_info.mem_range.stride

        #end: foreach_value
        #
        #endtask: do_bus_write



    async def do_bus_read(self, rw, sequencer, adapter):
        """
        Perform a bus read operation.

        Args:
            rw (UVMRegItem):
            sequencer (UVMSequencer):
            adapter (UVMRegAdapter):
        """
        addrs = []  # uvm_reg_addr_t[$]
        system_map = self.get_root_map()
        bus_width = self.get_n_bytes()
        byte_en = sv.get_vector_of_ones(bus_width)
        map_info = None
        size = 0
        n_bits = 0
        skip = 0
        lsb = 0
        curr_byte = 0
        n_access_extra = 0
        n_access = 0
        n_bits_init = 0
        accesses = []  # uvm_reg_bus_op[$]

        # print("do_bus_read Given rw was " + rw.convert2string())
        [map_info, n_bits_init, lsb, skip] = self.Xget_bus_infoX(rw, map_info, n_bits_init, lsb, skip)
        # Need a copy as this will be modified later
        addrs = map_info.addr.copy()

        # if a memory, adjust addresses based on offset
        if (rw.element_kind == UVM_MEM):
            for i in range(len(addrs)):
                addrs[i] = addrs[i] + map_info.mem_range.stride * rw.offset

        for val_idx in range(len(rw.value)):
            rw.value[val_idx] = 0

            # /* calculate byte_enables */
            if (rw.element_kind == UVM_FIELD):
                temp_be = 0
                ii = 0
                n_access_extra = lsb % (bus_width*8)
                n_access = n_access_extra + n_bits_init
                temp_be = n_access_extra
                while (temp_be >= 8):
                    # byte_en[ii] = 0
                    byte_en = sv.clear_bit(byte_en, ii)
                    ii += 1
                    temp_be -= 8

                temp_be += n_bits_init
                while(temp_be > 0):
                    # byte_en[ii] = 1
                    byte_en = sv.set_bit(byte_en, ii)
                    ii += 1
                    temp_be -= 8
                byte_en &= (1 << ii) - 1
                for i in range(skip):
                    addrs.pop_front()
                while addrs.size() > (int(n_bits_init/(bus_width*8)) + 1):
                    addrs.pop_back()
            #end
            curr_byte = 0
            n_bits = n_bits_init

            accesses = []
            for i in range(len(addrs)):
                rw_access = UVMRegBusOp()

                uvm_info(self.get_type_name(),
                   sv.sformatf("Reading address 'h%0h via map \"%s\"...",
                             addrs[i], self.get_full_name()), UVM_VERB_MEM_MAP)

                if (rw.element_kind == UVM_FIELD):
                    #for (int z=0;z<bus_width;z++)
                    for z in range(bus_width):
                        # rw_access.byte_en[z] = byte_en[curr_byte+z]
                        bit_val = sv.get_bit(byte_en, curr_byte + z)
                        rw_access.byte_en = sv.set_bit(rw_access.byte_en, z, bit_val)

                rw_access.kind = rw.kind
                rw_access.addr = addrs[i]
                rw_access.data = curr_byte
                rw_access.byte_en = byte_en
                rw_access.n_bits = n_bits
                if (n_bits > bus_width*8):
                    rw_access.n_bits = bus_width*8

                accesses.append(rw_access)

                curr_byte += bus_width
                n_bits -= bus_width * 8

            # if set utilize the order policy
            if(self.policy is not None):
                self.policy.order(accesses)

            # perform accesses
            for i in range(len(accesses)):
                rw_access = accesses[i]  # uvm_reg_bus_op
                bus_req = None  # uvm_sequence_item
                data = 0  # uvm_reg_data_logic_t
                curr_byte_ = 0

                curr_byte_ = rw_access.data
                rw_access.data = 0
                adapter.m_set_item(rw)
                bus_req = adapter.reg2bus(rw_access)
                adapter.m_set_item(None)
                if bus_req is None:
                    uvm_fatal("RegMem","adapter [" + adapter.get_name() + "] didnt return a bus transaction")

                bus_req.set_sequencer(sequencer)
                await rw.parent.start_item(bus_req, rw.prior)

                if (rw.parent is not None and i == 0):
                    rw.parent.mid_do(rw)

                await rw.parent.finish_item(bus_req)
                await bus_req.end_event.wait_on()

                if adapter.provides_responses:
                    bus_rsp = None  # uvm_sequence_item
                    op = 0  # uvm_access_e
                    # TODO: need to test for right trans type, if not put back in q
                    await rw.parent.get_base_response(bus_rsp)
                    rw_access = adapter.bus2reg(bus_rsp,rw_access)
                else:
                    adapter.bus2reg(bus_req,rw_access)

                data = rw_access.data & ((1 << bus_width*8)-1)  # mask the upper bits
                rw.status = rw_access.status

                # TODO
                #if (rw.status == UVM_IS_OK && (^data) === 1'bx):

                uvm_info(self.get_type_name(),
                   sv.sformatf("Read 0x%h at 0x%h via map %s: %s...", data,
                       addrs[i], self.get_full_name(), str(rw.status)), UVM_VERB_MEM_MAP)

                if (rw.status == UVM_NOT_OK):
                    break

                rw.value[val_idx] |= data << curr_byte_*8

                if (rw.parent is not None and i == len(addrs)-1):
                    rw.parent.post_do(rw)

            #foreach (addrs[i])
            for i in range(len(addrs)):
                addrs[i] = addrs[i] + map_info.mem_range.stride

            if (rw.element_kind == UVM_FIELD):
                rw.value[val_idx] = (rw.value[val_idx] >> (n_access_extra)) & ((1<<size)-1)
        #endtask: do_bus_read


    async def do_write(self, rw):
        """
        Perform a write operation.

        Args:
            rw (UVMRegItem): Register item for the write op.
        """
        tmp_parent_seq = None  # uvm_sequence_base
        system_map = self.get_root_map()
        adapter = system_map.get_adapter()
        sequencer = system_map.get_sequencer()

        if (adapter is not None and adapter.parent_sequence is not None):
            o = None
            seq = None
            o = adapter.parent_sequence.clone()
            #assert($cast(seq,o))
            seq = o
            seq.set_parent_sequence(rw.parent)
            rw.parent = seq
            tmp_parent_seq = seq

        if rw.parent is None:
            #rw.parent = new("default_parent_seq")
            rw.parent = UVMSequenceBase("default_parent_seq")
            tmp_parent_seq = rw.parent

        if adapter is None:
            uvm_debug(self, 'do_write', 'Start seq because adapter is None')
            rw.set_sequencer(sequencer)
            await rw.parent.start_item(rw,rw.prior)
            await rw.parent.finish_item(rw)
            await rw.end_event.wait_on()
        else:
            uvm_debug(self, 'do_write', 'do_bus_write because adapter exists')
            await self.do_bus_write(rw, sequencer, adapter)

        # TODO
        #  if (tmp_parent_seq is not None)
        #    sequencer.m_sequence_exiting(tmp_parent_seq)
        #
        #endtask


    async def do_read(self, rw):
        """
        Perform a read operation.

        Args:
            rw (UVMRegItem): Register item for the read op.
        """
        tmp_parent_seq = None  # uvm_sequence_base
        system_map = self.get_root_map()
        adapter = system_map.get_adapter()
        sequencer = system_map.get_sequencer()

        if (adapter is not None and adapter.parent_sequence is not None):
            o = None  # uvm_object
            seq = None  # uvm_sequence_base
            o = adapter.parent_sequence.clone()
            # assert($cast(seq,o)) TODO check this
            seq = o
            seq.set_parent_sequence(rw.parent)
            rw.parent = seq
            tmp_parent_seq = seq

        if rw.parent is None:
            rw.parent = UVMSequenceBase("default_parent_seq")
            tmp_parent_seq = rw.parent

        if adapter is None:
            rw.set_sequencer(sequencer)
            await rw.parent.start_item(rw, rw.prior)
            await rw.parent.finish_item(rw)
            await rw.end_event.wait_on()
        else:
            await self.do_bus_read(rw, sequencer, adapter)

        if tmp_parent_seq is not None:
            sequencer.m_sequence_exiting(tmp_parent_seq)



    def Xget_bus_infoX(self, rw, map_info, size, lsb, addr_skip):
        """
        Returns bus info based on given register item.

        Args:
            rw (UVMRegItem):
            map_info (UVMRegMapInfo):
            size (int):
            lsb (int):
            addr_skip (int):
        Returns:
        Raises:
        """
        if rw.element_kind == UVM_MEM:
            mem = None  # uvm_mem
            if rw.element is None:  # || !$cast(mem,rw.element)):
                uvm_fatal("REG/CAST", "uvm_reg_item 'element_kind' is UVM_MEM, " +
                    "but 'element' does not point to a memory: " + rw.get_name())
            mem = rw.element
            map_info = self.get_mem_map_info(mem)
            size = mem.get_n_bits()
        elif rw.element_kind == UVM_REG:
            rg = None  # uvm_reg
            if(rw.element is None):  # || !$cast(rg,rw.element))
                uvm_fatal("REG/CAST", "uvm_reg_item 'element_kind' is UVM_REG, " +
                    "but 'element' does not point to a register: " + rw.get_name())
            rg = rw.element
            map_info = self.get_reg_map_info(rg)
            size = rg.get_n_bits()
        elif rw.element_kind == UVM_FIELD:
            field = None  # uvm_reg_field
            if rw.element is None:  # || !$cast(field,rw.element))
                uvm_fatal("REG/CAST", "uvm_reg_item 'element_kind' is UVM_FIELD, " +
                    "but 'element' does not point to a field: " + rw.get_name())
            field = rw.element
            map_info = self.get_reg_map_info(field.get_parent())
            size = field.get_n_bits()
            lsb = field.get_lsb_pos()
            addr_skip = (int(lsb/(self.get_n_bytes())*8))
        else:
            raise Exception("rw.element_kind value illegal: " +
                    str(rw.element_kind))
        return [map_info, size, lsb, addr_skip]


    #   extern virtual function string      convert2string()

    #   extern virtual function uvm_object  clone()
    #   extern virtual function void        do_print (uvm_printer printer)
    #   extern virtual function void        do_copy   (uvm_object rhs)
    #   //extern virtual function bit       do_compare (uvm_object rhs, uvm_comparer comparer)
    #   //extern virtual function void      do_pack (uvm_packer packer)
    #   //extern virtual function void      do_unpack (uvm_packer packer)
    #
    #
    #    // Function: set_transaction_order_policy
    #    // set the transaction order policy
    #    function void set_transaction_order_policy(uvm_reg_transaction_order_policy pol)
    #        policy = pol
    #    endfunction
    #
    #    // Function: get_transaction_order_policy
    #    // set the transaction order policy
    #    function uvm_reg_transaction_order_policy get_transaction_order_policy()
    #        return policy
    #    endfunction
    #
    #endclass: uvm_reg_map
uvm_object_utils(UVMRegMap)

#---------------
# Initialization
#---------------
#
#
# m_set_mem_offset
#
#function void uvm_reg_map::m_set_mem_offset(uvm_mem mem,
#                                            uvm_reg_addr_t offset,
#                                            bit unmapped)
#
#   if (!self.m_mems_info.exists(mem)):
#      `uvm_error("RegModel",
#         {"Cannot modify offset of memory '",mem.get_full_name(),
#         "' in address map '",get_full_name(),
#         "' : memory not mapped in that address map"})
#      return
#   end
#
#   begin
#      UVMRegMapInfo info    = self.m_mems_info[mem]
#      uvm_reg_block    blk     = get_parent()
#      uvm_reg_map      top_map = get_root_map()
#      uvm_reg_addr_t   addrs[]
#
#      // if block is not locked, Xinit_address_mapX will resolve map when block is locked
#      if (blk.is_locked()):
#
#         // remove any existing cached addresses
#         if (!info.unmapped):
#           foreach (top_map.m_mems_by_offset[range]):
#              if (top_map.m_mems_by_offset[range] == mem)
#                 top_map.m_mems_by_offset.delete(range)
#           end
#         end
#
#         // if we are remapping...
#         if (!unmapped):
#            uvm_reg_addr_t addrs[],addrs_max[]
#            uvm_reg_addr_t min, max, min2, max2
#            int unsigned stride
#
#            void'(get_physical_addresses(offset,0,mem.get_n_bytes(),addrs))
#            min = (addrs[0] < addrs[addrs.size()-1]) ? addrs[0] : addrs[addrs.size()-1]
#            min2 = addrs[0]
#
#            void'(get_physical_addresses(offset,(mem.get_size()-1),
#                                         mem.get_n_bytes(),addrs_max))
#            max = (addrs_max[0] > addrs_max[addrs_max.size()-1]) ?
#               addrs_max[0] : addrs_max[addrs_max.size()-1]
#            max2 = addrs_max[0]
#            // address interval between consecutive mem locations
#            stride = (max2 - max)/(mem.get_size()-1)
#
#            // make sure new offset does not conflict with others
#            foreach (top_map.m_regs_by_offset[reg_addr]):
#               if (reg_addr >= min && reg_addr <= max):
#                  string a,b
#                  a = $sformatf("[%0h:%0h]",min,max)
#                  b = $sformatf("%0h",reg_addr)
#                  `uvm_warning("RegModel", {"In map '",get_full_name(),"' memory '",
#                      mem.get_full_name(), "' with range ",a,
#                      " overlaps with address of existing register '",
#                      top_map.m_regs_by_offset[reg_addr].get_full_name(),"': 'h",b})
#               end
#            end
#
#            foreach (top_map.m_mems_by_offset[range]):
#               if (min <= range.max && max >= range.max ||
#                   min <= range.min && max >= range.min ||
#                   min >= range.min && max <= range.max):
#                 string a,b
#                 a = $sformatf("[%0h:%0h]",min,max)
#                 b = $sformatf("[%0h:%0h]",range.min,range.max)
#                 `uvm_warning("RegModel", {"In map '",get_full_name(),"' memory '",
#                     mem.get_full_name(), "' with range ",a,
#                     " overlaps existing memory with range '",
#                     top_map.m_mems_by_offset[range].get_full_name(),"': ",b})
#                 end
#            end
#
#            begin
#              UVMRegMapAddrRange range = '{ min, max, stride }
#              top_map.m_mems_by_offset[range] = mem
#              info.addr  = addrs
#              info.mem_range = range
#            end
#
#         end
#      end
#
#      if (unmapped):
#        info.offset   = -1
#        info.unmapped = 1
#      end
#      else begin
#        info.offset   = offset
#        info.unmapped = 0
#      end
#
#   end
#endfunction
#
#
#
#------------
# get methods
#------------
#
#
#
# get_fields
#
#function void uvm_reg_map::get_fields(ref uvm_reg_field fields[$], input uvm_hier_e hier=UVM_HIER)
#
#   foreach (self.m_regs_info[rg_]):
#     uvm_reg rg = rg_
#     rg.get_fields(fields)
#   end
#
#   if (hier == UVM_HIER)
#     foreach (this.self.m_submaps[submap_]):
#       uvm_reg_map submap=submap_
#       submap.get_fields(fields)
#     end
#
#endfunction
#
#
# get_memories
#
#function void uvm_reg_map::get_memories(ref uvm_mem mems[$], input uvm_hier_e hier=UVM_HIER)
#
#   foreach (self.m_mems_info[mem])
#     mems.push_back(mem)
#
#   if (hier == UVM_HIER)
#     foreach (self.m_submaps[submap_]):
#       uvm_reg_map submap=submap_
#       submap.get_memories(mems)
#     end
#
#endfunction
#
#
# get_virtual_registers
#
#function void uvm_reg_map::get_virtual_registers(ref uvm_vreg regs[$], input uvm_hier_e hier=UVM_HIER)
#
#  uvm_mem mems[$]
#  get_memories(mems,hier)
#
#  foreach (mems[i])
#    mems[i].get_virtual_registers(regs)
#
#endfunction
#
#
# get_virtual_fields
#
#function void uvm_reg_map::get_virtual_fields(ref uvm_vreg_field fields[$], input uvm_hier_e hier=UVM_HIER)
#
#   uvm_vreg regs[$]
#   get_virtual_registers(regs,hier)
#
#   foreach (regs[i])
#       regs[i].get_fields(fields)
#
#endfunction
#
#
#----------
# Size and Overlap Detection
#---------
#
# set_base_addr
#
#function void uvm_reg_map::set_base_addr(uvm_reg_addr_t offset)
#   if (self.m_parent_map is not None):
#      self.m_parent_map.set_submap_offset(this, offset)
#   end
#   else begin
#      self.m_base_addr = offset
#      if (self.m_parent.is_locked()):
#         uvm_reg_map top_map = get_root_map()
#         top_map.Xinit_address_mapX()
#      end
#   end
#endfunction
#
#
# get_size
#
#function int unsigned uvm_reg_map::get_size()
#
#  int unsigned max_addr
#  int unsigned addr
#
#  // get max offset from registers
#  foreach (self.m_regs_info[rg_]):
#    uvm_reg rg = rg_
#    addr = self.m_regs_info[rg].offset + ((rg.get_n_bytes()-1)/self.m_n_bytes)
#    if (addr > max_addr) max_addr = addr
#  end
#
#  // get max offset from memories
#  foreach (self.m_mems_info[mem_]):
#    uvm_mem mem = mem_
#    addr = self.m_mems_info[mem].offset + (mem.get_size() * (((mem.get_n_bytes()-1)/self.m_n_bytes)+1)) -1
#    if (addr > max_addr) max_addr = addr
#  end
#
#  // get max offset from submaps
#  foreach (self.m_submaps[submap_]):
#    uvm_reg_map submap=submap_
#    addr = self.m_submaps[submap] + submap.get_size()
#    if (addr > max_addr) max_addr = addr
#  end
#
#  return max_addr + 1
#
#endfunction
#
#
#
#function void uvm_reg_map::Xverify_map_configX()
#   // Make sure there is a generic payload sequence for each map
#   // in the model and vice-versa if this is a root sequencer
#   bit error
#   uvm_reg_map root_map = get_root_map()
#
#   if (root_map.get_adapter() is None):
#      `uvm_error("RegModel", {"Map '",root_map.get_full_name(),
#                 "' does not have an adapter registered"})
#      error++
#   end
#   if (root_map.get_sequencer() is None):
#      `uvm_error("RegModel", {"Map '",root_map.get_full_name(),
#                 "' does not have a sequencer registered"})
#      error++
#   end
#   if (error):
#      `uvm_fatal("RegModel", {"Must register an adapter and sequencer ",
#                 "for each top-level map in RegModel model"})
#      return
#   end
#
#endfunction
#
#
#--------------
# Get-By-Offset
#--------------
#
# get_mem_by_offset
#
#function uvm_mem uvm_reg_map::get_mem_by_offset(uvm_reg_addr_t offset)
#   if (!self.m_parent.is_locked()):
#      `uvm_error("RegModel", $sformatf("Cannot memory register by offset: Block %s is not locked.", self.m_parent.get_full_name()))
#      return None
#   end
#
#   foreach (self.m_mems_by_offset[range]):
#      if (range.min <= offset && offset <= range.max):
#         return self.m_mems_by_offset[range]
#      end
#   end
#
#   return None
#endfunction
#
#-------------
# Standard Ops
#-------------
#
# do_print
#
#function void uvm_reg_map::do_print (uvm_printer printer)
#   uvm_reg  regs[$]
#   uvm_vreg vregs[$]
#   uvm_mem  mems[$]
#   uvm_endianness_e endian
#   uvm_reg_map maps[$]
#   string prefix
#   uvm_sequencer_base sqr=get_sequencer()
#
#   super.do_print(printer)
#  printer.print_generic(get_name(), self.get_type_name(), -1, convert2string())
#
#   endian = get_endian(UVM_NO_HIER)
#   $sformat(convert2string, "%s -- %0d bytes (%s)", convert2string,
#            get_n_bytes(UVM_NO_HIER), endian.name())
#
#   printer.print_generic("endian","",-2,endian.name())
#   if(sqr is not None)
#    printer.print_generic("effective sequencer",sqr.get_type_name(),-2,sqr.get_full_name())
#
#   get_registers(regs,UVM_NO_HIER)
#   foreach (regs[j])
#        printer.print_generic(regs[j].get_name(), regs[j].get_type_name(),-2,$sformatf("@%0d +'h%0x",regs[j].get_inst_id(),regs[j].get_address(this)))
#
#
#   get_memories(mems)
#   foreach (mems[j])
#        printer.print_generic(mems[j].get_name(), mems[j].get_type_name(),-2,$sformatf("@%0d +'h%0x",mems[j].get_inst_id(),mems[j].get_address(0,this)))
#
#   get_virtual_registers(vregs)
#   foreach (vregs[j])
#        printer.print_generic(vregs[j].get_name(), vregs[j].get_type_name(),-2,$sformatf("@%0d +'h%0x",vregs[j].get_inst_id(),vregs[j].get_address(0,this)))
#
#   get_submaps(maps)
#   foreach (maps[j])
#        printer.print_object(maps[j].get_name(),maps[j])
#endfunction
#
# convert2string
#
#function string uvm_reg_map::convert2string()
#   uvm_reg  regs[$]
#   uvm_vreg vregs[$]
#   uvm_mem  mems[$]
#   uvm_endianness_e endian
#   string prefix
#
#   $sformat(convert2string, "%sMap %s", prefix, get_full_name())
#   endian = get_endian(UVM_NO_HIER)
#   $sformat(convert2string, "%s -- %0d bytes (%s)", convert2string,
#            get_n_bytes(UVM_NO_HIER), endian.name())
#   get_registers(regs)
#   foreach (regs[j]):
#      $sformat(convert2string, "%s\n%s", convert2string,
#               regs[j].convert2string());//{prefix, "   "}, this))
#   end
#   get_memories(mems)
#   foreach (mems[j]):
#      $sformat(convert2string, "%s\n%s", convert2string,
#               mems[j].convert2string());//{prefix, "   "}, this))
#   end
#   get_virtual_registers(vregs)
#   foreach (vregs[j]):
#      $sformat(convert2string, "%s\n%s", convert2string,
#               vregs[j].convert2string());//{prefix, "   "}, this))
#   end
#endfunction
#
#
# clone
#
#function uvm_object uvm_reg_map::clone()
#  //uvm_rap_map me
#  //me = new this
#  //return me
#  return None
#endfunction
#
#
# do_copy
#
#function void uvm_reg_map::do_copy (uvm_object rhs)
#  //uvm_reg_map rhs_
#  //assert($cast(rhs_,rhs))
#
#  //rhs_.regs = regs
#  //rhs_.mems = mems
#  //rhs_.vregs = vregs
#  //rhs_.blks = blks
#  //... and so on
#endfunction
