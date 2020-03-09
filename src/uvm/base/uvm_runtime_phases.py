#//
#//----------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------

import cocotb

from .uvm_task_phase import UVMTaskPhase
from .uvm_debug import uvm_debug

#// Title: UVM Run-Time Phases
#//
#// The run-time schedule is the pre-defined phase schedule
#// which runs concurrently to the <uvm_run_phase> global run phase.
#// By default, all <uvm_component>s using the run-time schedule
#// are synchronized with respect to the pre-defined phases in the schedule.
#// It is possible for components to belong to different domains
#// in which case their schedules can be unsynchronized.
#//
#// The names of the UVM phases (which will be returned by get_name() for a
#// phase instance) match the class names specified below with the "uvm_"
#// and "_phase" removed.  For example, the main phase corresponds to the
#// UVMMainPhase class below and has the name "main", which means that
#// the following can be used to call foo() at the start of main phase:
#//
#// | function void phase_started(uvm_phase phase)
#// |    if (phase.get_name()=="main") foo()
#// | endfunction
#//
#// The run-time phases are executed in the sequence they are specified below.
#//
#//

#// Class: uvm_pre_reset_phase
#//
#// Before reset is asserted.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::pre_reset_phase> method. This phase starts at the
#// same time as the <uvm_run_phase> unless a user defined phase is inserted
#// in front of this phase.
#//
#// Upon Entry:
#// - Indicates that power has been applied but not necessarily valid or stable.
#// - There should not have been any active clock edges
#//   before entry into this phase.
#//
#// Typical Uses:
#// - Wait for power good.
#// - Components connected to virtual interfaces should initialize
#//   their output to X's or Z's.
#// - Initialize the clock signals to a valid value
#// - Assign reset signals to X (power-on reset).
#// - Wait for reset signal to be asserted
#//   if not driven by the verification environment.
#//
#// Exit Criteria:
#// - Reset signal, if driven by the verification environment,
#//   is ready to be asserted.
#// - Reset signal, if not driven by the verification environment, is asserted.
#//


class UVMPreResetPhase(UVMTaskPhase):

    
    async def exec_task(self,comp, phase):
        await comp.pre_reset_phase(phase)

    m_inst = None
    type_name = "uvm_pre_reset_phase"

    @classmethod
    def get(cls):
        """         
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if cls.m_inst is None:
            cls.m_inst = UVMPreResetPhase()
            return cls.m_inst

    def __init__(self, name="pre_reset"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPreResetPhase.type_name

#//
#// Class: uvm_reset_phase
#//
#// Reset is asserted.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::reset_phase> method.
#//
#// Upon Entry:
#// - Indicates that the hardware reset signal is ready to be asserted.
#//
#// Typical Uses:
#// - Assert reset signals.
#// - Components connected to virtual interfaces should drive their output
#//   to their specified reset or idle value.
#// - Components and environments should initialize their state variables.
#// - Clock generators start generating active edges.
#// - De-assert the reset signal(s)  just before exit.
#// - Wait for the reset signal(s) to be de-asserted.
#//
#// Exit Criteria:
#// - Reset signal has just been de-asserted.
#// - Main or base clock is working and stable.
#// - At least one active clock edge has occurred.
#// - Output signals and state variables have been initialized.
#//


class UVMResetPhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.reset_phase(phase)

    m_inst = None
    type_name = "uvm_reset_phase"

    @classmethod
    def get(cls):
        """         
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if cls.m_inst is None:
            cls.m_inst = UVMResetPhase()
            return cls.m_inst

    def __init__(self, name="reset"):
        super().__init__(name)

    def get_type_name(self):
        return UVMResetPhase.type_name
#
#// Class: uvm_post_reset_phase
#//
#// After reset is de-asserted.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::post_reset_phase> method.
#//
#// Upon Entry:
#// - Indicates that the DUT reset signal has been de-asserted.
#//
#// Typical Uses:
#// - Components should start behavior appropriate for reset being inactive.
#//   For example, components may start to transmit idle transactions
#//   or interface training and rate negotiation.
#//   This behavior typically continues beyond the end of this phase.
#//
#// Exit Criteria:
#// - The testbench and the DUT are in a known, active state.
#//


class UVMPostResetPhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.post_reset_phase(phase)

    m_inst = None
    type_name = "uvm_post_reset_phase"

    @classmethod
    def get(cls):
        """ 
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMPostResetPhase()
            return cls.m_inst

    def __init__(self, name="post_reset"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPostResetPhase.type_name
#
#
#// Class: uvm_pre_configure_phase
#//
#// Before the DUT is configured by the SW.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::pre_configure_phase> method.
#//
#// Upon Entry:
#// - Indicates that the DUT has been completed reset
#//  and is ready to be configured.
#//
#// Typical Uses:
#// - Procedurally modify the DUT configuration information as described
#//   in the environment (and that will be eventually uploaded into the DUT).
#// - Wait for components required for DUT configuration to complete
#//   training and rate negotiation.
#//
#// Exit Criteria:
#// - DUT configuration information is defined.
#//


class UVMPreConfigurePhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.pre_configure_phase(phase)

    m_inst = None
    type_name = "uvm_pre_configure_phase"

    @classmethod
    def get(cls):
        """ 
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMPreConfigurePhase()
            return cls.m_inst

    def __init__(self, name="pre_configure"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPreConfigurePhase.type_name
#
#
#// Class: uvm_configure_phase
#//
#// The SW configures the DUT.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::configure_phase> method.
#//
#// Upon Entry:
#// - Indicates that the DUT is ready to be configured.
#//
#// Typical Uses:
#// - Components required for DUT configuration execute transactions normally.
#// - Set signals and program the DUT and memories
#//   (e.g. read/write operations and sequences)
#//   to match the desired configuration for the test and environment.
#//
#// Exit Criteria:
#// - The DUT has been configured and is ready to operate normally.
#//


class UVMConfigurePhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.configure_phase(phase)

    m_inst = None
    type_name = "uvm_configure_phase"

    @classmethod
    def get(cls):
        """ 
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMConfigurePhase()
            return cls.m_inst

    def __init__(self, name="configure"):
        super().__init__(name)

    def get_type_name(self):
        return UVMConfigurePhase.type_name
#
#// Class: uvm_post_configure_phase
#//
#// After the SW has configured the DUT.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::post_configure_phase> method.
#//
#// Upon Entry:
#// - Indicates that the configuration information has been fully uploaded.
#//
#// Typical Uses:
#// - Wait for configuration information to fully propagate and take effect.
#// - Wait for components to complete training and rate negotiation.
#// - Enable the DUT.
#// - Sample DUT configuration coverage.
#//
#// Exit Criteria:
#// - The DUT has been fully configured and enabled
#//   and is ready to start operating normally.
#//
class UVMPostConfigurePhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.post_configure_phase(phase)

    m_inst = None
    type_name = "uvm_post_configure_phase"

    @classmethod
    def get(cls):
        """ 
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMPostConfigurePhase()
            return cls.m_inst

    def __init__(self, name="post_configure"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPostConfigurePhase.type_name
#
#// Class: uvm_pre_main_phase
#//
#// Before the primary test stimulus starts.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::pre_main_phase> method.
#//
#// Upon Entry:
#// - Indicates that the DUT has been fully configured.
#//
#// Typical Uses:
#// - Wait for components to complete training and rate negotiation.
#//
#// Exit Criteria:
#// - All components have completed training and rate negotiation.
#// - All components are ready to generate and/or observe normal stimulus.
#//

class UVMPreMainPhase(UVMTaskPhase):

    
    async def exec_task(self,comp, phase):
        await comp.pre_main_phase(phase)

    m_inst = None
    type_name = "uvm_pre_main_phase"

    @classmethod
    def get(cls):
        """         
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMPreMainPhase()
            return cls.m_inst

    def __init__(self, name="pre_main"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPreMainPhase.type_name
#
#
#// Class: UVMMainPhase
#//
#// Primary test stimulus.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::main_phase> method.
#//
#// Upon Entry:
#// - The stimulus associated with the test objectives is ready to be applied.
#//
#// Typical Uses:
#// - Components execute transactions normally.
#// - Data stimulus sequences are started.
#// - Wait for a time-out or certain amount of time,
#//   or completion of stimulus sequences.
#//
#// Exit Criteria:
#// - Enough stimulus has been applied to meet the primary
#//   stimulus objective of the test.
#//


class UVMMainPhase(UVMTaskPhase):

    
    async def exec_task(self,comp, phase):
        uvm_debug(self, 'exec_task', 'yield main_phase for ' + comp.get_name())
        await comp.main_phase(phase)

    m_inst = None  # local static UVMMainPhase
    type_name = "UVMMainPhase"

    @classmethod
    def get(cls):
        """         
        Function: get
        Returns the singleton phase handle
        Returns:
        """
        if cls.m_inst is None:
            cls.m_inst = UVMMainPhase()
        return cls.m_inst

    def __init__(self, name="main"):
        super().__init__(name)

    def get_type_name(self):
        return UVMMainPhase.type_name


#// Class: uvm_post_main_phase
#//
#// After enough of the primary test stimulus.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::post_main_phase> method.
#//
#// Upon Entry:
#// - The primary stimulus objective of the test has been met.
#//
#// Typical Uses:
#// - Included for symmetry.
#//
#// Exit Criteria:
#// - None.
#//


class UVMPostMainPhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.post_main_phase(phase)

    m_inst = None
    type_name = "uvm_post_main_phase"

    @classmethod
    def get(cls):
        """ 
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMPostMainPhase()
            return cls.m_inst

    def __init__(self, name="post_main"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPostMainPhase.type_name
#
#
#// Class: uvm_pre_shutdown_phase
#//
#// Before things settle down.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::pre_shutdown_phase> method.
#//
#// Upon Entry:
#// - None.
#//
#// Typical Uses:
#// - Included for symmetry.
#//
#// Exit Criteria:
#// - None.
#//
class UVMPreShutdownPhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.pre_shutdown_phase(phase)

    m_inst = None
    type_name = "uvm_pre_shutdown_phase"

    @classmethod
    def get(cls):
        """         
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMPreShutdownPhase()
            return cls.m_inst

    def __init__(self, name="pre_shutdown"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPreShutdownPhase.type_name
#
#
#// Class: uvm_shutdown_phase
#//
#// Letting things settle down.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::shutdown_phase> method.
#//
#// Upon Entry:
#// - None.
#//
#// Typical Uses:
#// - Wait for all data to be drained out of the DUT.
#// - Extract data still buffered in the DUT,
#//   usually through read/write operations or sequences.
#//
#// Exit Criteria:
#// - All data has been drained or extracted from the DUT.
#// - All interfaces are idle.
#//
class UVMShutdownPhase(UVMTaskPhase):

    
    async def exec_task(self,comp, phase):
        await comp.shutdown_phase(phase)

    m_inst = None
    type_name = "uvm_shutdown_phase"

    @classmethod
    def get(cls):
        """         
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if(cls.m_inst is None):
            cls.m_inst = UVMShutdownPhase()
            return cls.m_inst

    def __init__(self, name="shutdown"):
        super().__init__(name)

    def get_type_name(self):
        return UVMShutdownPhase.type_name


#// Class: uvm_post_shutdown_phase
#//
#// After things have settled down.
#//
#// <UVMTaskPhase> that calls the
#// <uvm_component::post_shutdown_phase> method.  The end of this phase is
#// synchronized to the end of the <uvm_run_phase> phase unless a user defined
#// phase is added after this phase.
#//
#// Upon Entry:
#// - No more "data" stimulus is applied to the DUT.
#//
#// Typical Uses:
#// - Perform final checks that require run-time access to the DUT
#//   (e.g. read accounting registers or dump the content of memories).
#//
#// Exit Criteria:
#// - All run-time checks have been satisfied.
#// - The <uvm_run_phase> phase is ready to end.
#//
class UVMPostShutdownPhase(UVMTaskPhase):
    
    async def exec_task(self,comp, phase):
        await comp.post_shutdown_phase(phase)

    m_inst = None
    type_name = "uvm_post_shutdown_phase"

    @classmethod
    def get(cls):
        """ 
           Function: get
           Returns the singleton phase handle
        Returns:
        """
        if cls.m_inst is None:
            cls.m_inst = UVMPostShutdownPhase()
            return cls.m_inst

    def __init__(self, name="post_shutdown"):
        super().__init__(name)

    def get_type_name(self):
        return UVMPostShutdownPhase.type_name
