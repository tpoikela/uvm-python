#//
#// -------------------------------------------------------------
#//    Copyright 2010-2011 Synopsys, Inc.
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

from cocotb_coverage.coverage import coverage_section, CoverPoint, CoverCross

from uvm.reg import (UVMReg, UVMRegField, UVMMem, UVMRegBlock,
    UVM_CVR_FIELD_VALS, UVM_CVR_REG_BITS, UVM_CVR_ADDR_MAP,
    UVM_BIG_ENDIAN)
from uvm.macros import uvm_object_utils

#//
#// This example demonstrates how to include a coverage model
#// in a register model.
#//
#// Three coverage models are included:
#//   - Register level coverage
#//   - Address-leel coverage
#//   - Field value coverage
#//
#// This example demonstrates *how* to integrate a coverage model
#// in a UVM Register model. The details of the coverage model itself
#// are generator-specific and outside the scope of UVM.
#//


def cond(is_read, byte_en):
    return is_read is False and ((byte_en & 0x1) == 1)


class reg_R(UVMReg):

    CgBits = coverage_section(
        CoverPoint('top.cb_bits.wF1_0',
            xf=lambda data, byte_en, is_read, m_curr: cond(is_read, byte_en) and (m_curr & data & (1 << 1)),
            bins=[True, False]
        ),  # {m_current[0],m_data[0]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF1_1', xf = lambda a: a, bins = []) #  {m_current[1],m_data[1]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF1_2', xf = lambda a: a, bins = []) #  {m_current[2],m_data[2]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF1_3', xf = lambda a: a, bins = []) #  {m_current[3],m_data[3]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF2_0', xf = lambda a: a, bins = []) #  {m_current[4],m_data[4]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF2_1', xf = lambda a: a, bins = []) #  {m_current[5],m_data[5]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF2_2', xf = lambda a: a, bins = []) #  {m_current[6],m_data[6]} iff (!m_is_read  and  m_be[0])
        #      @CoverPoint('wF2_3', xf = lambda a: a, bins = []) #  {m_current[7],m_data[7]} iff (!m_is_read  and  m_be[0])
    )  # Close coverage section


    #   cg_vals = coverage_section(
    #      @CoverPoint('F1', xf = lambda a: a, bins = []) #  F1.value[3:0]
    #      @CoverPoint('F2', xf = lambda a: a, bins = []) #  F2.value[3:0]
    #      @CoverCross('F1F2', items = [ F1, F2
    #   ) # Close coverage section


    def __init__(self, name="reg_R"):
        super().__init__(name, 8)
        self.has_cover = self.build_coverage(UVM_CVR_REG_BITS + UVM_CVR_FIELD_VALS)
        if self.has_coverage(UVM_CVR_REG_BITS):
            # self.cg_bits = covergroup()
            pass
        if self.has_coverage(UVM_CVR_FIELD_VALS):
            # self.cg_vals = covergroup()
            pass
        self.m_current = 0
        self.m_data = 0
        self.m_be = 0
        self.m_is_read = False

    def build(self):
        self.F1 = UVMRegField.type_id.create("F1",None, self.get_full_name())
        self.F1.configure(self, 4, 0, "RW", 0, 0x00, 1, 1, 1)
        self.rand('F1')
        self.F1.set_compare()

        self.F2 = UVMRegField.type_id.create("F2",None,self.get_full_name())
        self.F2.configure(self, 4, 4, "RO", 0, 0xA, 1, 1, 1)
        self.rand('F2')


    def sample(self, data, byte_en, is_read, _map):
        if self.get_coverage(UVM_CVR_REG_BITS):
            self.m_current = self.get()
            self.m_data    = data
            self.m_be      = byte_en
            self.m_is_read = is_read
            self.sample_bits_cg(data, byte_en, is_read, self.m_current)

    @CgBits
    def sample_bits_cg(self, data, byte_en, is_read, m_current):
        pass

    def sample_fields_cg(self):
        pass

    def sample_values(self):
        super().sample_values()
        if self.get_coverage(UVM_CVR_FIELD_VALS):
            self.sample_fields_cg()

uvm_object_utils(reg_R)



