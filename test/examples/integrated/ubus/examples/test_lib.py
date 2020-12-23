#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela
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
from cocotb.triggers import Timer

from uvm.base import *
from uvm.comps import UVMTest
from uvm.macros import uvm_component_utils, uvm_fatal, uvm_info
from ubus_example_tb import ubus_example_tb
from ubus_example_master_seq_lib import read_modify_write_seq
from ubus_slave_seq_lib import slave_memory_seq
from uvm.seq import UVMSequence


class ubus_example_base_test(UVMTest):


    def __init__(self, name="ubus_example_base_test", parent=None):
        super().__init__(name, parent)
        self.test_pass = True
        self.ubus_example_tb0 = None
        self.printer = None

    def build_phase(self, phase):
        super().build_phase(phase)
        # Enable transaction recording for everything
        UVMConfigDb.set(self, "*", "recording_detail", UVM_FULL)
        # Create the tb
        self.ubus_example_tb0 = ubus_example_tb.type_id.create("ubus_example_tb0", self)
        # Create a specific depth printer for printing the created topology
        self.printer = UVMTablePrinter()
        self.printer.knobs.depth = 3

        arr = []
        if UVMConfigDb.get(None, "*", "vif", arr) is True:
            UVMConfigDb.set(self, "*", "vif", arr[0])
        else:
            uvm_fatal("NOVIF", "Could not get vif from config DB")


    def end_of_elaboration_phase(self, phase):
        # Set verbosity for the bus monitor for this demo
        if self.ubus_example_tb0.ubus0.bus_monitor is not None:
            self.ubus_example_tb0.ubus0.bus_monitor.set_report_verbosity_level(UVM_FULL)
        uvm_info(self.get_type_name(),
            sv.sformatf("Printing the test topology :\n%s", self.sprint(self.printer)), UVM_LOW)


    #  task run_phase(uvm_phase phase)
    #    //set a drain-time for the environment if desired
    #    phase.phase_done.set_drain_time(this, 50)
    #  endtask : run_phase

    def extract_phase(self, phase):
        self.err_msg = ""
        if self.ubus_example_tb0.scoreboard0.sbd_error:
            self.test_pass = False
            self.err_msg += '\nScoreboard error flag set'
        if self.ubus_example_tb0.scoreboard0.num_writes == 0:
            self.test_pass = False
            self.err_msg += '\nnum_writes == 0 in scb'
        if self.ubus_example_tb0.scoreboard0.num_init_reads == 0:
            self.test_pass = False
            self.err_msg += '\nnum_init_reads == 0 in scb'


    def report_phase(self, phase):
        if self.test_pass:
            uvm_info(self.get_type_name(), "** UVM TEST PASSED **", UVM_NONE)
        else:
            uvm_fatal(self.get_type_name(), "** UVM TEST FAIL **\n" +
                self.err_msg)


    #endclass : ubus_example_base_test
uvm_component_utils(ubus_example_base_test)

#// Read Modify Write Read Test

class test_read_modify_write(ubus_example_base_test):

    def __init__(self, name="test_read_modify_write", parent=None):
        super().__init__(name, parent)

    def build_phase(self, phase):
        UVMConfigDb.set(self, "ubus_example_tb0.ubus0.masters[0].sequencer.run_phase",
                "default_sequence", read_modify_write_seq.type_id.get())
        UVMConfigDb.set(self, "ubus_example_tb0.ubus0.slaves[0].sequencer.run_phase",
                "default_sequence", slave_memory_seq.type_id.get())
        #    // Create the tb
        super().build_phase(phase)

    
    async def run_phase(self, phase):
        phase.raise_objection(self, "test_read_modify_write OBJECTED")
        master_sqr = self.ubus_example_tb0.ubus0.masters[0].sequencer
        slave_sqr = self.ubus_example_tb0.ubus0.slaves[0].sequencer

        uvm_info("TEST_TOP", "Forking master_proc now", UVM_LOW)
        master_seq = read_modify_write_seq("r_mod_w_seq")
        master_proc = cocotb.fork(master_seq.start(master_sqr))

        slave_seq = slave_memory_seq("mem_seq")
        slave_proc = cocotb.fork(slave_seq.start(slave_sqr))
        #await [slave_proc, master_proc.join()]
        await sv.fork_join_any([slave_proc, master_proc])
        phase.drop_objection(self, "test_read_modify_write drop objection")
        if not master_seq.test_pass:
            self.test_pass = False


uvm_component_utils(test_read_modify_write)


