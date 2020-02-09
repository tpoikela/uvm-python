TODO list for UVM examples
==========================

The examples that are converted should be marked into this file. If conversion
has started, mark it as [WIP], or if it works correctly, then mark it [DONE]

DONE
------------------

Add only finished examples here. All tests should be passing and no fatal errors
should occur (unless the purpose of example is to cause uvm_fatal).

### Simple examples ###

[DONE] trivial/
[DONE] basic_examples/event_pool/
[DONE] basic_examples/module/
[DONE] basic_examples/pkg/
[DONE] hello_world/
[DONE] sequence/basic_read_write_sequence/
[DONE] callbacks/
[DONE] factory/
[DONE] interfaces/
[DONE] objections/
[DONE] phases/basic
[DONE] phases/timeout

### Registers ###

[DONE] registers/models/user-defined
[DONE] registers/primer/
[DONE] registers/vertical_reuse
[DONE] configuration/automated
[DONE] configuration/manual

[DONE] tlm1/bidir
[DONE] tlm1/fifo
[DONE] tlm1/hierarchy
[DONE] tlm1/producer_consumer

WIP
------------------

Files in this section are Work in Progress (WIP). This means the example is
being converted into working Python code.


TODO (NOT STARTED)
------------------

### SIMPLE EXAMPLES ###


phases/run_test/Makefile.icarus
phases/run_test/test.sv


### REGISTERS ###

registers/common/any_agent.sv
registers/common/any_config.sv
registers/common/apb/apb_agent.sv
registers/common/apb/apb_master.sv
registers/common/apb/apb_monitor.sv
registers/common/reg_agent.sv

These are not needed by any examples:
registers/common/wishbone/agent.sv
registers/common/wishbone/config.sv
registers/common/wishbone/cycle.sv
registers/common/wishbone/driver.sv
registers/common/wishbone/wb_if.sv
registers/common/wishbone/wishbone.sv

registers/integration/10direct/Makefile.icarus
registers/integration/10direct/tb_env.sv

registers/integration/20layered/Makefile.icarus
registers/integration/20layered/tb_env.sv

registers/integration/common/dut.sv
registers/integration/common/regmodel.sv
registers/integration/common/tb_top.sv
registers/integration/common/test.sv

registers/models/aliasing/Makefile.icarus
registers/models/aliasing/regmodel.sv
registers/models/aliasing/tb_env.sv
registers/models/aliasing/tb_run.sv

registers/models/broadcast/dut.sv
registers/models/broadcast/Makefile.icarus
registers/models/broadcast/regmodel.sv
registers/models/broadcast/tb_env.sv
registers/models/broadcast/tb_run.sv
registers/models/broadcast/tb_top.sv

registers/models/coverage/Makefile.icarus
registers/models/coverage/regmodel.sv
registers/models/coverage/tb_env.sv
registers/models/coverage/tb_run.sv

registers/models/fifo_reg/dut.sv
registers/models/fifo_reg/Makefile.icarus
registers/models/fifo_reg/reg_model.sv
registers/models/fifo_reg/tb_env.sv
registers/models/fifo_reg/tb_run.sv

registers/models/not_yet_implemented/Makefile.icarus
registers/models/not_yet_implemented/regmodel.sv
registers/models/not_yet_implemented/tb_env.sv
registers/models/not_yet_implemented/tb_run.sv

registers/models/reg_without_field/Makefile.icarus
registers/models/reg_without_field/regmodel.sv
registers/models/reg_without_field/tb_env.sv
registers/models/reg_without_field/tb_run.sv

registers/models/ro_wo_same_addr/Makefile.icarus
registers/models/ro_wo_same_addr/regmodel.sv
registers/models/ro_wo_same_addr/tb_env.sv
registers/models/ro_wo_same_addr/tb_run.sv

registers/models/shared_reg/blk_env.sv
registers/models/shared_reg/blk_pkg.sv
registers/models/shared_reg/blk_run.sv
registers/models/shared_reg/blk_seqlib.sv
registers/models/shared_reg/blk_testlib.sv
registers/models/shared_reg/Makefile.icarus
registers/models/shared_reg/reg_B.sv
registers/models/shared_reg/reg_pkg.sv

registers/sequence_api/blk_dut.sv
registers/sequence_api/blk_env.sv
registers/sequence_api/blk_pkg.sv
registers/sequence_api/blk_reg_pkg.sv
registers/sequence_api/blk_run.sv
registers/sequence_api/blk_seqlib.sv
registers/sequence_api/blk_testlib.sv
registers/sequence_api/blk_top.sv
registers/sequence_api/Makefile.icarus
registers/sequence_api/README.txt
registers/sequence_api/reg_B.sv

### TLM2 ###

tlm2/blocking_simple/apb_rw.sv
tlm2/blocking_simple/initiator.sv
tlm2/blocking_simple/Makefile.icarus
tlm2/blocking_simple/target.sv
tlm2/blocking_simple/tb_env.sv
tlm2/blocking_simple/tb_run.sv

tlm2/nonblocking_simple/device.sv
tlm2/nonblocking_simple/host.sv
tlm2/nonblocking_simple/Makefile.icarus
tlm2/nonblocking_simple/README.txt
tlm2/nonblocking_simple/tb_env.sv
tlm2/nonblocking_simple/tb_run.sv
tlm2/nonblocking_simple/usb_xfer.sv

tlm2/temporal_decoupling/apb_rw.sv
tlm2/temporal_decoupling/initiator.sv
tlm2/temporal_decoupling/Makefile.icarus
tlm2/temporal_decoupling/target.sv
tlm2/temporal_decoupling/tb_env.sv
tlm2/temporal_decoupling/tb_run.sv

