
import cocotb
from cocotb.triggers import Timer
from .uvm_report_object import UVMReportObject
from .uvm_object_globals import (UVM_NONE, UVM_MEDIUM, UVM_PHASE_DONE, UVM_INFO,
    UVM_CHECK_FIELDS, UVM_PHASE_SCHEDULE)
from .uvm_common_phases import UVMBuildPhase
from .uvm_domain import UVMDomain
from .uvm_debug import uvm_debug
from .uvm_object import UVMObject
from .uvm_queue import UVMQueue
from .uvm_pool import UVMEventPool
from .sv import sv, uvm_split_string
from ..macros import uvm_info, uvm_fatal, uvm_warning, uvm_error
from .uvm_recorder import UVMRecorder
from .uvm_globals import uvm_is_match
from .uvm_factory import UVMObjectWrapper
from .uvm_links import (UVMRelatedLink, UVMParentChildLink)


class VerbositySetting:
    def __init__(self):
        self.comp = ""
        self.phase = ""
        self.id = ""
        self.offset = 0
        self.verbosity = UVM_MEDIUM

CLONE_ERR = ("Attempting to clone '%s'.  Clone cannot be called on a uvm_component. "
    + " The clone target variable will be set to None.")



class uvm_cmdline_parsed_arg_t:
    def __init__(self):
        self.arg = ""
        self.args = []
        self.used = 0


#------------------------------------------------------------------------------
#
# CLASS: uvm_component
#
# The uvm_component class is the root base class for UVM components. In
# addition to the features inherited from <uvm_object> and <uvm_report_object>,
# uvm_component provides the following interfaces:
#
# Hierarchy - provides methods for searching and traversing the component
#     hierarchy.
#
# Phasing - defines a phased test flow that all components follow, with a
#     group of standard phase methods and an API for custom phases and
#     multiple independent phasing domains to mirror DUT behavior e.g. power
#
# Reporting - provides a convenience interface to the <uvm_report_handler>. All
#     messages, warnings, and errors are processed through this interface.
#
# Transaction recording - provides methods for recording the transactions
#     produced or consumed by the component to a transaction database (vendor
#     specific).
#
# Factory - provides a convenience interface to the <uvm_factory>. The factory
#     is used to create new components and other objects based on type-wide and
#     instance-specific configuration.
#
# The uvm_component is automatically seeded during construction using UVM
# seeding, if enabled. All other objects must be manually reseeded, if
# appropriate. See <uvm_object::reseed> for more information.
#
#------------------------------------------------------------------------------

