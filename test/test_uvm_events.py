# File to test uvm_events implementation

import cocotb
from cocotb.triggers import Timer, Join, Combine

from uvm_testlib import *

from uvm.base.uvm_event import *

#class MultiEvent(Waitable):
#    """
#    Waits until all the passed triggers have fired.
#
#    Like most triggers, this simply returns itself.
#    """
#    @decorators.coroutine
#    def _wait(self):
#        waiters = []
#        e = Event()
#        triggers = list(self.triggers)
#
#        # start a parallel task for each trigger
#        for t in triggers:
#            @cocotb.coroutine
#            def waiter(t=t):
#                try:
#                    yield t
#                finally:
#                    triggers.remove(t)
#                    if not triggers:
#                        e.set()
#            waiters.append(cocotb.fork(waiter()))
#
#        # wait for the last waiter to complete
#        yield e.wait()
#        raise ReturnValue(self)

@cocotb.coroutine
def wait_events(events):
    waiters = []
    e = Event()
    triggers = list(events)

    # start a parallel task for each trigger
    for t in triggers:
        @cocotb.coroutine
        def waiter(t=t):
            try:
                yield t.wait()
            finally:
                triggers.remove(t)
                if not triggers:
                    e.set()
        waiters.append(cocotb.fork(waiter()))

    # wait for the last waiter to complete
    yield e.wait()
    raise ReturnValue(self)


@cocotb.coroutine
def setters(events):
    for e in events:
        yield Timer(10)
        e.set()

@cocotb.test(skip=False)
def test_multi_events(dut):
    e1 = Event('e1')
    e2 = Event('e2')
    #yield MultiEven(e1, e2)
    yield wait_events([e1])
    #cocotb.fork(setters([e1, e2]))
    #yield e1.wait()
    #yield e2.wait()
    print "All OK"

@cocotb.test(skip=True)
def test_uvm_event(dut):
    evt1 = UVMEvent('MyEvent1')
    evt2 = UVMEvent('MyEvent2')
    n1 = cocotb.fork(notify_event(evt1, 10))
    n2 = cocotb.fork(notify_event(evt2, 20))
    yield evt1.wait_trigger()
    d1 = evt1.get_trigger_data()
    yield evt2.wait_trigger()
    d2 = evt2.get_trigger_data()
    if d1 != 10 or d2 != 20:
        raise Exception('Event data error. d1: {}, d2: {}'.format(d1, d2))

@cocotb.coroutine
def notify_event(evt, after = 10):
    yield Timer(after)
    evt.trigger(after)
