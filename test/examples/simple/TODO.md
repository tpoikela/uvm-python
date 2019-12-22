TODO list for UVM examples
==========================

The examples that are converted should be marked into this file. If conversion
has started, mark it as [WIP], or if it works correctly, then mark it [DONE]

DONE
------------------

Add only finished examples here. All tests should be passing and no fatal errors
should occur (unless the purpose of example is to cause uvm_fatal).

[DONE] trivial/
[DONE] basic_examples/event_pool/
[DONE] basic_examples/module/
[DONE] sequence/basic_read_write_sequence/

[DONE] registers/models/

WIP
------------------

Files in this section are Work in Progress (WIP). This means the example is
being converted into working Python code.

[WIP] basic_examples/pkg/

[WIP] hello_world/consumer.sv
[WIP] hello_world/hello_world.sv
[WIP] hello_world/packet.sv
[WIP] hello_world/producer.sv
[WIP] hello_world/top.sv

[WIP2] registers/primer/cmdline_test.sv
[WIP2] registers/primer/dut.sv
[WIP2] registers/primer/primer.pdf
[WIP2] registers/primer/reg_model.sv
[WIP2] registers/primer/tb_env.sv
[WIP2] registers/primer/tb_top.sv
[WIP2] registers/primer/testlib.sv
[WIP2] registers/primer/test.sv
[WIP2] registers/primer/user_test.sv

TODO (NOT STARTED)
------------------

callbacks/Makefile.icarus
callbacks/top.sv

configuration/automated/classA.svh
configuration/automated/classB.svh
configuration/automated/classC.svh
configuration/automated/Makefile.icarus
configuration/automated/my_env_pkg.sv
configuration/automated/top.sv
configuration/manual/classA.svh
configuration/manual/classB.svh
configuration/manual/classC.svh
configuration/manual/Makefile.icarus
configuration/manual/my_env_pkg.sv
configuration/manual/top.sv

factory/env_pkg.sv
factory/gen_pkg.sv
factory/Makefile.icarus
factory/packet_pkg.sv
factory/test.sv

interfaces/interface.sv
interfaces/Makefile.icarus

objections/Makefile.icarus
objections/simple.sv

phases/basic/Makefile.icarus
phases/basic/test.sv

phases/run_test/Makefile.icarus
phases/run_test/test.sv

phases/timeout/Makefile.icarus
phases/timeout/tb_env.svh
phases/timeout/tb_timer.svh
phases/timeout/test.sv

README.txt

registers/common/any_agent.sv
registers/common/any_config.sv
registers/common/apb/apb_agent.sv
registers/common/apb/apb_master.sv
registers/common/apb/apb_monitor.sv
registers/common/reg_agent.sv
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

registers/vertical_reuse/blk_dut.sv
registers/vertical_reuse/blk_env.sv
registers/vertical_reuse/blk_pkg.sv
registers/vertical_reuse/blk_reg_pkg.sv
registers/vertical_reuse/blk_run.sv
registers/vertical_reuse/blk_seqlib.sv
registers/vertical_reuse/blk_testlib.sv
registers/vertical_reuse/blk_top.sv
registers/vertical_reuse/Makefile.icarus
registers/vertical_reuse/reg_B.sv
registers/vertical_reuse/reg_S.sv
registers/vertical_reuse/sys_dut.sv
registers/vertical_reuse/sys_env.sv
registers/vertical_reuse/sys_pkg.sv
registers/vertical_reuse/sys_reg_pkg.sv
registers/vertical_reuse/sys_run.sv
registers/vertical_reuse/sys_seqlib.sv
registers/vertical_reuse/sys_testlib.sv
registers/vertical_reuse/sys_top.sv

tlm1/bidir/bidir.sv
tlm1/bidir/Makefile.icarus

tlm1/fifo/Makefile.icarus
tlm1/fifo/test.sv

tlm1/hierarchy/hierarchy.sv
tlm1/hierarchy/Makefile.icarus

tlm1/producer_consumer/fifo.sv
tlm1/producer_consumer/Makefile.icarus

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

callbacks:
Makefile.icarus
top.sv

configuration:
automated
manual

configuration/automated:
classA.svh
classB.svh
classC.svh
Makefile.icarus
my_env_pkg.sv
top.sv

