#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
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
#----------------------------------------------------------------------
"""
Title: UVM Common Phases

The common phases are the set of function and task phases that all
`UVMComponent`s execute together.
All `UVMComponent`s are always synchronized
with respect to the common phases.

The names of the UVM phases (which will be returned by get_name() for a
phase instance) match the class names specified below with the "uvm_"
and "_phase" removed.  For example, the build phase corresponds to the
uvm_build_phase class below and has the name "build", which means that
the following can be used to call foo() at the end of the build phase
(after all lower levels have finished build)::

  def phase_ended(self, phase):
      if (phase.get_name()=="build"):
          self.foo()

The common phases are executed in the sequence they are specified below.
"""

import cocotb

from .uvm_topdown_phase import UVMTopdownPhase
from .uvm_bottomup_phase import UVMBottomupPhase
from .uvm_debug import uvm_debug
from .uvm_task_phase import UVMTaskPhase
#from .uvm_common_phases import *



class UVMBuildPhase(UVMTopdownPhase):
    """
    Class: UVMBuildPhase

    Create and configure of testbench structure
    `UVMTopdownPhase` that calls the `UVMComponent.build_phase` method.

    Upon entry:
      The top-level components have been instantiated under `UVMRoot`.
      Current simulation time is still equal to 0 but some "delta cycles" may have occurred

    Typical Uses:
      Instantiate sub-components.
      Instantiate register model.
      Get configuration values for the component being built.
      Set configuration values for sub-components.

    Exit Criteria:
      All `UVMComponent`s have been instantiated.
    """


    def __init__(self, name="build"):
        UVMTopdownPhase.__init__(self, name)

    def exec_func(self, comp, phase):
        comp.build_phase(phase)

    #local static uvm_build_phase m_inst
    m_inst = None
    type_name = "uvm_build_phase"

    @classmethod
    def get(cls):
        """
        Function: get
        Returns the singleton phase handle

        Returns:
            UVMBuildPhase:
        """
        uvm_debug(cls, 'get', 'called with ' + str(cls))
        if UVMBuildPhase.m_inst is None:
            uvm_debug(cls, 'get', "UVMBuildPhase is none. Returning new class")
            UVMBuildPhase.m_inst = UVMBuildPhase()
        return UVMBuildPhase.m_inst

    def get_type_name(self):
        return UVMBuildPhase.type_name


class UVMConnectPhase(UVMBottomupPhase):
    """
    Establish cross-component connections.

    `UVMBottomupPhase` that calls the
    `UVMComponent.connect_phase` method.

    Upon Entry:
    - All components have been instantiated.
    - Current simulation time is still equal to 0
      but some "delta cycles" may have occurred.

    Typical Uses:
    - Connect TLM ports and exports.
    - Connect TLM initiator sockets and target sockets.
    - Connect register model to adapter components.
    - Setup explicit phase domains.

    Exit Criteria:
    - All cross-component connections have been established.
    - All independent phase domains are set.

    """
    def exec_func(self, comp, phase):
        comp.connect_phase(phase)

    m_inst = None
    type_name = "uvm_connect_phase"

    @classmethod
    def get(cls):
        """
        Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMConnectPhase.m_inst is None:
            UVMConnectPhase.m_inst = UVMConnectPhase()
        return UVMConnectPhase.m_inst

    def __init__(self, name="connect"):
        UVMBottomupPhase.__init__(self, name)

    def get_type_name(self):
        return UVMConnectPhase.type_name


class UVMEndOfElaborationPhase(UVMBottomupPhase):
    """
    Fine-tune the testbench.

    `UVMBottomupPhase` that calls the
    `UVMComponent.end_of_elaboration_phase` method.

    Upon Entry:
    - The verification environment has been completely assembled.
    - Current simulation time is still equal to 0
      but some "delta cycles" may have occurred.

    Typical Uses:
    - Display environment topology.
    - Open files.
    - Define additional configuration settings for components.

    Exit Criteria:
    - None.
    """
    def exec_func(self, comp, phase):
        comp.end_of_elaboration_phase(phase)

    m_inst = None
    type_name = "uvm_end_of_elaboration_phase"

    @classmethod
    def get(cls):
        """
        Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMEndOfElaborationPhase.m_inst is None:
            UVMEndOfElaborationPhase.m_inst = UVMEndOfElaborationPhase()
        return UVMEndOfElaborationPhase.m_inst

    def __init__(self, name="end_of_elaboration"):
        UVMBottomupPhase.__init__(self, name)

    def get_type_name(self):
        return UVMEndOfElaborationPhase.type_name