class UVMComponent(UVMReportObject):
    """ Base class for defining UVM components"""

    #// Variable: print_config_matches
    #//
    #// Setting this static variable causes uvm_config_db::get() to print info about
    #// matching configuration settings as they are being applied.
    print_config_matches = False

    #  Function: new
    #
    #  Creates a new component with the given leaf instance ~name~ and handle
    #  to its ~parent~.  If the component is a top-level component (i.e. it is
    #  created in a static module or interface), ~parent~ should be ~None~.
    #
    #  The component will be inserted as a child of the ~parent~ object, if any.
    #  If ~parent~ already has a child by the given ~name~, an error is produced.
    #
    #  If ~parent~ is ~None~, then the component will become a child of the
    #  implicit top-level component, ~uvm_top~.
    #
    #  All classes derived from uvm_component must call super.new(name,parent).
    def __init__(self, name, parent):
        UVMReportObject.__init__(self, name)
        self.m_children = {}  # uvm_component[string]

        #// Variable: print_enabled
        #//
        #// This bit determines if this component should automatically be printed as a
        #// child of its parent object.
        #//
        #// By default, all children are printed. However, this bit allows a parent
        #// component to disable the printing of specific children.
        self.print_enabled = True
        self.m_current_phase = None
        self.m_parent = None
        self.m_children_by_handle = {}
        self.m_children_ordered = []

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
        # process    m_phase_process

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
            uvm_fatal("COMP/INTERNAL",
                    "attempt to find build phase object failed",UVM_NONE)
        if bld.get_state() == UVM_PHASE_DONE:
            parent_name = top.get_full_name()
            if parent is not None:
                parent_name = parent.get_full_name()
            uvm_fatal("ILLCRT", ("It is illegal to create a component ('" +
                name + "' under '" + parent_name + "') after the build phase has ended."))

        if name == "":
            name = "COMP_" + UVMObject.inst_count

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
        if self.m_parent.add_child(self) is False:
            self.m_parent = None

        self.m_domain = parent.m_domain  # by default, inherit domains from parents

        # Now that inst name is established, reseed (if use_uvm_seeding is set)
        self.reseed()

        # Do local configuration settings
        arr = []
        from .uvm_config_db import UVMConfigDb
        if (UVMConfigDb.get(self, "", "recording_detail", arr)):
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

    # Function: get_parent
    #
    # Returns a handle to this component's parent, or ~None~ if it has no parent.
    def get_parent(self):
        return self.m_parent

    # Function: get_full_name
    #
    # Returns the full hierarchical name of this object. The default
    # implementation concatenates the hierarchical name of the parent, if any,
    # with the leaf name of this object, as given by <uvm_object::get_name>.
    def get_full_name(self):
        """ Returns the full hierarchical name of component """
        if self.m_name == "":
            return self.get_name()
        else:
            return self.m_name

    # Function: get_children
    #
    # This function populates the end of the ~children~ array with the
    # list of this component's children.
    #
    #|   uvm_component array[$]
    #|   my_comp.get_children(array)
    #|   foreach(array[i])
    #|     do_something(array[i])
    def get_children(self, children):
        for name in self.m_children:
            children.append(self.m_children[name])

    # Function: get_child
    def get_child(self, name):
        if name in self.m_children:
            return self.m_children[name]

    # Function: get_next_child
    def get_next_child(self):
        self.child_ptr += 1
        if (self.child_ptr < len(self.m_children_ordered)):
            return self.m_children_ordered[self.child_ptr]
        return None

    # Function: get_first_child
    #
    # These methods are used to iterate through this component's children, if
    # any. For example, given a component with an object handle, ~comp~, the
    # following code calls <uvm_object::print> for each child:
    #
    #|    string name
    #|    uvm_component child
    #|    if (comp.get_first_child(name))
    #|      do begin
    #|        child = comp.get_child(name)
    #|        child.print()
    #|      end while (comp.get_next_child(name))
    def get_first_child(self):
        self.child_ptr = 0
        return self.m_children_ordered[0]

    # Function: get_num_children
    #
    # Returns the number of this component's children.
    def get_num_children(self):
        return len(self.m_children_ordered)

    # Function: has_child
    #
    # Returns 1 if this component has a child with the given ~name~, 0 otherwise.
    def has_child(self, name):
        return name in self.m_children

    # Function - set_name
    #
    # Renames this component to ~name~ and recalculates all descendants'
    # full names. This is an internal function for now.
    def set_name(self, name):
        if self.m_name != "":
            uvm_error("INVSTNM", ("It is illegal to change the name of a component."
                + "The component name will not be changed to \"{}\"".format(name)))
            return
        super().set_name(name)
        self.m_set_full_name()

    # Function: lookup
    #
    # Looks for a component with the given hierarchical ~name~ relative to this
    # component. If the given ~name~ is preceded with a '.' (dot), then the search
    # begins relative to the top level (absolute lookup). The handle of the
    # matching component is returned, else ~None~. The name must not contain
    # wildcards.
    # TODO extern function uvm_component lookup (string name)
    def lookup(self, name):
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
        #endfunction


    # Function: get_depth
    #
    # Returns the component's depth from the root level. uvm_top has a
    # depth of 0. The test and any other top level components have a depth
    # of 1, and so on.
    # TODO extern function int unsigned get_depth()
    def get_depth(self):
        if self.m_name == "":
            return 0
        get_depth = 1
        for i in range(len(self.m_name)):
            if (self.m_name[i] == "."):
                get_depth += 1
        return get_depth
        #endfunction
        #

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

    # Function: build_phase
    #
    # The <uvm_build_phase> phase implementation method.
    #
    # Any override should call super.build_phase(phase) to execute the automatic
    # configuration of fields registered in the component by calling
    # <apply_config_settings>.
    # To turn off automatic configuration for a component,
    # do not call super.build_phase(phase).
    #
    # This method should never be called directly.
    def build_phase(self, phase):
        self.m_build_done = True
        self.build()

    # For backward compatibility the base <build_phase> method calls <build>.
    def build(self):
        self.m_build_done = True
        self.apply_config_settings(UVMComponent.print_config_matches)
        if self.m_phasing_active == 0:
            uvm_warning("UVM_DEPRECATED",
                    "build()/build_phase() has been called explicitly")

    # Function: connect_phase
    #
    # The <uvm_connect_phase> phase implementation method.
    #
    # This method should never be called directly.
    def connect_phase(self, phase):
        pass

    # For backward compatibility the base connect_phase method calls connect.
    # extern virtual function void connect()

    # Function: end_of_elaboration_phase
    #
    # The <uvm_end_of_elaboration_phase> phase implementation method.
    #
    # This method should never be called directly.
    def end_of_elaboration_phase(self, phase):
        pass

    # For backward compatibility the base <end_of_elaboration_phase> method calls <end_of_elaboration>.
    # extern virtual function void end_of_elaboration()

    # Function: start_of_simulation_phase
    #
    # The <uvm_start_of_simulation_phase> phase implementation method.
    #
    # This method should never be called directly.

    def start_of_simulation_phase(self, phase):
        self.start_of_simulation()
        return

    # For backward compatibility the base <start_of_simulation_phase> method calls <start_of_simulation>.
    # extern virtual function void start_of_simulation()
    def start_of_simulation(self):
        return

    # Task: run_phase
    #
    # The <uvm_run_phase> phase implementation method.
    #
    # This task returning or not does not indicate the end
    # or persistence of this phase.
    # Thus the phase will automatically
    # end once all objections are dropped using ~phase.drop_objection()~.
    #
    # Any processes forked by this task continue to run
    # after the task returns,
    # but they will be killed once the phase ends.
    #
    # The run_phase task should never be called directly.
    @cocotb.coroutine
    def run_phase(self, phase):
        uvm_debug(self, 'run_phase', self.get_name() + ' yielding self.run()')
        # self.m_run_process = cocotb.fork(self.run())
        # yield self.m_run_process
        yield self.run()

    # For backward compatibility the base <run_phase> method calls <run>.
    # extern virtual task run()
    @cocotb.coroutine
    def run(self):
        uvm_debug(self, 'run', self.get_name() + ' yield Timer(0) in self.run()')
        yield Timer(0)

    #// Task: pre_reset_phase
    #//
    #// The <uvm_pre_reset_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task pre_reset_phase(uvm_phase phase)
    @cocotb.coroutine
    def pre_reset_phase(self, phase):
        yield Timer(0)

    #// Task: reset_phase
    #//
    #// The <uvm_reset_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task reset_phase(uvm_phase phase)
    @cocotb.coroutine
    def reset_phase(self, phase):
        yield Timer(0)

    #// Task: post_reset_phase
    #//
    #// The <uvm_post_reset_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task post_reset_phase(uvm_phase phase)
    @cocotb.coroutine
    def post_reset_phase(self, phase):
        yield Timer(0)

    #// Task: pre_configure_phase
    #//
    #// The <uvm_pre_configure_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task pre_configure_phase(uvm_phase phase)
    @cocotb.coroutine
    def pre_configure_phase(self, phase):
        yield Timer(0)

    #// Task: configure_phase
    #//
    #// The <uvm_configure_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task configure_phase(uvm_phase phase)
    @cocotb.coroutine
    def configure_phase(self, phase):
        yield Timer(0)

    #// Task: post_configure_phase
    #//
    #// The <uvm_post_configure_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task post_configure_phase(uvm_phase phase)
    @cocotb.coroutine
    def post_configure_phase(self, phase):
        yield Timer(0)

    #// Task: pre_main_phase
    #//
    #// The <uvm_pre_main_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task pre_main_phase(uvm_phase phase)
    @cocotb.coroutine
    def pre_main_phase(self, phase):
        yield Timer(0)

    #// Task: main_phase
    #//
    #// The <uvm_main_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task main_phase(uvm_phase phase)
    @cocotb.coroutine
    def main_phase(self, phase):
        yield Timer(0)

    #// Task: post_main_phase
    #//
    #// The <uvm_post_main_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task post_main_phase(uvm_phase phase)
    @cocotb.coroutine
    def post_main_phase(self, phase):
        yield Timer(0)

    #// Task: pre_shutdown_phase
    #//
    #// The <uvm_pre_shutdown_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task pre_shutdown_phase(uvm_phase phase)
    @cocotb.coroutine
    def pre_shutdown_phase(self, phase):
        yield Timer(0)

    #// Task: shutdown_phase
    #//
    #// The <uvm_shutdown_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task shutdown_phase(uvm_phase phase)
    @cocotb.coroutine
    def shutdown_phase(self, phase):
        yield Timer(0)

    #// Task: post_shutdown_phase
    #//
    #// The <uvm_post_shutdown_phase> phase implementation method.
    #//
    #// This task returning or not does not indicate the end
    #// or persistence of this phase.
    #// It is necessary to raise an objection
    #// using ~phase.raise_objection()~ to cause the phase to persist.
    #// Once all components have dropped their respective objection
    #// using ~phase.drop_objection()~, or if no components raises an
    #// objection, the phase is ended.
    #//
    #// Any processes forked by this task continue to run
    #// after the task returns,
    #// but they will be killed once the phase ends.
    #//
    #// This method should not be called directly.
    #extern virtual task post_shutdown_phase(uvm_phase phase)
    @cocotb.coroutine
    def post_shutdown_phase(self, phase):
        yield Timer(0)

    #// Function: extract_phase
    #//
    #// The <uvm_extract_phase> phase implementation method.
    #//
    #// This method should never be called directly.
    def extract_phase(self, phase):
        pass

    #// For backward compatibility the base extract_phase method calls extract.
    #extern virtual function void extract()

    #// Function: check_phase
    #//
    #// The <uvm_check_phase> phase implementation method.
    #//
    #// This method should never be called directly.
    def check_phase(self, phase):
        pass

    #// For backward compatibility the base check_phase method calls check.
    #extern virtual function void check()

    #// Function: report_phase
    #//
    #// The <uvm_report_phase> phase implementation method.
    #//
    #// This method should never be called directly.
    def report_phase(self, phase):
        pass

    #// Function: final_phase
    #//
    #// The <uvm_final_phase> phase implementation method.
    #//
    #// This method should never be called directly.
    def final_phase(self, phase):
        self.m_rh._close_files()

    #// Function: phase_started
    #//
    #// Invoked at the start of each phase. The ~phase~ argument specifies
    #// the phase being started. Any threads spawned in this callback are
    #// not affected when the phase ends.
    def phase_started(self, phase):
        pass

    #// Function: phase_ready_to_end
    #//
    #// Invoked when all objections to ending the given ~phase~ and all
    #// sibling phases have been dropped, thus indicating that ~phase~ is
    #// ready to begin a clean exit. Sibling phases are any phases that
    #// have a common successor phase in the schedule plus any phases that
    #// sync'd to the current phase. Components needing to consume delta
    #// cycles or advance time to perform a clean exit from the phase
    #// may raise the phase's objection.
    #//
    #// |phase.raise_objection(this,"Reason")
    #//
    #// It is the responsibility of this component to drop the objection
    #// once it is ready for this phase to end (and processes killed).
    #// If no objection to the given ~phase~ or sibling phases are raised,
    #// then phase_ended() is called after a delta cycle.  If any objection
    #// is raised, then when all objections to ending the given ~phase~
    #// and siblings are dropped, another iteration of phase_ready_to_end
    #// is called.  To prevent endless iterations due to coding error,
    #// after 20 iterations, phase_ended() is called regardless of whether
    #// previous iteration had any objections raised.
    #
    #extern virtual function void phase_ready_to_end (uvm_phase phase)

    #// Function: phase_ended
    #//
    #// Invoked at the end of each phase. The ~phase~ argument specifies
    #// the phase that is ending.  Any threads spawned in this callback are
    #// not affected when the phase ends.
    def phase_ended(self, phase):
        pass

    def phase_ready_to_end(self, phase):
        pass

    #//--------------------------------------------------------------------
    #// phase / schedule / domain API
    #//--------------------------------------------------------------------

    #
    #// Function: set_domain
    #//
    #// Apply a phase domain to this component and, if ~hier~ is set,
    #// recursively to all its children.
    #//
    #// Calls the virtual <define_domain> method, which derived components can
    #// override to augment or replace the domain definition of its base class.
    #//
    #extern function void set_domain(uvm_domain domain, int hier=1)
    #// set_domain
    #// ----------
    #// assigns this component [tree] to a domain. adds required schedules into graph
    #// If called from build, ~hier~ won't recurse into all chilren (which don't exist yet)
    #// If we have components inherit their parent's domain by default, then ~hier~
    #// isn't needed and we need a way to prevent children from inheriting this component's domain
    #
    def set_domain(self, domain, hier=True):
        # build and store the custom domain
        self.m_domain = domain
        self.define_domain(domain)
        if hier is True:
            for c in self.m_children:
                self.m_children[c].set_domain(domain)

    # Function: get_domain
    #
    # Return handle to the phase domain set on this component
    def get_domain(self):
        return self.m_domain

    #// Function: define_domain
    #//
    #// Builds custom phase schedules into the provided ~domain~ handle.
    #//
    #// This method is called by <set_domain>, which integrators use to specify
    #// this component belongs in a domain apart from the default 'uvm' domain.
    #//
    #// Custom component base classes requiring a custom phasing schedule can
    #// augment or replace the domain definition they inherit by overriding
    #// their ~defined_domain~. To augment, overrides would call super.define_domain().
    #// To replace, overrides would not call super.define_domain().
    #//
    #// The default implementation adds a copy of the ~uvm~ phasing schedule to
    #// the given ~domain~, if one doesn't already exist, and only if the domain
    #// is currently empty.
    #//
    #// Calling <set_domain>
    #// with the default ~uvm~ domain (i.e. <uvm_domain::get_uvm_domain> ) on
    #// a component with no ~define_domain~ override effectively reverts the
    #// that component to using the default ~uvm~ domain. This may be useful
    #// if a branch of the testbench hierarchy defines a custom domain, but
    #// some child sub-branch should remain in the default ~uvm~ domain,
    #// call <set_domain> with a new domain instance handle with ~hier~ set.
    #// Then, in the sub-branch, call <set_domain> with the default ~uvm~ domain handle,
    #// obtained via <uvm_domain::get_uvm_domain>.
    #//
    #// Alternatively, the integrator may define the graph in a new domain externally,
    #// then call <set_domain> to apply it to a component.
    #extern virtual protected function void define_domain(uvm_domain domain)
    def define_domain(self, domain):
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
        #
        #endfunction

    #// Function: set_phase_imp
    #//
    #// Override the default implementation for a phase on this component (tree) with a
    #// custom one, which must be created as a singleton object extending the default
    #// one and implementing required behavior in exec and traverse methods
    #//
    #// The ~hier~ specifies whether to apply the custom functor to the whole tree or
    #// just this component.
    def set_phase_imp(self, phase, imp, hier=1):
        self.m_phase_imps[phase] = imp
        if hier:
            for c in self.m_children:
                self.m_children[c].set_phase_imp(phase,imp,hier)
    #endfunction

    #
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

    #// Function: resolve_bindings
    #//
    #// Processes all port, export, and imp connections. Checks whether each port's
    #// min and max connection requirements are met.
    #//
    #// It is called just before the end_of_elaboration phase.
    #//
    #// Users should not call directly.
    def resolve_bindings(self):
        return

    #extern function string massage_scope(string scope)

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

    #// Function: check_config_usage
    #//
    #// Check all configuration settings in a components configuration table
    #// to determine if the setting has been used, overridden or not used.
    #// When ~recurse~ is 1 (default), configuration for this and all child
    #// components are recursively checked. This function is automatically
    #// called in the check phase, but can be manually called at any time.
    #//
    #// To get all configuration information prior to the run phase, do something
    #// like this in your top object:
    #//|  function void start_of_simulation_phase(uvm_phase phase)
    #//|    check_config_usage()
    #//|  endfunction

    #extern function void check_config_usage (bit recurse=1)

    #// Function: apply_config_settings
    #//
    #// Searches for all config settings matching this component's instance path.
    #// For each match, the appropriate set_*_local method is called using the
    #// matching config setting's field_name and value. Provided the set_*_local
    #// method is implemented, the component property associated with the
    #// field_name is assigned the given value.
    #//
    #// This function is called by <uvm_component::build_phase>.
    #//
    #// The apply_config_settings method determines all the configuration
    #// settings targeting this component and calls the appropriate set_*_local
    #// method to set each one. To work, you must override one or more set_*_local
    #// methods to accommodate setting of your component's specific properties.
    #// Any properties registered with the optional `uvm_*_field macros do not
    #// require special handling by the set_*_local methods; the macros provide
    #// the set_*_local functionality for you.
    #//
    #// If you do not want apply_config_settings to be called for a component,
    #// then the build_phase() method should be overloaded and you should not call
    #// super.build_phase(phase). Likewise, apply_config_settings can be overloaded to
    #// customize automated configuration.
    #//
    #// When the ~verbose~ bit is set, all overrides are printed as they are
    #// applied. If the component's <print_config_matches> property is set, then
    #// apply_config_settings is automatically called with ~verbose~ = 1.

    #extern virtual function void apply_config_settings (bit verbose = 0)
    def apply_config_settings(self, verbose=0):
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
        #endfunction



    #// Function: print_config_settings
    #//
    #// Called without arguments, print_config_settings prints all configuration
    #// information for this component, as set by previous calls to <uvm_config_db::set()>.
    #// The settings are printing in the order of their precedence.
    #//
    #// If ~field~ is specified and non-empty, then only configuration settings
    #// matching that field, if any, are printed. The field may not contain
    #// wildcards.
    #//
    #// If ~comp~ is specified and non-~None~, then the configuration for that
    #// component is printed.
    #//
    #// If ~recurse~ is set, then configuration information for all ~comp~'s
    #// children and below are printed as well.
    #//
    #// This function has been deprecated.  Use print_config instead.

    #extern function void print_config_settings (string field="",
    #                                            uvm_component comp=None,
    #                                            bit recurse=0)
    def print_config_settings(self, field="", comp=None, recurse=False):
        UVMComponent.have_been_warned = False
        if not UVMComponent.have_been_warned:
            uvm_warning("deprecated",
                    "uvm_component::print_config_settings has been deprecated.  Use print_config() instead")
        UVMComponent.have_been_warned = True
        self.print_config(recurse, 1)

    #// Function: print_config
    #//
    #// Print_config_settings prints all configuration information for this
    #// component, as set by previous calls to <uvm_config_db::set()> and exports to
    #// the resources pool.  The settings are printing in the order of
    #// their precedence.
    #//
    #// If ~recurse~ is set, then configuration information for all
    #// children and below are printed as well.
    #//
    #// if ~audit~ is set then the audit trail for each resource is printed
    #// along with the resource name and value
    #extern function void print_config(bit recurse = 0, bit audit = 0)
    def print_config(self, recurse=False, audit=False):
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
    #// If ~recurse~ is set, then configuration information for all
    #// children and below are printed as well.

    #extern function void print_config_with_audit(bit recurse = 0)


    #//----------------------------------------------------------------------------
    #// Group: Objection Interface
    #//----------------------------------------------------------------------------
    #//
    #// These methods provide object level hooks into the <uvm_objection>
    #// mechanism.
    #//
    #//----------------------------------------------------------------------------


    #// Function: raised
    #//
    #// The ~raised~ callback is called when this or a descendant of this component
    #// instance raises the specified ~objection~. The ~source_obj~ is the object
    #// that originally raised the objection.
    #// The ~description~ is optionally provided by the ~source_obj~ to give a
    #// reason for raising the objection. The ~count~ indicates the number of
    #// objections raised by the ~source_obj~.

    #virtual function void raised (uvm_objection objection, uvm_object source_obj,
    #    string description, int count)
    #endfunction


    #// Function: dropped
    #//
    #// The ~dropped~ callback is called when this or a descendant of this component
    #// instance drops the specified ~objection~. The ~source_obj~ is the object
    #// that originally dropped the objection.
    #// The ~description~ is optionally provided by the ~source_obj~ to give a
    #// reason for dropping the objection. The ~count~ indicates the number of
    #// objections dropped by the ~source_obj~.

    #virtual function void dropped (uvm_objection objection, uvm_object source_obj,
    #    string description, int count)
    #endfunction
    def dropped(self, objection, source_obj, description, count):
        pass

    #// Task: all_dropped
    #//
    #// The ~all_droppped~ callback is called when all objections have been
    #// dropped by this component and all its descendants.  The ~source_obj~ is the
    #// object that dropped the last objection.
    #// The ~description~ is optionally provided by the ~source_obj~ to give a
    #// reason for raising the objection. The ~count~ indicates the number of
    #// objections dropped by the ~source_obj~.

    #virtual task all_dropped (uvm_objection objection, uvm_object source_obj,
    #    string description, int count)
    #endtask
    def all_dropped(self, objection, source_obj, description, count):
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
    #// whose type corresponds to the preregistered type name, ~requested_type_name~,
    #// and instance name, ~name~. This method is equivalent to:
    #//
    #//|  factory.create_component_by_name(requested_type_name,
    #//|                                   get_full_name(), name, this)
    #//
    #// If the factory determines that a type or instance override exists, the type
    #// of the component created may be different than the requested type. See
    #// <set_type_override> and <set_inst_override>. See also <uvm_factory> for
    #// details on factory operation.

    #extern function uvm_component create_component (string requested_type_name,
    #                                                string name)


    #// Function: create_object
    #//
    #// A convenience function for <uvm_factory::create_object_by_name>,
    #// this method calls upon the factory to create a new object
    #// whose type corresponds to the preregistered type name,
    #// ~requested_type_name~, and instance name, ~name~. This method is
    #// equivalent to:
    #//
    #//|  factory.create_object_by_name(requested_type_name,
    #//|                                get_full_name(), name)
    #//
    #// If the factory determines that a type or instance override exists, the
    #// type of the object created may be different than the requested type.  See
    #// <uvm_factory> for details on factory operation.

    #extern function uvm_object create_object (string requested_type_name,
    #                                          string name="")


    #// Function: set_type_override_by_type
    #//
    #// A convenience function for <uvm_factory::set_type_override_by_type>, this
    #// method registers a factory override for components and objects created at
    #// this level of hierarchy or below. This method is equivalent to:
    #//
    #//|  factory.set_type_override_by_type(original_type, override_type,replace)
    #//
    #// The ~relative_inst_path~ is relative to this component and may include
    #// wildcards. The ~original_type~ represents the type that is being overridden.
    #// In subsequent calls to <uvm_factory::create_object_by_type> or
    #// <uvm_factory::create_component_by_type>, if the requested_type matches the
    #// ~original_type~ and the instance paths match, the factory will produce
    #// the ~override_type~.
    #//
    #// The original and override type arguments are lightweight proxies to the
    #// types they represent. See <set_inst_override_by_type> for information
    #// on usage.

    #extern static function void set_type_override_by_type
    #                                           (uvm_object_wrapper original_type,
    #                                            uvm_object_wrapper override_type,
    #                                            bit replace=1)


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
    #// The ~relative_inst_path~ is relative to this component and may include
    #// wildcards. The ~original_type~ represents the type that is being overridden.
    #// In subsequent calls to <uvm_factory::create_object_by_type> or
    #// <uvm_factory::create_component_by_type>, if the requested_type matches the
    #// ~original_type~ and the instance paths match, the factory will produce the
    #// ~override_type~.
    #//
    #// The original and override types are lightweight proxies to the types they
    #// represent. They can be obtained by calling ~type::get_type()~, if
    #// implemented by ~type~, or by directly calling ~type::type_id::get()~, where
    #// ~type~ is the user type and ~type_id~ is the name of the typedef to
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


    #// Function: set_type_override
    #//
    #// A convenience function for <uvm_factory::set_type_override_by_name>,
    #// this method configures the factory to create an object of type
    #// ~override_type_name~ whenever the factory is asked to produce a type
    #// represented by ~original_type_name~.  This method is equivalent to:
    #//
    #//|  factory.set_type_override_by_name(original_type_name,
    #//|                                    override_type_name, replace)
    #//
    #// The ~original_type_name~ typically refers to a preregistered type in the
    #// factory. It may, however, be any arbitrary string. Subsequent calls to
    #// create_component or create_object with the same string and matching
    #// instance path will produce the type represented by override_type_name.
    #// The ~override_type_name~ must refer to a preregistered type in the factory.

    #extern static function void set_type_override(string original_type_name,
    #                                              string override_type_name,
    #                                              bit    replace=1)


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
    #// The ~relative_inst_path~ is relative to this component and may include
    #// wildcards. The ~original_type_name~ typically refers to a preregistered type
    #// in the factory. It may, however, be any arbitrary string. Subsequent calls
    #// to create_component or create_object with the same string and matching
    #// instance path will produce the type represented by ~override_type_name~.
    #// The ~override_type_name~ must refer to a preregistered type in the factory.

    #extern function void set_inst_override(string relative_inst_path,
    #                                       string original_type_name,
    #                                       string override_type_name)


    #// Function: print_override_info
    #//
    #// This factory debug method performs the same lookup process as create_object
    #// and create_component, but instead of creating an object, it prints
    #// information about what type of object would be created given the
    #// provided arguments.

    #extern function void print_override_info(string requested_type_name,
    #                                         string name="")

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

    #extern function void set_report_id_verbosity_hier (string id,
    #                                                int verbosity)

    #// Function: set_report_severity_id_verbosity_hier
    #//
    #// These methods recursively associate the specified verbosity with reports of
    #// the given ~severity~, ~id~, or ~severity-id~ pair. A verbosity associated
    #// with a particular severity-id pair takes precedence over a verbosity
    #// associated with id, which takes precedence over a verbosity associated
    #// with a severity.
    #//
    #// For a list of severities and their default verbosities, refer to
    #// <uvm_report_handler>.

    #extern function void set_report_severity_id_verbosity_hier(uvm_severity severity,
    #                                                        string id,
    #                                                        int verbosity)


    #// Function: set_report_severity_action_hier

    #extern function void set_report_severity_action_hier (uvm_severity severity,
    #                                                      uvm_action action)
    def set_report_severity_action_hier(self, severity, action):
        self.set_report_severity_action(severity, action)
        for c in self.m_children:
            self.m_children[c].set_report_severity_action_hier(severity, action)
    #endfunction


    #// Function: set_report_id_action_hier

    #extern function void set_report_id_action_hier (string id,
    #                                                uvm_action action)

    #// Function: set_report_severity_id_action_hier
    #//
    #// These methods recursively associate the specified action with reports of
    #// the given ~severity~, ~id~, or ~severity-id~ pair. An action associated
    #// with a particular severity-id pair takes precedence over an action
    #// associated with id, which takes precedence over an action associated
    #// with a severity.
    #//
    #// For a list of severities and their default actions, refer to
    #// <uvm_report_handler>.

    #extern function void set_report_severity_id_action_hier(uvm_severity severity,
    #                                                        string id,
    #                                                        uvm_action action)
    def set_report_id_action_hier(self, id, action):
        self.set_report_id_action(id, action)
        for c in self.m_children:
            self.m_children[c].set_report_id_action_hier(id, action)


    #// Function: set_report_default_file_hier

    #extern function void set_report_default_file_hier (UVM_FILE file)
    def set_report_default_file_hier(self, file):
        self.set_report_default_file(file)
        for c in self.m_children:
            self.m_children[c].set_report_default_file_hier(file)
    #endfunction

    #// Function: set_report_severity_file_hier

    #extern function void set_report_severity_file_hier (uvm_severity severity,
    #                                                    UVM_FILE file)

    #// Function: set_report_id_file_hier

    #extern function void set_report_id_file_hier (string id,
    #                                              UVM_FILE file)

    #// Function: set_report_severity_id_file_hier
    #//
    #// These methods recursively associate the specified FILE descriptor with
    #// reports of the given ~severity~, ~id~, or ~severity-id~ pair. A FILE
    #// associated with a particular severity-id pair takes precedence over a FILE
    #// associated with id, which take precedence over an a FILE associated with a
    #// severity, which takes precedence over the default FILE descriptor.
    #//
    #// For a list of severities and other information related to the report
    #// mechanism, refer to <uvm_report_handler>.

    #extern function void set_report_severity_id_file_hier(uvm_severity severity,
    #                                                      string id,
    #                                                      UVM_FILE file)


    #// Function: set_report_verbosity_level_hier
    #//
    #// This method recursively sets the maximum verbosity level for reports for
    #// this component and all those below it. Any report from this component
    #// subtree whose verbosity exceeds this maximum will be ignored.
    #//
    #// See <uvm_report_handler> for a list of predefined message verbosity levels
    #// and their meaning.

    #  extern function void set_report_verbosity_level_hier (int verbosity)
    def set_report_verbosity_level_hier(self, verbosity):
        self.set_report_verbosity_level(verbosity)
        for c in self.m_children:
            self.m_children[c].set_report_verbosity_level_hier(verbosity)

    # Function: pre_abort
    #
    # This callback is executed when the message system is executing a
    # <UVM_EXIT> action. The exit action causes an immediate termination of
    # the simulation, but the pre_abort callback hook gives components an
    # opportunity to provide additional information to the user before
    # the termination happens. For example, a test may want to executed
    # the report function of a particular component even when an error
    # condition has happened to force a premature termination you would
    # write a function like:
    #
    #| function void mycomponent::pre_abort()
    #|   report()
    #| endfunction
    #
    # The pre_abort() callback hooks are called in a bottom-up fashion.
    def pre_abort(self):
        pass

    # m_do_pre_abort
    # --------------
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

    #// Function: accept_tr
    #//
    #// This function marks the acceptance of a transaction, ~tr~, by this
    #// component. Specifically, it performs the following actions:
    #//
    #// - Calls the ~tr~'s <uvm_transaction::accept_tr> method, passing to it the
    #//   ~accept_time~ argument.
    #//
    #// - Calls this component's <do_accept_tr> method to allow for any post-begin
    #//   action in derived classes.
    #//
    #// - Triggers the component's internal accept_tr event. Any processes waiting
    #//   on this event will resume in the next delta cycle.

    #extern function void accept_tr (uvm_transaction tr, time accept_time = 0)
    def accept_tr(self, tr, accept_time=0):
        e = None
        tr.accept_tr(accept_time)
        self.do_accept_tr(tr)
        e = self.event_pool.get("accept_tr")
        if e is not None:
            e.trigger()


    #// Function: do_accept_tr
    #//
    #// The <accept_tr> method calls this function to accommodate any user-defined
    #// post-accept action. Implementations should call super.do_accept_tr to
    #// ensure correct operation.
    #
    #extern virtual protected function void do_accept_tr (uvm_transaction tr)
    def do_accept_tr(self, tr):
        return

    #// Function: begin_tr
    #//
    #// This function marks the start of a transaction, ~tr~, by this component.
    #// Specifically, it performs the following actions:
    #//
    #// - Calls ~tr~'s <uvm_transaction::begin_tr> method, passing to it the
    #//   ~begin_time~ argument. The ~begin_time~ should be greater than or equal
    #//   to the accept time. By default, when ~begin_time~ = 0, the current
    #//   simulation time is used.
    #//
    #//   If recording is enabled (recording_detail != UVM_OFF), then a new
    #//   database-transaction is started on the component's transaction stream
    #//   given by the stream argument. No transaction properties are recorded at
    #//   this time.
    #//
    #// - Calls the component's <do_begin_tr> method to allow for any post-begin
    #//   action in derived classes.
    #//
    #// - Triggers the component's internal begin_tr event. Any processes waiting
    #//   on this event will resume in the next delta cycle.
    #//
    #// A handle to the transaction is returned. The meaning of this handle, as
    #// well as the interpretation of the arguments ~stream_name~, ~label~, and
    #// ~desc~ are vendor specific.

    # extern function integer begin_tr (uvm_transaction tr,
    #                                   string stream_name="main",
    #                                   string label="",
    #                                   string desc="",
    #                                   time begin_time=0,
    #                                   integer parent_handle=0)
    def begin_tr(self, tr, stream_name="main", label="", desc="", begin_time=0,
            parent_handle=0):
        return self.m_begin_tr(tr, parent_handle, stream_name, label, desc, begin_time)


    #// Function: begin_child_tr
    #//
    #// This function marks the start of a child transaction, ~tr~, by this
    #// component. Its operation is identical to that of <begin_tr>, except that
    #// an association is made between this transaction and the provided parent
    #// transaction. This association is vendor-specific.

    #extern function integer begin_child_tr (uvm_transaction tr,
    #                                        integer parent_handle=0,
    #                                        string stream_name="main",
    #                                        string label="",
    #                                        string desc="",
    #                                        time begin_time=0)
    def begin_child_tr(self, tr, parent_handle=0, stream_name="main", label="", desc="",
            begin_time=0):
        return self.m_begin_tr(tr, parent_handle, stream_name, label, desc, begin_time)


    #// Function: do_begin_tr
    #//
    #// The <begin_tr> and <begin_child_tr> methods call this function to
    #// accommodate any user-defined post-begin action. Implementations should call
    #// super.do_begin_tr to ensure correct operation.

    #extern virtual protected
    #  function void do_begin_tr (uvm_transaction tr,
    #                             string stream_name,
    #                             integer tr_handle)
    def do_begin_tr(self, tr, stream_name, tr_handle):
        return

    #// Function: end_tr
    #//
    #// This function marks the end of a transaction, ~tr~, by this component.
    #// Specifically, it performs the following actions:
    #//
    #// - Calls ~tr~'s <uvm_transaction::end_tr> method, passing to it the
    #//   ~end_time~ argument. The ~end_time~ must at least be greater than the
    #//   begin time. By default, when ~end_time~ = 0, the current simulation time
    #//   is used.
    #//
    #//   The transaction's properties are recorded to the database-transaction on
    #//   which it was started, and then the transaction is ended. Only those
    #//   properties handled by the transaction's do_record method (and optional
    #//   `uvm_*_field macros) are recorded.
    #//
    #// - Calls the component's <do_end_tr> method to accommodate any post-end
    #//   action in derived classes.
    #//
    #// - Triggers the component's internal end_tr event. Any processes waiting on
    #//   this event will resume in the next delta cycle.
    #//
    #// The ~free_handle~ bit indicates that this transaction is no longer needed.
    #// The implementation of free_handle is vendor-specific.

    #extern function void end_tr (uvm_transaction tr,
    #                             time end_time=0,
    #                             bit free_handle=1)
    def end_tr(self, tr, end_time=0, free_handle=1):
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
        #endfunction


    #// Function: do_end_tr
    #//
    #// The <end_tr> method calls this function to accommodate any user-defined
    #// post-end action. Implementations should call super.do_end_tr to ensure
    #// correct operation.

    #extern virtual protected function void do_end_tr (uvm_transaction tr,
    #                                                  integer tr_handle)
    def do_end_tr(self, tr, tr_handle):
        return

    #// Function: record_error_tr
    #//
    #// This function marks an error transaction by a component. Properties of the
    #// given uvm_object, ~info~, as implemented in its <uvm_object::do_record> method,
    #// are recorded to the transaction database.
    #//
    #// An ~error_time~ of 0 indicates to use the current simulation time. The
    #// ~keep_active~ bit determines if the handle should remain active. If 0,
    #// then a zero-length error transaction is recorded. A handle to the
    #// database-transaction is returned.
    #//
    #// Interpretation of this handle, as well as the strings ~stream_name~,
    #// ~label~, and ~desc~, are vendor-specific.

    #extern function integer record_error_tr (string stream_name="main",
    #                                         uvm_object info=None,
    #                                         string label="error_tr",
    #                                         string desc="",
    #                                         time   error_time=0,
    #                                         bit    keep_active=0)


    #// Function: record_event_tr
    #//
    #// This function marks an event transaction by a component.
    #//
    #// An ~event_time~ of 0 indicates to use the current simulation time.
    #//
    #// A handle to the transaction is returned. The ~keep_active~ bit determines
    #// if the handle may be used for other vendor-specific purposes.
    #//
    #// The strings for ~stream_name~, ~label~, and ~desc~ are vendor-specific
    #// identifiers for the transaction.

    #extern function integer record_event_tr (string stream_name="main",
    #                                         uvm_object info=None,
    #                                         string label="event_tr",
    #                                         string desc="",
    #                                         time   event_time=0,
    #                                         bit    keep_active=0)

    #// Function: get_tr_stream
    #// Returns a tr stream with ~this~ component's full name as a scope.
    #//
    #// Streams which are retrieved via this method will be stored internally,
    #// such that later calls to ~get_tr_stream~ will return the same stream
    #// reference.
    #//
    #// The stream can be removed from the internal storage via a call
    #// to <free_tr_stream>.
    #//
    #// Parameters:
    #// name - Name for the stream
    #// stream_type_name - Type name for the stream (Default = "")
    #extern virtual function uvm_tr_stream get_tr_stream(string name,
    #                                                    string stream_type_name="")
    def get_tr_stream(self, name, stream_type_name=""):
        db = self.m_get_tr_database()  # uvm_tr_database
        if name not in self.m_streams:
            self.m_streams[name] = {}
        if stream_type_name not in self.m_streams[name]:
            self.m_streams[name][stream_type_name] = db.open_stream(name,
                    self.get_full_name(), stream_type_name)
        return self.m_streams[name][stream_type_name]


    #// Function: free_tr_stream
    #// Frees the internal references associated with ~stream~.
    #//
    #// The next call to <get_tr_stream> will result in a newly created
    #// <uvm_tr_stream>.  If the current stream is open (or closed),
    #// then it will be freed.
    #extern virtual function void free_tr_stream(uvm_tr_stream stream)


    #// Variable: self.tr_database
    #//
    #// Specifies the <uvm_tr_database> object to use for <begin_tr>
    #// and other methods in the <Recording Interface>.
    #// Default is <uvm_coreservice_t::get_default_tr_database>.
    #uvm_tr_database self.tr_database

    #extern virtual function uvm_tr_database m_get_tr_database()
    def m_get_tr_database(self):
        if self.tr_database is None:
            from .uvm_coreservice import UVMCoreService
            cs = UVMCoreService.get()
            self.tr_database = cs.get_default_tr_database()
        return self.tr_database

    #//----------------------------------------------------------------------------
    #//                     PRIVATE or PSUEDO-PRIVATE members
    #//                      *** Do not call directly ***
    #//         Implementation and even existence are subject to change.
    #//----------------------------------------------------------------------------
    #// Most local methods are prefixed with m_, indicating they are not
    #// user-level methods. SystemVerilog does not support friend classes,
    #// which forces some otherwise internal methods to be exposed (i.e. not
    #// be protected via 'local' keyword). These methods are also prefixed
    #// with m_ to indicate they are not intended for public use.
    #//
    #// Internal methods will not be documented, although their implementa-
    #// tions are freely available via the open-source license.
    #//----------------------------------------------------------------------------

    #protected uvm_domain m_domain;    // set_domain stores our domain handle


    #//TND review protected, provide read-only accessor.
    #uvm_phase            m_current_phase;            // the most recently executed phase
    #protected process    m_phase_process

    #/*protected*/ bit  m_build_done
    #/*protected*/ int  m_phasing_active

    #extern                   function void set_int_local(string field_name,
    #                                                     uvm_bitstream_t value,
    #                                                     bit recurse=1)
    def set_int_local(self, field_name, value, recurse=1):
        #  // call the super function to get child recursion and any registered fields
        super().set_int_local(field_name, value, recurse)

        # set the local properties
        if uvm_is_match(field_name, "recording_detail"):
            self.recording_detail = value


    #/*protected*/ uvm_component m_parent
    #protected     uvm_component m_children[string]
    #protected     uvm_component m_children_by_handle[uvm_component]
    #extern protected virtual function bit  m_add_child(uvm_component child)

    #// m_set_full_name
    #// ---------------
    def m_set_full_name(self):
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
    #endfunction

    #// do_resolve_bindings
    #// -------------------
    def do_resolve_bindings(self):
        for s in self.m_children:
            self.m_children[s].do_resolve_bindings()
        self.resolve_bindings()

    #extern                   function void do_flush()

    #extern virtual           function void flush ()

    #extern local             function void m_extract_name(string name ,
    #                                                      output string leaf ,
    #                                                      output string remainder )
    def m_extract_name(self, name, leaf, remainder):
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


    #// overridden to disable
    #extern virtual function uvm_object create (string name="")
    def create(self, name=""):
        uvm_error("ILLCRT",
            "create cannot be called on a uvm_component. Use create_component instead.")
        return None


    #extern virtual function uvm_object clone  ()
    def clone(self):
        uvm_error("ILLCLN", sv.sformatf(CLONE_ERR, self.get_full_name()))
        return None

    #local uvm_tr_stream m_main_stream

    #extern protected function integer m_begin_tr (uvm_transaction tr,
    #                                              integer parent_handle=0,
    #                                              string stream_name="main", string label="",
    #                                              string desc="", time begin_time=0)
    def m_begin_tr(self, tr, parent_handle=0, stream_name="main", label="",
            desc="", begin_time=0):
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

    #// Internal methods for setting up command line messaging stuff
    #extern function void m_set_cl_msg_args
    def m_set_cl_msg_args(self):
        self.m_set_cl_verb()
        #self.m_set_cl_action() # TODO
        #self.m_set_cl_sev() # TODO
        #endfunction

    #extern function void m_set_cl_verb
    def m_set_cl_verb(self):
        #  // _ALL_ can be used for ids
        #  // +uvm_set_verbosity=<comp>,<id>,<verbosity>,<phase|time>,<offset>
        #  // +uvm_set_verbosity=uvm_test_top.env0.agent1.*,_ALL_,UVM_FULL,time,800
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        from .uvm_cmdline_processor import UVMCmdlineProcessor

        values = []  # static string values[$]
        first = 1  # static bit first = 1
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
            if first and (len_match or (clp.m_convert_verb(args[2], setting.verbosity) == 0)):
                values.delete(i)
            else:
                setting.comp = args[0]
                setting.id = args[1]
                clp.m_convert_verb(args[2],setting.verbosity)
                setting.phase = args[3]
                setting.offset = 0
                if len(args) == 5:
                    setting.offset = args[4].atoi()
                if ((setting.phase == "time") and (self == top)):
                    UVMComponent.m_time_settings.push_back(setting)

                if uvm_is_match(setting.comp, self.get_full_name()):
                    if((setting.phase == "" or setting.phase == "build" or
                        setting.phase == "time") and setting.offset == 0):

                        if(setting.id == "_ALL_"):
                            self.set_report_verbosity_level(setting.verbosity)
                        else:
                            self.set_report_id_verbosity(setting.id, setting.verbosity)
                    else:
                        if(setting.phase != "time"):
                            self.m_verbosity_settings.append(setting)

        # TODO do time based settings
        #  if(this == top):
        #    fork begin
        #      time last_time = 0
        #      if (m_time_settings.size() > 0)
        #        m_time_settings.sort() with ( item.offset )
        #      foreach(m_time_settings[i]):
        #        uvm_component comps[$]
        #        top.find_all(m_time_settings[i].comp,comps)
        #        #(m_time_settings[i].offset - last_time)
        #        last_time = m_time_settings[i].offset
        #        if(m_time_settings[i].id == "_ALL_"):
        #           foreach(comps[j]):
        #             comps[j].set_report_verbosity_level(m_time_settings[i].verbosity)
        #           end
        #        end
        #        else begin
        #          foreach(comps[j]):
        #            comps[j].set_report_id_verbosity(m_time_settings[i].id, m_time_settings[i].verbosity)
        #          end
        #        end
        #      end
        #    end join_none // fork begin
        #  end
        #
        #  first = 0
        #endfunction

    #extern function void m_set_cl_action

    #extern function void m_set_cl_sev

    #m_verbosity_setting self.m_verbosity_settings[$]
    #static m_verbosity_setting m_time_settings[$]

    #// does the pre abort callback hierarchically
    #extern /*local*/ function void m_do_pre_abort


    #static uvm_cmdline_parsed_arg_t m_uvm_applied_cl_action[$]
    #static uvm_cmdline_parsed_arg_t m_uvm_applied_cl_sev[$]

    def add_child(self, child):
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

    #extern function void m_apply_verbosity_settings(uvm_phase phase)
    def m_apply_verbosity_settings(self, phase):
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
                self.m_verbosity_settings.delete(i)

    # Added by tpoikela
    def kill(self):
        if self.m_run_process is not None:
            self.m_run_process.kill()
    #endclass uvm_component


