#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------

import cocotb
from cocotb.triggers import Timer, Combine
from cocotb.utils import get_sim_time

from uvm import *

NUM_SEQS = 1
NUM_LOOPS = 1

#UVMDebug.full_debug()


def to_string(X):
    return X.convert2string()


BUS_READ = 0
BUS_WRITE = 1

STATUS_OK = 0
STATUS_NOT_OK = 1


class bus_trans(UVMSequenceItem):

    def __init__(self, name=""):
        UVMSequenceItem.__init__(self, name)
        self.addr = 0
        self.data = 0
        self.op = 0
        self.rand('addr', range(0, 1 << 30))
        self.rand('data', range(0, (1 << 30) - 1))
        self.rand('op', [BUS_READ, BUS_WRITE])

    def do_copy(self, rhs):
        rhs_ = rhs
        if not sv.cast(rhs_, rhs):
            uvm_error("do_copy", "cast failed, check type compatability")
        UVMSequenceItem.do_copy(self, rhs)

        self.addr = rhs_.addr
        self.data = rhs_.data
        self.op = rhs_.op

    def do_compare(self, rhs, comparer):
        rhs_ = rhs  # bus_trans rhs_
        #if(!$cast(rhs_, rhs))
        #        `uvm_fatal("do_compare", "cast failed, check type compatability")
        return (self.op == rhs_.op) and (self.addr == rhs_.addr) and (self.data == rhs_.data)

    def convert2string(self):
        return sv.sformatf("op %s: addr=%0h, data=%0h",
            str(self.op), self.addr, self.data)

uvm_object_utils(bus_trans)


class bus_req(bus_trans):
    def __init__(self, name=""):
        UVMSequenceItem.__init__(self, name)
uvm_object_utils(bus_req)


class bus_rsp(bus_trans):

    def __init__(self, name=""):
        bus_trans.__init__(self, name)
        self.status = 0

    def do_copy(self, rhs):
        rhs_ = rhs
        #bus_rsp rhs_
        #if(!$cast(rhs_, rhs))
        #    uvm_fatal("do_copy", "cast failed, check type compatability")

        super.do_copy(rhs_)
        self.status = rhs_.status

    def convert2string(self):
        return sv.sformatf("op %s, status=%s",
                bus_trans.convert2string(self), str(self.status))


uvm_object_utils(bus_rsp)


class my_driver(UVMDriver):

    def __init__(self, name, parent):
        UVMDriver.__init__(self, name, parent)
        self.data_array = {}  # int data_array[511:0]
        self.nitems = 0
        self.recording_detail = UVM_HIGH


    async def run_phase(self, phase):
        req = None
        rsp = None

        while True:
            uvm_info("DRIVER", "my_driver getting the req now..",
                UVM_MEDIUM)
            qreq = []
            await self.seq_item_port.get(qreq)

            self.nitems += 1
            req = qreq[0]
            self.begin_tr(req)
            rsp = bus_rsp("bus_rsp")
            rsp.set_id_info(req)

            # Actually do the read or write here
            if req.op == BUS_READ:
                rsp.addr = req.addr  # [8:0]
                if rsp.addr in self.data_array:
                    rsp.data = self.data_array[rsp.addr]
                else:
                    rsp.data = 0xFFFFABCD
                uvm_info("sending", to_string(rsp), UVM_MEDIUM)
            else:
                self.data_array[req.addr] = req.data
                uvm_info("sending", to_string(req), UVM_MEDIUM)
            await self.seq_item_port.put(rsp)
            self.end_tr(req)


uvm_component_utils(my_driver)


class SoCLevelSeq(UVMSequence):

    def __init__(self, name=""):
        UVMSequence.__init__(self, name)
        self.seq_delay_ns = 10
        self.rand('seq_delay_ns', range(10, 90))

    async def body(self):
        sys0_seq = SubSysLevelSeq('sys0_seq')
        # await sys0_seq.start(None, self)
        await uvm_do_on_with(self, sys0_seq, None,
            lambda num_blk_seq: num_blk_seq == 10,
            lambda blk_level_delay_ns: blk_level_delay_ns in [10, 20, 30],
        )
        await Timer(self.seq_delay_ns, "NS")
        sys2_seq = SubSysLevelSeq('sys2_seq')
        # We don't randomize the 2nd sequence
        await sys2_seq.start(None, self)


class SubSysLevelSeq(UVMSequence):
    def __init__(self, name=""):
        UVMSequence.__init__(self, name)
        self.num_blk_seq = 5
        self.rand('num_blk_seq', range(1, 11))
        self.blk_level_delay_ns = 25
        self.rand('blk_level_delay_ns', range(5, 50))

    async def body(self):
        for i in range(self.num_blk_seq):
            blk_seq = BlockLevelSeq('blk_level_seq')
            await blk_seq.start(None, self)
            await Timer(self.blk_level_delay_ns, "NS")

