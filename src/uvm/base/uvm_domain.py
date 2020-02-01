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
from .uvm_object_globals import *
from .uvm_globals import *
from .uvm_debug import *
from ..macros import uvm_error


from .uvm_runtime_phases import (UVMMainPhase, UVMPreResetPhase,
    UVMResetPhase, UVMPostResetPhase, UVMConfigurePhase,
    UVMPreMainPhase, UVMShutdownPhase)


# UVMPhases
build_ph = None
connect_ph = None
end_of_elaboration_ph = None
start_of_simulation_ph = None
run_ph = None
extract_ph = None
check_ph = None
report_ph = None

#------------------------------------------------------------------------------
#
# Class: uvm_domain
#
#------------------------------------------------------------------------------
#
# Phasing schedule node representing an independent branch of the schedule.
# Handle used to assign domains to components or hierarchies in the testbench
#


class UVMDomain(UVMPhase):

    m_common_domain = None
    m_uvm_domain = None
    m_domains = {}  # string -> UVMDomain
    m_uvm_schedule = None

    # Function: get_domains
    #
    # Provides a list of all domains in the provided ~domains~ argument.
    #
    def get_domains(domains=None):
        if domains is not None:
            raise Exception("get_domains() you must capture the retval")
        return UVMDomain.m_domains

    # Function: get_uvm_schedule
    #
    # Get the "UVM" schedule, which consists of the run-time phases that
    # all components execute when participating in the "UVM" domain.
    #
    @classmethod
    def get_uvm_schedule(cls):
        cls.get_uvm_domain()
        return UVMDomain.m_uvm_schedule

    # Function: get_common_domain
    #
    # Get the "common" domain, which consists of the common phases that
    # all components execute in sync with each other. Phases in the "common"
    # domain are build, connect, end_of_elaboration, start_of_simulation, run,
    # extract, check, report, and final.
    @classmethod
    def get_common_domain(cls):
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
        start_of_simulation_ph = domain.find(UVMStartofSimulationPhase.get());
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
        #
        #
        return UVMDomain.m_common_domain

    # Function: add_uvm_phases
    #
    # Appends to the given ~schedule~ the built-in UVM phases.
    #
    @classmethod
    def add_uvm_phases(cls, schedule):
        schedule.add(UVMPreResetPhase.get())
        schedule.add(UVMResetPhase.get())
        schedule.add(UVMPostResetPhase.get())
        #schedule.add(uvm_pre_configure_phase::get());
        schedule.add(UVMConfigurePhase.get())
        #  schedule.add(uvm_post_configure_phase::get());
        schedule.add(UVMPreMainPhase.get())
        schedule.add(UVMMainPhase.get())
        #  schedule.add(uvm_post_main_phase::get());
        #  schedule.add(uvm_pre_shutdown_phase::get());
        schedule.add(UVMShutdownPhase.get())
        #  schedule.add(uvm_post_shutdown_phase::get());

    # Function: get_uvm_domain
    #
    # Get a handle to the singleton ~uvm~ domain
    #
    @classmethod
    def get_uvm_domain(cls):
        if UVMDomain.m_uvm_domain is None:
            UVMDomain.m_uvm_domain = UVMDomain("uvm")
            UVMDomain.m_uvm_schedule = UVMPhase("uvm_sched", UVM_PHASE_SCHEDULE)
            UVMDomain.add_uvm_phases(UVMDomain.m_uvm_schedule)
            UVMDomain.m_uvm_domain.add(UVMDomain.m_uvm_schedule)
        return UVMDomain.m_uvm_domain

    # Function: new
    #
    # Create a new instance of a phase domain.
    def __init__(self, name):
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


    # jump_all
    # --------
    @classmethod
    def jump_all(cls, phase):
        #  uvm_domain domains[string];
        domains = UVMDomain.get_domains() # string -> uvm_domain
        for idx in domains:
            domains[idx].jump(phase);

    #endclass UVMDomain

def check_phase_exists(name, phase):
    if phase is None:
        msg = 'Phase ' + name + ' is None! in UVMDomain.get_common_domain()'
        raise Exception(msg)

import unittest

class TestUVMDomain(unittest.TestCase):

    def test_common(self):
        common = UVMDomain.get_common_domain()
        self.assertNotEqual(common, None)
        bld = common.find(UVMBuildPhase.get())
        self.assertNotEqual(bld, None)

    def test_add_and_find(self):
        my_ph = UVMPhase('my_ph')
        dm = UVMDomain('my domain')
        dm.add(my_ph)
        my_ph2 = dm.find(my_ph)
        self.assertNotEqual(my_ph2, None)
        self.assertEqual(my_ph2.get_name(), 'my_ph')


if __name__ == '__main__':
    unittest.main()
