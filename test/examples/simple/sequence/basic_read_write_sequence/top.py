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

from uvm.base.uvm_debug import UVMDebug
from uvm.base.sv import sv
from uvm.base.uvm_globals import run_test
from uvm.base.uvm_object_globals import UVM_MEDIUM, UVM_HIGH
from uvm.base.uvm_phase import UVMPhase
from uvm.seq import UVMSequence, UVMSequenceItem, UVMSequencer
from uvm.macros import *
from uvm.comps import UVMDriver, UVMEnv

NUM_SEQS = 1
NUM_LOOPS = 10
USE_FIELD_MACROS = 0

#UVMDebug.full_debug()

def toSTRING(X):
    if USE_FIELD_MACROS:
        return X.sprint()
    else:
        return X.convert2string()

#Remark 1:
#
#- this example shows two alternative approaches to handle local properties -
#
#When the define USE_FIELD_MACROS is set, the code is utilizing the uvm_field_xxx macros
#to mark transaction fields as "uvm fields". Doing so automatically infers code which handles
#compare,print,copy,record,pack,unpack without any additional implementation from the user side.
#This is typically shorter to write and easier to maintain on the user side. On the other hand a generic
#implementation might not be as fast and custom tailored.
#
#The two styles can be mixed for most of the uvm_field functionality (manually handling few fields and
#use a default implementation for some others). Only the component level auto configuration for fields is for
#`uvm_field_* annotated members only. it means that only when the uvm_field_* macros are used these fields  will be
#set to their configured values automatically.


#Remark 2:
#
#All classes in this example utilize the uvm_(object|component)[_param]_utils macro. Althrough its not mandatory
#for UVM it is good practice since this macro will register the class in the UVM factory automatically. See the user
#guide for more information regarding uvm factory use models


#bus_op_t = sv.enum(BUS_READ, BUS_WRITE)
#status_t = sv.enum(STATUS_OK, STATUS_NOT_OK)
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

    if USE_FIELD_MACROS == 0:
        def do_copy(self, rhs):
            #bus_trans rhs_
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
            return sv.sformatf("op %s: addr=%03x, data=%02x",
                str(self.op), self.addr, self.data)

        # NOTE: in contrast to the USE_FIELD_MACROS version this doesnt implement pack/unpack/print/record/...
        #`endif

if USE_FIELD_MACROS:
    uvm_object_utils_begin(bus_trans)
    uvm_field_int('addr',UVM_DEFAULT)
    uvm_field_int('data',UVM_DEFAULT)
    uvm_field_enum('op',UVM_DEFAULT)
    uvm_field_utils_end(bus_trans)
else:
    uvm_object_utils(bus_trans)

#//--------------------------------------------------------------------
#// bus_req
#//--------------------------------------------------------------------
class bus_req(bus_trans):
    def __init__(self, name=""):
        UVMSequenceItem.__init__(self, name)
uvm_object_utils(bus_req)

#//--------------------------------------------------------------------
#// bus_rsp
#//--------------------------------------------------------------------
class bus_rsp(bus_trans):

    def __init__(self, name=""):
        bus_trans.__init__(self, name)
        self.status = 0

    if USE_FIELD_MACROS:
        pass
    else:

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

        # NOTE: in contrast to the USE_FIELD_MACROS version this doesnt implement pack/unpack/print/record/...


if USE_FIELD_MACROS:
    uvm_object_utils_begin(bus_rsp)
    uvm_field_enum('status', UVM_DEFAULT)
    uvm_object_utils_end(bus_rsp)
else:
    uvm_object_utils(bus_rsp)


class my_driver(UVMDriver):

    def __init__(self, name, parent):
        UVMDriver.__init__(self, name, parent)
        self.data_array = [0] * 512  # int data_array[511:0]
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
                rsp.data = self.data_array[rsp.addr]
                uvm_info("sending", toSTRING(rsp), UVM_MEDIUM)
            else:
                self.data_array[req.addr] = req.data
                uvm_info("sending", toSTRING(req), UVM_MEDIUM)
            await self.seq_item_port.put(rsp)
            self.end_tr(req)

uvm_component_utils(my_driver)


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

#uvm_object_param_utils(sequenceA)
uvm_object_utils(sequenceA)


class env(UVMEnv):
    #local uvm_sequencer #(bus_req, bus_rsp) sqr
    #local my_driver #(bus_req, bus_rsp) drv 

    def __init__(self, name, parent):
        UVMEnv.__init__(self, name, parent)
        self.drv = None
        self.sqr = None
        self.error = False

    def build_phase(self, phase):
        UVMEnv.build_phase(self, phase)
        self.sqr = UVMSequencer("sequence_controller", self)
        # create and connect driver
        self.drv = my_driver("my_driver", self)
        uvm_info("ENV", "Connecting ports now here", UVM_MEDIUM)
        self.drv.seq_item_port.connect(self.sqr.seq_item_export)

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        fork_procs = []
        for i in range(NUM_SEQS):
            the_sequence = sequenceA("sequence_" + str(i))
            fork_procs.append(cocotb.fork(the_sequence.start(self.sqr, None)))
        join_list = list(map(lambda t: t.join(), fork_procs))
        await Combine(*join_list)
        phase.drop_objection(self)

    def check_phase(self, phase):
        if self.drv.nitems != (2 * NUM_SEQS * NUM_LOOPS):
            self.error = True
            self.uvm_report_error('env', sv.sformatf("nitems: Exp %0d, Got %0d",
                NUM_SEQS * NUM_LOOPS, self.drv.nitems))


uvm_component_utils(env)


@cocotb.test()
async def test_module_top(dut):
    UVMPhase.m_phase_trace = True
    e = env("env_name", parent=None)
    uvm_info("top","In top initial block", UVM_MEDIUM)
    await run_test()
    sim_time = sim_time = get_sim_time('ns')

    if sim_time == 0:
        raise Exception('Sim time has not progressed')
    else:
        if sim_time < 50.0:
            msg = "Exp: > 50, got: " + str(sim_time)
            raise Exception('Wrong sim time at the end: ' + msg)
    if e.error is True:
        raise Exception('Env had errors')