#//------------------------------------------------------------------------------
#// IMPLEMENTATION
#//------------------------------------------------------------------------------
#
#//------------------------------------------------------------------------------
#//
#// CLASS- uvm_component
#//
#//------------------------------------------------------------------------------
#
#// m_add_child
#// -----------
#
#function bit uvm_component::m_add_child(uvm_component child)
#
#  if (m_children.exists(child.get_name()) &&
#      m_children[child.get_name()] != child):
#      `uvm_warning("BDCLD",
#        $sformatf("A child with the name '%0s' (type=%0s) already exists.",
#           child.get_name(), m_children[child.get_name()].get_type_name()))
#      return 0
#  end
#
#  if (m_children_by_handle.exists(child)):
#      `uvm_warning("BDCHLD",
#        $sformatf("A child with the name '%0s' %0s %0s'",
#                  child.get_name(),
#                  "already exists in parent under name '",
#                  m_children_by_handle[child].get_name()))
#      return 0
#    end
#
#  m_children[child.get_name()] = child
#  m_children_by_handle[child] = child
#  return 1
#endfunction
#
#
#
#//------------------------------------------------------------------------------
#//
#// Hierarchy Methods
#//
#//------------------------------------------------------------------------------
#
#
#// get_children
#// ------------
#
#function void uvm_component::get_children(ref uvm_component children[$])
#  foreach(m_children[i])
#    children.push_back(m_children[i])
#endfunction
#
#
#// get_first_child
#// ---------------
#
#function int uvm_component::get_first_child(ref string name)
#  return m_children.first(name)
#endfunction
#
#
#// get_next_child
#// --------------
#
#function int uvm_component::get_next_child(ref string name)
#  return m_children.next(name)
#endfunction
#
#
#// get_child
#// ---------
#
#function uvm_component uvm_component::get_child(string name)
#  if (m_children.exists(name))
#    return m_children[name]
#  `uvm_warning("NOCHILD",{"Component with name '",name,
#       "' is not a child of component '",get_full_name(),"'"})
#  return None
#endfunction
#
#
#// has_child
#// ---------
#
#function int uvm_component::has_child(string name)
#  return m_children.exists(name)
#endfunction
#
#
#// get_num_children
#// ----------------
#
#function int uvm_component::get_num_children()
#  return m_children.num()
#endfunction
#
#// flush
#// -----
#
#function void uvm_component::flush()
#  return
#endfunction
#
#
#// do_flush  (flush_hier?)
#// --------
#
#function void uvm_component::do_flush()
#  foreach( m_children[s] )
#    m_children[s].do_flush()
#  flush()
#endfunction
#
#
#
#//------------------------------------------------------------------------------
#//
#// Factory Methods
#//
#//------------------------------------------------------------------------------
#
#
#
#
#// print_override_info
#// -------------------
#
#function void  uvm_component::print_override_info (string requested_type_name,
#                                                   string name="")
#  uvm_coreservice_t cs = uvm_coreservice_t::get()
#  uvm_factory factory=cs.get_factory()
#  factory.debug_create_by_name(requested_type_name, get_full_name(), name)
#endfunction
#
#
#// create_component
#// ----------------
#
#function uvm_component uvm_component::create_component (string requested_type_name,
#                                                        string name)
#  uvm_coreservice_t cs = uvm_coreservice_t::get()
#  uvm_factory factory=cs.get_factory()
#  return factory.create_component_by_name(requested_type_name, get_full_name(),
#                                          name, this)
#endfunction
#
#
#// create_object
#// -------------
#
#function uvm_object uvm_component::create_object (string requested_type_name,
#                                                  string name="")
#  uvm_coreservice_t cs = uvm_coreservice_t::get()
#  uvm_factory factory=cs.get_factory()
#  return factory.create_object_by_name(requested_type_name,
#                                       get_full_name(), name)
#endfunction
#
#
#// set_type_override (static)
#// -----------------
#
#function void uvm_component::set_type_override (string original_type_name,
#                                                string override_type_name,
#                                                bit    replace=1)
#   uvm_coreservice_t cs = uvm_coreservice_t::get()
#   uvm_factory factory=cs.get_factory()
#   factory.set_type_override_by_name(original_type_name,override_type_name, replace)
#endfunction
#
#
#// set_type_override_by_type (static)
#// -------------------------
#
#function void uvm_component::set_type_override_by_type (uvm_object_wrapper original_type,
#                                                        uvm_object_wrapper override_type,
#                                                        bit    replace=1)
#  uvm_coreservice_t cs = uvm_coreservice_t::get()
#  uvm_factory factory=cs.get_factory()
#   factory.set_type_override_by_type(original_type, override_type, replace)
#endfunction
#
#
#// set_inst_override
#// -----------------
#
#function void  uvm_component::set_inst_override (string relative_inst_path,
#                                                 string original_type_name,
#                                                 string override_type_name)
#  string full_inst_path
#  uvm_coreservice_t cs = uvm_coreservice_t::get()
#  uvm_factory factory=cs.get_factory()
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
#// set_inst_override_by_type
#// -------------------------
#
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
#
#
#
#//------------------------------------------------------------------------------
#//
#// Hierarchical report configuration interface
#//
#//------------------------------------------------------------------------------
#
#// set_report_id_verbosity_hier
#// -------------------------
#
#function void uvm_component::set_report_id_verbosity_hier( string id, int verbosity)
#  set_report_id_verbosity(id, verbosity)
#  foreach( m_children[c] )
#    m_children[c].set_report_id_verbosity_hier(id, verbosity)
#endfunction
#
#
#// set_report_severity_id_verbosity_hier
#// ----------------------------------
#
#function void uvm_component::set_report_severity_id_verbosity_hier( uvm_severity severity,
#                                                                 string id,
#                                                                 int verbosity)
#  set_report_severity_id_verbosity(severity, id, verbosity)
#  foreach( m_children[c] )
#    m_children[c].set_report_severity_id_verbosity_hier(severity, id, verbosity)
#endfunction
#
#
#
#
#// set_report_id_action_hier
#// -------------------------
#
#function void uvm_component::set_report_id_action_hier( string id, uvm_action action)
#  set_report_id_action(id, action)
#  foreach( m_children[c] )
#    m_children[c].set_report_id_action_hier(id, action)
#endfunction
#
#
#// set_report_severity_id_action_hier
#// ----------------------------------
#
#function void uvm_component::set_report_severity_id_action_hier( uvm_severity severity,
#                                                                 string id,
#                                                                 uvm_action action)
#  set_report_severity_id_action(severity, id, action)
#  foreach( m_children[c] )
#    m_children[c].set_report_severity_id_action_hier(severity, id, action)
#endfunction
#
#
#// set_report_severity_file_hier
#// -----------------------------
#
#function void uvm_component::set_report_severity_file_hier( uvm_severity severity,
#                                                            UVM_FILE file)
#  set_report_severity_file(severity, file)
#  foreach( m_children[c] )
#    m_children[c].set_report_severity_file_hier(severity, file)
#endfunction
#
#
#
#
#// set_report_id_file_hier
#// -----------------------
#
#function void uvm_component::set_report_id_file_hier( string id, UVM_FILE file)
#  set_report_id_file(id, file)
#  foreach( m_children[c] )
#    m_children[c].set_report_id_file_hier(id, file)
#endfunction
#
#
#// set_report_severity_id_file_hier
#// --------------------------------
#
#function void uvm_component::set_report_severity_id_file_hier ( uvm_severity severity,
#                                                                string id,
#                                                                UVM_FILE file)
#  set_report_severity_id_file(severity, id, file)
#  foreach( m_children[c] )
#    m_children[c].set_report_severity_id_file_hier(severity, id, file)
#endfunction
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
#
#
#//------------------------------
#// current phase convenience API
#//------------------------------
#
#// phase_ended
#// -----------
#
#function void uvm_component::phase_ended(uvm_phase phase)
#endfunction
#
#
#// phase_ready_to_end
#// ------------------
#
#function void uvm_component::phase_ready_to_end (uvm_phase phase)
#endfunction
#
#//------------------------------
#// phase / schedule / domain API
#//------------------------------
#// methods for VIP creators and integrators to use to set up schedule domains
#// - a schedule is a named, organized group of phases for a component base type
#// - a domain is a named instance of a schedule in the master phasing schedule
#
#
#
#
#
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
#//------------------------------------------------------------------------------
#//
#// Recording interface
#//
#//------------------------------------------------------------------------------
#
#
#
#
#
#// free_tr_stream
#// --------------
#function void uvm_component::free_tr_stream(uvm_tr_stream stream)
#   // Check the None case...
#   if (stream is None)
#     return
#
#   // Then make sure this name/type_name combo exists
#   if (!m_streams.exists(stream.get_name()) ||
#       !m_streams[stream.get_name()].exists(stream.get_stream_type_name()))
#     return
#
#   // Then make sure this name/type_name combo is THIS stream
#   if (m_streams[stream.get_name()][stream.get_stream_type_name()] != stream)
#     return
#
#   // Then delete it from the arrays
#   m_streams[stream.get_name()].delete(stream.get_type_name())
#   if (m_streams[stream.get_name()].size() == 0)
#     m_streams.delete(stream.get_name())
#
#   // Finally, free the stream if necessary
#   if (stream.is_open() || stream.is_closed()):
#      stream.free()
#   end
#endfunction : free_tr_stream
#
#

