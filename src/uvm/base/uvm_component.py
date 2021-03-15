#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2013      NVIDIA Corporation
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
#//------------------------------------------------------------------------------

from typing import List, Dict

import cocotb
from cocotb.triggers import Timer
from .uvm_report_object import UVMReportObject
from .uvm_object_globals import (UVM_NONE, UVM_MEDIUM, UVM_PHASE_DONE, UVM_INFO,
    UVM_CHECK_FIELDS, UVM_PHASE_SCHEDULE, UVM_WARNING, UVM_ERROR, UVM_FATAL)

from .uvm_common_phases import UVMBuildPhase
from .uvm_domain import UVMDomain
from .uvm_debug import uvm_debug
from .uvm_object import UVMObject
from .uvm_queue import UVMQueue
from .uvm_pool import UVMEventPool
from .sv import sv, uvm_split_string
from ..macros import uvm_info, uvm_fatal, uvm_warning, uvm_error
from .uvm_recorder import UVMRecorder
from .uvm_globals import (uvm_is_match, uvm_string_to_action,
        uvm_string_to_severity, uvm_zero_delay)
from .uvm_factory import UVMObjectWrapper
from .uvm_links import (UVMRelatedLink, UVMParentChildLink)

INV_WARN1 = ("+uvm_set_action requires 4 arguments, but %0d given for command "
    + "+uvm_set_action=%s, Usage: +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>")

INV_WARN2 = ("Bad severity argument \"%s\" given to command +uvm_set_action=%s,"
    + "Usage: +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>")

INV_WARN3 = ("Bad action argument \"%s\" given to command +uvm_set_action=%s, "
    + "Usage: +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>")

INV_WARN4 = ("+uvm_set_severity requires 4 arguments, but %0d given for command "
    + "+uvm_set_severity=%s, Usage: +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>")

INV_WARN5 = ("Bad severity argument \"%s\" given to command +uvm_set_severity=%s,"
    + " Usage: +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>")

INV_WARN6 = ("Bad severity argument \"%s\" given to command +uvm_set_severity=%s, "
    + "Usage: +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>")


class VerbositySetting:
    """
    The verbosity settings may have a specific phase to start at.
    We will do this work in the phase_started callback.
        :ivar UVMComponent comp: Component related to the settings
        :ivar UVMPhase phase: Phase in which settings apply.
        :ivar int id: ID for verbosity setting
        :ivar int offset: Time offset for verbosity setting
        :ivar int verbosity: Verbosity level of the setting.
    """
    def __init__(self):
        self.comp = ""
        self.phase = ""
        self.id = ""
        self.offset = 0
        self.verbosity = UVM_MEDIUM

    def convert2string(self):
        return "Comp: {}, phase: {}, ID: {}, offset: {}, verb: {}".format(
            self.comp, self.phase, self.id, self.offset, self.verbosity)



CLONE_ERR = ("Attempting to clone '%s'.  Clone cannot be called on a uvm_component. "
    + " The clone target variable will be set to None.")



class uvm_cmdline_parsed_arg_t:
    """
    Class used to return arguments and associated data parsed from cmd line
    arguments. These are usually plusargs given with +ARG_NAME=ARG_VALUE

    :ivar str arg: Argument name
    :ivar list args: Values of given argument.
    :ivar int used: Logs how many times arg is used.
    """
    def __init__(self):
        self.arg = ""
        self.args = []
        self.used = 0


