UVM library for Python
======================

This is a port of Universal Verification Methodology (UVM) 1.2 to Python and
cocotb. Only Icarus Verilog (iverilog) has been used for testing the code so
far, but the plan is to include verilator in ther regressions as well.

Current status: Testbenches can already be written with all the typical UVM 
components. UVM Phasing is in place, and working. Stimulus can be generated
using hierarchical sequences. Register
layer supports already read/write to registers (via frontdoor), and to 
memories (frontdoor and backdoor). TLM 1.0 is fully implemented.

NOTE: Despite the working state, the project is under development, and still
missing lot of functionality. But please try it out, and let me know if
something you require should be added, or even better, add it yourself, test it
and create a pull request!

See `Makefile` for working examples. More features will be added incrementally.

To run all tests:
```
    make test
```

