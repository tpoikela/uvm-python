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

from typing import Dict

from .uvm_phase import UVMPhase
from .uvm_object_globals import UVM_PHASE_DOMAIN, UVM_PHASE_SCHEDULE
from .uvm_debug import uvm_debug
from ..macros import uvm_error


from .uvm_runtime_phases import (UVMMainPhase, UVMPreResetPhase,
    UVMResetPhase, UVMPostResetPhase, UVMPreConfigurePhase, UVMConfigurePhase,
    UVMPostConfigurePhase,
    UVMPreMainPhase, UVMPostMainPhase, UVMPreShutdownPhase, UVMShutdownPhase,
    UVMPostShutdownPhase)


# UVMPhases
build_ph = None
connect_ph = None
end_of_elaboration_ph = None
start_of_simulation_ph = None
run_ph = None
extract_ph = None
check_ph = None
report_ph = None



class UVMDomain(UVMPhase):
    """
    Class: UVMDomain

    Phasing schedule node representing an independent branch of the schedule.
    Handle used to assign domains to components or hierarchies in the testbench.
    Domain is basically a container for the uvm phases, or custom phases if
    custom schedule is created.
    """

    m_common_domain = None
    m_uvm_domain = None
    m_domains: Dict[str, 'UVMDomain'] = {}
    m_uvm_schedule = None  # type: UVMPhase

    @classmethod
    def get_domains(cls, domains=None) -> Dict[str, 'UVMDomain']:
        """
        Returns a list of all domains.

        Args:
            domains:
        Returns:
            list[UVMDomain]: List of all domains
        Raises:
            Exception
        """
        if domains is not None:
            raise Exception("get_domains() you must capture the retval")
        return cls.m_domains

    @classmethod
    def get_uvm_schedule(cls):
        """
        Get the "UVM" schedule, which consists of the run-time phases that
        all components execute when participating in the "UVM" domain.

        Returns:
            UVMPhase: Returns UVM schedule consisting of uvm phases.
        """
        cls.get_uvm_domain()
        return cls.m_uvm_schedule

    @classmethod
    def get_common_domain(cls):
        """
        Function: get_common_domain

        Get the "common" domain, which consists of the common phases that
        all components execute in sync with each other. Phases in the "common"
        domain are build, connect, end_of_elaboration, start_of_simulation, run,
        extract, check, report, and final.
        Returns:
        """
        domain = None
        schedule = None
        if UVMDomain.m_common_domain is not None:
            return UVMDomain.m_common_domain

        domain = UVMDomain("common")
        uvm_debug(cls, 'get_common_domain', 'Adding BuildPhase now')
        from .uvm_common_phases import (UVMBuildPhase, UVMConnectPhase,
                UVMEndOfElaborationPhase, UVMStartofSimulationPhase, UVMRunPhase,
                UVMExtractPhase, UVMCheckPhase, UVMReportPhase, UVMFinalPhase)
        domain.add(UVMBuildPhase.get())
        domain.add(UVMConnectPhase.get())
        domain.add(UVMEndOfElaborationPhase.get())
        domain.add(UVMStartofSimulationPhase.get())
        domain.add(UVMRunPhase.get())
        domain.add(UVMExtractPhase.get())
        domain.add(UVMCheckPhase.get())
        domain.add(UVMReportPhase.get())
        domain.add(UVMFinalPhase.get())
        UVMDomain.m_domains["common"] = domain

        # for backward compatibility, make common phases visible;
        # same as uvm_<name>_phase::get().
        uvm_debug(cls, 'get_common_domain', 'Before find() BuildPhase')
        build = UVMBuildPhase.get()
        build_ph               = domain.find(build)
        check_phase_exists('build', build_ph)
        connect_ph             = domain.find(UVMConnectPhase.get())
        check_phase_exists('connect', connect_ph)
        end_of_elaboration_ph  = domain.find(UVMEndOfElaborationPhase.get())
        check_phase_exists('end_of_elaboration', end_of_elaboration_ph)
        start_of_simulation_ph = domain.find(UVMStartofSimulationPhase.get())
        check_phase_exists('start_of_simulation', start_of_simulation_ph)
        run_ph                 = domain.find(UVMRunPhase.get())
        check_phase_exists('run', run_ph)
        extract_ph             = domain.find(UVMExtractPhase.get())
        check_phase_exists('extract', extract_ph)
        check_ph               = domain.find(UVMCheckPhase.get())
        check_phase_exists('check', check_ph)
        report_ph              = domain.find(UVMReportPhase.get())
        check_phase_exists('report', report_ph)
        UVMDomain.m_common_domain = domain

        domain = UVMDomain.get_uvm_domain()
        UVMDomain.m_common_domain.add(domain,
                with_phase=UVMDomain.m_common_domain.find(UVMRunPhase.get()))

        return UVMDomain.m_common_domain

    @classmethod
    def add_uvm_phases(cls, schedule):
        """
        Appends to the given `schedule` the built-in UVM phases.

        Args:
            schedule (UVMPhase): Phase to be added to the schedule.
        """
        schedule.add(UVMPreResetPhase.get())
        schedule.add(UVMResetPhase.get())
        schedule.add(UVMPostResetPhase.get())
        schedule.add(UVMPreConfigurePhase.get())
        schedule.add(UVMConfigurePhase.get())
        schedule.add(UVMPostConfigurePhase.get())
        schedule.add(UVMPreMainPhase.get())
        schedule.add(UVMMainPhase.get())
        schedule.add(UVMPostMainPhase.get())
        schedule.add(UVMPreShutdownPhase.get())
        schedule.add(UVMShutdownPhase.get())
        schedule.add(UVMPostShutdownPhase.get())

    @classmethod
    def get_uvm_domain(cls):
        """
        Get a handle to the singleton `uvm` domain

        Returns:
            UVMDomain: Singleton instance of uvm domain
        """
        if UVMDomain.m_uvm_domain is None:
            UVMDomain.m_uvm_domain = UVMDomain("uvm")
            UVMDomain.m_uvm_schedule = UVMPhase("uvm_sched", UVM_PHASE_SCHEDULE)
            UVMDomain.add_uvm_phases(UVMDomain.m_uvm_schedule)
            UVMDomain.m_uvm_domain.add(UVMDomain.m_uvm_schedule)
        return UVMDomain.m_uvm_domain

    def __init__(self, name):
        """
        Create a new instance of a phase domain.

        Args:
            name:
        """
        super().__init__(name, UVM_PHASE_DOMAIN)
        if name in UVMDomain.m_domains:
            uvm_error("UNIQDOMNAM",
                    "Domain created with non-unique name '{}'".format(name))
        UVMDomain.m_domains[name] = self

    # Function: jump
    #
    # jumps all active phases of this domain to to-phase if
    # there is a path between active-phase and to-phase
    #def jump(self, phase):
    #  uvm_phase phases[$];
    #
    #  m_get_transitive_children(phases);
    #
    #  phases = phases.find(item) with (item.get_state() inside {[UVM_PHASE_STARTED:UVM_PHASE_CLEANUP]});
    #
    #  foreach(phases[idx])
    #      if(phases[idx].is_before(phase) || phases[idx].is_after(phase))
    #          phases[idx].jump(phase);


    @classmethod
    def jump_all(cls, phase):
        """
        jump_all
        --------
        Args:
            phase:
        """
        #  uvm_domain domains[string];
        domains = UVMDomain.get_domains()  # string -> uvm_domain
        for idx in domains:
            domains[idx].jump(phase)

    #endclass UVMDomain

# tpoikela: Added for additional verification
def check_phase_exists(name, phase):
    if phase is None:
        msg = 'Phase ' + name + ' is None! in UVMDomain.get_common_domain()'
        raise Exception(msg)