class mem_M(UVMMem):


    CgAddr = coverage_section(
        CoverPoint(
            'top.cg_addr.MIN_MID_MAX',
            # *Note that lambda args must match sample() args (omit self)
            xf=lambda offset, is_read, _map: offset,
            bins=[(0), (1,126), (127)],
            bins_labels=['MIN', 'MID', 'MAX']
        ),
        CoverPoint(
            'top.cg_addr.read_write',
            # *Note that lambda args must match sample() args (omit self)
            xf=lambda offset, is_read, _map: is_read,
            bins=[True, False],
            bins_labels=['READ', 'WRITE']
        )
    )


    def __init__(self, name="mem_M"):
        super().__init__(name, 128, 8, "RW")
        self.m_offset = 0
        self.has_cover = self.build_coverage(UVM_CVR_ADDR_MAP)
        if self.has_coverage(UVM_CVR_ADDR_MAP):
            pass
            #self.cg_addr = covergroup()


    @CgAddr
    # *Note that lambda args must match sample() args (omit self)
    def sample(self, offset, is_read, _map):
        if self.get_coverage(UVM_CVR_ADDR_MAP):
            self.m_offset  = offset


uvm_object_utils(mem_M)


class block_B(UVMRegBlock):

    CgAddrRange = coverage_section(
        CoverPoint(
            'top.reg_block_range.Ra',
            xf=lambda addr: addr,
            bins=[0x0000]
        ),
        CoverPoint('top.reg_block_range.Rb',
            xf=lambda addr: addr,
            bins=[0x0100]
        ),
        CoverPoint('top.reg_block_range.mem',
            xf=lambda addr: addr,
            bins=[0x2000, (0x2001, 0x23FE), 0x23FF],
            bins_labels=['MIN', 'MID', 'MAX']
        )
    )

    CgVals = coverage_section(
        CoverPoint('top.reg_block_vals.Ra',
            xf=lambda ra, rb: ra,  # Ra.F1.value[3:0]
            bins=range(16)),
        CoverPoint('top.reg_block_vals.Rb',
            xf=lambda ra, rb: rb,  # Rb.F1.value[3:0]
            bins=range(16)),
        CoverCross('top.reg_block_B.RaRb', items=['top.reg_block_vals.Ra',
            'top.reg_block_vals.Rb'])
    )  # Close coverage section


    def __init__(self, name="B"):
        super().__init__(name)
        self.has_cover = self.build_coverage(UVM_CVR_ADDR_MAP+UVM_CVR_FIELD_VALS)
        self.m_offset = 0
        if self.has_coverage(UVM_CVR_ADDR_MAP):
            pass
            # self.cg_addr = covergroup()
        if self.has_coverage(UVM_CVR_FIELD_VALS):
            pass
            #self.cg_vals = covergroup()


    def build(self):

        self.default_map = self.create_map("", 0, 4, UVM_BIG_ENDIAN, 0)

        self.Ra = reg_R.type_id.create("Ra",None,self.get_full_name())
        self.Ra.configure(self, None)
        self.Ra.build()
        self.rand('Ra')

        self.Rb = reg_R.type_id.create("Rb",None,self.get_full_name())
        self.Rb.configure(self, None)
        self.Rb.build()
        self.rand('Rb')

        self.M = mem_M.type_id.create("M",None,self.get_full_name())
        self.M.configure(self)

        self.default_map.add_reg(self.Ra, 0x0000, "RW")
        self.default_map.add_reg(self.Rb, 0x0100, "RW")
        self.default_map.add_mem(self.M, 0x2000, "RW")


    def sample(self, offset, is_read, _map):
        if self. get_coverage(UVM_CVR_ADDR_MAP):
            self.m_offset  = offset
            self.sample_addr_cg(offset)


    @CgAddrRange
    def sample_addr_cg(self, offset):
        pass

    def sample_vals_cg(self, ra, rb):
        pass

    def sample_values(self):
        super().sample_values()
        if self.get_coverage(UVM_CVR_FIELD_VALS):
            ra = self.Ra.F1.value
            rb = self.Rb.F1.value
            self.sample_vals_cg(ra, rb)


uvm_object_utils(block_B)
