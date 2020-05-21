#
#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#----------------------------------------------------------------------

from .uvm_phase import UVMPhase
from .uvm_object_globals import (UVM_DEBUG, UVM_PHASE_ENDED, UVM_PHASE_EXECUTING, UVM_PHASE_IMP,
                                 UVM_PHASE_READY_TO_END, UVM_PHASE_STARTED)
from .uvm_domain import UVMDomain
from .uvm_debug import uvm_debug
from .uvm_globals import uvm_report_fatal, uvm_report_info


class UVMBottomupPhase(UVMPhase):
    """
    Base class for function phases that operate bottom-up.
    The pure virtual function execute() is called for each component.
    This is the default traversal so is included only for naming.

    A bottom-up function phase completes when the <execute()> method
    has been called and returned on all applicable components
    in the hierarchy.
    """


    def __init__(self, name):
        """
        Create a new instance of a bottom-up phase.

        Args:
            name (str): Name of the phase.
        """
        UVMPhase.__init__(self, name, UVM_PHASE_IMP)


    def traverse(self, comp, phase, state):
        """
        Traverses the component tree in bottom-up order, calling `execute` for
        each component.

        Args:
            comp (UVMComponent): Top-level component for traversal
            phase (UVMPhase):
            state:
        """
        uvm_debug(self, 'traverse', self.get_name() + ' traversing bottomup phase now with ' +
                comp.get_name())
        name = ""
        phase_domain = phase.get_domain()
        comp_domain = comp.get_domain()

        if comp.has_first_child():
            child = comp.get_first_child()
            while child is not None:
                self.traverse(child, phase, state)
                child = comp.get_next_child()

        if UVMPhase.m_phase_trace:
            dom_name = "unknown"
            if comp_domain is not None:
                dom_name = comp_domain.get_name()
            uvm_report_info("PH_TRACE",("bottomup-phase phase={} state={} comp={} comp.domain={} phase.domain={}"
                  .format(phase.get_name(), str(state), comp.get_full_name(),
                      dom_name, phase_domain.get_name())), UVM_DEBUG)

        if phase_domain == UVMDomain.get_common_domain() or phase_domain == comp_domain:
            if state == UVM_PHASE_STARTED:
                comp.m_current_phase = phase
                comp.m_apply_verbosity_settings(phase)
                comp.phase_started(phase)
            elif state == UVM_PHASE_EXECUTING:
                ph = self
                if self in comp.m_phase_imps:
                    ph = comp.m_phase_imps[self]
                ph.execute(comp, phase)
            elif state == UVM_PHASE_READY_TO_END:
                comp.phase_ready_to_end(phase)
            elif state == UVM_PHASE_ENDED:
                comp.phase_ended(phase)
                comp.m_current_phase = None
            else:
                uvm_report_fatal("PH_BADEXEC", "bottomup phase traverse internal error")

    def execute(self, comp, phase):
        """
        Executes the bottom-up phase `phase` for the component `comp`.

        Args:
            comp (UVMComponent):
            phase (UVMPhase):
        """
        # reseed this process for random stability
        #process proc = process::self()
        #proc.srandom(uvm_create_random_seed(phase.get_type_name(), comp.get_full_name()))
        comp.m_current_phase = phase
        self.exec_func(comp,phase)