#
#
#// record_error_tr
#// ---------------
#
#function integer uvm_component::record_error_tr (string stream_name="main",
#                                                 uvm_object info=None,
#                                                 string label="error_tr",
#                                                 string desc="",
#                                                 time   error_time=0,
#                                                 bit    keep_active=0)
#   uvm_recorder recorder
#   string etype
#   uvm_tr_stream stream
#   uvm_tr_database db = m_get_tr_database()
#   integer handle
#
#   if(keep_active) etype = "Error, Link"
#   else etype = "Error"
#
#   if(error_time == 0) error_time = $realtime
#
#   if ((stream_name=="") || (stream_name=="main")):
#      if (m_main_stream is None)
#        m_main_stream = self.tr_database.open_stream("main", this.get_full_name(), "TVM")
#      stream = m_main_stream
#   end
#   else
#     stream = get_tr_stream(stream_name)
#
#   handle = 0
#   if (stream is not None):
#
#      recorder = stream.open_recorder(label,
#                                    error_time,
#                                    etype)
#
#      if (recorder is not None):
#         if (label != "")
#           recorder.record_string("label", label)
#         if (desc != "")
#           recorder.record_string("desc", desc)
#         if (infois not None)
#           info.record(recorder)
#
#         recorder.close(error_time)
#
#         if (keep_active == 0):
#            recorder.free()
#         end
#         else begin
#            handle = recorder.get_handle()
#         end
#      end // if (recorder is not None)
#   end // if (stream is not None)
#
#   return handle
#endfunction
#
#
#// record_event_tr
#// ---------------
#
#function integer uvm_component::record_event_tr (string stream_name="main",
#                                                 uvm_object info=None,
#                                                 string label="event_tr",
#                                                 string desc="",
#                                                 time   event_time=0,
#                                                 bit    keep_active=0)
#   uvm_recorder recorder
#   string etype
#   integer handle
#   uvm_tr_stream stream
#   uvm_tr_database db = m_get_tr_database()
#
#  if(keep_active) etype = "Event, Link"
#  else etype = "Event"
#
#   if(event_time == 0) event_time = $realtime
#
#   if ((stream_name=="") || (stream_name=="main")):
#      if (m_main_stream is None)
#        m_main_stream = self.tr_database.open_stream("main", this.get_full_name(), "TVM")
#      stream = m_main_stream
#   end
#   else
#     stream = get_tr_stream(stream_name)
#
#   handle = 0
#   if (stream is not None):
#      recorder = stream.open_recorder(label,
#                                    event_time,
#                                    etype)
#
#      if (recorder is not None):
#         if (label != "")
#           recorder.record_string("label", label)
#         if (desc != "")
#           recorder.record_string("desc", desc)
#         if (infois not None)
#           info.record(recorder)
#
#         recorder.close(event_time)
#
#         if (keep_active == 0):
#            recorder.free()
#         end
#         else begin
#            handle = recorder.get_handle()
#         end
#      end // if (recorder is not None)
#   end // if (stream is not None)
#
#   return handle
#endfunction
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
#function string uvm_component::massage_scope(string scope)
#
#  // uvm_top
#  if(scope == "")
#    return "^$"
#
#  if(scope == "*")
#    return {get_full_name(), ".*"}
#
#  // absolute path to the top-level test
#  if(scope == "uvm_test_top")
#    return "uvm_test_top"
#
#  // absolute path to uvm_root
#  if(scope[0] == ".")
#    return {get_full_name(), scope}
#
#  return {get_full_name(), ".", scope}
#
#endfunction