configuration/manual:
classA.svh
classB.svh
classC.svh
Makefile.icarus
my_env_pkg.sv
top.sv

factory:
env_pkg.sv
gen_pkg.sv
Makefile.icarus
packet_pkg.sv
test.sv

hello_world:
consumer.sv
hello_world.sv
Makefile.icarus
packet.sv
producer.sv
top.sv

interfaces:
interface.sv
Makefile.icarus

objections:
Makefile.icarus
simple.sv

phases:
basic
run_test
timeout

phases/basic:
Makefile.icarus
test.sv

phases/run_test:
Makefile.icarus
test.sv

phases/timeout:
Makefile.icarus
tb_env.svh
tb_timer.svh
test.sv

registers:
common
integration
models
primer
sequence_api
vertical_reuse

registers/common:
any_agent.sv
any_config.sv
apb
reg_agent.sv
wishbone

registers/common/apb:
apb_agent.sv
apb_master.sv
apb_monitor.sv

registers/common/wishbone:
agent.sv
config.sv
cycle.sv
driver.sv
wb_if.sv
wishbone.sv

registers/integration:
10direct
20layered
common

registers/integration/10direct:
Makefile.icarus
tb_env.sv

registers/integration/20layered:
Makefile.icarus
tb_env.sv

registers/integration/common:
dut.sv
regmodel.sv
tb_top.sv
test.sv

registers/models:
aliasing
broadcast
coverage
fifo_reg
not_yet_implemented
reg_without_field
ro_wo_same_addr
shared_reg
user-defined

registers/models/aliasing:
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv

registers/models/broadcast:
dut.sv
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv
tb_top.sv

registers/models/coverage:
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv

registers/models/fifo_reg:
dut.sv
Makefile.icarus
reg_model.sv
tb_env.sv
tb_run.sv

registers/models/not_yet_implemented:
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv

registers/models/reg_without_field:
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv

registers/models/ro_wo_same_addr:
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv

registers/models/shared_reg:
blk_env.sv
blk_pkg.sv
blk_run.sv
blk_seqlib.sv
blk_testlib.sv
Makefile.icarus
reg_B.sv
reg_pkg.sv

registers/models/user-defined:
dut.sv
Makefile.icarus
regmodel.sv
tb_env.sv
tb_run.sv

registers/primer:
cmdline_test.sv
dut.sv
Makefile.icarus
primer.pdf
reg_model.sv
tb_env.sv
tb_top.sv
testlib.sv
test.sv
user_test.sv

registers/sequence_api:
blk_dut.sv
blk_env.sv
blk_pkg.sv
blk_reg_pkg.sv
blk_run.sv
blk_seqlib.sv
blk_testlib.sv
blk_top.sv
Makefile.icarus
README.txt
reg_B.sv

registers/vertical_reuse:
blk_dut.sv
blk_env.sv
blk_pkg.sv
blk_reg_pkg.sv
blk_run.sv
blk_seqlib.sv
blk_testlib.sv
blk_top.sv
Makefile.icarus
reg_B.sv
reg_S.sv
sys_dut.sv
sys_env.sv
sys_pkg.sv
sys_reg_pkg.sv
sys_run.sv
sys_seqlib.sv
sys_testlib.sv
sys_top.sv

tlm1:
bidir
fifo
hierarchy
producer_consumer

tlm1/bidir:
bidir.sv
Makefile.icarus

tlm1/fifo:
Makefile.icarus
test.sv

tlm1/hierarchy:
hierarchy.sv
Makefile.icarus

tlm1/producer_consumer:
fifo.sv
Makefile.icarus

tlm2:
blocking_simple
nonblocking_simple
temporal_decoupling

tlm2/blocking_simple:
apb_rw.sv
initiator.sv
Makefile.icarus
target.sv
tb_env.sv
tb_run.sv

tlm2/nonblocking_simple:
device.sv
host.sv
Makefile.icarus
README.txt
tb_env.sv
tb_run.sv
usb_xfer.sv

tlm2/temporal_decoupling:
apb_rw.sv
initiator.sv
Makefile.icarus
target.sv
tb_env.sv
tb_run.sv

trivial:
component.sv
Makefile.icarus
