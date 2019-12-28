
ifeq ($(TEST), )
    UNIT_ARGS = unit/*.py
else
    UNIT_ARGS = unit.$(TEST)
endif

test: test-simple test-integrated test-unit

test-simple:
	make -C test/examples/simple

test-integrated:
	make -C test/examples/integrated

test-unit:
	python -m unittest $(UNIT_ARGS)