#// Large word read/write test
#class test_r8_w8_r4_w4 extends ubus_example_base_test
#
#  `uvm_component_utils(test_r8_w8_r4_w4)
#
#  function new(string name = "test_r8_w8_r4_w4", uvm_component parent=null)
#    super.new(name,parent)
#  endfunction : new
#
#  virtual function void build_phase(uvm_phase phase)
#  begin
#    super.build_phase(phase)
#    uvm_config_db#(uvm_object_wrapper)::set(this,
#		      "ubus_example_tb0.ubus0.masters[0].sequencer.run_phase",
#			       "default_sequence",
#				r8_w8_r4_w4_seq::type_id::get())
#    uvm_config_db#(uvm_object_wrapper)::set(this,
#		      "ubus_example_tb0.ubus0.slaves[0].sequencer.run_phase",
#			       "default_sequence",
#				slave_memory_seq::type_id::get())
#  end
#  endfunction : build_phase
#
#endclass : test_r8_w8_r4_w4


# Virtual sequence for running masters and slaves
class seq_2m_4s(UVMSequence):
    def __init__(self, name):
        UVMSequence.__init__(self, name)
        # Populate these with sequencers to start sequences
        self.master_sqr = []
        self.slave_sqr = []

    
    async def body(self):
        # TODO create sequences and fork them
        i = 0
        for sqr in self.master_sqr:
            master_seq = read_modify_write_seq("r_mod_w_seq_" + str(i))
            master_proc = cocotb.fork(master_seq.start(sqr))
            i += 1
            # code...
        i = 0
        for sqr in self.slave_sqr:
            slave_seq = slave_memory_seq("mem_seq_" + str(i))
            slave_proc = cocotb.fork(slave_seq.start(sqr))
            i += 1
        await Timer(0, "NS")

#// 2 Master, 4 Slave test
class test_2m_4s(ubus_example_base_test):
    #
    #
    def __init__(self, name="test_2m_4s", parent=None):
        super().__init__(name, parent)

    def build_phase(self, phase):
        # loop_read_modify_write_seq lrmw_seq

        # Overides to the ubus_example_tb build_phase()
        # Set the topology to 2 masters, 4 slaves
        UVMConfigDb.set(self, "ubus_example_tb0.ubus0", "num_masters", 2)
        UVMConfigDb.set(self, "ubus_example_tb0.ubus0", "num_slaves", 4)
        ubus_example_base_test.build_phase(self, phase)

        # Control the number of RMW loops
        #    uvm_config_db#(int)::set(this,"ubus_example_tb0.ubus0.masters[0].sequencer.loop_read_modify_write_seq", "itr", 6)
        #    uvm_config_db#(int)::set(this,"ubus_example_tb0.ubus0.masters[1].sequencer.loop_read_modify_write_seq", "itr", 8)
        #
        #     // Define the sequences to run in the run phase
        #    uvm_config_db#(uvm_object_wrapper)::set(this,"*.ubus0.masters[0].sequencer.main_phase",
        #			       "default_sequence",
        #				loop_read_modify_write_seq::type_id::get())
        #     lrmw_seq = loop_read_modify_write_seq::type_id::create()
        #    uvm_config_db#(uvm_sequence_base)::set(this,
        #			       "ubus_example_tb0.ubus0.masters[1].sequencer.main_phase",
        #			       "default_sequence",
        #				lrmw_seq)
        #
        #     for(int i = 0; i < 4; i++):
        #	string slname
        #	$swrite(slname,"ubus_example_tb0.ubus0.slaves[%0d].sequencer", i)
        #	uvm_config_db#(uvm_object_wrapper)::set(this, {slname,".run_phase"},
        #						  "default_sequence",
        #						  slave_memory_seq::type_id::get())
        #     end
        #
        #    // Create the tb
        #    super.build_phase(phase)
        #  end
        #  endfunction : build_phase

    
    async def run_phase(self, phase):
        phase.raise_objection(self, "test_2m_4s objects", 1)
        top_seq = seq_2m_4s("seq_2m_4s")
        for slave in self.ubus_example_tb0.ubus0.slaves:
            top_seq.slave_sqr.append(slave.sequencer)
        for master in self.ubus_example_tb0.ubus0.masters:
            top_seq.master_sqr.append(master.sequencer)
        # TODO add handles for sequencers
        await top_seq.start(None)  # vseq runs with sequencer
        await Timer(1000, "NS")
        phase.drop_objection(self)


    def connect_phase(self, phase):
        # Connect other slaves monitor to scoreboard
        for i in range(1, 4):
            self.ubus_example_tb0.ubus0.slaves[i].monitor.item_collected_port.connect(
                self.ubus_example_tb0.scoreboard0.item_collected_export)


    def end_of_elaboration_phase(self, phase):
        # Set up slave address map for ubus0 (slaves[0] is overwritten here)
        self.ubus_example_tb0.ubus0.set_slave_address_map("slaves[0]", 0x0000, 0x3fff)
        self.ubus_example_tb0.ubus0.set_slave_address_map("slaves[1]", 0x4000, 0x7fff)
        self.ubus_example_tb0.ubus0.set_slave_address_map("slaves[2]", 0x8000, 0xBfff)
        self.ubus_example_tb0.ubus0.set_slave_address_map("slaves[3]", 0xC000, 0xFfff)
        super().end_of_elaboration_phase(phase)


uvm_component_utils(test_2m_4s)
