![Build](https://github.com/tpoikela/uvm-python/workflows/Build/badge.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/tpoikela/uvm-python/badge.svg?branch=master)](https://coveralls.io/github/tpoikela/uvm-python?branch=master)
[![PyPI version](https://badge.fury.io/py/uvm-python.svg)](https://badge.fury.io/py/uvm-python)

UVM library for Python
======================

This is a port of SystemVerilog (SV) Universal Verification Methodology (UVM)
1.2 to Python and cocotb. Only Icarus Verilog (iverilog) has been used for
testing the code so
far, but the plan is to include verilator in the regressions as well.

See documentation for more details:
  - [uvm-python Documentation](https://uvm-python.readthedocs.io/).
  - [uvm-python User's Guide](https://uvm-python.readthedocs.io/en/latest/uvm_users_guide_1.2.html)

Why bother?
-----------

UVM is not currently supported by any open source/free tools. cocotb offers
excellent solution to interact with any simulator (free/proprietary), so
testbenches can be written in Python as well. `uvm-python` tries to offer
an API similar to the original SV version. This means that many UVM verificaton
skills are transferable from SV to Python very easily.

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

or directly from source files (for latest development version):

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

class NewTest(UVMTest):

    async def run_phase(self, phase):
        phase.raise_objection(self)
        await Timer(100, "NS")
        phase.drop_objection(self)

uvm_component_utils(NewTest)

@cocotb.test()
async def test_dut(dut):
    await run_test('NewTest')
```

Current status
--------------
Current status: Testbenches can already be written with all the typical UVM 
components. UVM Phasing is in place, and working. Stimulus can be generated
using hierarchical sequences. Register
layer supports already read/write to registers (via frontdoor), and to 
memories (frontdoor and backdoor). TLM 1.0 is implemented,
put/get/analysis interfaces are done, and master/slave interfaces work. Initial
implementation of TLM2.0 has also been added. The table below summarizes the
status:

| Feature    | Status                                                    |
| ---------  | ------                                                    |
| TLM1.0     | Done                                                      |
| TLM2.0     | Started, 2/3 examples working                             |
| Components | Done                                                      |
| Phases     | Done                                                      |
| Sequences  | Partially done, hier sequences work                       |
| Registers  | Reg/mem access working, built-in sequences partially done |

NOTE: Despite many working examples, the project is under development, and still
missing a lot of functionality. Please try it out, and let me know if
something you require should be added, or even better, add it yourself, test it
and create a pull request!


HDL Simulators
--------------

Icarus Verilog (iverilog v11.0) and verilator (v4.030+) are free simulators, which can
be used with cocotb. uvm-python uses cocotb to interface with these simulators.
Memory backdoor access has issues with packed multi-dimensional arrays in
verilator.

Proprietary simulators that work with cocotb can of course be used with
uvm-python as well.
