# File to test uvm_events implementation with simulator

import cocotb
from cocotb.triggers import Timer, Join, Combine

from uvm_testlib import *
from uvm.base.uvm_event import UVMEvent


#@cocotb.coroutine
#def wait_events(events):
#    waiters = []
#    e = Event()
#    triggers = list(events)
#
#    # start a parallel task for each trigger
#    for t in triggers:
#        @cocotb.coroutine
#        def waiter(t=t):
#            try:
#                yield t.wait()
#            finally:
#                triggers.remove(t)
#                if not triggers:
#                    e.set()
#        waiters.append(cocotb.fork(waiter()))
#
#    # wait for the last waiter to complete
#    yield e.wait()
#    raise ReturnValue(self)

#@cocotb.coroutine
#def setters(events):
#    for e in events:
#        yield Timer(10)
#        e.set()

@cocotb.test(skip=False)
async def test_single_event(dut):
    e1 = UVMEvent('e1')
    #e2 = UVMEvent('e2')
    #yield wait_events([e1])

    
    async def notify_evt():
        await Timer(100, "NS")
        e1.trigger(123)
    cocotb.fork(notify_evt())
    await e1.wait_trigger()

    end_time = sv.realtime()
    data = e1.get_trigger_data()
    if end_time < 100 or data != 123:
        raise Exception('Test failed')


@cocotb.test(skip=False)
async def test_uvm_event(dut):
    evt1 = UVMEvent('MyEvent1')
    evt2 = UVMEvent('MyEvent2')
    n1 = cocotb.fork(notify_event(evt1, 10))
    n2 = cocotb.fork(notify_event(evt2, 20))
    await evt1.wait_trigger()
    d1 = evt1.get_trigger_data()
    await evt2.wait_trigger()
    d2 = evt2.get_trigger_data()
    if d1 != 10 or d2 != 20:
        raise Exception('Event data error. d1: {}, d2: {}'.format(d1, d2))


async def notify_event(evt, after=10):
    await Timer(after, "NS")
    evt.trigger(after)