class UVMComponent(UVMReportObject):
    """
    Base class for defining UVM components
    The uvm_component class is the root base class for UVM components. In
    addition to the features inherited from `UVMObject` and `UVMReportObject`,
    uvm_component provides the following interfaces:

    Hierarchy:
      provides methods for searching and traversing the component hierarchy.

    Phasing
      defines a phased test flow that all components follow, with a
      group of standard phase methods and an API for custom phases and
      multiple independent phasing domains to mirror DUT behavior e.g. power

    Reporting
      provides a convenience interface to the `UVMReportHandler`. All
      messages, warnings, and errors are processed through this interface.

    Transaction recording
        provides methods for recording the transactions
        produced or consumed by the component to a transaction database (vendor
        specific).

    Factory
        provides a convenience interface to the `UVMFactory`. The factory
        is used to create new components and other objects based on type-wide and
        instance-specific configuration.

    The `UVMComponent` is automatically seeded during construction using UVM
    seeding, if enabled. All other objects must be manually reseeded, if
    appropriate. See `UVMObject.reseed` for more information.

    Most local methods within the class are prefixed with m_, indicating they are
    not user-level methods.

    :cvar bool print_config_matches: Setting this static variable causes
        `UVMConfigDb.get` to print info about
        matching configuration settings as they are being applied.

    :ivar UVMTrDatabase tr_database: Specifies the `UVMTrDatabase` object to use
        for `begin_tr` and other methods in the <Recording Interface>.
        Default is `UVMCoreService.get_default_tr_database`.
    """

    print_config_matches = False
    m_time_settings: List[VerbositySetting] = []

    def __init__(self, name, parent):
        """
        Creates a new component with the given leaf instance `name` and handle
        to its `parent`.  If the component is a top-level component (i.e. it is
        created in a static module or interface), `parent` should be `None`.

        The component will be inserted as a child of the `parent` object, if any.
        If `parent` already has a child by the given `name`, an error is produced.

        If `parent` is `None`, then the component will become a child of the
        implicit top-level component, `uvm_top`.

        All classes derived from uvm_component must call super.new(name,parent).
        Args:
            name (str): Name of the component.
            parent (UVMComponent): Parent component.
        """
        super().__init__(name)
        self.m_children: Dict[str, 'UVMComponent'] = {}  # uvm_component[string]

        #// Variable: print_enabled
        #//
        #// This bit determines if this component should automatically be printed as a
        #// child of its parent object.
        #//
        #// By default, all children are printed. However, this bit allows a parent
        #// component to disable the printing of specific children.
        self.print_enabled = True
        self.m_current_phase = None  # the most recently executed phase
        self.m_parent = None
        self.m_children_by_handle: Dict['UVMComponent', 'UVMComponent'] = {}
        self.m_children_ordered: List['UVMComponent'] = []

        self.m_build_done = False
        self.m_phasing_active = 0
        self.recording_detail = UVM_NONE
        self.m_name = ""
        self.m_verbosity_settings = []
        self.m_main_stream = None

        # functors to override uvm_root defaults
        self.m_phase_imps = {}  # uvm_phase[uvm_phase]

        self.child_ptr = -1
        self.m_tr_h = {}  # uvm_recorder m_tr_h[uvm_transaction]

        self.m_run_process = None

        self.tr_database = None  # uvm_tr_database
        self.m_domain = None
        self.m_phase_process = None  # process

        self.event_pool: UVMEventPool = UVMEventPool("evt_pool")

        self.m_streams = {}  # uvm_tr_stream [string][string]

        # If uvm_top, reset name to "" so it doesn't show in full paths then return
        if parent is None and name == "__top__":
            self.set_name("")
            #UVMReportObject.set_name(self, name)
            #self.m_name = self.get_name()
            return

        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        top = cs.get_root()

        # Check that we're not in or past end_of_elaboration
        common = UVMDomain.get_common_domain()
        bld = common.find(UVMBuildPhase.get())
        if bld is None:
            uvm_fatal("COMP/INTERNAL", "attempt to find build phase object failed")
        if bld.get_state() == UVM_PHASE_DONE:
            parent_name = top.get_full_name()
            if parent is not None:
                parent_name = parent.get_full_name()
            uvm_fatal("ILLCRT", ("It is illegal to create a component ('" +
                name + "' under '" + parent_name + "') after the build phase has ended."))

        if name == "":
            name = "COMP_" + str(UVMObject.m_inst_count)

        if parent == self:
            uvm_fatal("THISPARENT",
                    "cannot set the parent of a component to itself")

        if parent is None:
            parent = top

        if self.uvm_report_enabled(UVM_MEDIUM+1, UVM_INFO, "NEWCOMP"):
            nname = parent.get_full_name()
            if parent == top:
                nname = "uvm_top"
            uvm_info("NEWCOMP", "Creating " + nname + "." + name, UVM_MEDIUM+1)

        if parent.has_child(name) and self != parent.get_child(name):
            if parent == top:
                error_str = ("Name '" + name + "' is not unique to other top-level "
                    + "instances. If parent is a module, build a unique name by combining the "
                    + "the module name and component name: $sformatf('%m.%s','"
                    + name + "').")
                uvm_fatal("CLDEXT", error_str)
            else:
                uvm_fatal("CLDEXT",
                    sv.sformatf("Cannot set '%s' as a child of '%s', %s",
                      name, parent.get_full_name(), "which already has a child by that name."))
            return

        self.m_parent = parent

        self.set_name(name)
        if self.m_parent.m_add_child(self) is False:
            self.m_parent = None

        self.m_domain = parent.m_domain  # by default, inherit domains from parents

        # Now that inst name is established, reseed (if use_uvm_seeding is set)
        self.reseed()

        # Do local configuration settings
        arr = []
        from .uvm_config_db import UVMConfigDb
        if UVMConfigDb.get(self, "", "recording_detail", arr):
            self.recording_detail = arr[0]

        self.m_rh.set_name(self.get_full_name())
        self.set_report_verbosity_level(parent.get_report_verbosity_level())
        self.m_set_cl_msg_args()


    #----------------------------------------------------------------------------
    # Group: Hierarchy Interface
    #----------------------------------------------------------------------------
    #
    # These methods provide user access to information about the component
    # hierarchy, i.e., topology.
    #
    #----------------------------------------------------------------------------

    def get_parent(self):
        """
        Function: get_parent

        Returns a handle to this component's parent, or `None` if it has no parent.
        Returns:
            UVMComponent: Parent of this component.
        """
        return self.m_parent

    def get_full_name(self) -> str:
        """
        Returns the full hierarchical name of this object. The default
        implementation concatenates the hierarchical name of the parent, if any,
        with the leaf name of this object, as given by `UVMObject.get_name`.

        Returns:
            str: Full hierarchical name of this component.
        """
        if self.m_name == "":
            return self.get_name()
        else:
            return self.m_name

    def get_children(self, children):
        """
        This function populates the end of the `children` array with the
        list of this component's children.

        .. code-block:: python

           array = []
           my_comp.get_children(array)
           for comp in array:
               do_something(comp)

        Args:
            children (list): List into which child components are appended
        """
        for name in self.m_children:
            children.append(self.m_children[name])

    def get_child(self, name):
        """
        Args:
            name (str): Name of desired child
        Returns:
            UVMComponent: Child component matching name.
        """
        if name in self.m_children:
            return self.m_children[name]

    def get_next_child(self):
        """
        Returns:
            UVMComponent: Next child component.
        """
        self.child_ptr += 1
        if (self.child_ptr < len(self.m_children_ordered)):
            return self.m_children_ordered[self.child_ptr]
        return None

    def get_first_child(self):
        """
        These methods are used to iterate through this component's children, if
        any. For example, given a component with an object handle, `comp`, the
        following code calls `UVMObject.print` for each child:

        .. code-block:: python

            name = ""
            child = comp.get_first_child()
            while child is not None:
                child.print()
                child = comp.get_next_child()

        Returns:
            UVMComponent: First child component.
        """
        self.child_ptr = 0
        if len(self.m_children_ordered) > 0:
            return self.m_children_ordered[0]
        return None

    def get_num_children(self):
        """
        Returns:
            int: The number of this component's children.
        """
        return len(self.m_children_ordered)

    def has_child(self, name):
        """
        Args:
            name (str): Desired child component name.
        Returns:
            bool: True if this component has a child with the given `name`,
            False otherwise.
        """
        return name in self.m_children

    def set_name(self, name):
        """
        Renames this component to `name` and recalculates all descendants'
        full names. This is an internal function for now.

        Args:
            name (str): New name
        """
        if self.m_name != "":
            uvm_error("INVSTNM", ("It is illegal to change the name of a component."
                + "The component name will not be changed to \"{}\"".format(name)))
            return
        super().set_name(name)
        self.m_set_full_name()

    def lookup(self, name):
        """
        Looks for a component with the given hierarchical `name` relative to this
        component. If the given `name` is preceded with a '.' (dot), then the search
        begins relative to the top level (absolute lookup). The handle of the
        matching component is returned, else `None`. The name must not contain
        wildcards.

        Args:
            name:
        Returns:
            UVMComponent: Matching component, or None is no match is found.
        """
        leaf = ""
        remainder = ""
        comp = None
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        top = cs.get_root()

        comp = self
        [leaf, remainder] = self.m_extract_name(name, leaf, remainder)

        if leaf == "":
            comp = top  # absolute lookup
            [leaf, remainder] = self.m_extract_name(remainder, leaf, remainder)

        if comp.has_child(leaf) is False:
            uvm_warning("Lookup Error",
               sv.sformatf("Cannot find child %0s from comp %s",leaf,
                   comp.get_name()))
            return None

        if remainder != "":
            return comp.m_children[leaf].lookup(remainder)
        return comp.m_children[leaf]


    def get_depth(self) -> int:
        """
        Returns the component's depth from the root level. uvm_top has a
        depth of 0. The test and any other top level components have a depth
        of 1, and so on.

        Returns:
            int: The component's depth from the root level
        """
        if self.m_name == "":
            return 0
        get_depth = 1
        for i in range(len(self.m_name)):
            if (self.m_name[i] == "."):
                get_depth += 1
        return get_depth


    #----------------------------------------------------------------------------
    # Group: Phasing Interface
    #----------------------------------------------------------------------------
    #
    # These methods implement an interface which allows all components to step
    # through a standard schedule of phases, or a customized schedule, and
    # also an API to allow independent phase domains which can jump like state
    # machines to reflect behavior e.g. power domains on the DUT in different
    # portions of the testbench. The phase tasks and functions are the phase
    # name with the _phase suffix. For example, the build phase function is
    # <build_phase>.
    #
    # All processes associated with a task-based phase are killed when the phase
    # ends. See <uvm_task_phase> for more details.
    #----------------------------------------------------------------------------

    def build_phase(self, phase):
        """
        The `UVMBuildPhase` phase implementation method.

        Any override should call super().build_phase(phase) to execute the automatic
        configuration of fields registered in the component by calling
        `apply_config_settings`.
        To turn off automatic configuration for a component,
        do not call super().build_phase(phase).

        This method should never be called directly.

        Args:
            phase (UVMPhase):
        """
        self.m_build_done = True
        self.build()

    def build(self):
        """
        For backward compatibility the base `build_phase` method calls `build`.
        """
        self.m_build_done = True
        self.apply_config_settings(UVMComponent.print_config_matches)
        if self.m_phasing_active == 0:
            uvm_warning("UVM_DEPRECATED",
                    "build()/build_phase() has been called explicitly")

    def connect_phase(self, phase):
        """
        The `UVMConnectPhase` phase implementation method.

        This method should never be called directly.

        Args:
            phase (UVMPhase):
        """
        pass

    # For backward compatibility the base connect_phase method calls connect.
    # extern virtual function void connect()

    def end_of_elaboration_phase(self, phase):
        """
        The `UVMEndOfElaborationPhase` phase implementation method.

        This method should never be called directly.

        Args:
            phase (UVMPhase):
        """
        pass

    # For backward compatibility the base <end_of_elaboration_phase> method calls <end_of_elaboration>.
    # extern virtual function void end_of_elaboration()


    def start_of_simulation_phase(self, phase):
        """
        The `UVMStartOfSimulationPhase` phase implementation method.

        This method should never be called directly.

        Args:
            phase (UVMPhase):
        """
        self.start_of_simulation()
        return

    def start_of_simulation(self):
        """
        For backward compatibility the base `start_of_simulation_phase` method calls `start_of_simulation`.
        extern virtual function void start_of_simulation()
        """
        return


    async def run_phase(self, phase):
        """
        Task: run_phase

        The `UVMRunPhase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        Thus the phase will automatically
        end once all objections are dropped using ~phase.drop_objection()~.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        The run_phase task should never be called directly.
        """
        uvm_debug(self, 'run_phase', self.get_name() + ' yielding self.run()')
        # self.m_run_process = cocotb.fork(self.run())
        # yield self.m_run_process
        await self.run()

    # For backward compatibility the base <run_phase> method calls <run>.
    # extern virtual task run()

    async def run(self):
        uvm_debug(self, 'run', self.get_name() + ' yield Timer(0) in self.run()')
        await uvm_zero_delay()

    async def pre_reset_phase(self, phase):
        """
        Task: pre_reset_phase

        The `uvm_pre_reset_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def reset_phase(self, phase):
        """
        Task: reset_phase

        The `uvm_reset_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def post_reset_phase(self, phase):
        """
        Task: post_reset_phase

        The `uvm_post_reset_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def pre_configure_phase(self, phase):
        """
        Task: pre_configure_phase

        The `uvm_pre_configure_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def configure_phase(self, phase):
        """
        Task: configure_phase

        The `uvm_configure_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def post_configure_phase(self, phase):
        """
        Task: post_configure_phase

        The `uvm_post_configure_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def pre_main_phase(self, phase):
        """
        Task: pre_main_phase

        The `uvm_pre_main_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def main_phase(self, phase):
        """
        Task: main_phase

        The `uvm_main_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def post_main_phase(self, phase):
        """
        Task: post_main_phase

        The `uvm_post_main_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def pre_shutdown_phase(self, phase):
        """
        Task: pre_shutdown_phase

        The `uvm_pre_shutdown_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def shutdown_phase(self, phase):
        """
        Task: shutdown_phase

        The `uvm_shutdown_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    async def post_shutdown_phase(self, phase):
        """
        Task: post_shutdown_phase

        The `uvm_post_shutdown_phase` phase implementation method.

        This task returning or not does not indicate the end
        or persistence of this phase.
        It is necessary to raise an objection
        using ~phase.raise_objection()~ to cause the phase to persist.
        Once all components have dropped their respective objection
        using ~phase.drop_objection()~, or if no components raises an
        objection, the phase is ended.

        Any processes forked by this task continue to run
        after the task returns,
        but they will be killed once the phase ends.

        This method should not be called directly.
        Args:
            phase:
        """
        await uvm_zero_delay()

    def extract_phase(self, phase):
        """
        The `UVMExtractPhase` phase implementation method.

        This method should never be called directly.
        Args:
            phase:
        """
        pass

    #// For backward compatibility the base extract_phase method calls extract.
    #extern virtual function void extract()

    def check_phase(self, phase):
        """
        The `UVMCheckPhase` phase implementation method.

        This method should never be called directly.
        Args:
            phase:
        """
        pass

    #// For backward compatibility the base check_phase method calls check.
    #extern virtual function void check()

    def report_phase(self, phase):
        """
        The `UVMReportPhase` phase implementation method.

        This method should never be called directly.
        Args:
            phase:
        """
        pass

    def final_phase(self, phase):
        """
        The `UVMFinalPhase` phase implementation method.

        This method should never be called directly.
        Args:
            phase:
        """
        # self.m_rh._close_files()
        pass

    def phase_started(self, phase):
        """
        Invoked at the start of each phase. The `phase` argument specifies
        the phase being started. Any threads spawned in this callback are
        not affected when the phase ends.

        Args:
            phase:
        """
        pass


    def phase_ended(self, phase):
        """
        Invoked at the end of each phase. The `phase` argument specifies
        the phase that is ending.  Any threads spawned in this callback are
        not affected when the phase ends.

        Args:
            phase:
        """
        pass

    def phase_ready_to_end(self, phase):
        """
        Function: phase_ready_to_end

        Invoked when all objections to ending the given `phase` and all
        sibling phases have been dropped, thus indicating that `phase` is
        ready to begin a clean exit. Sibling phases are any phases that
        have a common successor phase in the schedule plus any phases that
        sync'd to the current phase. Components needing to consume delta
        cycles or advance time to perform a clean exit from the phase
        may raise the phase's objection.

        .. code-block:: python
            phase.raise_objection(self, "Reason")

        It is the responsibility of this component to drop the objection
        once it is ready for this phase to end (and processes killed).
        If no objection to the given `phase` or sibling phases are raised,
        then phase_ended() is called after a delta cycle.  If any objection
        is raised, then when all objections to ending the given `phase`
        and siblings are dropped, another iteration of phase_ready_to_end
        is called.  To prevent endless iterations due to coding error,
        after 20 iterations, phase_ended() is called regardless of whether
        previous iteration had any objections raised.
        """
        pass

    #//--------------------------------------------------------------------
    #// phase / schedule / domain API
    #//--------------------------------------------------------------------

    def set_domain(self, domain, hier=True):
        """
        Apply a phase domain to this component and, if `hier` is set,
        recursively to all its children.

        Calls the virtual `define_domain` method, which derived components can
        override to augment or replace the domain definition of its base class.

        Assigns this component [tree] to a domain. adds required schedules into graph
        If called from build, `hier` won't recurse into all chilren (which don't exist yet)
        If we have components inherit their parent's domain by default, then `hier`
        isn't needed and we need a way to prevent children from inheriting this component's domain

        Args:
            domain:
            hier:
        """
        # build and store the custom domain
        self.m_domain = domain
        self.define_domain(domain)
        if hier is True:
            for c in self.m_children:
                self.m_children[c].set_domain(domain)

    def get_domain(self):
        """
        Return handle to the phase domain set on this component

        Returns:
        """
        return self.m_domain

    def define_domain(self, domain):
        """
        Builds custom phase schedules into the provided `domain` handle.

        This method is called by `set_domain`, which integrators use to specify
        this component belongs in a domain apart from the default 'uvm' domain.

        Custom component base classes requiring a custom phasing schedule can
        augment or replace the domain definition they inherit by overriding
        their `defined_domain`. To augment, overrides would call super.define_domain().
        To replace, overrides would not call super.define_domain().

        The default implementation adds a copy of the `uvm` phasing schedule to
        the given `domain`, if one doesn't already exist, and only if the domain
        is currently empty.

        Calling `set_domain`
        with the default `uvm` domain (i.e. <uvm_domain::get_uvm_domain> ) on
        a component with no `define_domain` override effectively reverts the
        that component to using the default `uvm` domain. This may be useful
        if a branch of the testbench hierarchy defines a custom domain, but
        some child sub-branch should remain in the default `uvm` domain,
        call `set_domain` with a new domain instance handle with `hier` set.
        Then, in the sub-branch, call `set_domain` with the default `uvm` domain handle,
        obtained via <uvm_domain::get_uvm_domain>.

        Alternatively, the integrator may define the graph in a new domain externally,
        then call `set_domain` to apply it to a component.

        Args:
            domain:
        """
        from .uvm_phase import UVMPhase
        from .uvm_common_phases import UVMRunPhase
        schedule = None  # uvm_phase
        #  //schedule = domain.find(uvm_domain::get_uvm_schedule())
        schedule = domain.find_by_name("uvm_sched")
        if schedule is None:
            # uvm_domain common
            schedule = UVMPhase("uvm_sched", UVM_PHASE_SCHEDULE)
            UVMDomain.add_uvm_phases(schedule)
            domain.add(schedule)
            common = UVMDomain.get_common_domain()
            if common.find(domain,0) is None:
                common.add(domain, with_phase=UVMRunPhase.get())


    def set_phase_imp(self, phase, imp, hier=1):
        """
        Override the default implementation for a phase on this component (tree) with a
        custom one, which must be created as a singleton object extending the default
        one and implementing required behavior in exec and traverse methods

        The `hier` specifies whether to apply the custom functor to the whole tree or
        just this component.

        Args:
            phase:
            imp:
            hier:
        """
        self.m_phase_imps[phase] = imp
        if hier:
            for c in self.m_children:
                self.m_children[c].set_phase_imp(phase,imp,hier)


    #// Task: suspend
    #//
    #// Suspend this component.
    #//
    #// This method must be implemented by the user to suspend the
    #// component according to the protocol and functionality it implements.
    #// A suspended component can be subsequently resumed using <resume()>.
    #extern virtual task suspend ()


    #// Task: resume
    #//
    #// Resume this component.
    #//
    #// This method must be implemented by the user to resume a component
    #// that was previously suspended using <suspend()>.
    #// Some component may start in the suspended state and
    #// may need to be explicitly resumed.
    #extern virtual task resume ()


    def resolve_bindings(self) -> None:
        """
        Processes all port, export, and imp connections. Checks whether each port's
        min and max connection requirements are met.

        It is called just before the end_of_elaboration phase.

        Users should not call directly.
        """
        return

    #extern function string massage_scope(string scope)
    def massage_scope(self, scope: str) -> str:
        # uvm_top
        if scope == "":
            return "^$"

        if scope == "*":
            return self.get_full_name() + ".*"

        # absolute path to the top-level test
        if(scope == "uvm_test_top"):
            return "uvm_test_top"

        # absolute path to uvm_root
        if(scope[0] == "."):
            return self.get_full_name() + scope
        return self.get_full_name() + "." + scope

    #//----------------------------------------------------------------------------
    #// Group: Configuration Interface
    #//----------------------------------------------------------------------------
    #//
    #// Components can be designed to be user-configurable in terms of its
    #// topology (the type and number of children it has), mode of operation, and
    #// run-time parameters (knobs). The configuration interface accommodates
    #// this common need, allowing component composition and state to be modified
    #// without having to derive new classes or new class hierarchies for
    #// every configuration scenario.
    #//
    #//----------------------------------------------------------------------------

    def check_config_usage(self, recurse=1) -> None:
        """
        Check all configuration settings in a components configuration table
        to determine if the setting has been used, overridden or not used.
        When `recurse` is 1 (default), configuration for this and all child
        components are recursively checked. This function is automatically
        called in the check phase, but can be manually called at any time.

        To get all configuration information prior to the run phase, do something
        like this in your top object:

        .. code-block:: python

          def start_of_simulation_phase(self, phase):
            self.check_config_usage()

        Args:
            recurse:
        """
        from .uvm_resource import UVMResourcePool
        rp = UVMResourcePool.get()
        rq = rp.find_unused_resources()
        if len(rq) == 0:
            return
        uvm_info("CFGNRD"," ::: The following resources have at least one write and no reads :::",UVM_INFO)
        rp.print_resources(rq, 1)

    def apply_config_settings(self, verbose=0):
        """
        Searches for all config settings matching this component's instance path.
        For each match, the appropriate set_*_local method is called using the
        matching config setting's field_name and value. Provided the set_*_local
        method is implemented, the component property associated with the
        field_name is assigned the given value.

        This function is called by <uvm_component::build_phase>.

        The apply_config_settings method determines all the configuration
        settings targeting this component and calls the appropriate set_*_local
        method to set each one. To work, you must override one or more set_*_local
        methods to accommodate setting of your component's specific properties.
        Any properties registered with the optional `uvm_*_field macros do not
        require special handling by the set_*_local methods; the macros provide
        the set_*_local functionality for you.

        If you do not want apply_config_settings to be called for a component,
        then the build_phase() method should be overloaded and you should not call
        super.build_phase(phase). Likewise, apply_config_settings can be overloaded to
        customize automated configuration.

        When the `verbose` bit is set, all overrides are printed as they are
        applied. If the component's `print_config_matches` property is set, then
        apply_config_settings is automatically called with `verbose` = 1.

        Args:
            verbose (bool): If true, prints more verbose information
        """
        from .uvm_resource import UVMResourcePool
        rp = UVMResourcePool.get()  # uvm_resource_pool
        rq = UVMQueue()  # uvm_queue#(uvm_resource_base) rq
        r = None  # uvm_resource_base r
        name = ""
        search_name = ""
        i = 0
        j = 0

        # populate an internal 'field_array' with list of
        # fields declared with `uvm_field macros (checking
        # that there aren't any duplicates along the way)
        self._m_uvm_field_automation(None, UVM_CHECK_FIELDS, "")

        T_cont = UVMObject._m_uvm_status_container
        # if no declared fields, nothing to do.
        if len(T_cont.field_array) == 0:
            return

        if verbose:
            uvm_info("CFGAPL","applying configuration settings", UVM_NONE)

        #  // The following is VERY expensive. Needs refactoring. Should
        #  // get config only for the specific field names in 'field_array'.
        #  // That's because the resource pool is organized first by field name.
        #  // Can further optimize by encoding the value for each 'field_array'
        #  // entry to indicate string, uvm_bitstream_t, or object. That way,
        #  // we call 'get' for specific fields of specific types rather than
        #  // the search-and-cast approach here.
        rq = rp.lookup_scope(self.get_full_name())
        rq = UVMResourcePool.sort_by_precedence(rq)

        # // rq is in precedence order now, so we have to go through in reverse
        # // order to do the settings.
        #  for(int i=rq.size()-1; i>=0; --i):
        for i in range(len(rq)):

            r = rq[i]
            name = r.get_name()
            # // does name have brackets [] in it?
            while j < len(name):
                if (name[j] == "[" or name[j] == "."):
                    break
                j += 1

            # // If it does have brackets then we'll use the name
            # // up to the brackets to search __m_uvm_status_container.field_array
            if j < len(name):
                search_name = name[0:j]
            else:
                search_name = name

            if search_name not in T_cont.field_array and search_name != "recording_detail":
                continue

            if verbose:
                uvm_info("CFGAPL",sv.sformatf("applying configuration to field %s", name),UVM_NONE)

            val = r.read(self)
            if isinstance(val, int):
                self.set_int_local(name, val)
            elif isinstance(val, UVMObject):
                self.set_object_local(name, val, 0)
            elif isinstance(val, UVMObjectWrapper):
                self.set_object_local(name, val.obj, val.clone)
            elif isinstance(val, str):
                self.set_string_local(name, val)
            elif verbose:
                uvm_info("CFGAPL", sv.sformatf("field %s has an unsupported type", name), UVM_NONE)
        T_cont.field_array.clear()


    def print_config_settings(self, field="", comp=None, recurse=False):
        """
        Function: print_config_settings

        Called without arguments, print_config_settings prints all configuration
        information for this component, as set by previous calls to <uvm_config_db::set()>.
        The settings are printing in the order of their precedence.

        If `field` is specified and non-empty, then only configuration settings
        matching that field, if any, are printed. The field may not contain
        wildcards.

        If `comp` is specified and non-`None`, then the configuration for that
        component is printed.

        If `recurse` is set, then configuration information for all `comp`'s
        children and below are printed as well.

        This function has been deprecated.  Use print_config instead.
        Args:
            field (str): Print all config related to given field,
            comp (UVMComponent): If given, print config only for that component.
            recurse (bool): If true, recurse to all children
        """
        UVMComponent.have_been_warned = False
        if not UVMComponent.have_been_warned:
            uvm_warning("deprecated",
                    "uvm_component::print_config_settings has been deprecated.  Use print_config() instead")
        UVMComponent.have_been_warned = True
        self.print_config(recurse, 1)

    def print_config(self, recurse=False, audit=False) -> None:
        """
        Function: print_config

        Print_config prints all configuration information for this
        component, as set by previous calls to `UVMConfigDb.set` and exports to
        the resources pool.  The settings are printing in the order of
        their precedence.

        If `recurse` is set, then configuration information for all
        children and below are printed as well.

        if `audit` is set then the audit trail for each resource is printed
        along with the resource name and value
        Args:
            recurse (bool): If true, recurse to child components
            audit (bool): If true, print audit trail for each resource.
        """
        from .uvm_resource import UVMResourcePool
        rp = UVMResourcePool.get()
        uvm_info("CFGPRT","visible resources:", UVM_INFO)
        rp.print_resources(rp.lookup_scope(self.get_full_name()), audit)
        if recurse:
            for key in self.m_children:
                c = self.m_children[key]
                c.print_config(recurse, audit)


    #// Function: print_config_with_audit
    #//
    #// Operates the same as print_config except that the audit bit is
    #// forced to 1.  This interface makes user code a bit more readable as
    #// it avoids multiple arbitrary bit settings in the argument list.
    #//
    #// If `recurse` is set, then configuration information for all
    #// children and below are printed as well.
    def print_config_with_audit(self, recurse=0):
        self.print_config(recurse, 1)


    #//----------------------------------------------------------------------------
    #// Group: Objection Interface
    #//----------------------------------------------------------------------------
    #//
    #// These methods provide object level hooks into the `UVMObjection`
    #// mechanism.
    #//
    #//----------------------------------------------------------------------------


    #// Function: raised
    #//
    #// The `raised` callback is called when this or a descendant of this component
    #// instance raises the specified `objection`. The `source_obj` is the object
    #// that originally raised the objection.
    #// The `description` is optionally provided by the `source_obj` to give a
    #// reason for raising the objection. The `count` indicates the number of
    #// objections raised by the `source_obj`.
    def raised(self, objection, source_obj, description, count):
        pass


    def dropped(self, objection, source_obj, description, count):
        """
        The `dropped` callback is called when this or a descendant of this component
        instance drops the specified `objection`. The `source_obj` is the object
        that originally dropped the objection.
        The `description` is optionally provided by the `source_obj` to give a
        reason for dropping the objection. The `count` indicates the number of
        objections dropped by the `source_obj`.

        Args:
            objection (UVMObjection):
            source_obj (UVMObject):
            description (str):
            count (int):
        """
        pass

    async def all_dropped(self, objection, source_obj, description, count):
        """
        The `all_droppped` callback is called when all objections have been
        dropped by this component and all its descendants.  The `source_obj` is the
        object that dropped the last objection.
        The `description` is optionally provided by the `source_obj` to give a
        reason for raising the objection. The `count` indicates the number of
        objections dropped by the `source_obj`.

        Args:
            objection:
            source_obj:
            description:
            count:
        """
        pass

    #//----------------------------------------------------------------------------
    #// Group: Factory Interface
    #//----------------------------------------------------------------------------
    #//
    #// The factory interface provides convenient access to a portion of UVM's
    #// <uvm_factory> interface. For creating new objects and components, the
    #// preferred method of accessing the factory is via the object or component
    #// wrapper (see <uvm_component_registry #(T,Tname)> and
    #// <uvm_object_registry #(T,Tname)>). The wrapper also provides functions
    #// for setting type and instance overrides.
    #//
    #//----------------------------------------------------------------------------

    #// Function: create_component
    #//
    #// A convenience function for <uvm_factory::create_component_by_name>,
    #// this method calls upon the factory to create a new child component
    #// whose type corresponds to the preregistered type name, `requested_type_name`,
    #// and instance name, `name`. This method is equivalent to:
    #//
    #//|  factory.create_component_by_name(requested_type_name,
    #//|                                   get_full_name(), name, this)
    #//
    #// If the factory determines that a type or instance override exists, the type
    #// of the component created may be different than the requested type. See
    #// <set_type_override> and <set_inst_override>. See also <uvm_factory> for
    #// details on factory operation.
    def create_component(self, requested_type_name, name):
        factory = _get_factory()
        return factory.create_component_by_name(requested_type_name,
            self.get_full_name(), name, self)

    #// Function: create_object
    #//
    #// A convenience function for <uvm_factory::create_object_by_name>,
    #// this method calls upon the factory to create a new object
    #// whose type corresponds to the preregistered type name,
    #// `requested_type_name`, and instance name, `name`. This method is
    #// equivalent to:
    #//
    #//|  factory.create_object_by_name(requested_type_name,
    #//|                                get_full_name(), name)
    #//
    #// If the factory determines that a type or instance override exists, the
    #// type of the object created may be different than the requested type.  See
    #// <uvm_factory> for details on factory operation.
    def create_object(self, requested_type_name, name=""):
        factory = _get_factory()
        return factory.create_object_by_name(requested_type_name,
            self.get_full_name(), name)


    #// Function: set_type_override_by_type
    #//
    #// A convenience function for `UVMFactory.set_type_override_by_type`, this
    #// method registers a factory override for components and objects created at
    #// this level of hierarchy or below. This method is equivalent to:
    #//
    #//|  factory.set_type_override_by_type(original_type, override_type,replace)
    #//
    #// The `relative_inst_path` is relative to this component and may include
    #// wildcards. The `original_type` represents the type that is being overridden.
    #// In subsequent calls to `UVMFactory.create_object_by_type` or
    #// `UVMFactory.create_component_by_type`, if the requested_type matches the
    #// `original_type` and the instance paths match, the factory will produce
    #// the `override_type`.
    #//
    #// The original and override type arguments are lightweight proxies to the
    #// types they represent. See <set_inst_override_by_type> for information
    #// on usage.
    #extern static function void set_type_override_by_type
    #                                           (uvm_object_wrapper original_type,
    #                                            uvm_object_wrapper override_type,
    #                                            bit replace=1)
    @classmethod
    def set_type_override_by_type(cls, original_type, override_type, replace=1):
        factory = _get_factory()
        factory.set_type_override_by_type(original_type, override_type, replace)


    #// Function: set_inst_override_by_type
    #//
    #// A convenience function for <uvm_factory::set_inst_override_by_type>, this
    #// method registers a factory override for components and objects created at
    #// this level of hierarchy or below. In typical usage, this method is
    #// equivalent to:
    #//
    #//|  factory.set_inst_override_by_type( original_type,
    #//|                                     override_type,
    #//|                                     {get_full_name(),".",
    #//|                                      relative_inst_path})
    #//
    #// The `relative_inst_path` is relative to this component and may include
    #// wildcards. The `original_type` represents the type that is being overridden.
    #// In subsequent calls to `UVMFactory.create_object_by_type` or
    #// `UVMFactory.create_component_by_type`, if the requested_type matches the
    #// `original_type` and the instance paths match, the factory will produce the
    #// `override_type`.
    #//
    #// The original and override types are lightweight proxies to the types they
    #// represent. They can be obtained by calling ~type::get_type()~, if
    #// implemented by `type`, or by directly calling ~type::type_id::get()~, where
    #// `type` is the user type and `type_id` is the name of the typedef to
    #// <uvm_object_registry #(T,Tname)> or <uvm_component_registry #(T,Tname)>.
    #//
    #// If you are employing the `uvm_*_utils macros, the typedef and the get_type
    #// method will be implemented for you. For details on the utils macros
    #// refer to <Utility and Field Macros for Components and Objects>.
    #//
    #// The following example shows `uvm_*_utils usage:
    #//
    #//|  class comp extends uvm_component
    #//|    `uvm_component_utils(comp)
    #//|    ...
    #//|  endclass
    #//|
    #//|  class mycomp extends uvm_component
    #//|    `uvm_component_utils(mycomp)
    #//|    ...
    #//|  endclass
    #//|
    #//|  class block extends uvm_component
    #//|    `uvm_component_utils(block)
    #//|    comp c_inst
    #//|    virtual function void build_phase(uvm_phase phase)
    #//|      set_inst_override_by_type("c_inst",comp::get_type(),
    #//|                                         mycomp::get_type())
    #//|    endfunction
    #//|    ...
    #//|  endclass
    #extern function void set_inst_override_by_type(string relative_inst_path,
    #                                               uvm_object_wrapper original_type,
    #                                               uvm_object_wrapper override_type)
    #function void uvm_component::set_inst_override_by_type (string relative_inst_path,
    #                                                        uvm_object_wrapper original_type,
    #                                                        uvm_object_wrapper override_type)
    #  string full_inst_path
    #  uvm_coreservice_t cs = uvm_coreservice_t::get()
    #  uvm_factory factory=cs.get_factory()
    #
    #  if (relative_inst_path == "")
    #    full_inst_path = get_full_name()
    #  else
    #    full_inst_path = {get_full_name(), ".", relative_inst_path}
    #
    #  factory.set_inst_override_by_type(original_type, override_type, full_inst_path)
    #
    #endfunction


    #// Function: set_type_override
    #//
    #// A convenience function for <uvm_factory::set_type_override_by_name>,
    #// this method configures the factory to create an object of type
    #// `override_type_name` whenever the factory is asked to produce a type
    #// represented by `original_type_name`.  This method is equivalent to:
    #//
    #//|  factory.set_type_override_by_name(original_type_name,
    #//|                                    override_type_name, replace)
    #//
    #// The `original_type_name` typically refers to a preregistered type in the
    #// factory. It may, however, be any arbitrary string. Subsequent calls to
    #// create_component or create_object with the same string and matching
    #// instance path will produce the type represented by override_type_name.
    #// The `override_type_name` must refer to a preregistered type in the factory.
    @classmethod
    def set_type_override(cls, original_type_name, override_type_name,
            replace=1):
        factory = _get_factory()
        factory.set_type_override_by_name(original_type_name,override_type_name, replace)


    #// Function: set_inst_override
    #//
    #// A convenience function for <uvm_factory::set_inst_override_by_name>, this
    #// method registers a factory override for components created at this level
    #// of hierarchy or below. In typical usage, this method is equivalent to:
    #//
    #//|  factory.set_inst_override_by_name(original_type_name,
    #//|                                    override_type_name,
    #//|                                    {get_full_name(),".",
    #//|                                     relative_inst_path}
    #//|                                     )
    #//
    #// The `relative_inst_path` is relative to this component and may include
    #// wildcards. The `original_type_name` typically refers to a preregistered type
    #// in the factory. It may, however, be any arbitrary string. Subsequent calls
    #// to create_component or create_object with the same string and matching
    #// instance path will produce the type represented by `override_type_name`.
    #// The `override_type_name` must refer to a preregistered type in the factory.

    #extern function void set_inst_override(string relative_inst_path,
    #                                       string original_type_name,
    #                                       string override_type_name)


    #// Function: print_override_info
    #//
    #// This factory debug method performs the same lookup process as create_object
    #// and create_component, but instead of creating an object, it prints
    #// information about what type of object would be created given the
    #// provided arguments.
    def print_override_info(self, requested_type_name, name=""):
        factory = _get_factory()
        factory.debug_create_by_name(requested_type_name, self.get_full_name(), name)


    #//----------------------------------------------------------------------------
    #// Group: Hierarchical Reporting Interface
    #//----------------------------------------------------------------------------
    #//
    #// This interface provides versions of the set_report_* methods in the
    #// <uvm_report_object> base class that are applied recursively to this
    #// component and all its children.
    #//
    #// When a report is issued and its associated action has the LOG bit set, the
    #// report will be sent to its associated FILE descriptor.
    #//----------------------------------------------------------------------------

    #// Function: set_report_id_verbosity_hier
    def set_report_id_verbosity_hier(self, id, verbosity):
        self.set_report_id_verbosity(id, verbosity)
        for c in self.m_children:
            self.m_children[c].set_report_id_verbosity_hier(id, verbosity)

    #// Function: set_report_severity_id_verbosity_hier
    #//
    #// These methods recursively associate the specified verbosity with reports of
    #// the given `severity`, `id`, or ~severity-id~ pair. A verbosity associated
    #// with a particular severity-id pair takes precedence over a verbosity
    #// associated with id, which takes precedence over a verbosity associated
    #// with a severity.
    #//
    #// For a list of severities and their default verbosities, refer to
    #// `UVMReportHandler`.
    def set_report_severity_id_verbosity_hier(self, severity, id, verbosity):
        self.set_report_severity_id_verbosity(severity, id, verbosity)
        for c in self.m_children:
            self.m_children[c].set_report_severity_id_verbosity_hier(severity, id, verbosity)


    def set_report_severity_action_hier(self, severity, action):
        """
        Args:
            severity:
            action:
        """
        self.set_report_severity_action(severity, action)
        for c in self.m_children:
            self.m_children[c].set_report_severity_action_hier(severity, action)


    def set_report_severity_id_action_hier(self, severity, id, action):
        self.set_report_severity_id_action(severity, id, action)
        for c in self.m_children:
            self.m_children[c].set_report_severity_id_action_hier(severity, id, action)


    def set_report_id_action_hier(self, id, action):
        """
        These methods recursively associate the specified action with reports of
        the given `severity`, `id`, or ~severity-id~ pair. An action associated
        with a particular severity-id pair takes precedence over an action
        associated with id, which takes precedence over an action associated
        with a severity.

        For a list of severities and their default actions, refer to
        `UVMReportHandler`.

        Args:
            id (str): Message ID to use ('' = all)
            action:
        """
        self.set_report_id_action(id, action)
        for c in self.m_children:
            self.m_children[c].set_report_id_action_hier(id, action)


    def set_report_default_file_hier(self, file):
        """
        Sets default report file hierarchically. All `UVM_LOG` actions are
        written into this file, unless more specific file is set.

        Args:
            file:
        """
        self.set_report_default_file(file)
        for c in self.m_children:
            self.m_children[c].set_report_default_file_hier(file)

    #// Function: set_report_severity_file_hier
    def set_report_severity_file_hier(self, severity, file):
        self.set_report_severity_file(severity, file)
        for c in self.m_children:
            self.m_children[c].set_report_severity_file_hier(severity, file)

    #// Function: set_report_id_file_hier
    def set_report_id_file_hier(self, id, file):
        self.set_report_id_file(id, file)
        for c in self.m_children:
            self.m_children[c].set_report_id_file_hier(id, file)

    #// Function: set_report_severity_id_file_hier
    #//
    #// These methods recursively associate the specified FILE descriptor with
    #// reports of the given `severity`, `id`, or ~severity-id~ pair. A FILE
    #// associated with a particular severity-id pair takes precedence over a FILE
    #// associated with id, which take precedence over an a FILE associated with a
    #// severity, which takes precedence over the default FILE descriptor.
    #//
    #// For a list of severities and other information related to the report
    #// mechanism, refer to `UVMReportHandler`.
    def set_report_severity_id_file_hier(self, severity, id, file):
        self.set_report_severity_id_file(severity, id, file)
        for c in self.m_children:
            self.m_children[c].set_report_severity_id_file_hier(severity, id, file)


    def set_report_verbosity_level_hier(self, verbosity):
        """
        This method recursively sets the maximum verbosity level for reports for
        this component and all those below it. Any report from this component
        subtree whose verbosity exceeds this maximum will be ignored.

        See `UVMReportHandler` for a list of predefined message verbosity levels
        and their meaning.

        Args:
            verbosity:
        """
        self.set_report_verbosity_level(verbosity)
        for c in self.m_children:
            self.m_children[c].set_report_verbosity_level_hier(verbosity)

    def pre_abort(self):
        """
        This callback is executed when the message system is executing a
        `UVM_EXIT` action. The exit action causes an immediate termination of
        the simulation, but the pre_abort callback hook gives components an
        opportunity to provide additional information to the user before
        the termination happens. For example, a test may want to executed
        the report function of a particular component even when an error
        condition has happened to force a premature termination you would
        write a function like:

        .. code-block:: python

            def pre_abort(self):
               self.report()

        The pre_abort() callback hooks are called in a bottom-up fashion.
        """
        pass


    def m_do_pre_abort(self):
        for child in self.m_children:
            self.m_children[child].m_do_pre_abort()
        self.pre_abort()

    #//----------------------------------------------------------------------------
    #// Group: Recording Interface
    #//----------------------------------------------------------------------------
    #// These methods comprise the component-based transaction recording
    #// interface. The methods can be used to record the transactions that
    #// this component "sees", i.e. produces or consumes.
    #//
    #// The API and implementation are subject to change once a vendor-independent
    #// use-model is determined.
    #//----------------------------------------------------------------------------


    def accept_tr(self, tr, accept_time=0):
        """
        This function marks the acceptance of a transaction, `tr`, by this
        component. Specifically, it performs the following actions:

        - Calls the `tr`'s <uvm_transaction::accept_tr> method, passing to it the
          `accept_time` argument.

        - Calls this component's <do_accept_tr> method to allow for any post-begin
          action in derived classes.

        - Triggers the component's internal accept_tr event. Any processes waiting
          on this event will resume in the next delta cycle.
        Args:
            tr:
            accept_time:
        """
        e = None
        tr.accept_tr(accept_time)
        self.do_accept_tr(tr)
        e = self.event_pool.get("accept_tr")
        if e is not None:
            e.trigger()


    def do_accept_tr(self, tr):
        """
        The `accept_tr` method calls this function to accommodate any user-defined
        post-accept action. Implementations should call super.do_accept_tr to
        ensure correct operation.

        #extern virtual protected function void do_accept_tr (uvm_transaction tr)
        Args:
            tr:
        """
        return


    def begin_tr(self, tr, stream_name="main", label="", desc="", begin_time=0,
            parent_handle=0):
        """
        This function marks the start of a transaction, `tr`, by this component.
        Specifically, it performs the following actions:

        - Calls `tr`'s <uvm_transaction::begin_tr> method, passing to it the
          `begin_time` argument. The `begin_time` should be greater than or equal
          to the accept time. By default, when `begin_time` = 0, the current
          simulation time is used.

          If recording is enabled (recording_detail != UVM_OFF), then a new
          database-transaction is started on the component's transaction stream
          given by the stream argument. No transaction properties are recorded at
          this time.

        - Calls the component's <do_begin_tr> method to allow for any post-begin
          action in derived classes.

        - Triggers the component's internal begin_tr event. Any processes waiting
          on this event will resume in the next delta cycle.

        A handle to the transaction is returned. The meaning of this handle, as
        well as the interpretation of the arguments `stream_name`, `label`, and
        `desc` are vendor specific.
        Args:
            tr:
            stream_name:
            label:
            desc:
            begin_time:
            parent_handle:
        Returns:
        """
        return self.m_begin_tr(tr, parent_handle, stream_name, label, desc, begin_time)



    def begin_child_tr(self, tr, parent_handle=0, stream_name="main", label="", desc="",
            begin_time=0):
        """
        This function marks the start of a child transaction, `tr`, by this
        component. Its operation is identical to that of <begin_tr>, except that
        an association is made between this transaction and the provided parent
        transaction. This association is vendor-specific.

        Args:
            tr:
            parent_handle:
            stream_name:
            label:
            desc:
            begin_time:
        Returns:
        """
        return self.m_begin_tr(tr, parent_handle, stream_name, label, desc, begin_time)



    def do_begin_tr(self, tr, stream_name, tr_handle):
        """
        The <begin_tr> and <begin_child_tr> methods call this function to
        accommodate any user-defined post-begin action. Implementations should call
        super.do_begin_tr to ensure correct operation.

        Args:
            tr:
            stream_name:
            tr_handle:
        """
        return


    def end_tr(self, tr, end_time=0, free_handle=1):
        """
        Function: end_tr

        This function marks the end of a transaction, `tr`, by this component.
        Specifically, it performs the following actions:

        - Calls `tr`'s <uvm_transaction::end_tr> method, passing to it the
          `end_time` argument. The `end_time` must at least be greater than the
          begin time. By default, when `end_time` = 0, the current simulation time
          is used.

          The transaction's properties are recorded to the database-transaction on
          which it was started, and then the transaction is ended. Only those
          properties handled by the transaction's do_record method (and optional
          `uvm_*_field macros) are recorded.

        - Calls the component's <do_end_tr> method to accommodate any post-end
          action in derived classes.

        - Triggers the component's internal end_tr event. Any processes waiting on
          this event will resume in the next delta cycle.

        The `free_handle` bit indicates that this transaction is no longer needed.
        The implementation of free_handle is vendor-specific.
        Args:
            tr:
            end_time:
            free_handle:
        """
        e = None  # uvm_event#(uvm_object) e
        recorder = None  # uvm_recorder recorder
        # db: uvm_tr_database = self.m_get_tr_database()

        if tr is None:
            return

        tr.end_tr(end_time, free_handle)

        if self.recording_detail != UVM_NONE:
            if tr in self.m_tr_h:

                recorder = self.m_tr_h[tr]
                self.do_end_tr(tr, recorder.get_handle())  # callback
                del self.m_tr_h[tr]
                tr.record(recorder)
                recorder.close(end_time)

                if free_handle:
                    recorder.free()
            else:
                self.do_end_tr(tr, 0)  # callback


        e = self.event_pool.get("end_tr")
        if e is not None:
            e.trigger()


    def do_end_tr(self, tr, tr_handle):
        """
        The <end_tr> method calls this function to accommodate any user-defined
        post-end action. Implementations should call super.do_end_tr to ensure
        correct operation.

        Args:
            tr:
            tr_handle:
        """
        return

    #// Function: record_error_tr
    #//
    #// This function marks an error transaction by a component. Properties of the
    #// given uvm_object, `info`, as implemented in its <uvm_object::do_record> method,
    #// are recorded to the transaction database.
    #//
    #// An `error_time` of 0 indicates to use the current simulation time. The
    #// `keep_active` bit determines if the handle should remain active. If 0,
    #// then a zero-length error transaction is recorded. A handle to the
    #// database-transaction is returned.
    #//
    #// Interpretation of this handle, as well as the strings `stream_name`,
    #// `label`, and `desc`, are vendor-specific.
    #extern function integer record_error_tr (string stream_name="main",
    #                                         uvm_object info=None,
    #                                         string label="error_tr",
    #                                         string desc="",
    #                                         time   error_time=0,
    #                                         bit    keep_active=0)
    def record_error_tr(self, stream_name="main", info=None, label="error_tr", desc="",
            error_time=0, keep_active=0):
        recorder = None  # uvm_recorder
        etype = ""
        handle = 0
        stream = None  # uvm_tr_stream
        db = self.m_get_tr_database()  # uvm_tr_database

        if keep_active:
            etype = "Event, Link"
        else:
            etype = "Event"

        if error_time == 0:
            error_time = sv.realtime()

        if (stream_name == "" or stream_name == "main"):
            if self.m_main_stream is None:
                self.m_main_stream = self.tr_database.open_stream("main", self.get_full_name(), "TVM")
            stream = self.m_main_stream
        else:
            stream = self.get_tr_stream(stream_name)

        handle = 0
        if stream is not None:
            recorder = stream.open_recorder(label, error_time, etype)

            if recorder is not None:
                if label != "":
                    recorder.record_string("label", label)
                if desc != "":
                    recorder.record_string("desc", desc)
                if info is not None:
                    info.record(recorder)

                recorder.close(error_time)

                if keep_active == 0:
                    recorder.free()
                else:
                    handle = recorder.get_handle()
        return handle


    #// Function: record_event_tr
    #//
    #// This function marks an event transaction by a component.
    #//
    #// An `event_time` of 0 indicates to use the current simulation time.
    #//
    #// A handle to the transaction is returned. The `keep_active` bit determines
    #// if the handle may be used for other vendor-specific purposes.
    #//
    #// The strings for `stream_name`, `label`, and `desc` are vendor-specific
    #// identifiers for the transaction.
    #extern function integer record_event_tr (string stream_name="main",
    #                                         uvm_object info=None,
    #                                         string label="event_tr",
    #                                         string desc="",
    #                                         time   event_time=0,
    #                                         bit    keep_active=0)
    def record_event_tr(self, stream_name="main", info=None, label="event_tr",
            desc="", event_time=0,keep_active=0):
        recorder = None  # uvm_recorder
        etype = ""
        handle = 0
        stream = None  # uvm_tr_stream
        db = self.m_get_tr_database()  # uvm_tr_database

        if keep_active:
            etype = "Event, Link"
        else:
            etype = "Event"

        if event_time == 0:
            event_time = sv.realtime()

        if (stream_name == "" or stream_name=="main"):
            if self.m_main_stream is None:
                self.m_main_stream = self.tr_database.open_stream("main", self.get_full_name(), "TVM")
            stream = self.m_main_stream
        else:
            stream = self.get_tr_stream(stream_name)

        handle = 0
        if stream is not None:
            recorder = stream.open_recorder(label, event_time, etype)

            if recorder is not None:
                if label != "":
                    recorder.record_string("label", label)
                if desc != "":
                    recorder.record_string("desc", desc)
                if info is not None:
                    info.record(recorder)

                recorder.close(event_time)

                if keep_active == 0:
                    recorder.free()
                else:
                    handle = recorder.get_handle()
        return handle


    def get_tr_stream(self, name, stream_type_name=""):
        """
        Streams which are retrieved via this method will be stored internally,
        such that later calls to `get_tr_stream` will return the same stream
        reference.

        The stream can be removed from the internal storage via a call
        to `free_tr_stream`.

        Args:
            name (str):Name for the stream
            stream_type_name: Type name for the stream (Default = "")
        Returns:
            UVMTrStream: Stream with this component's full name as scope.
        """
        db = self.m_get_tr_database()  # uvm_tr_database
        if name not in self.m_streams:
            self.m_streams[name] = {}
        if stream_type_name not in self.m_streams[name]:
            self.m_streams[name][stream_type_name] = db.open_stream(name,
                    self.get_full_name(), stream_type_name)
        return self.m_streams[name][stream_type_name]


    #// Function: free_tr_stream
    #// Frees the internal references associated with `stream`.
    #//
    #// The next call to <get_tr_stream> will result in a newly created
    #// <uvm_tr_stream>.  If the current stream is open (or closed),
    #// then it will be freed.
    #extern virtual function void free_tr_stream(uvm_tr_stream stream)
    def free_tr_stream(self, stream):
        # Check the None case...
        if stream is None:
            return

        str_name = stream.get_name()
        str_type_name = stream.get_stream_type_name()
        # Then make sure this name/type_name combo exists
        if (str_name not in self.m_streams or str_type_name not in
                self.m_streams[str_name]):
            return

        # Then make sure this name/type_name combo is THIS stream
        if self.m_streams[str_name][str_type_name] != stream:
            return

        # Then delete it from the arrays
        del self.m_streams[str_name][str_type_name]
        if len(self.m_streams[str_name]) == 0:
            del self.m_streams[str_name]

        # Finally, free the stream if necessary
        if stream.is_open() or stream.is_closed():
            stream.free()


    def m_get_tr_database(self):
        """
        Returns:
        """
        if self.tr_database is None:
            from .uvm_coreservice import UVMCoreService
            cs = UVMCoreService.get()
            self.tr_database = cs.get_default_tr_database()
        return self.tr_database



    def set_int_local(self, field_name, value, recurse=1):
        """
        Args:
            field_name:
            value:
            recurse:
        """
        # call the super function to get child recursion and any registered fields
        super().set_int_local(field_name, value, recurse)

        # set the local properties
        if uvm_is_match(field_name, "recording_detail"):
            self.recording_detail = value


    def m_set_full_name(self):
        """
        m_set_full_name
        ---------------
        """
        #if self.m_parent is None:
        #    uvm_fatal("Should not be called with uvm_root")

        from .uvm_root import UVMRoot
        #top = UVMRoot.get()
        # top = None
        top = []
        if sv.cast(top, self.m_parent, UVMRoot) or self.m_parent is None:
            self.m_name = self.get_name()
        else:
            self.m_name = self.m_parent.get_full_name() + "." + self.get_name()

        for c in self.m_children:
            tmp = self.m_children[c]
            tmp.m_set_full_name()


    def do_resolve_bindings(self):
        """
        do_resolve_bindings
        -------------------
        """
        for s in self.m_children:
            self.m_children[s].do_resolve_bindings()
        self.resolve_bindings()

    #extern                   function void do_flush()
    def do_flush(self):
        for c in self.m_children:
            self.m_children[c].do_flush()
        self.flush()


    #extern virtual function void flush ()
    def flush(self):
        pass


    def m_extract_name(self, name, leaf, remainder):
        """
        Args:
            name:
            leaf:
            remainder:
        Returns:
        """
        _len = len(name)

        i = 0
        for i in range(len(name)):
            if name[i] == ".":
                break

        if i == _len - 1:
            leaf = name
            remainder = ""
            return [leaf, remainder]

        leaf = name[0:i]
        remainder = name[i + 1: _len]

        return [leaf, remainder]
        #endfunction


    def create(self, name=""):
        """
        Overridden to disable component creation using this method.

        Args:
            name (str): Name of the component.
        Returns:
            None - Create cannot be called on `UVMComponent`
        """
        uvm_error("ILLCRT",
            "create cannot be called on a uvm_component. Use create_component instead.")
        return None


    def clone(self):
        """
        Components cannot be cloned. Added this to show `uvm_error` whenever a
        cloning is attempted.

        Returns:
            None - Components cannot be cloned.
        """
        uvm_error("ILLCLN", sv.sformatf(CLONE_ERR, self.get_full_name()))
        return None


    def m_begin_tr(self, tr, parent_handle=0, stream_name="main", label="",
            desc="", begin_time=0):
        """
        Args:
            tr (UVMTransaction):
            parent_handle:
            stream_name (str):
            label (str):
            desc (str):
            begin_time (int):
        Returns:
        """
        e = None  # uvm_event#(uvm_object) e
        name = ""
        kind = ""
        db = None  # uvm_tr_database db
        handle = 0
        link_handle = 0
        stream = None  # uvm_tr_stream
        # uvm_recorder
        recorder = None
        parent_recorder = None
        link_recorder = None

        if tr is None:
            return 0

        db = self.m_get_tr_database()
        if parent_handle != 0:
            parent_recorder = UVMRecorder.get_recorder_from_handle(parent_handle)

        if parent_recorder is None:
            seq = []  # uvm_sequence_item
            from ..seq.uvm_sequence_item import UVMSequenceItem
            if (sv.cast(seq,tr, UVMSequenceItem)):
                seq = seq[0]
                parent_seq = seq.get_parent_sequence()
                if (parent_seq is not None):
                    parent_recorder = parent_seq.m_tr_recorder

        if parent_recorder is not None:
            link_handle = tr.begin_child_tr(begin_time, parent_recorder.get_handle())
        else:
            link_handle = tr.begin_tr(begin_time)

        if link_handle != 0:
            link_recorder = UVMRecorder.get_recorder_from_handle(link_handle)

        if tr.get_name() != "":
            name = tr.get_name()
        else:
            name = tr.get_type_name()

        # TODO needed for recording only
        if self.recording_detail != UVM_NONE:
            if (stream_name == "") or (stream_name == "main"):
                if self.m_main_stream is None:
                    self.m_main_stream = db.open_stream("main", self.get_full_name(), "TVM")
                    stream = self.m_main_stream
            else:
                stream = self.get_tr_stream(stream_name)

            if stream is not None:
                kind = "Begin_End, Link"
                if parent_recorder is None:
                    kind = "Begin_No_Parent, Link"
                recorder = stream.open_recorder(name, begin_time, kind)

                if recorder is not None:
                    if label != "":
                        recorder.record_string("label", label)
                    if desc != "":
                        recorder.record_string("desc", desc)

                    if parent_recorder is not None:
                        self.tr_database.establish_link(UVMParentChildLink.get_link(parent_recorder,
                                                                                  recorder))
                    if link_recorder is not None:
                        self.tr_database.establish_link(UVMRelatedLink.get_link(recorder,
                                                                             link_recorder))
                    self.m_tr_h[tr] = recorder

            handle = 0
            if recorder is not None:
                handle = recorder.get_handle()
            self.do_begin_tr(tr, stream_name, handle)

        e = self.event_pool.get("begin_tr")
        if e is not None:
            e.trigger(tr)
        return handle


    #type_name = "uvm_component"
    #def get_type_name(self):
    #    return UVMComponent.type_name

    #extern         function void   do_print(uvm_printer printer)

    def m_set_cl_msg_args(self):
        """
        Internal methods for setting up command line messaging stuff
        #extern function void m_set_cl_msg_args
        """
        self.m_set_cl_verb()
        self.m_set_cl_action()
        self.m_set_cl_sev()


    first_m_set_cl_verb = 1

    def m_set_cl_verb(self):
        """
        #extern function void m_set_cl_verb
        """
        #  // _ALL_ can be used for ids
        #  // +uvm_set_verbosity=<comp>,<id>,<verbosity>,<phase|time>,<offset>
        #  // +uvm_set_verbosity=uvm_test_top.env0.agent1.*,_ALL_,UVM_FULL,time,800
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        from .uvm_cmdline_processor import UVMCmdlineProcessor

        values = []  # static string values[$]
        args = []  # string args[$]
        clp = UVMCmdlineProcessor.get_inst()
        cs = UVMCoreService.get()
        top = cs.get_root()

        if len(values) == 0:
            clp.get_arg_values("+uvm_set_verbosity=", values)

        for i in range(len(values)):
            setting = VerbositySetting()
            args.clear()
            uvm_split_string(values[i], ",", args)

            # Warning is already issued in uvm_root, so just don't keep it
            len_match = len(args) not in [4, 5]
            setting.verbosity = clp.m_convert_verb(args[2])
            if UVMComponent.first_m_set_cl_verb and (len_match or setting.verbosity == -1):
                del values[i]
            else:
                setting.comp = args[0]
                setting.id = args[1]
                setting.verbosity = clp.m_convert_verb(args[2])
                setting.phase = args[3]
                setting.offset = 0
                if len(args) == 5:
                    setting.offset = int(args[4])
                if ((setting.phase == "time") and (self == top)):
                    UVMComponent.m_time_settings.append(setting)

                if uvm_is_match(setting.comp, self.get_full_name()):
                    if((setting.phase == "" or setting.phase == "build" or
                            setting.phase == "time") and setting.offset == 0):

                        if setting.id == "_ALL_":
                            self.set_report_verbosity_level(setting.verbosity)
                        else:
                            self.set_report_id_verbosity(setting.id, setting.verbosity)
                    else:
                        if setting.phase != "time":
                            self.m_verbosity_settings.append(setting)

        if self == top:
            cocotb.fork(self.m_fork_time_settings(top))
        UVMComponent.first_m_set_cl_verb = 0


    async def m_fork_time_settings(self, top):
        m_time_settings = UVMComponent.m_time_settings
        #fork begin
        last_time = 0
        if len(m_time_settings) > 0:
            m_time_settings.sort(key=lambda item: item.offset)
        for i in range(len(m_time_settings)):
            comps = []
            top.find_all(m_time_settings[i].comp, comps)
            duration = m_time_settings[i].offset - last_time
            last_time = m_time_settings[i].offset
            cocotb.fork(self.m_set_comp_settings(i, comps.copy(), duration))
        #end join_none // fork begin


    async def m_set_comp_settings(self, i, comps, dur):
        m_time_settings = UVMComponent.m_time_settings
        await Timer(dur)
        if m_time_settings[i].id == "_ALL_":
            for comp in comps:
                comp.set_report_verbosity_level(m_time_settings[i].verbosity)
        else:
            for comp in comps:
                comp.set_report_id_verbosity(m_time_settings[i].id, m_time_settings[i].verbosity)


    initialized_m_set_cl_action = 0

    #extern function void m_set_cl_action
    def m_set_cl_action(self):
        # _ALL_ can be used for ids or severities
        # +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>
        # +uvm_set_action=uvm_test_top.env0.*,_ALL_,UVM_ERROR,UVM_NO_ACTION
        sev = 0
        action = 0

        if not UVMComponent.initialized_m_set_cl_action:
            from .uvm_cmdline_processor import UVMCmdlineProcessor
            values = []
            UVMCmdlineProcessor.uvm_cmdline_proc.get_arg_values("+uvm_set_action=", values)
            for idx in range(len(values)):
                t = uvm_cmdline_parsed_arg_t()
                args = []
                uvm_split_string(values[idx], ",", args)

                if len(args) != 4:
                    uvm_warning("INVLCMDARGS", sv.sformatf(INV_WARN1, len(args), values[idx]))

                if((args[2] != "_ALL_") and not uvm_string_to_severity(args[2], sev)):
                    uvm_warning("INVLCMDARGS", sv.sformatf(INV_WARN2, args[2], values[idx]))
                    continue

                if not uvm_string_to_action(args[3], action):
                    uvm_warning("INVLCMDARGS", sv.sformatf(INV_WARN3, args[3], values[idx]))
                    continue
                t.args = args
                t.arg = values[idx]
                UVMComponent.m_uvm_applied_cl_action.append(t)

            UVMComponent.initialized_m_set_cl_action = 1

        for i in range(len(UVMComponent.m_uvm_applied_cl_action)):
            args = UVMComponent.m_uvm_applied_cl_action[i].args

            if not uvm_is_match(args[0], self.get_full_name()):
                continue

            sev = uvm_string_to_severity(args[2], sev)
            action = uvm_string_to_action(args[3], action)

            UVMComponent.m_uvm_applied_cl_action[i].used += 1
            if args[1] == "_ALL_":
                if args[2] == "_ALL_":
                    self.set_report_severity_action(UVM_INFO, action)
                    self.set_report_severity_action(UVM_WARNING, action)
                    self.set_report_severity_action(UVM_ERROR, action)
                    self.set_report_severity_action(UVM_FATAL, action)
                else:
                    self.set_report_severity_action(sev, action)
            else:
                if args[2] == "_ALL_":
                    self.set_report_id_action(args[1], action)
                else:
                    self.set_report_severity_id_action(sev, args[1], action)

    initialized_m_set_cl_sev = 0

    #extern function void m_set_cl_sev
    def m_set_cl_sev(self):
        #  // _ALL_ can be used for ids or severities
        #  //  +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>
        #  //  +uvm_set_severity=uvm_test_top.env0.*,BAD_CRC,UVM_ERROR,UVM_WARNING

        orig_sev = 0
        sev = 0

        if not UVMComponent.initialized_m_set_cl_sev:
            values = []
            from .uvm_cmdline_processor import UVMCmdlineProcessor
            UVMCmdlineProcessor.uvm_cmdline_proc.get_arg_values("+uvm_set_severity=",values)
            for idx in range(len(values)):
                t = uvm_cmdline_parsed_arg_t()
                args = []  # string[$]
                uvm_split_string(values[idx], ",", args)
                if len(args) != 4:
                    uvm_warning("INVLCMDARGS", sv.sformatf(INV_WARN4, len(args), values[idx]))
                    continue

                if args[2] != "_ALL_" and not uvm_string_to_severity(args[2], orig_sev):
                    uvm_warning("INVLCMDARGS", sv.sformatf(INV_WARN5, args[2], values[idx]))
                    continue

                if uvm_string_to_severity(args[3], sev) == -1:
                    uvm_warning("INVLCMDARGS", sv.sformatf(INV_WARN6, args[3], values[idx]))
                    continue

                t.args = args
                t.arg = values[idx]
                UVMComponent.m_uvm_applied_cl_sev.append(t)
            UVMComponent.initialized_m_set_cl_sev = 1
        m_uvm_applied_cl_sev = UVMComponent.m_uvm_applied_cl_sev

        for i in range(len(m_uvm_applied_cl_sev)):
            args = m_uvm_applied_cl_sev[i].args

            if not uvm_is_match(args[0], self.get_full_name()):
                continue

            orig_sev = uvm_string_to_severity(args[2], orig_sev)
            sev = uvm_string_to_severity(args[3], sev)
            m_uvm_applied_cl_sev[i].used += 1
            if (args[1] == "_ALL_" and args[2] == "_ALL_"):
                self.set_report_severity_override(UVM_INFO,sev)
                self.set_report_severity_override(UVM_WARNING,sev)
                self.set_report_severity_override(UVM_ERROR,sev)
                self.set_report_severity_override(UVM_FATAL,sev)
            elif (args[1] == "_ALL_"):
                self.set_report_severity_override(orig_sev,sev)
            elif (args[2] == "_ALL_"):
                self.set_report_severity_id_override(UVM_INFO,args[1],sev)
                self.set_report_severity_id_override(UVM_WARNING,args[1],sev)
                self.set_report_severity_id_override(UVM_ERROR,args[1],sev)
                self.set_report_severity_id_override(UVM_FATAL,args[1],sev)
            else:
                self.set_report_severity_id_override(orig_sev,args[1],sev)


    m_uvm_applied_cl_action: List[uvm_cmdline_parsed_arg_t] = []
    m_uvm_applied_cl_sev: List[uvm_cmdline_parsed_arg_t] = []

    def m_add_child(self, child):
        if child.get_name() in self.m_children:
            old_child = self.m_children[child.get_name()]
            uvm_warning("BDCLD",
                    "A child with name {} (type={}) exists"
                    .format(child.get_name(), old_child.get_type_name()))
            return False

        self.m_children[child.get_name()] = child
        self.m_children_ordered.append(child)
        self.m_children_by_handle[child] = child
        return True

    def has_first_child(self):
        return len(self.m_children_ordered) > 0

    def has_next_child(self):
        return len(self.m_children_ordered) > (self.child_ptr + 1)

    def m_apply_verbosity_settings(self, phase):
        """
        #extern function void m_apply_verbosity_settings(uvm_phase phase)
        Args:
            phase:
        """
        pass
        for i in self.m_verbosity_settings:
            if phase.get_name() == self.m_verbosity_settings[i].phase:
                if self.m_verbosity_settings[i].offset == 0:
                    if self.m_verbosity_settings[i].id == "_ALL_":
                        self.set_report_verbosity_level(self.m_verbosity_settings[i].verbosity)
                    else:
                        self.set_report_id_verbosity(self.m_verbosity_settings[i].id,
                                self.m_verbosity_settings[i].verbosity)
                else:
                    #process p = process::self()
                    #string p_rand = p.get_randstate()
                    #fork begin
                    setting = self.m_verbosity_settings[i]
                    #setting.offset
                    if setting.id == "_ALL_":
                        self.set_report_verbosity_level(setting.verbosity)
                    else:
                        self.set_report_id_verbosity(setting.id, setting.verbosity)
                    #end join_none
                    #p.set_randstate(p_rand)
                # Remove after use
                del self.m_verbosity_settings[i]

    def kill(self):
        """
        Kill internal run process of this component.
        """
        if self.m_run_process is not None:
            if hasattr(self.m_run_process, 'kill'):
                self.m_run_process.kill()
            else:
                print("No kill() available")


#//------------------------------------------------------------------------------
#//
#// Factory Methods
#//
#//------------------------------------------------------------------------------

#
#
#// set_inst_override
#// -----------------
#
#function void  uvm_component::set_inst_override (string relative_inst_path,
#                                                 string original_type_name,
#                                                 string override_type_name)
#  full_inst_path = ""
#  factory= _get_factory()
#
#  if (relative_inst_path == "")
#    full_inst_path = get_full_name()
#  else
#    full_inst_path = {get_full_name(), ".", relative_inst_path}
#
#  factory.set_inst_override_by_name(
#                            original_type_name,
#                            override_type_name,
#                            full_inst_path)
#endfunction
#
#
#
#
#//------------------------------------------------------------------------------
#//
#// Phase interface
#//
#//------------------------------------------------------------------------------
#
#
#// phase methods
#//--------------
#// these are prototypes for the methods to be implemented in user components
#// build_phase() has a default implementation, the others have an empty default
#
#// these phase methods are common to all components in UVM. For backward
#// compatibility, they call the old style name (without the _phse)
#
#function void uvm_component::connect_phase(uvm_phase phase)
#  connect()
#  return
#endfunction
#function void uvm_component::end_of_elaboration_phase(uvm_phase phase)
#  end_of_elaboration()
#  return
#endfunction
#function void uvm_component::extract_phase(uvm_phase phase)
#  extract()
#  return
#endfunction
#function void uvm_component::check_phase(uvm_phase phase)
#  check()
#  return
#endfunction
#function void uvm_component::report_phase(uvm_phase phase)
#  report()
#  return
#endfunction
#
#
#// These are the old style phase names. In order for runtime phase names
#// to not conflict with user names, the _phase postfix was added.
#
#function void uvm_component::connect();             return; endfunction
#function void uvm_component::end_of_elaboration();  return; endfunction
#function void uvm_component::extract();             return; endfunction
#function void uvm_component::check();               return; endfunction
#function void uvm_component::report();              return; endfunction
#function void uvm_component::final_phase(uvm_phase phase);         return; endfunction
#
#// these runtime phase methods are only called if a set_domain() is done
#
#//------------------------------
#// phase / schedule / domain API
#//------------------------------
#// methods for VIP creators and integrators to use to set up schedule domains
#// - a schedule is a named, organized group of phases for a component base type
#// - a domain is a named instance of a schedule in the master phasing schedule
#
#
#// suspend
#// -------
#
#task uvm_component::suspend()
#   `uvm_warning("COMP/SPND/UNIMP", "suspend() not implemented")
#endtask
#
#
#// resume
#// ------
#
#task uvm_component::resume()
#   `uvm_warning("COMP/RSUM/UNIMP", "resume() not implemented")
#endtask
#
#
#
#
#
#
#//------------------------------------------------------------------------------
#//
#// Configuration interface
#//
#//------------------------------------------------------------------------------
#
#

