
ifeq ($(TEST), )
    UNIT_ARGS = unit/*.py
else
    UNIT_ARGS = unit.$(TEST)
endif

test: test-unit test-minimal test-simple test-integrated test-sim-integration
	find test/examples -name results*.xml -exec cat {} \; > results.log
	bash ci/check_errors.sh

test-minimal:
	make -C test/examples/minimal

test-simple:
	make -C test/examples/simple

test-integrated:
ifneq ($(SIM), verilator)
	make -C test/examples/integrated
endif

test-unit:
	python -m unittest $(UNIT_ARGS)

test-sim-integration:
	make -C test/sim_integration MODULE=test_uvm_events
	make -C test

lint:
	flake8 ./uvm --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 ./uvm --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Target for unit test coverage
cov:
	coverage run --include='src/uvm/**/*.py' -m unittest $(UNIT_ARGS)
	coverage html
	# Requires coveralls installation, .coveralls.yml and repo_token
	coveralls

cov-all:
	# Need to run unit tests separately for this
	coverage run -m unittest unit/*.py
	COVERAGE=1 COVERAGE_RCFILE=$(PWD)/.coveragerc make test
	find -name '.coverage.*' | xargs coverage combine  # Merge cov from all tests
	COVERAGE_RCFILE=$(PWD)/.coveragerc coverage html

# Target to clean up the sim directories, logfiles etc
clean:
	find test/ -name 'sim_build*' -exec rm -rf {} \;
	find test/ -name 'results*.xml' -exec rm -vf {} \;

stubgen:
	stubgen .venv/lib/python3.7/site-packages/cocotb_coverage
	stubgen ../cocotb/cocotb

typecheck:
	mypy src ./out/*

pytype:
	pytype --config=./pytype.cfg
