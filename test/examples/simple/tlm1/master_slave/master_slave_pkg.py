#
#//----------------------------------------------------------------------
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

# About: master_slave_test
#
# This toy example uses TLM master/slave ports and transport-interface.
#
# Walk through the test:
# ======================
# 1. Master comps will generate NUM_ITEMS transactions.
#
# 2. Bus will accept the transactions, and route them to correct slaves or
#    memories.
#
# 3. Memories respond to writes/reads in blocking manner. Slave also does the
#    same. IO Slave uses transport to communicate with an IO port.
#
# 4. IO Port blocks on READ but WRITES are non-blocking (shoot and forget)>
#
# 5. Top_env does some checks at the end to ensure some transactions have been
#    completed.

import cocotb
from cocotb.triggers import Timer

from uvm import *
from enum import Enum

# These can be changed to vary the topology
NUM_MASTERS = 5  # 6 fatals out
NUM_SLAVES = 34  # 35 gets stuck, >= 36 fatals out
NUM_MEMS = 10 # 11 gets stuck

#ratio = 3
#NUM_MASTERS = 2 * ratio
#NUM_SLAVES = 4 * ratio
#NUM_MEMS = 4 * ratio


class Cmd(Enum):
    READ = 0
    WRITE = 1


NUM_ITEMS = 100
MEM_ADDR_MASK = 0xFFFFF
MEM_ADDR_OFFSET = MEM_ADDR_MASK + 1
SLAVE_ADDR_OFFSET = 0x1000


def get_slv_addr(i):
    addr = SLAVE_ADDR_OFFSET + i * SLAVE_ADDR_OFFSET
    if addr >= MEM_ADDR_OFFSET:
        raise Exception("slave_addr {} out of range (<= {}), i: {}".format(addr,
            MEM_ADDR_OFFSET, i))
    return addr


def get_master_addr(i):
    addr = 0x10 + i * 0x10
    if addr >= SLAVE_ADDR_OFFSET:
        raise Exception("master_addr {} out of range (<= {})".format(addr,
            SLAVE_ADDR_OFFSET))
    return addr



def get_mem_addr(i):
    return MEM_ADDR_OFFSET + i * MEM_ADDR_OFFSET


#----------------------------------------------------------------------
# class transaction
#----------------------------------------------------------------------


class transaction(UVMTransaction):


    def __init__(self, name='trans'):
        super().__init__(name)
        self.addr = 0
        self.data = 0
        self.cmd = Cmd.READ
        addr_list = []
        for i in range(NUM_SLAVES):
            addr_list.append(get_slv_addr(i))
        for i in range(NUM_MEMS):
            addr_list.append(get_mem_addr(i))
        self.rand("data", range((1 << 32) - 1))
        self.rand("addr", addr_list)
        self.rand("cmd", [Cmd.READ, Cmd.WRITE])

    def do_copy(self, t):
        self.data = t.data
        self.addr = t.addr

    def do_compare(self, a, b):
        return a.data == b.data and a.addr == b.addr

    def do_clone(self):
        t = transaction()
        t.copy(self)
        return t

    def convert2string(self):
        s = sv.sformatf("[ addr = %s, data = %s cmd: %s]", hex(self.addr),
                hex(self.data), str(self.cmd))
        return s


uvm_object_utils(transaction)


#----------------------------------------------------------------------
# component master
#----------------------------------------------------------------------

