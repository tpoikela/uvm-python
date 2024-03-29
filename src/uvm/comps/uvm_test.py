#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http:#www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#------------------------------------------------------------------------------


from ..base.uvm_component import UVMComponent

class UVMTest(UVMComponent):
    """
    This class is the virtual base class for the user-defined tests.

    The `UVMTest` class should be used as the base class for user-defined
    tests. Doing so provides the ability to select which test to execute using
    the UVM_TESTNAME command line or argument to the `UVMRoot.run_test` task.

    For example

    .. code-block:: shell

      prompt> SIM_COMMAND +UVM_TESTNAME=test_bus_retry

    The global run_test() task should be specified inside a function decorated
    with `@cocotb.test()` (the parentheses are important!) such as

    .. code-block:: python
        import cocotb
        from uvm import run_test
        @cocotb.test()
        def initial(dut):
            await run_test();

    Multiple tests, identified by their type name, can be
    selected for execution from the command line.
    Random seed selection is also available on the command line.

    If +UVM_TESTNAME=test_name is specified, then an object of type 'test_name'
    is created by factory and phasing begins. Here, it is presumed that the
    test will instantiate the test environment, or the test environment will
    have already been instantiated before the call to `run_test()`.

    If the specified test_name cannot be created by the `UVMFactory`, then a
    fatal error occurs. If run_test() is called without UVM_TESTNAME being
    specified, then all components constructed before the call to run_test will
    be cycled through their simulation phases.

    Deriving from `UVMTest` will allow you to distinguish tests from other
    component types that inherit from `UVMComponent` directly. Such tests will
    automatically inherit features that may be added to uvm_test in the future.
    """

    type_name = "uvm_test"

    # Function: new
    #
    # Creates and initializes an instance of this class using the normal
    # constructor arguments for <uvm_component>: ~name~ is the name of the
    # instance, and ~parent~ is the handle to the hierarchical parent, if any.
    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)

    def get_type_name(self):
      return UVMTest.type_name
