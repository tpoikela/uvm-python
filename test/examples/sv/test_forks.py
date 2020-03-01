
import cocotb
from cocotb.triggers import Timer
from uvm import sv


async def proc1(args):
    await Timer(10, "NS")
    args['ok1'] = True


async def proc2(args):
    await Timer(15, "NS")
    args['ok2'] = True
    await Timer(5, "NS")


@cocotb.test()
async def test_fork_join_any(dut):
    state = {'ok1': False, 'ok2': False}
    fork1 = cocotb.fork(proc1(state))
    fork2 = cocotb.fork(proc2(state))
    await sv.fork_join_any([fork1, fork2])
    if state['ok1'] is False:
        raise Exception('ok1 must be True')
    if state['ok2'] is True:
        raise Exception('ok2 must be False due to fork_join_any')
    await Timer(20, "NS")
    if state['ok2'] is False:
        raise Exception('ok2 must be True after 20ns')


@cocotb.test()
async def test_fork_join(dut):
    state = {'ok1': False, 'ok2': False}
    fork1 = cocotb.fork(proc1(state))
    fork2 = cocotb.fork(proc2(state))
    await sv.fork_join([fork1, fork2])
    if state['ok1'] is False:
        raise Exception('ok1 must be True')
    if state['ok2'] is False:
        raise Exception('ok2 must be True due to fork_join')

#@cocotb.test()
#async def test_fork_join_none(dut):
#    fork1 = cocotb.fork(proc1(state))
#    fork2 = cocotb.fork(proc2(state))
#    forks = sv.fork_join_none([proc1(state), proc2(state)])


@cocotb.test()
async def test_forks_kill(dut):
    state = {'ok1': False, 'ok2': False}
    fork1 = cocotb.fork(proc1(state))
    fork2 = cocotb.fork(proc2(state))
    await sv.fork_join_any([fork1, fork2])
    fork2.kill()
    await Timer(20, "NS")
    if state['ok1'] is False:
        raise Exception('ok1 must be True')
    if state['ok2'] is True:
        raise Exception('ok2 must be False due to kill()')
