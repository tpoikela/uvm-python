import cocotb
from cocotb.triggers import Timer
from uvm import *

class NewTest(UVMTest):
    @cocotb.coroutine
    def run_phase(self, phase):
        phase.raise_objection(self)
        yield Timer(100, "NS")
        phase.drop_objection(self)

uvm_component_utils(NewTest)

class NewTest2(NewTest):
    pass

@cocotb.test()
def test_dut(dut):
    yield run_test('NewTest')

@cocotb.test()
def test_dut2(dut):
    yield run_test('NewTest2')