#// Undocumented struct for storing clone bit along w/
#// object on set_config_object(...) calls
#class uvm_config_object_wrapper
#   uvm_object obj
#   bit clone
#endclass : uvm_config_object_wrapper

#// check_config_usage
#// ------------------
#
#function void uvm_component::check_config_usage ( bit recurse=1 )
#  uvm_resource_pool rp = uvm_resource_pool::get()
#  uvm_queue#(uvm_resource_base) rq
#
#  rq = rp.find_unused_resources()
#
#  if(rq.size() == 0)
#    return
#
#  uvm_info("CFGNRD"," ::: The following resources have at least one write and no reads :::",UVM_INFO)
#  rp.print_resources(rq, 1)
#endfunction

#
#
#
#
#
#// print_config_with_audit
#// -----------------------
#
#function void uvm_component::print_config_with_audit(bit recurse = 0)
#  print_config(recurse, 1)
#endfunction
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
#
#

#
#// m_set_cl_action
#// ---------------
#
#function void uvm_component::m_set_cl_action
#  // _ALL_ can be used for ids or severities
#  // +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>
#  // +uvm_set_action=uvm_test_top.env0.*,_ALL_,UVM_ERROR,UVM_NO_ACTION
#
#  static bit initialized = 0
#  uvm_severity sev
#  uvm_action action
#
#  if(!initialized):
#	string values[$]
#    void'(uvm_cmdline_proc.get_arg_values("+uvm_set_action=",values))
#	foreach(values[idx]):
#		uvm_cmdline_parsed_arg_t t
#		string args[$]
#	 	uvm_split_string(values[idx], ",", args)
#
#		if(args.size() != 4):
#	   		`uvm_warning("INVLCMDARGS", $sformatf("+uvm_set_action requires 4 arguments, but %0d given for command +uvm_set_action=%s, Usage: +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>", args.size(), values[idx]))
#	   		continue
#   		end
#   		if((args[2] != "_ALL_") && !uvm_string_to_severity(args[2], sev)):
#	   		`uvm_warning("INVLCMDARGS", $sformatf("Bad severity argument \"%s\" given to command +uvm_set_action=%s, Usage: +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>", args[2], values[idx]))
#	   		continue
#   		end
#   		if(!uvm_string_to_action(args[3], action)):
#	   		`uvm_warning("INVLCMDARGS", $sformatf("Bad action argument \"%s\" given to command +uvm_set_action=%s, Usage: +uvm_set_action=<comp>,<id>,<severity>,<action[|action]>", args[3], values[idx]))
#	   		continue
#   		end
#   		t.args=args
#   		t.arg=values[idx]
#   		m_uvm_applied_cl_action.push_back(t)
#	end
#	initialized=1
#  end
#
#  foreach(m_uvm_applied_cl_action[i]):
#	string args[$] = m_uvm_applied_cl_action[i].args
#
#	if (!uvm_is_match(args[0], get_full_name()) ) continue
#
#	void'(uvm_string_to_severity(args[2], sev))
#	void'(uvm_string_to_action(args[3], action))
#
#    m_uvm_applied_cl_action[i].used++
#    if(args[1] == "_ALL_"):
#      if(args[2] == "_ALL_"):
#        set_report_severity_action(UVM_INFO, action)
#        set_report_severity_action(UVM_WARNING, action)
#        set_report_severity_action(UVM_ERROR, action)
#        set_report_severity_action(UVM_FATAL, action)
#      end
#      else begin
#        set_report_severity_action(sev, action)
#      end
#    end
#    else begin
#      if(args[2] == "_ALL_"):
#        set_report_id_action(args[1], action)
#      end
#      else begin
#        set_report_severity_id_action(sev, args[1], action)
#      end
#    end
#  end
#
#endfunction
#
#
#// m_set_cl_sev
#// ------------
#
#function void uvm_component::m_set_cl_sev
#  // _ALL_ can be used for ids or severities
#  //  +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>
#  //  +uvm_set_severity=uvm_test_top.env0.*,BAD_CRC,UVM_ERROR,UVM_WARNING
#
#  static bit initialized
#  uvm_severity orig_sev, sev
#
#  if(!initialized):
#	string values[$]
#    void'(uvm_cmdline_proc.get_arg_values("+uvm_set_severity=",values))
#	foreach(values[idx]):
#		uvm_cmdline_parsed_arg_t t
#		string args[$]
#	 	uvm_split_string(values[idx], ",", args)
#	 	if(args.size() != 4):
#      		`uvm_warning("INVLCMDARGS", $sformatf("+uvm_set_severity requires 4 arguments, but %0d given for command +uvm_set_severity=%s, Usage: +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>", args.size(), values[idx]))
#      		continue
#    	end
#    	if(args[2] != "_ALL_" && !uvm_string_to_severity(args[2], orig_sev)):
#      		`uvm_warning("INVLCMDARGS", $sformatf("Bad severity argument \"%s\" given to command +uvm_set_severity=%s, Usage: +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>", args[2], values[idx]))
#      		continue
#    	end
#    	if(!uvm_string_to_severity(args[3], sev)):
#      		`uvm_warning("INVLCMDARGS", $sformatf("Bad severity argument \"%s\" given to command +uvm_set_severity=%s, Usage: +uvm_set_severity=<comp>,<id>,<orig_severity>,<new_severity>", args[3], values[idx]))
#      		continue
#    	end
#
#	 	t.args=args
#    	t.arg=values[idx]
#	 	m_uvm_applied_cl_sev.push_back(t)
#	end
#	initialized=1
#  end
#
#  foreach(m_uvm_applied_cl_sev[i]):
#  	string args[$]=m_uvm_applied_cl_sev[i].args
#
#    if (!uvm_is_match(args[0], get_full_name()) ) continue
#
#	void'(uvm_string_to_severity(args[2], orig_sev))
#	void'(uvm_string_to_severity(args[3], sev))
#    m_uvm_applied_cl_sev[i].used++
#    if(args[1] == "_ALL_" && args[2] == "_ALL_"):
#      set_report_severity_override(UVM_INFO,sev)
#      set_report_severity_override(UVM_WARNING,sev)
#      set_report_severity_override(UVM_ERROR,sev)
#      set_report_severity_override(UVM_FATAL,sev)
#    end
#    else if(args[1] == "_ALL_"):
#      set_report_severity_override(orig_sev,sev)
#    end
#    else if(args[2] == "_ALL_"):
#      set_report_severity_id_override(UVM_INFO,args[1],sev)
#      set_report_severity_id_override(UVM_WARNING,args[1],sev)
#      set_report_severity_id_override(UVM_ERROR,args[1],sev)
#      set_report_severity_id_override(UVM_FATAL,args[1],sev)
#    end
#    else begin
#      set_report_severity_id_override(orig_sev,args[1],sev)
#    end
#  end
#endfunction
#
#
#
#
#// m_do_pre_abort
#// --------------
#
#function void uvm_component::m_do_pre_abort
#  foreach(m_children[i])
#    m_children[i].m_do_pre_abort()
#  pre_abort()
#endfunction

