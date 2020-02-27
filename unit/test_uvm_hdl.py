
import unittest

from uvm.dpi.uvm_hdl import uvm_hdl

class MemSlot():
    def __init__(self):
        self.value = 0
    def __int__(self):
        return self.value

class MockMem():
    def __init__(self, size):
        self.size = size
        self.mem_sig = [MemSlot()] * size

class MockDut():
    def __init__(self, top=True):
        self.signal = MemSlot()
        self.mem = MockMem(16)
        self.mem_2d = [MockMem(8), MockMem(8)]
        if top is True:
            self.sub_dut = MockDut(top=False)


class TestUVMHDL(unittest.TestCase):
    pass

    #def test_uvm_hdl_split_path(self):
    #    path1 = "dut.mem"
    #    spl = uvm_hdl.split_path(path1)
    #    self.assertEqual(spl, ['dut', 'mem'])
    #    path2 = "dut.mem[3]"
    #    spl = uvm_hdl.split_path(path2)
    #    self.assertEqual(spl, ['dut', 'mem', '[3]'])
    #    path3 = "dut.mem[3][7]"
    #    spl = uvm_hdl.split_path(path3)
    #    self.assertEqual(spl, ['dut', 'mem', '[3]', '[7]'])
    #    path4 = "dut.mem[5].ram_sig[9]"
    #    spl = uvm_hdl.split_path(path4)
    #    self.assertEqual(spl, ['dut', 'mem', '[5]', 'ram_sig', '[9]'])

    #def test_uvm_hdl_read(self):
    #    dut = MockDut()
    #    dut.mem.mem_sig[2] = 0x2
    #    val = []
    #    uvm_hdl.set_dut(dut)
    #    uvm_hdl.uvm_hdl_read('dut.mem.mem_sig[2]', val)
    #    self.assertEqual(val[0], 0x2)
    #    val = []
    #    dut.mem_2d[0].mem_sig[7] = 0xF
    #    uvm_hdl.uvm_hdl_read('dut.mem_2d[0].mem_sig[7]', val)
    #    self.assertEqual(val[0], 0xF)

    #def test_uvm_hdl_deposit(self):
    #    dut = MockDut()
    #    uvm_hdl.set_dut(dut)
    #    # Should raise an error
    #    # uvm_hdl.uvm_hdl_deposit('dut.error.signal', 0xABCD)
    #    uvm_hdl.uvm_hdl_deposit('dut.signal', 0xABCD)
    #    self.assertEqual(dut.signal.value, 0xABCD)

    #    uvm_hdl.uvm_hdl_deposit('dut.sub_dut.signal', 0xAFFF)
    #    self.assertEqual(dut.sub_dut.signal.value, 0xAFFF)

    #    for i in range(16):
    #        value = 0xF + 2 * i
    #        uvm_hdl.uvm_hdl_deposit('dut.mem.mem_sig[{}]'.format(i), value)
    #        msg = "uvm_hdl_deposit to mem{} OK".format(i)
    #        self.assertEqual(dut.mem.mem_sig[i].value, value, msg)



if __name__ == '__main__':
    unittest.main()
