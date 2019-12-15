
test: test-trivial test-basic_examples test-sequence test-hello_world test-registers

test-trivial:
	make -C trivial

test-basic_examples:
	make -C basic_examples/pkg
	make -C basic_examples/event_pool
	make -C basic_examples/module

test-sequence:
	make -C sequence/basic_read_write_sequence

test-hello_world:
	make -C hello_world/

test-registers:
	make -C registers/models/user-defined