#// Undocumented struct for storing clone bit along w/
#// object on set_config_object(...) calls
#class uvm_config_object_wrapper
#   uvm_object obj
#   bit clone
#endclass : uvm_config_object_wrapper


#
#
#// do_print (override)
#// --------
#
#function void uvm_component::do_print(uvm_printer printer)
#  string v
#  super.do_print(printer)
#
#  // It is printed only if its value is other than the default (UVM_NONE)
#  if(uvm_verbosity'(recording_detail) != UVM_NONE)
#    case (recording_detail)
#      UVM_LOW : printer.print_generic("recording_detail", "uvm_verbosity",
#        $bits(recording_detail), "UVM_LOW")
#      UVM_MEDIUM : printer.print_generic("recording_detail", "uvm_verbosity",
#        $bits(recording_detail), "UVM_MEDIUM")
#      UVM_HIGH : printer.print_generic("recording_detail", "uvm_verbosity",
#        $bits(recording_detail), "UVM_HIGH")
#      UVM_FULL : printer.print_generic("recording_detail", "uvm_verbosity",
#        $bits(recording_detail), "UVM_FULL")
#      default : printer.print_field_int("recording_detail", recording_detail,
#        $bits(recording_detail), UVM_DEC, , "integral")
#    endcase
#
#endfunction

def _get_factory():
    from .uvm_coreservice import UVMCoreService
    cs = UVMCoreService.get()
    factory = cs.get_factory()
    return factory
