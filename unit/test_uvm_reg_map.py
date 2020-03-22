
import unittest
from uvm.reg import (UVMRegMap, UVMRegBlock, UVMReg, UVMMem)
from uvm.reg.uvm_reg_model import *


class TestUVMRegMap(unittest.TestCase):


    def test_map_base(self):
        reg_map = UVMRegMap()
        reg_blk = UVMRegBlock('my_blk')
        reg_map.configure(reg_blk, base_addr=0, n_bytes=32, endian=0,
                byte_addressing=1)
        reg_blk.add_map(reg_map)
        r1 = UVMReg('r1', 32, False)
        r1.configure(reg_blk)
        reg_map.add_reg(r1, 4)
        reg_blk.lock_model()
        self.assertEqual(r1.get_offset(), 4)
        r1.set_offset(reg_map, 16)
        self.assertEqual(r1.get_offset(), 16)
        reg_map.reset(kind="SOFT")


    def test_add_parent_map(self):
        pass


    def test_get_physical_addresses(self):
        # reg_map = UVMRegMap()
        reg_blk = UVMRegBlock('my_blk2')
        reg_map = reg_blk.create_map("default_map2", 0x0, 4,
                UVM_LITTLE_ENDIAN)
        reg_blk.default_map = reg_map

        #reg_blk.add_map(reg_map)
        mem = UVMMem("my_mem_inst", 1024, 32, "RW")
        mem.configure(reg_blk, "")

        reg_map.m_system_n_bytes = 4
        reg_map.m_n_bytes = 4
        reg_map.add_mem(mem, 0x2000, "RW")
        reg_map.Xinit_address_mapX()

        mem_offset = 8192
        nbytes = 4
        addrs = []
        bus_width = reg_map.get_physical_addresses(mem_offset, 0, nbytes, addrs)
        self.assertEqual(addrs[0], mem_offset)

        mem_offset += 4
        bus_width = reg_map.get_physical_addresses(mem_offset, 0, nbytes, addrs)
        self.assertEqual(addrs[0], mem_offset)
        self.assertEqual(bus_width, 4)


    def test_error_conditions(self):
        reg_blk = UVMRegBlock('my_blk2')
        reg_map = reg_blk.create_map("default_map2", 0x0, 4,
            UVM_LITTLE_ENDIAN)
        reg_map.set_sequencer(None, None)
        reg_map.set_submap_offset(None, 0x123)
        err = reg_map.get_submap_offset(None)
        self.assertEqual(err, -1)
