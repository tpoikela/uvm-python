
test: test-trivial test-basic_examples test-sequence test-hello_world\
    test-registers test-tlm1 test-configuration test-callbacks test-factory

test-trivial:
	make -C trivial/

test-basic_examples:
	make -C basic_examples/pkg/
	make -C basic_examples/event_pool/
	make -C basic_examples/module/

test-sequence:
	make -C sequence/basic_read_write_sequence/

test-hello_world:
	make -C hello_world/

test-tlm1:
	make -C tlm1/producer_consumer/
	make -C tlm1/hierarchy/
	make -C tlm1/fifo/
	make -C tlm1/bidir/

test-callbacks:
	make -C callbacks/

test-factory:
	make -C factory/

test-configuration:
	make -C configuration/manual/
	make -C configuration/automated/

test-registers:
	make -C registers/models/user-defined/
	make -C registers/vertical_reuse/ IMG=BLK SIMARGS="+UVM_TESTNAME=blk_R_test"
	make -C registers/vertical_reuse/ clean
	make -C registers/vertical_reuse/ SIMARGS="+UVM_TESTNAME=sys_R_test"
	make -C registers/primer/ UVM_TEST=cmdline_test UVM_REG_SEQ=UVMRegHWResetSeq
	make -C registers/primer/ UVM_TEST=cmdline_test UVM_REG_SEQ=user_test_seq
	make -C registers/primer/ UVM_TEST=cmdline_test UVM_REG_SEQ=mem_test_seq
