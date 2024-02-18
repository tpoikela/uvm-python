![Build](https://github.com/tpoikela/uvm-python/workflows/Build/badge.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/tpoikela/uvm-python/badge.svg?branch=master)](https://coveralls.io/github/tpoikela/uvm-python?branch=master)
[![PyPI version](https://badge.fury.io/py/uvm-python.svg)](https://badge.fury.io/py/uvm-python)

UVM library for Python
======================

uvm-python is a Python and cocotb-based port of the SystemVerilog Universal
Verification Methodology (UVM) 1.2. The code has been extensively tested using
Icarus Verilog (iverilog) and Verilator.

Currently, there are no open source/free tools available for working with
SystemVerilog UVM. However, with the use of cocotb, testbenches can be written
in Python, making it possible to work with both free and proprietary simulators.
The uvm-python package offers an API that is similar to the original SV-UVM
version, making it easy for users to transfer their UVM verification skills and
API knowledge from SV to Python.

For those looking to port a larger amount of SystemVerilog code to use
uvm-python, the package includes a regex-based script, `bin/sv2py.pl`, that can be
used as a starting point. However, note that significant manual edits may still
be required to ensure the code works correctly.

For more information, please refer to the `uvm-python` documentation and user's
guide.

Documentation:
  - [uvm-python Documentation](https://uvm-python.readthedocs.io/).
  - [uvm-python User's Guide](https://uvm-python.readthedocs.io/en/latest/uvm_users_guide_1.2.html)

Documentation
-------------

The documentation is available on `readthedocs.io` in
[uvm-python HTML documentation](https://uvm-python.readthedocs.io/).

Installation
------------

You can install uvm-python as a normal Python package. It is recommended to use
[venv](https://docs.python.org/3/library/venv.html) to create a virtual
environment for Python prior to installation.

Install from PyPi using pip:
```shell
python -m pip install uvm-python
```

or directly from source files (for the latest development version):

```shell
git clone https://github.com/tpoikela/uvm-python.git
cd uvm-python
python -m pip install . # If venv is used
# Or without venv, and no sudo:
python -m pip install --user .  # Omit --user for global installation
```

See [Makefile](test/examples/simple/Makefile) for working examples. You can
also use Makefiles in `test/examples/simple` as a
template for your project.

Running the examples and development
------------------------------------

See `test/examples/simple/Makefile` for working examples. More features/examples will be added
incrementally.

To run all tests:
```shell
    SIM=icarus make test  # Use iverilog as a simulator
```

To run unit tests only:
```
    make test-unit  # Does not require simulator
```

### Minimal working example ###

`uvm-python` must be installed prior to running the example. Alternatively, you
can create a symlink to the `uvm` source folder:

```shell
cd test/examples/minimal
ln -s ../../../src/uvm uvm
SIM=icarus make
```

You can find the
source code for this example [here](test/examples/minimal). This example
creates a test component, registers it with the UVM factory, and starts the test.

You can execute the example by running `SIM=icarus make`. Alternatively, you can
run it with `SIM=verilator make`.

```make
# File: Makefile
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES ?= new_dut.sv
TOPLEVEL := new_dut
MODULE   ?= new_test
include $(shell cocotb-config --makefiles)/Makefile.sim
```

The top-level module must match `TOPLEVEL` in `Makefile`:

```verilog
// File: new_dut.sv
module new_dut(input clk, input rst, output[7:0] byte_out);
    assign byte_out = 8'hAB;
endmodule: new_dut
```

The Python test file name must match `MODULE` in `Makefile`:

```python
# File: new_test.py
import cocotb
from cocotb.triggers import Timer
from uvm import *

@uvm_component_utils
class NewTest(UVMTest):

    async def run_phase(self, phase: UVMPhase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        uvm_info("NEW_TEST", "Test passed, all OK", UVM_MEDIUM)
        phase.drop_objection(self)


@cocotb.test()
async def test_dut(dut):
    await run_test('NewTest')
```

Current status
--------------

Testbenches can already be written with all the typical UVM 
components. UVM Phasing is in place, and working. Stimulus can be generated
using (even hierarchical) sequences. Register
layer supports already read/write to registers (via frontdoor), and to 
memories (frontdoor and backdoor). TLM 1.0 is implemented,
put/get/analysis interfaces are done, and master/slave interfaces work. Initial
implementation of TLM2.0 has also been added. The table below summarizes the
status:

| Feature    | Status                                                    |
| ---------  | ------                                                    |
| TLM1.0     | Done                                                      |
| TLM2.0     | Done                                                      |
| Components | Done                                                      |
| Phases     | Done                                                      |
| Objections | Test and env-level objections work                        |
| Sequences  | Partially done, hier sequences work                       |
| Registers  | Reg/mem access working, built-in sequences partially done |

Please try it out, and let me know if
something you require should be added, or even better, add it yourself, test it
and create a pull request!

HDL Simulators
--------------

Tested with Icarus Verilog (iverilog v13.0 (devel)) and verilator (v5.008). The
exact commit for iverilog can be found from `ci/install_iverilog.sh`.

Icarus Verilog and verilator are free simulators, which can
be used with cocotb. uvm-python uses cocotb to interface with these simulators.
Memory backdoor access has issues with packed multi-dimensional arrays in
verilator. Also, some other examples are not working with verilator yet.

Proprietary simulators that work with cocotb should work with
uvm-python as well, but haven't been tested.

Related projects
----------------

  - [cocotb](https://github.com/cocotb/cocotb) cosimulation library for writing testbenches in Python
  - [uvm-python-verification-lib](https://github.com/jg-fossh/uvm-python-verification-lib) UVM Python Verification Agents Library