class master(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.master_port = UVMMasterPort("master_port", self)
        self.num_items = 0
        self.use_blocking = True
        self.tag = "MASTER"

    
    async def run_phase(self, phase):
        for i in range(NUM_ITEMS):
            t = transaction()
            if not t.randomize():
                uvm_error("GEN", "Failed to randomize transaction")
            else:
                t.addr = t.addr
            uvm_info(self.tag, sv.sformatf("sending  : %s", t.convert2string()), UVM_MEDIUM)
            if t.cmd == Cmd.WRITE:
                await self.master_port.put(t)
            else:
                await self.master_port.get([t])
            self.num_items += 1
            await Timer(sv.urandom_range(1, 10) * 10, "NS")


# Base class for slave components

class slave_base(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.slave_port = UVMSlaveImp('slave_port', self)

    def try_put(self, t):
        return False

    def can_put(self, t):
        return False

    def try_get(self, t):
        return False

    def can_get(self, t):
        return False

    def try_peek(self, t):
        return False

    def can_peek(self, t):
        return False

    
    async def get(self, t):
        await Timer(0)

    
    async def put(self, t):
        await Timer(0)

    
    async def peek(self, t):
        await Timer(0)


class bus(slave_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.addr_map = {}
        self.req_fifo = UVMTLMFIFO('bus_fifo')
        self.master_ports = {}
        self.master_port = UVMMasterImp('master_port', self)

    def add_comp(self, addr, comp, port_name=''):
        port = None
        # if addr in self.addr_map:
        if port_name == "":
            if hasattr(comp, 'master_port'):
                port_name = 'master_port'
                port = getattr(comp, 'master_port')
            elif hasattr(comp, 'slave_port'):
                port_name = 'slave_port'
                port = getattr(comp, 'slave_port')
            else:
                uvm_fatal("BUS/NO_PORT",
                    "Unable to find master/slave port, and no port name given!")
        # pname = port  # TODO support for any port name
        if port is not None:
            self.addr_map[addr] = {"comp": comp}
            if port_name == 'master_port':
                port.connect(self.master_port)
            else:
                self.master_ports[addr] = UVMSlavePort('bus_port_' +
                        comp.get_name(), self)
                self.master_ports[addr].connect(port)

    
    async def get(self, t):
        addr = t[0].addr
        if addr in self.addr_map:
            await self.master_ports[addr].get(t)
        else:
            uvm_error('BUS_READ_ERR', "No addr {} in map".format(addr))

    
    async def put(self, t):
        addr = t.addr
        if addr in self.addr_map:
            await self.master_ports[addr].put(t)
        else:
            uvm_error('BUS_WRITE_ERR', "No addr {} in map".format(addr))

#----------------------------------------------------------------------
# componenet slave
#----------------------------------------------------------------------


class slave(slave_base):


    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.num_put = 0
        self.num_get = 0

    def num_cmds(self):
        return self.num_put + self.num_get

    
    async def put(self, t):
        await Timer(10, "NS")
        uvm_info("SLAVE_PUT", "Received cmd", UVM_MEDIUM)
        self.num_put += 1


    
    async def get(self, t):
        await Timer(10, "NS")
        uvm_info("SLAVE_GET", "Received cmd", UVM_MEDIUM)
        self.num_get += 1


class io_slave(slave):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.trans_port = UVMTransportPort('trans_imp', self)

    
    async def put(self, t):
        await Timer(10, "NS")
        uvm_info("SLAVE_PUT", "Received cmd", UVM_MEDIUM)
        self.num_put += 1
        rsp = []
        if self.trans_port.nb_transport(t, rsp):
            uvm_info(self.tag, "Transport put to IO port OK")


    
    async def get(self, t):
        await Timer(10, "NS")
        uvm_info("IO_SLAVE_GET",
            "Oh no! We hit the blocking IO slave read. This will take long time",
            UVM_MEDIUM)
        self.num_get += 1
        rsp = []
        await self.trans_port.transport(t[0], rsp)
        t.clear()
        t.append(rsp[0])


class io_port(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.trans_imp = UVMTransportImp('trans_imp', self)
        self.num_io_writes = 0
        self.num_io_reads = 0

    # IO Reads implemented as blocking
    
    async def transport(self, req, rsp):
        await Timer(500, "NS")
        self.num_io_reads += 1
        rsp.append("READ DONE")

    # Writes implemented as non-blocking
    def nb_transport(self, req, rsp):
        self.num_io_writes += 1
        # Data goes to /dev/null etc
        rsp.append("WRITE DONE")

#  //----------------------------------------------------------------------
#  // componenet bfm
#  //----------------------------------------------------------------------

class memory(slave_base):


    def __init__(self, name, parent, size=256):
        super().__init__(name, parent)
        self.size = 256
        self.mem = {}
        self.num_reads = 0
        self.num_writes = 0
        for i in range(self.size):
            self.mem[i] = 0x0

    def num_cmds(self):
        return self.num_reads + self.num_writes

    
    async def put(self, t):
        await self.wait_access()
        addr = t.addr & MEM_ADDR_MASK
        if addr in self.mem:
            self.num_writes += 1
            uvm_info("MEM_WRITE", "Wrote data [{:0X}]: {:0X}".format(addr,
                t.data), UVM_MEDIUM)
            self.mem[addr] = t.data

    
    async def get(self, t):
        await self.wait_access()
        addr = t[0].addr & MEM_ADDR_MASK
        if addr in self.mem:
            self.num_reads += 1
            t.append(self.mem[addr])
            uvm_info("MEM_READ", "Read data [{:0X}]: {:0X}".format(addr,
                self.mem[addr]), UVM_MEDIUM)

    
    async def wait_access(self):
        await Timer(10, "NS")


    
    async def run_phase(self, phase):
        while True:
            await Timer(100, "NS")


class listener(UVMSubscriber):  # (transaction)
    def __init__(self, name, parent):
        super().__init__(name,parent)

    def write(self, t):
        uvm_info(m_name, sv.sformatf("Received: %s", t.convert2string()), UVM_MEDIUM)


#  //----------------------------------------------------------------------
#  // componenet top
#  //----------------------------------------------------------------------

class env_top(UVMEnv):


    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.masters = []
        self.slaves = []
        self.mems = []
        self.bus = None

    def build_phase(self, phase):
        self.bus = bus("bus", self)
        # Need to call these in build() because this creates some TLM ports
        for i in range(NUM_MASTERS):
            mast = master("master_" + str(i), self)
            mast.tag = mast.tag + "__" + str(i)
            self.masters.append(mast)
            addr = get_master_addr(i)
            self.bus.add_comp(addr, mast)

        for i in range(NUM_SLAVES):
            slv = None
            if sv.urandom_range(0, 9) == 0:
                slv = io_slave("io_slave_" + str(i), self)
                io_port_inst = io_port("io_port_" + str(i), self)
                # P2P connection, not done via bus
                slv.trans_port.connect(io_port_inst.trans_imp)
            else:
                slv = slave("slave_" + str(i), self)
            self.slaves.append(slv)
            addr = get_slv_addr(i)
            self.bus.add_comp(addr, slv)
        for i in range(NUM_MEMS):
            mem_inst = memory("mem_" + str(i), self)
            self.mems.append(mem_inst)
            self.bus.add_comp(get_mem_addr(i), mem_inst)


    def connect_phase(self, phase):
        pass

    
    async def run_phase(self, phase):
        phase.raise_objection(self)
        uvm_info("ENV_TOP", "run_phase started", UVM_MEDIUM)
        await Timer(NUM_ITEMS * 110, "NS")
        phase.drop_objection(self)


    def all_ok(self):
        num_master_cmds = NUM_MASTERS * NUM_ITEMS
        num_slave_cmds = 0
        num_mem_cmds = 0
        for i in range(NUM_SLAVES):
            num_slave_cmds += self.slaves[i].num_cmds()
        for i in range(NUM_MEMS):
            num_mem_cmds += self.mems[i].num_cmds()

        if (num_slave_cmds + num_mem_cmds) != num_master_cmds:
            slv_cmd = num_slave_cmds + num_mem_cmds
            uvm_error("ENV_TOP", "Cmd mismatch: {} vs master: {}".format(
                slv_cmd, num_master_cmds))
            return False
        else:
            return True
# uvm_component_utils(env_top)
