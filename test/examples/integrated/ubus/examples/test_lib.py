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

from uvm.base import *
from uvm.comps import UVMTest
from uvm.macros import uvm_component_utils
from ubus_example_tb import ubus_example_tb
from ubus_example_master_seq_lib import read_modify_write_seq
from ubus_slave_seq_lib import slave_memory_seq

#// Base Test
#class ubus_example_base_test extends uvm_test
class ubus_example_base_test(UVMTest):

    #  ubus_example_tb ubus_example_tb0
    #  uvm_table_printer printer
    #  bit test_pass = 1
    #
    #  function new(string name = "ubus_example_base_test",
    def __init__(self, name="ubus_example_base_test", parent=None):
        UVMTest.__init__(self, name, parent)
        self.test_pass = True
        self.ubus_example_tb0 = None
        self.printer = None

    def build_phase(self, phase):
        UVMTest.build_phase(self, phase)
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
            self.uvm_report_fatal("NOVIF", "Could not get vif from config DB")

        #  endfunction : build_phase

    #  function void end_of_elaboration_phase(uvm_phase phase)
    #    // Set verbosity for the bus monitor for this demo
    #     if(ubus_example_tb0.ubus0.bus_monitor != null)
    #       ubus_example_tb0.ubus0.bus_monitor.set_report_verbosity_level(UVM_FULL)
    #    `self.uvm_report_info(get_type_name(),
    #      $sformatf("Printing the test topology :\n%s", this.sprint(printer)), UVM_LOW)
    #  endfunction : end_of_elaboration_phase
    #

    #  task run_phase(uvm_phase phase)
    #    //set a drain-time for the environment if desired
    #    phase.phase_done.set_drain_time(this, 50)
    #  endtask : run_phase

    def extract_phase(self, phase):
        if self.ubus_example_tb0.scoreboard0.sbd_error:
            self.test_pass = False
        if self.ubus_example_tb0.scoreboard0.num_writes == 0:
            self.test_pass = False
        if self.ubus_example_tb0.scoreboard0.num_init_reads == 0:
            self.test_pass = False


    def report_phase(self, phase):
        if self.test_pass:
            self.uvm_report_info(self.get_type_name(), "** UVM TEST PASSED **", UVM_NONE)
        else:
            self.uvm_report_fatal(self.get_type_name(), "** UVM TEST FAIL **")
    #  endfunction

    #endclass : ubus_example_base_test
uvm_component_utils(ubus_example_base_test)

#// Read Modify Write Read Test
#class test_read_modify_write extends ubus_example_base_test
class test_read_modify_write(ubus_example_base_test):

    def __init__(self, name="test_read_modify_write", parent=None):
        ubus_example_base_test.__init__(self, name, parent)

    def build_phase(self, phase):
        UVMConfigDb.set(self, "ubus_example_tb0.ubus0.masters[0].sequencer.run_phase",
                "default_sequence", read_modify_write_seq.type_id.get())
        UVMConfigDb.set(self, "ubus_example_tb0.ubus0.slaves[0].sequencer.run_phase",
                "default_sequence", slave_memory_seq.type_id.get())
        #    // Create the tb
        ubus_example_base_test.build_phase(self, phase)
        #  endfunction : build_phase

    @cocotb.coroutine
    def run_phase(self, phase):
        phase.raise_objection(self)
        master_sqr = self.ubus_example_tb0.ubus0.masters[0].sequencer
        slave_sqr = self.ubus_example_tb0.ubus0.slaves[0].sequencer

        master_seq = read_modify_write_seq("r_mod_w_seq")
        master_proc = cocotb.fork(master_seq.start(master_sqr))

        slave_seq = slave_memory_seq("mem_seq")
        slave_proc = cocotb.fork(slave_seq.start(slave_sqr))
        yield [slave_proc, master_proc.join()]
        phase.drop_objection(self)

    #endclass : test_read_modify_write
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
#
#
#// 2 Master, 4 Slave test
#class test_2m_4s extends ubus_example_base_test
#
#  `uvm_component_utils(test_2m_4s)
#
#  function new(string name = "test_2m_4s", uvm_component parent=null)
#    super.new(name,parent)
#  endfunction : new
#
#  virtual function void build_phase(uvm_phase phase)
#     loop_read_modify_write_seq lrmw_seq
#
#  begin
#    // Overides to the ubus_example_tb build_phase()
#    // Set the topology to 2 masters, 4 slaves
#    uvm_config_db#(int)::set(this,"ubus_example_tb0.ubus0",
#			       "num_masters", 2)
#    uvm_config_db#(int)::set(this,"ubus_example_tb0.ubus0",
#			       "num_slaves", 4)
#
#   // Control the number of RMW loops
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
#
#  function void connect_phase(uvm_phase phase)
#    // Connect other slaves monitor to scoreboard
#    ubus_example_tb0.ubus0.slaves[1].monitor.item_collected_port.connect(
#      ubus_example_tb0.scoreboard0.item_collected_export)
#    ubus_example_tb0.ubus0.slaves[2].monitor.item_collected_port.connect(
#      ubus_example_tb0.scoreboard0.item_collected_export)
#    ubus_example_tb0.ubus0.slaves[3].monitor.item_collected_port.connect(
#      ubus_example_tb0.scoreboard0.item_collected_export)
#  endfunction : connect_phase
#
#  function void end_of_elaboration_phase(uvm_phase phase)
#    // Set up slave address map for ubus0 (slaves[0] is overwritten here)
#    ubus_example_tb0.ubus0.set_slave_address_map("slaves[0]", 16'h0000, 16'h3fff)
#    ubus_example_tb0.ubus0.set_slave_address_map("slaves[1]", 16'h4000, 16'h7fff)
#    ubus_example_tb0.ubus0.set_slave_address_map("slaves[2]", 16'h8000, 16'hBfff)
#    ubus_example_tb0.ubus0.set_slave_address_map("slaves[3]", 16'hC000, 16'hFfff)
#     super.end_of_elaboration_phase(phase)
#  endfunction : end_of_elaboration_phase
#
#endclass : test_2m_4s
