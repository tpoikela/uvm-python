UVM library for Python
======================

This is a port of SystemVerilog (SV) Universal Verification Methodology (UVM)
1.2 to Python and cocotb. Only Icarus Verilog (iverilog) has been used for
testing the code so
far, but the plan is to include verilator in ther regressions as well.

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
memories (frontdoor and backdoor). TLM 1.0 is fully implemented.

NOTE: Despite the working state, the project is under development, and still
missing lot of functionality. But please try it out, and let me know if
something you require should be added, or even better, add it yourself, test it
and create a pull request!

Running and examples
--------------------

See `Makefile` for working examples. More features/examples will be added
incrementally.

To run all tests:
```
    make test
```

