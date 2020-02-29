import cocotb
from cocotb.triggers import Timer
from uvm import *

class NewTest(UVMTest):
    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        phase.drop_objection(self)

uvm_component_utils(NewTest)

class NewTest2(NewTest):
    pass

@cocotb.test()
def test_dut(dut):
    await run_test('NewTest')

@cocotb.test()
def test_dut2(dut):
    await run_test('NewTest2')
