![Build](https://github.com/tpoikela/uvm-python/workflows/Build/badge.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/tpoikela/uvm-python/badge.svg?branch=master)](https://coveralls.io/github/tpoikela/uvm-python?branch=master)

UVM library for Python
======================

This is a port of SystemVerilog (SV) Universal Verification Methodology (UVM)
1.2 to Python and cocotb. Only Icarus Verilog (iverilog) has been used for
testing the code so
far, but the plan is to include verilator in the regressions as well.

Why bother?
-----------

UVM is not currently supported by any open source/free tools. cocotb offers
excellent solution to interact with any simulator (free/commercial), so
testbenches can be written in Python as well. `uvm-python` tries to offer
an API similar to the original SV version. This means that many UVM verificaton
skills are transferable from SV to Python very easily.

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
| TLM2.0     | Started, 1st example working                              |
| Components | Done                                                      |
| Phases     | Done                                                      |
| Sequences  | Partially done, hier sequences work                       |
| Registers  | Reg/mem access working, built-in sequences partially done |

NOTE: Despite the working state, the project is under development, and still
missing a lot of functionality. Please try it out, and let me know if
something you require should be added, or even better, add it yourself, test it
and create a pull request!

Installation
------------

You can install uvm-python as a normal Python package:

```shell
git clone https://github.com/tpoikela/uvm-python.git
cd uvm-python
python -m pip install --user .  # Omit --user for global installation
```

See `Makefile` for working examples. You can use Makefiles in `test/examples` as a
template for your project.

Development and Running the examples
------------------------------------

See `Makefile` for working examples. More features/examples will be added
incrementally.

To run all tests:
```shell
    SIM=icarus make test  # Use iverilog as a simulator
```

To run unit tests only:
```
    make test-unit  # Does not require simulator
```

HDL Simulators
--------------

Icarus Verilog (iverilog v11.0) and verilator (v4.020+) are free simulators, which can
be used with cocotb. uvm-python uses cocotb to interface with these simulators.

Commercial simulators that work with cocotb can of course be used with
uvm-python as well.
