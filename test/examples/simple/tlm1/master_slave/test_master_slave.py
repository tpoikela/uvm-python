
import cocotb
from cocotb.triggers import Timer
from uvm import (UVMTest, run_test)
from uvm.macros import (uvm_component_utils, uvm_fatal)

from master_slave_pkg import env_top

test_dur = 1000  # NS


class master_slave_test(UVMTest):

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def build_phase(self, phase):
        self.env = env_top("env_master_slave", self)

    @cocotb.coroutine
    def run_phase(self, phase):
        phase.raise_objection(self)
        yield Timer(test_dur, "NS")
        phase.drop_objection(self)


    def check_phase(self, phase):
        if not self.env.all_ok():
            uvm_fatal("ENV_NOT_OK", "There were errors in the env")


uvm_component_utils(master_slave_test)


@cocotb.test()
def master_slave_top(dut):
    yield run_test()