class UVMStartofSimulationPhase(UVMBottomupPhase):
    """
    Get ready for DUT to be simulated.

    `UVMBottomupPhase` that calls the
    `UVMComponent.start_of_simulation_phase` method.

    Upon Entry:
      - Other simulation engines, debuggers, hardware assisted platforms and
        all other run-time tools have been started and synchronized.
      - The verification environment has been completely configured
        and is ready to start.
      - Current simulation time is still equal to 0
        but some "delta cycles" may have occurred.

    Typical Uses:
      - Display environment topology
      - Set debugger breakpoint
      - Set initial run-time configuration values.

    Exit Criteria:
      - None.
    """

    def __init__(self, name="start_of_simulation"):
        UVMBottomupPhase.__init__(self, name)

    def exec_func(self, comp, phase):
        comp.start_of_simulation_phase(phase)

    m_inst = None  # uvm_start_of_simulation_phase
    type_name = "uvm_start_of_simulation_phase"

    @classmethod
    def get(cls):
        """
        Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMStartofSimulationPhase.m_inst is None:
            UVMStartofSimulationPhase.m_inst = UVMStartofSimulationPhase()
        return UVMStartofSimulationPhase.m_inst

    def get_type_name(self):
        return UVMStartofSimulationPhase.type_name
    #endclass



class UVMRunPhase(UVMTaskPhase):
    """
    Stimulate the DUT.

    This `UVMTaskPhase` calls the
    `UVMComponent.run_phase` virtual method. This phase runs in
    parallel to the runtime phases, `UVMPreResetPhase` through
    `UVMPostShutdownPhase`. All components in the testbench
    are synchronized with respect to the run phase regardless of
    the phase domain they belong to.

    Upon Entry:
    - Indicates that power has been applied.
    - There should not have been any active clock edges before entry
      into this phase (e.g. x->1 transitions via initial blocks).
    - Current simulation time is still equal to 0
      but some "delta cycles" may have occurred.

    Typical Uses:
    - Components implement behavior that is exhibited for the entire
      run-time, across the various run-time phases.
    - Backward compatibility with OVM.

    Exit Criteria:
    - The DUT no longer needs to be simulated, and
    - The <uvm_post_shutdown_phase> is ready to end

    The run phase terminates in one of two ways.

    1. All run_phase objections are dropped:

      When all objections on the run_phase objection have been dropped,
      the phase ends and all of its threads are killed.
      If no component raises a run_phase objection immediately upon
      entering the phase, the phase ends immediately.


    2. Timeout:

      The phase ends if the timeout expires before all objections are dropped.
      By default, the timeout is set to 9200 seconds.
      You may override this via <uvm_root::set_timeout>.

      If a timeout occurs in your simulation, or if simulation never
      ends despite completion of your test stimulus, then it usually indicates
      that a component continues to object to the end of a phase.
    """


    async def exec_task(self, comp, phase):
        uvm_debug(self, 'exec_task', comp.get_name() + ' yielding comp.run_phase()')
        # tpoikela, modification  of original to allow handle for proc
        #yield comp.run_phase(phase)
        comp.m_run_process = cocotb.fork(comp.run_phase(phase))
        await comp.m_run_process

        #parent = comp.get_parent()
        #if parent is not None and parent.get_name() == '__top__':
        #    for i in range(10):
        #        yield Timer(0, "NS")
        #else:
        #    if parent is not None:
        #            comp.get_name())
        uvm_debug(self, 'exec_task', comp.get_name() + ' returned from comp.run_phase()')

    m_inst = None  # static uvm_run_phase
    type_name = "uvm_run_phase"

    @classmethod
    def get(cls):
        """
          Function: get
          Returns the singleton phase handle
        Returns:
        """
        if UVMRunPhase.m_inst is None:
            UVMRunPhase.m_inst = UVMRunPhase()
        return UVMRunPhase.m_inst

    def __init__(self, name="run"):
        UVMTaskPhase.__init__(self, name)

    def get_type_name(self):
        return UVMRunPhase.type_name


class UVMExtractPhase(UVMBottomupPhase):
    """
    Extract data from different points of the verification environment.

    `UVMBottomupPhase` that calls the
    `UVMComponent.extract_phase` method.

    Upon Entry:
    - The DUT no longer needs to be simulated.
    - Simulation time will no longer advance.

    Typical Uses:
    - Extract any remaining data and final state information
      from scoreboard and testbench components
    - Probe the DUT (via zero-time hierarchical references
      and/or backdoor accesses) for final state information.
    - Compute statistics and summaries.
    - Display final state information
    - Close files.

    Exit Criteria:
    - All data has been collected and summarized.
    """

    def exec_func(self, comp, phase):
        comp.extract_phase(phase)

    m_inst = None  # uvm_extract_phase
    type_name = "uvm_extract_phase"

    @classmethod
    def get(cls):
        """
        Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMExtractPhase.m_inst is None:
            UVMExtractPhase.m_inst = UVMExtractPhase()
        return UVMExtractPhase.m_inst

    def __init__(self, name="extract"):
        UVMBottomupPhase.__init__(self, name)

    def get_type_name(self):
        return UVMExtractPhase.type_name