uvm_object_utils(SubSysLevelSeq)


class BlockLevelSeq(UVMSequence):
    def __init__(self, name=""):
        UVMSequence.__init__(self, name)

    async def body(self):
        seqr = None
        arr = []
        if not UVMConfigDb.get(UVMRoot.get(), "", "SEQR", arr):
            uvm_fatal("NO_SEQR", "BlockLevelSeq did not get sequencer")
        seqr = arr[0]
        bs = bus_trans('bus_trans')
        #await self.start_item(bs, sequencer=seqr)
        self.m_sequencer = seqr
        await uvm_do_with(self, bs)
        #    lambda addr: addr in [0],
        #    lambda data: 0xFFFFFFFF
        #)
        #await self.finish_item(bs)



class sequenceA(UVMSequence):

    #local static integer g_my_id = 1
    g_my_id = 1

    def __init__(self, name=""):
        UVMSequence.__init__(self, name)
        self.my_id = sequenceA.g_my_id
        sequenceA.g_my_id += 1


    async def body(self):
        req = None  # REQ  req
        rsp = None  # RSP  rsp
        uvm_info("sequenceA", "Starting sequence", UVM_MEDIUM)

        for i in range(NUM_LOOPS):
            #req = uvm_create(req, self.m_sequencer)
            uvm_info("sequenceA", "Starting item " + str(i), UVM_MEDIUM)
            req = bus_req("my_req")
            await Timer(10, "NS")

            req.addr = (self.my_id * NUM_LOOPS) + i
            req.data = self.my_id + i + 55
            req.op   = BUS_WRITE

            if self.m_sequencer is None:
                raise Exception("Null sequencer CRASH")

            # uvm_send(req)
            await self.start_item(req)
            await self.finish_item(req)
            uvm_info("sequenceA", "getting response1 for " + str(i), UVM_MEDIUM)
            rsp = []
            await self.get_response(rsp)
            uvm_info("sequenceA", "got response1 for " + str(i) + ": " +
                    rsp[0].convert2string(), UVM_MEDIUM)

            #uvm_create(req)
            req = bus_req("my_req")
            req.addr = (self.my_id * NUM_LOOPS) + i
            req.data = 0
            req.op   = BUS_READ

            #uvm_send(req)
            await self.start_item(req)
            await self.finish_item(req)
            uvm_info("sequenceA", "getting response2 for " + str(i), UVM_MEDIUM)
            rsp = []
            await self.get_response(rsp)

            rsp = rsp[0]
            if rsp.data != (self.my_id + i + 55):
                uvm_error("SequenceA", sv.sformatf("Error, addr: %0d, expected data: %0d, actual data: %0d",
                    req.addr, req.data, rsp.data))
        uvm_info("sequenceA", "Finishing sequence", UVM_MEDIUM)

uvm_object_utils(sequenceA)


class env(UVMEnv):

    def __init__(self, name, parent):
        UVMEnv.__init__(self, name, parent)
        self.drv = None
        self.sqr = None
        self.error = False

    def build_phase(self, phase):
        UVMEnv.build_phase(self, phase)
        self.sqr = UVMSequencer("sequence_controller", self)
        UVMConfigDb.set(UVMRoot.get(), "", "SEQR", self.sqr)
        # create and connect driver
        self.drv = my_driver("my_driver", self)
        uvm_info("ENV", "Connecting ports now here", UVM_MEDIUM)
        self.drv.seq_item_port.connect(self.sqr.seq_item_export)


    async def run_phase(self, phase):
        phase.raise_objection(self)
        soc_seq = SoCLevelSeq('soc_seq')
        await soc_seq.start(None)
        phase.drop_objection(self)

    def check_phase(self, phase):
        if self.drv.nitems == 0:
            self.error = True
            self.uvm_report_error('env', sv.sformatf("nitems: Exp %0d, Got %0d",
                NUM_SEQS * NUM_LOOPS, self.drv.nitems))


uvm_component_utils(env)


@cocotb.test()
async def test_module_top(dut):
    # UVMPhase.m_phase_trace = True
    e = env("env_name", parent=None)
    uvm_info("top","In top initial block", UVM_MEDIUM)
    await run_test(dut=dut)
    sim_time = sim_time = get_sim_time('ns')

    if sim_time == 0:
        raise Exception('Sim time has not progressed')
    else:
        if sim_time < 50.0:
            msg = "Exp: > 50, got: " + str(sim_time)
            raise Exception('Wrong sim time at the end: ' + msg)
    if e.error is True:
        raise Exception('Env had errors')
