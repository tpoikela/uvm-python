
test: test-simple test-integrated test-unit

test-simple:
	make -C test/examples/simple

test-integrated:
	make -C test/examples/integrated

test-unit:
	python -m unittest unit/*.py