class UVMCheckPhase(UVMBottomupPhase):
    """
    Check for any unexpected conditions in the verification environment.

    `UVMBottomupPhase` that calls the
    `UVMComponent.check_phase` method.

    Upon Entry:
    - All data has been collected.

    Typical Uses:
    - Check that no unaccounted-for data remain.

    Exit Criteria:
    - Test is known to have passed or failed.
    """


    def exec_func(self, comp, phase):
        comp.check_phase(phase)

    m_inst = None  # uvm_check_phase

    type_name = "uvm_check_phase"

    @classmethod
    def get(cls):
        """     Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMCheckPhase.m_inst is None:
            UVMCheckPhase.m_inst = UVMCheckPhase()
        return UVMCheckPhase.m_inst

    def __init__(self, name="check"):
        UVMBottomupPhase.__init__(self, name)

    def get_type_name(self):
        return UVMCheckPhase.type_name


class UVMReportPhase(UVMBottomupPhase):
    """
    Report results of the test.

    `UVMBottomupPhase` that calls the
    `UVMComponent.report_phase` method.

    Upon Entry:
    - Test is known to have passed or failed.

    Typical Uses:
    - Report test results.
    - Write results to file.

    Exit Criteria:
    - End of test.
    """

    def exec_func(self, comp, phase):
        comp.report_phase(phase)

    m_inst = None  # uvm_report_phase

    type_name = "uvm_report_phase"

    @classmethod
    def get(cls):
        """     Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMReportPhase.m_inst is None:
            UVMReportPhase.m_inst = UVMReportPhase()
        return UVMReportPhase.m_inst

    def __init__(self, name="report"):
        UVMBottomupPhase.__init__(self, name)

    def get_type_name(self):
        return UVMReportPhase.type_name


class UVMFinalPhase(UVMBottomupPhase):
    """
    Tie up loose ends.

    `UVMTopdownPhase` that calls the
    `UVMComponent.final_phase` method.

    Upon Entry:
    - All test-related activity has completed.

    Typical Uses:
    - Close files.
    - Terminate co-simulation engines.

    Exit Criteria:
    - Ready to exit simulator.
    """

    def exec_func(self, comp, phase):
        comp.final_phase(phase)

    m_inst = None  # static uvm_final_phase

    type_name = "uvm_final_phase"

    @classmethod
    def get(cls):
        """     Function: get
        Returns the singleton phase handle
        Returns:
        """
        if UVMFinalPhase.m_inst is None:
            UVMFinalPhase.m_inst = UVMFinalPhase()
        return UVMFinalPhase.m_inst

    def __init__(self, name="final"):
        UVMBottomupPhase.__init__(self, name)

    def get_type_name(self):
        return UVMFinalPhase.type_name
