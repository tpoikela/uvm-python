
import cocotb
from cocotb.triggers import Timer, Join
from cocotb.result import TestFailure
import random

from uvm.base.uvm_mailbox import UVMMailbox

from uvm.comps.uvm_test import UVMTest
from uvm.base.uvm_globals import run_test
from uvm.base.uvm_debug import *
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_phase import *
from uvm.base.uvm_root import *
from uvm.macros.uvm_object_defines import *

class MyTest(UVMTest):
    def __init__(self, name, parent):
        UVMTest.__init__(self, name, parent)

    def build_phase(self, phase):
        UVMTest.build_phase(self, phase)
        print("Called build_phase() with", str(phase))

    def connect_phase(self, phase):
        UVMTest.connect_phase(self, phase)
        print("Called connect_phase() with", str(phase))

uvm_component_utils(MyTest)

@cocotb.test(skip=False)
async def mailbox_test(dut):
    npackets = 10
    fifo = UVMMailbox()
    #yield write_packets(fifo, 10)
    write_proc = cocotb.fork(write_packets(fifo, npackets))
    read_proc = cocotb.fork(read_packets(fifo, npackets))
    print("Waiting to join() the forked procs")
    #yield Timer(10)
    await write_proc.join(), read_proc.join()
    await Timer(10000)

class TestParentComp(UVMComponent):
    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)

    def build_phase(self, phase):
        UVMComponent.build_phase(self, phase)
        child1 = UVMComponent('child1', self)

class CompPhaseTest(UVMTest):
    def __init__(self, name, parent):
        UVMTest.__init__(self, name, parent)
        self.m_done_event = Event()
        self.all_done = False

    def final_phase(self, phase):
        self.all_done = True
        self.m_done_event.set()

# Runs the test without using uvm_top and the full framework
@cocotb.test(skip=False)
async def uvm_component_test(dut):
    #comp = UVMComponent('top', None)
    comp = TestParentComp('top', None)
    caller = UVMPhaseCaller(comp)
    caller.clear()
    caller.call_topdown_phase(comp, 'build_phase')
    caller.expect_call_order(['top', 'child1'])
    caller.clear()
    caller.call_bottomup_phase(comp, 'connect_phase')
    caller.expect_call_order(['child1', 'top'])
    #yield comp.run_phase({})
    await caller.call_topdown_task_phase(comp, 'run_phase')
    await Timer(100)

@cocotb.test(skip=False)
async def uvm_basic_top_test(dut):
    """ Test for checking that UVM is up and running """
    test = UVMTest('my test', None)
    test.dut = dut
    await run_test('MyTest')

@cocotb.test(skip=True)
async def uvm_phase_test(dut):
    uvm_root = UVMRoot.get()
    test_comp = CompPhaseTest('comp_phase_test', uvm_root)
    clp = UVMCmdlineProcessor.get_inst()
    print("tool=" + clp.get_tool_name() + " version=" + clp.get_tool_version())
    await run_test()
    await test_comp.m_done_event.wait()
    if not test_comp.all_done:
        raise Exception('Error in comp_phase_test')

# HELPERS


async def write_packets(fifo, n):
    nwritten = 0
    while nwritten < n:
        await fifo.put(n + 100)
        uvm_debug('', 'write_packets', "Wrote packet {} into FIFO".format(nwritten))
        nwritten += 1
        rand_delay = random.randint(1, 15)
        await Timer(rand_delay)
    uvm_debug('', 'write_packets', "Write completed".format(n))


async def read_packets(fifo, n):
    nread = 0
    while nread < n:
        q = []
        await fifo.get(q)
        print("Read packet {} into FIFO".format(nread))
        nread += 1
        if len(q) == 1:
            if q[0] != (n + 100):
                print("Error in n{}: Got: {}, Exp: {}".format(nread, q[0], n + 100))
        else:
            raise Exception('q.len must be 1 after get()')
        rand_delay = random.randint(1, 15)
        await Timer(rand_delay)
    print("read_packets completed")

class UVMPhaseCaller:
    """ Starts from a top comp, and calls given phases of all comps"""

    def __init__(self, top_comp, phases = []):
        self.comp = top_comp
        self.top_phase = UVMPhase('top')
        self.call_order = []

    def clear(self):
        self.call_order = []

    def call_topdown_phase(self, comp, name):
        if hasattr(comp, name):
            print("topdown OK for {}, {}".format(comp.get_name(), name))
            func = getattr(comp, name)
            func(self.top_phase)
            self.call_order.append(comp.get_name())
        else:
            raise Expection('No phase func {} in comp {}'.format(name,
                comp.get_name()))
        children = []
        comp.get_children(children)
        for c in children:
            self.call_topdown_phase(c, name)

    def call_bottomup_phase(self, comp, name):
        children = []
        comp.get_children(children)
        if len(children) == 0:
            if hasattr(comp, name):
                func = getattr(comp, name)
                func(self.top_phase)
                self.call_order.append(comp.get_name())
            else:
                raise Expection('No phase func {} in comp {}'.format(name,
                    comp.get_name()))
        else:
            for c in children:
                self.call_bottomup_phase(c, name)
            func = getattr(comp, name)
            func(self.top_phase)
            self.call_order.append(comp.get_name())
    
    
    async def call_topdown_task_phase(self, comp, name):
        #func = getattr(comp, name)
        #yield func(self.top_phase)
        children = []
        comp.get_children(children)
        if hasattr(comp, name):
             func = getattr(comp, name)
             await func(self.top_phase)
        else:
            raise Expection('No phase func {} in comp {}'.format(name,
                comp.get_name()))
        for c in children:
             await self.call_topdown_task_phase(c, name)

    def expect_call_order(self, exp_order):
        ii = 0
        if len(exp_order) != len(self.call_order):
            raise Exception('Call order len differs: {} vs {}'.format(
                len(exp_order), len(self.call_order)))
        for i in exp_order:
            if i != self.call_order[ii]:
                raise Exception('Call order error: Got {} Exp: {}'.format(
                    self.call_order[ii], i))
            ii += 1

