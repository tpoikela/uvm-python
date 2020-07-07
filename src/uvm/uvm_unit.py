""" Common code used in unit testing """

from uvm.reg.uvm_reg_block import UVMRegBlock
from uvm.reg.uvm_reg import UVMReg
from uvm.reg.uvm_reg_model import UVM_READ
from uvm.reg.uvm_reg_field import UVMRegField
from uvm.reg.uvm_reg_map import UVMRegMap


def create_reg(name, nbits=32, num_fields=1):
    reg = UVMReg(name, nbits)
    lsb_pos = 0
    nbits_per_fields = int(nbits / num_fields)
    msb_pos = nbits_per_fields - 1
    for i in range(num_fields):
        field = UVMRegField.type_id.create(name, None, reg.get_full_name())
        field.configure(reg, msb_pos, lsb_pos, "RW", 0, 0x00, 1, 1, 1)
        lsb_pos += nbits_per_fields
        msb_pos += nbits_per_fields
    return reg


def create_reg_block(name, num_regs=1):
    rb = UVMRegBlock(name)
    rb.default_map = rb.create_map("", 0, 4, 0, 0)
    offset = 0
    for i in range(num_regs):
        reg = create_reg("reg_" + str(i))
        reg.configure(rb, None)
        if rb.default_map is not None:
            rb.default_map.add_reg(reg, offset, "RW")
        offset += 4
    rb.configure(hdl_path='path.to.top')
    return rb

def create_reg_map(name):
    rb = create_reg_block('test_reg_block_for_map', 0)
    # rb.default_map = rb.create_map("", 0, 4, 0, 0)
    reg_map = rb.default_map
    return [reg_map, rb]

class TestPacket():

    def __init__(self, data=0, addr=0):
        self.data = data
        self.addr = addr

    def convert2string(self):
        return "Addr: " + str(self.addr)


class TestRegAdapter():

    def bus2reg(self, pkt, rw):
        rw.data = pkt.data
        rw.addr = pkt.addr
        rw.kind = UVM_READ
        return rw

    def reg2bus(self):
        pass


class MockObj:
    inst_id = 0

    """ Mock object for unit testing to reduce import deps between files """
    def __init__(self, name, parent):
        self.m_parent = parent
        self.m_name = name
        self.m_typename = "MockObj"
        self.m_inst_id = MockObj.inst_id
        MockObj.inst_id += 1

    def get_name(self):
        """Get name of this object """
        return self.m_name

    def get_full_name(self):
        """Get full name of this object """
        if self.m_parent is not None:
            return self.m_parent.get_full_name() + "." + self.m_name
        return self.m_name

    def get_parent(self):
        """Get parent of this object """
        return self.m_parent

    def get_type_name(self):
        return self.m_typename

    def get_inst_id(self):
        return self.m_inst_id


class MockCb(MockObj):

    def __init__(self, name):
        super().__init__(name, None)
        self.m_enabled = True

    def callback_mode(self, on=-1):
        return self.m_enabled
