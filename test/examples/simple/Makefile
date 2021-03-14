
test: test-trivial test-basic_examples test-sequence test-interfaces test-hello_world\
    test-registers test-tlm1 test-configuration test-callbacks test-factory\
    test-objections test-phases test-tlm2 test-cmdline test-reporting test-comps

test-trivial:
	make -C trivial/

test-basic_examples:
	make -C basic_examples/pkg/
	make -C basic_examples/event_pool/
	make -C basic_examples/module/

test-interfaces:
	make -C interfaces/

test-sequence:
	make -C sequence/basic_read_write_sequence/

test-hello_world:
	make -C hello_world/
	make -C hello_world/ UVM_TEST=top2

test-objections:
	make -C objections/

test-phases:
	make -C phases/basic/
	make -C phases/timeout/

test-tlm1:
	make -C tlm1/producer_consumer/
	make -C tlm1/hierarchy/
	make -C tlm1/fifo/
	make -C tlm1/bidir/
ifneq ($(SIM), verilator)
	make -C tlm1/master_slave/
endif

test-tlm2:
	make -C tlm2/blocking_simple/
	make -C tlm2/nonblocking_simple/

test-callbacks:
	make -C callbacks/

test-reporting:
	make -C reporting/

test-comps:
	make -C comps/comparator

test-cmdline:
	make -C cmdline/
	make -C cmdline/ UVM_TEST=TestMaxQuitCount

test-factory:
	make -C factory/

test-configuration:
	make -C configuration/manual/
	make -C configuration/automated/

test-registers:
	make -C registers/models/user-defined/
	make -C registers/vertical_reuse/ IMG=BLK UVM_TEST=blk_R_test SIM_BUILD=sim_build_blk
	make -C registers/vertical_reuse/ UVM_TEST=sys_R_test SIM_BUILD=sim_build_sys
	make -C registers/primer/ UVM_TEST=cmdline_test UVM_REG_SEQ=UVMRegHWResetSeq
	make -C registers/primer/ UVM_TEST=cmdline_test UVM_REG_SEQ=user_test_seq
	make -C registers/primer/ UVM_TEST=cmdline_test UVM_REG_SEQ=mem_test_seq
	make -C registers/models/coverage/
ifneq ($(SIM), verilator)
	make -C registers/integration/10direct/
endif
	make -C registers/models/fifo_reg/
