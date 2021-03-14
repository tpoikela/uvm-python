#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010-2011 Synopsys, Inc.
#   Copyright 2013      NVIDIA Corporation
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
#------------------------------------------------------------------------------

from typing import List

import cocotb
from cocotb.triggers import Timer, Event

from .sv import sv, uvm_split_string
from .uvm_component import UVMComponent
from .uvm_version import (uvm_cdn_copyright, uvm_cy_copyright, uvm_mgc_copyright, uvm_nv_copyright,
                          uvm_revision_string, uvm_snps_copyright, uvm_tpoikela_copyright)
from .uvm_cmdline_processor import UVMCmdlineProcessor
from .uvm_globals import (uvm_is_match, uvm_report_error, uvm_report_warning,
    uvm_zero_delay)
from .uvm_object_globals import (UVM_DEBUG, UVM_ERROR, UVM_FULL, UVM_HIGH,
    UVM_LOW, UVM_MEDIUM, UVM_NONE)
from .uvm_phase import UVMPhase
from .uvm_debug import uvm_debug
from .uvm_objection import UVMObjection
from .uvm_report_server import UVMReportServer
from .uvm_domain import end_of_elaboration_ph
from .uvm_common_phases import UVMEndOfElaborationPhase
from ..macros import uvm_info, uvm_fatal, UVM_DEFAULT_TIMEOUT
from ..uvm_macros import UVM_STRING_QUEUE_STREAMING_PACK
from .uvm_config_db import UVMConfigDb

MULTI_TESTS = ("Multiple ({}) +UVM_TESTNAME arguments provided on the command"
        + "line. '{}' will be used.  Provided list: {}.")

WARN_MSG1 = ("Multiple (%0d) +UVM_VERBOSITY arguments provided on the command"
        + " line.  '%s' will be used.  Provided list: %s.")

NON_STD_VERB = "Non-standard verbosity value, using provided '%0d'."

LINE = "----------------------------------------------------------------"

UVM_OBJECT_DO_NOT_NEED_CONSTRUCTOR = 0

MSG_MULTTIMOUT = ("Multiple (%0d) +UVM_TIMEOUT arguments provided on the command line. "
    + "'%s' will be used.  Provided list: %s.")

MSG_INVLCMDARGS = ("Invalid number of arguments found on the command line for setting "
    + "'+uvm_set_verbosity=%s'.  Setting ignored.")

WARN_MAX_QUIT_COUNT = ("Multiple (%0d) +UVM_MAX_QUIT_COUNT arguments provided "
    + "on the command line.  '%s' will be used.  Provided list: %s.")


class UVMRoot(UVMComponent):
    """
    The `UVMRoot` class serves as the implicit top-level and phase controller for
    all UVM components. Users do not directly instantiate `UVMRoot`. The UVM
    automatically creates a single instance of <uvm_root> that users can
    access via the global (uvm_pkg-scope) variable, ~uvm_top~.

    (see uvm_ref_root.gif)

    The ~uvm_top~ instance of ~uvm_root~ plays several key roles in the UVM.

    Implicit top-level - The ~uvm_top~ serves as an implicit top-level component.
    Any component whose parent is specified as ~None~ becomes a child of ~uvm_top~.
    Thus, all UVM components in simulation are descendants of ~uvm_top~.

    Phase control - ~uvm_top~ manages the phasing for all components.

    Search - Use ~uvm_top~ to search for components based on their
    hierarchical name. See `UVMRoot.find` and `UVMRoot.find_all`.

    Report configuration - Use ~uvm_top~ to globally configure
    report verbosity, log files, and actions. For example,
    ~uvm_top.set_report_verbosity_level_hier(UVM_FULL)~ would set
    full verbosity for all components in simulation.

    Global reporter - Because ~uvm_top~ is globally accessible (in uvm_pkg
    scope), UVM's reporting mechanism is accessible from anywhere
    outside ~uvm_component~, such as in modules and sequences.
    See <uvm_report_error>, <self.uvm_report_warning>, and other global
    methods.


    The ~uvm_top~ instance checks during the end_of_elaboration phase if any errors have
    been generated so far. If errors are found a UVM_FATAL error is being generated as result
    so that the simulation will not continue to the start_of_simulation_phase.
    """

    raise_exception_on_die = True
    m_relnotes_done = False

    @classmethod
    def get(cls) -> 'UVMRoot':
        """
        Static accessor for `UVMRoot`.

        The static accessor is provided as a convenience wrapper
        around retrieving the root via the `UVMCoreService.get_root`
        method::

            # Using the uvm_coreservice_t:
            uvm_coreservice_t cs
            uvm_root r
            cs = uvm_coreservice_t::get()
            r = cs.get_root()

            # Not using the uvm_coreservice_t:
            uvm_root r
            r = uvm_root::get()

        Returns:
            UVMRoot: Handle to the UVMRoot singleton.

        """
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        return cs.get_root()

    m_inst = None

    def __init__(self):
        UVMComponent.__init__(self, "__top__", None)
        #self.m_children = {}
        self.clp = UVMCmdlineProcessor.get_inst()
        #  // Variable: finish_on_completion
        #  //
        #  // If set, then run_test will call $finish after all phases are executed.
        self.finish_on_completion = True
        self.m_phase_all_done = False
        self.m_phase_all_done_event = Event('phase_all_done_event')
        # If set, then the entire testbench topology is printed just after completion
        # of the end_of_elaboration phase.
        self.enable_print_topology = False

        self.m_rh.set_name("reporter")
        self.report_header()

        #  // This sets up the global verbosity. Other command line args may
        #  // change individual component verbosity.
        self.m_check_verbosity()

        #  // Variable: top_levels
        #  //
        #  // This variable is a list of all of the top level components in UVM. It
        #  // includes the uvm_test_top component that is created by <run_test> as
        #  // well as any other top level components that have been instantiated
        #  // anywhere in the hierarchy.
        self.top_levels: List[UVMComponent] = []
        #  // Variable- phase_timeout
        #  //
        #  // Specifies the timeout for the run phase. Default is `UVM_DEFAULT_TIMEOUT
        self.phase_timeout = UVM_DEFAULT_TIMEOUT

        # Handle to the DUT (added for uvm-python)
        self._dut = None


    m_called_get_common_domain = False

    @classmethod
    def m_uvm_get_root(cls):
        """        internal function not to be used
           get the initialized singleton instance of uvm_root
        Returns:
        """
        from .uvm_domain import UVMDomain
        if UVMRoot.m_inst is None:
            UVMRoot.m_inst = UVMRoot()
        # tpoikela: Added flag to avoid infinite recursion
        if cls.m_called_get_common_domain is False:
            cls.m_called_get_common_domain = True
            UVMDomain.get_common_domain()
            UVMRoot.m_inst.m_domain = UVMDomain.get_uvm_domain()
            cls.m_called_get_common_domain = False
        return UVMRoot.m_inst


    #@cocotb.coroutine
    #def run_phase(self):
    # TODO at checks that sim_time == 0

    def get_type_name(self):
        return "uvm_root"

    def final_phase(self, phase):
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        tr_db = cs.get_default_tr_database()
        if tr_db.is_open():
            tr_db.close_db()


    @classmethod
    def get_dut(cls):
        return cls.get()._dut
    #----------------------------------------------------------------------------
    # Group: Simulation Control
    #----------------------------------------------------------------------------


    async def run_test(self, test_name="", dut=None):
        """
        Phases all components through all registered phases. If the optional
        test_name argument is provided, or if a command-line plusarg,
        +UVM_TESTNAME=TEST_NAME, is found, then the specified component is created
        just prior to phasing. The test may contain new verification components or
        the entire testbench, in which case the test and testbench can be chosen from
        the command line without forcing recompilation. If the global (package)
        variable, finish_on_completion, is set, then $finish is called after
        phasing completes.

        Args:
            test_name (str): Name of the test to run.
            dut: Handle to the DUT.
        """
        uvm_debug(self, 'run_test', 'Called with testname |' + test_name + '|')
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        factory = cs.get_factory()
        testname_plusarg = False
        test_names = []
        msg = ""
        uvm_test_top = None  # uvm_component
        self._dut = dut
        ##process phase_runner_proc; // store thread forked below for final cleanup

        # from .uvm_scheduler import UVMScheduler
        # cocotb.fork(UVMScheduler.get().run_event_loop())

        # Set up the process that decouples the thread that drops objections from
        # the process that processes drop/all_dropped objections. Thus, if the
        # original calling thread (the "dropper") gets killed, it does not affect
        # drain-time and propagation of the drop up the hierarchy.
        # Needs to be done in run_test since it needs to be in an
        # initial block to fork a process.
        uvm_debug(self, 'run_test', 'Calling m_init_objections')
        await UVMObjection.m_init_objections()

        # Retrieve the test names provided on the command line.  Command line
        # overrides the argument.
        test_name_count = self.clp.get_arg_values("+UVM_TESTNAME=", test_names)

        uvm_debug(self, 'run_test', 'Found testnames from cmdline: ' +
                str(test_names))
        # If at least one, use first in queue.
        if test_name_count > 0:
            test_name = test_names[0]
            uvm_debug(self, 'run_test', 'Found test name %s' % (test_name))
            testname_plusarg = True

        # If multiple, provided the warning giving the number, which one will be
        # used and the complete list.
        if test_name_count > 1:
            test_list = ""
            sep = ""
            for i in range(0, len(test_names)):
                if i != 0:
                    sep = ", "
                test_list = test_list + sep + test_names[i]
            self.uvm_report_warning("MULTTST", MULTI_TESTS.format(
                test_name_count, test_name, test_list), UVM_NONE)

        # if test now defined, create it using common factory
        uvm_debug(self, 'run_test', 'Running now test ' + test_name)
        if test_name != "":
            if "uvm_test_top" in self.m_children:
                uvm_fatal("TTINST",
                    "An uvm_test_top already exists via a previous call to run_test")
            #0; // forces shutdown because $finish is forked
            await uvm_zero_delay()
            uvm_debug(self, 'run_test', "factory.create in UVMRoot testname " + test_name)

            uvm_test_top = factory.create_component_by_name(test_name,
                "", "uvm_test_top", None)

            if uvm_test_top is None:
                if testname_plusarg:
                    msg = "command line +UVM_TESTNAME=" + test_name
                else:
                    msg = "call to run_test(" + test_name + ")"
                uvm_fatal("INVTST", "Requested test from " + msg + " not found.")
        await uvm_zero_delay()

        if len(self.m_children) == 0:
            uvm_fatal("NOCOMP", ("No components instantiated. You must either instantiate"
                   + " at least one component before calling run_test or use"
                   + " run_test to do so. To run a test using run_test,"
                   + " use +UVM_TESTNAME or supply the test name in"
                   + " the argument to run_test(). Exiting simulation."))
            return

        self.running_test_msg(test_name, uvm_test_top)

        # phase runner, isolated from calling process
        #fork begin
        # spawn the phase runner task
        #phase_runner_proc = process::self()
        uvm_debug(self, 'run_test', 'Forking now phases')
        cocotb.fork(UVMPhase.m_run_phases())
        uvm_debug(self, 'run_test', 'After phase-fork executing')
        #end
        #join_none
        await uvm_zero_delay()
        ##0; // let the phase runner start

        uvm_debug(self, 'run_test', 'Waiting all phases to complete JKJK')
        await self.wait_all_phases_done()
        uvm_debug(self, 'run_test', 'All phases are done now JKJK')

        #// clean up after ourselves
        #phase_runner_proc.kill()
        l_rs = get_report_server()
        l_rs.report_summarize()
        if self.finish_on_completion:
            # TODO should be linked to cocotb somehow
            self.uvm_report_info('FINISH', '$finish was reached in run_test()', UVM_NONE)


    async def wait_all_phases_done(self):
        await self.m_phase_all_done_event.wait()
        #wait (m_phase_all_done == 1)

    def die(self):
        """
        This method is called by the report server if a report reaches the maximum
        quit count or has a UVM_EXIT action associated with it, e.g., as with
        fatal errors.

        Calls the <uvm_component::pre_abort()> method
        on the entire `uvm_component` hierarchy in a bottom-up fashion.
        It then calls <uvm_report_server::report_summarize> and terminates the simulation.

        Raises:
            Exception:
        """
        l_rs = get_report_server()
        # do the pre_abort callbacks
        self.m_do_pre_abort()
        l_rs.report_summarize()
        #$finish
        if UVMRoot.raise_exception_on_die:
            raise Exception('die(): $finish from UVMRoot')

    def running_test_msg(self, test_name, uvm_test_top):
        if test_name == "":
            self.uvm_report_info("RNTST", "Running test ...", UVM_LOW)
        elif test_name == uvm_test_top.get_type_name():
            self.uvm_report_info("RNTST", "Running test " + test_name + "...", UVM_LOW)
        else:
            self.uvm_report_info("RNTST", ("Running test " + uvm_test_top.get_type_name()
                + " (via factory override for test \"" + test_name + "\")..."), UVM_LOW)

    m_uvm_timeout_overridable = 1
    #  // Function: set_timeout
    #  //
    #  // Specifies the timeout for the simulation. Default is <`UVM_DEFAULT_TIMEOUT>
    #  //
    #  // The timeout is simply the maximum absolute simulation time allowed before a
    #  // ~FATAL~ occurs.  If the timeout is set to 20ns, then the simulation must end
    #  // before 20ns, or a ~FATAL~ timeout will occur.
    #  //
    #  // This is provided so that the user can prevent the simulation from potentially
    #  // consuming too many resources (Disk, Memory, CPU, etc) when the testbench is
    #  // essentially hung.
    #  //
    #  //
    def set_timeout(self, timeout, overridable=1):
        if UVMRoot.m_uvm_timeout_overridable == 0:
            self.uvm_report_info("NOTIMOUTOVR", sv.sformatf(
                "Global timeout setting %0d is not overridable to %0d due to a previous setting.",
                self.phase_timeout, timeout), UVM_NONE)
            return

        UVMRoot.m_uvm_timeout_overridable = overridable
        self.phase_timeout = timeout


    #  //----------------------------------------------------------------------------
    #  // Group: Topology
    #  //----------------------------------------------------------------------------


    def find(self, comp_match):
        """
        Find components from the hierarchy.

        Args:
            comp_match (str): String to match.
        Returns:
            UVMComponent: First component matching the string.
        """
        comp_list = []

        self.find_all(comp_match, comp_list)

        if len(comp_list) > 1:
            uvm_report_warning("MMATCH",
            sv.sformatf("Found %0d components matching '%s'. Returning first match, %0s.",
                      len(comp_list), comp_match,comp_list[0].get_full_name()), UVM_NONE)

        if len(comp_list) == 0:
            uvm_report_warning("CMPNFD",
              "Component matching '", comp_match,
               "' was not found in the list of uvm_components", UVM_NONE)
            return None

        return comp_list[0]

    def find_all(self, comp_match, comps: List[UVMComponent], comp=None):
        """
        Returns the component handle (find) or list of components handles
        (find_all) matching a given string. The string may contain the wildcards,
        * and ?. Strings beginning with '.' are absolute path names. If the optional
        argument comp is provided, then search begins from that component down
        (default=all components).

        Args:
            comp_match (str):
            comps (list):
            comp (UVMComponent):
        """
        if comp is None:
            comp = self
        self.m_find_all_recurse(comp_match, comps, comp)

    def print_topology(self, printer=None):
        """
        Print the verification environment's component topology. The
        `printer` is a `UVMPrinter` object that controls the format
        of the topology printout; a `None` printer prints with the
        default output.

        Args:
            printer (UVMPrinter):
        """
        # s = ""
        if len(self.m_children) == 0:
            self.uvm_report_warning("EMTCOMP", "print_topology - No UVM components to print.",
                    UVM_NONE)
            return

        if printer is None:
            from .uvm_global_vars import uvm_default_printer
            printer = uvm_default_printer

        for c in self.m_children:
            if self.m_children[c].print_enabled:
                printer.print_object("", self.m_children[c])
        self.uvm_report_info("UVMTOP", "UVM testbench topology:\n" + printer.emit(), UVM_NONE)



    def m_find_all_recurse(self, comp_match, comps: List[UVMComponent], comp=None):
        """
          PRIVATE members
         extern function void m_find_all_recurse(string comp_match,
                                                 ref uvm_component comps[$],
                                                 input uvm_component comp=None);
        Args:
            comp_match:
            comps:
            comp:
        """
        child_comp = None

        if comp.has_first_child():
            child_comp = comp.get_first_child()
            while True:
                self.m_find_all_recurse(comp_match, comps, child_comp)
                if not comp.has_next_child():
                    break
                else:
                    child_comp = comp.get_next_child()
        if uvm_is_match(comp_match, comp.get_full_name()) and comp.get_name() != "":
            comps.append(comp)



    #  extern protected function new ()

    def m_add_child(self, child: UVMComponent) -> bool:
        """
        Add child to the top levels array.
        Args:
            child (UVMComponent):
        Returns:
            bool: True if adding child succeeds, False otherwise.
        """
        if super().m_add_child(child):
            if child.get_name() == "uvm_test_top":
                self.top_levels.insert(0, child)
            else:
                self.top_levels.append(child)
            return True
        else:
            return False


    def build_phase(self, phase: UVMPhase) -> None:
        """
         extern function void build_phase(uvm_phase phase)
        Args:
            phase:
        """
        UVMComponent.build_phase(self, phase)
        self.m_set_cl_msg_args()
        self.m_do_verbosity_settings()
        self.m_do_timeout_settings()
        self.m_do_factory_settings()
        self.m_do_config_settings()
        self.m_do_max_quit_settings()
        self.m_do_dump_args()


    def m_do_verbosity_settings(self) -> None:
        """
         extern local function void m_do_verbosity_settings()
        """
        set_verbosity_settings = []
        split_vals = []
        #tmp_verb = 0

        # Retrieve them all into set_verbosity_settings
        self.clp.get_arg_values("+uvm_set_verbosity=", set_verbosity_settings)

        for i in range(len(set_verbosity_settings)):
            uvm_split_string(set_verbosity_settings[i], ",", split_vals)
            if len(split_vals) < 4 or len(split_vals) > 5:
                self.uvm_report_warning("INVLCMDARGS",
                  sv.sformatf(MSG_INVLCMDARGS, set_verbosity_settings[i]), UVM_NONE, "", "")

            # Invalid verbosity
            if self.clp.m_convert_verb(split_vals[2]) == -1:
                self.uvm_report_warning("INVLCMDVERB",
                  sv.sformatf("Invalid verbosity found on the command line for setting '%s'.",
                  set_verbosity_settings[i]), UVM_NONE, "", "")
        #endfunction
        #
        #

    def m_do_timeout_settings(self) -> None:
        """
         extern local function void m_do_timeout_settings()
        """
        timeout_settings = []
        timeout = ""
        timeout_int = 0
        override_spec = ""
        timeout_count = self.clp.get_arg_values("+UVM_TIMEOUT=", timeout_settings)

        if timeout_count == 0:
            return
        else:
            timeout = timeout_settings[0]
            if timeout_count > 1:
                timeout_list = ""
                sep = ""
                for i in range(len(timeout_settings)):
                    if i != 0:
                        sep = "; "
                    timeout_list = timeout_list + sep + timeout_settings[i]

                self.uvm_report_warning("MULTTIMOUT",
                  sv.sformatf(MSG_MULTTIMOUT, timeout_count, timeout, timeout_list), UVM_NONE)

            self.uvm_report_info("TIMOUTSET",
                sv.sformatf("'+UVM_TIMEOUT=%s' provided on the command line is being applied.",
                    timeout), UVM_NONE)

            matches = sv.sscanf(timeout,"%d,%s", timeout_int, override_spec)
            if len(matches) == 2:
                override_spec, timeout_int = matches
            if override_spec == "YES":
                self.set_timeout(timeout_int, 1)
            elif override_spec == "NO":
                self.set_timeout(timeout_int, 0)
            else:
                self.set_timeout(timeout_int, 1)


    def m_do_factory_settings(self) -> None:
        """
         extern local function void m_do_factory_settings()
        """
        args = []

        self.clp.get_arg_matches("/^\\+(UVM_SET_INST_OVERRIDE|uvm_set_inst_override)=/",args)
        for i in range(len(args)):
            value = args[i][23:len(args[i])]
            self.m_process_inst_override(value)

        self.clp.get_arg_matches("/^\\+(UVM_SET_TYPE_OVERRIDE|uvm_set_type_override)=/",args)
        for i in range(len(args)):
            value = args[i][23:len(args[i])]
            self.m_process_type_override(value)


    def m_process_inst_override(self, ovr) -> None:
        """
        extern local function void m_process_inst_override(string ovr)
        Args:
            ovr:
        """
        from .uvm_coreservice import UVMCoreService
        split_val = []
        cs = UVMCoreService.get()
        factory = cs.get_factory()

        uvm_split_string(ovr, ",", split_val)

        if len(split_val) != 3:
            self.uvm_report_error("UVM_CMDLINE_PROC", "Invalid setting for +uvm_set_inst_override="
                + ovr
                + ", setting must specify <requested_type>,<override_type>,<instance_path>", UVM_NONE)
            return

        uvm_info("INSTOVR",
            "Applying instance override from the command line: +uvm_set_inst_override=" + str(ovr),
            UVM_NONE)
        factory.set_inst_override_by_name(split_val[0], split_val[1], split_val[2])
        #endfunction
        #

    def m_process_type_override(self, ovr):
        """
         extern local function void m_process_type_override(string ovr)
        Args:
            ovr:
        """
        pass  # TODO


    def m_do_config_settings(self):
        """
        Processes config value options set from cmdline:
          +uvm_set_config_int=
          +uvm_set_config_string=
        """
        args = []

        self.clp.get_arg_matches("/^\\+(UVM_SET_CONFIG_INT|uvm_set_config_int)=/", args)
        for i in range(len(args)):
            self.m_process_config(args[i][20:len(args[i])], 1)

        self.clp.get_arg_matches("/^\\+(UVM_SET_CONFIG_STRING|uvm_set_config_string)=/",args)
        for i in range(len(args)):
            self.m_process_config(args[i][23:len(args[i])], 0)

        # TODO might not be needed, ever
        #self.clp.get_arg_matches("/^\\+(UVM_SET_DEFAULT_SEQUENCE|uvm_set_default_sequence)=/", args)
        #for i in range(len(args)):
        #    self.m_process_default_sequence(args[i][26:len(args[i])])


    #  extern local function void m_do_max_quit_settings()
    def m_do_max_quit_settings(self):
        max_quit_settings = []
        max_quit_count = 0
        max_quit = ""
        split_max_quit = []
        max_quit_int = 0
        srvr = UVMReportServer.get_server()
        max_quit_count = self.clp.get_arg_values("+UVM_MAX_QUIT_COUNT=", max_quit_settings)
        if max_quit_count == 0:
            return
        else:
            max_quit = max_quit_settings[0]
            if max_quit_count > 1:
                max_quit_list = ""
                sep = ""
                for i in range(len(max_quit_settings)):
                    if i != 0:
                        sep = "; "
                    max_quit_list = max_quit_list + sep + max_quit_settings[i]

                self.uvm_report_warning("MULTMAXQUIT",
                  sv.sformatf(WARN_MAX_QUIT_COUNT,
                  max_quit_count, max_quit, max_quit_list), UVM_NONE)

            self.uvm_report_info("MAXQUITSET",
                sv.sformatf("'+UVM_MAX_QUIT_COUNT=%s' provided on the command line is being applied.",
                    max_quit), UVM_NONE)
            uvm_split_string(max_quit, ",", split_max_quit)
            max_quit_int = int(split_max_quit[0])
            if len(split_max_quit) > 1:
                if split_max_quit[1] == "YES":
                    srvr.set_max_quit_count(max_quit_int, 1)
                elif split_max_quit[1] == "NO":
                    srvr.set_max_quit_count(max_quit_int, 0)
            else:
                srvr.set_max_quit_count(max_quit_int, 1)

    def m_do_dump_args(self):
        """
         extern local function void m_do_dump_args()
        """
        dump_args = []
        all_args = []
        out_string = ""
        if self.clp.get_arg_matches("+UVM_DUMP_CMDLINE_ARGS", dump_args):
            all_args = self.clp.get_args()
            for i in range(len(all_args)):
                if (all_args[i] == "__-f__"):
                    continue
                out_string = out_string + all_args[i] + " "
            uvm_info("DUMPARGS", out_string, UVM_NONE)


    def m_process_config(self, cfg, is_int):
        """
        extern local function void m_process_config(string cfg, bit is_int)
        Args:
            cfg:
            is_int:
        """
        from .uvm_coreservice import UVMCoreService
        v = 0
        split_val = []
        cs = UVMCoreService.get()
        m_uvm_top = cs.get_root()

        uvm_split_string(cfg, ",", split_val)
        if len(split_val) == 1:
            uvm_report_error("UVM_CMDLINE_PROC", ("Invalid +uvm_set_config command\""
                + cfg + "\" missing field and value: component is \""
                + split_val[0] + "\""), UVM_NONE)
            return

        if len(split_val) == 2:
            uvm_report_error("UVM_CMDLINE_PROC", "Invalid +uvm_set_config command\""
                + cfg + "\" missing value: component is \"" + split_val[0]
                + "\"  field is \"" + split_val[1] + "\"", UVM_NONE)
            return

        if len(split_val) > 3:
            uvm_report_error("UVM_CMDLINE_PROC", sv.sformatf(
                "Invalid +uvm_set_config command\"%s\" : expected only 3 fields (component, field and value).",
                cfg), UVM_NONE)
            return

        if is_int:
            if len(split_val[2]) > 2:
                #base = split_val[2].substr(0,1)
                base = split_val[2][0:2]
                extval = split_val[2][2:len(split_val[2])]
                if base in ["'b", "0b"]:
                    v = int(extval, 2)
                elif base == "'o":
                    v = int(extval, 8)
                elif base == "'d":
                    v = int(extval, 10)
                elif base in ["'h", "'x", "0x"]:
                    v = int(extval, 16)
                else:
                    v = int(split_val[2])
            else:
                v = int(split_val[2])

            self.uvm_report_info("UVM_CMDLINE_PROC", ("Applying config setting "
                    + "from the command line: +uvm_set_config_int=" + cfg), UVM_NONE)
            UVMConfigDb.set(m_uvm_top, split_val[0], split_val[1], v)
        else:
            self.uvm_report_info("UVM_CMDLINE_PROC",
                "Applying config setting from the command line: +uvm_set_config_string=" + cfg, UVM_NONE)
            UVMConfigDb.set(m_uvm_top, split_val[0], split_val[1], split_val[2])


    #  extern local function void m_process_default_sequence(string cfg)

    def m_check_verbosity(self):
        """
         extern function void m_check_verbosity()
        """
        verb_string = ""
        verb_settings = []
        verb_count = 0
        plusarg = 0
        verbosity = UVM_MEDIUM

        # Retrieve the verbosities provided on the command line.
        verb_count = self.clp.get_arg_values("+UVM_VERBOSITY=", verb_settings)
        if verb_count:
            verb_settings.append(verb_string)

        # If none provided, provide message about the default being used.
        if verb_count == 0:
            self.uvm_report_info("DEFVERB",
                "No verbosity specified on the command line.  Using the default: UVM_MEDIUM", UVM_NONE)
        #
        # If at least one, use the first.
        if verb_count > 0:
            verb_string = verb_settings[0]
            plusarg = 1

        # If more than one, provide the warning stating how many, which one will
        # be used and the complete list.
        if (verb_count > 1):
            verb_list = ""
            sep = ""
            for i in range(len(verb_settings)):
                if (i != 0):
                    sep = ", "
                verb_list = verb_list + sep + verb_settings[i]
            self.uvm_report_warning("MULTVERB",
              sv.sformatf(WARN_MSG1, verb_count, verb_string, verb_list), UVM_NONE)

        if (plusarg == 1):
            # case(verb_string)
            if verb_string == "UVM_NONE":
                verbosity = UVM_NONE
            elif verb_string == "NONE":
                verbosity = UVM_NONE
            elif verb_string == "UVM_LOW":
                verbosity = UVM_LOW
            elif verb_string == "LOW":
                verbosity = UVM_LOW
            elif verb_string == "UVM_MEDIUM":
                verbosity = UVM_MEDIUM
            elif verb_string == "MEDIUM":
                verbosity = UVM_MEDIUM
            elif verb_string == "UVM_HIGH":
                verbosity = UVM_HIGH
            elif verb_string == "HIGH":
                verbosity = UVM_HIGH
            elif verb_string == "UVM_FULL":
                verbosity = UVM_FULL
            elif verb_string == "FULL":
                verbosity = UVM_FULL
            elif verb_string == "UVM_DEBUG":
                verbosity = UVM_DEBUG
            elif verb_string == "DEBUG":
                verbosity = UVM_DEBUG
            else:
                verbosity = int(verb_string)
                if verbosity > 0:
                    self.uvm_report_info("NSTVERB",
                            sv.sformatf(NON_STD_VERB, verbosity), UVM_NONE)
                if verbosity == 0:
                    verbosity = UVM_MEDIUM
                    self.uvm_report_warning("ILLVERB", "Illegal verbosity value, using default of UVM_MEDIUM.", UVM_NONE)

        self.set_report_verbosity_level_hier(verbosity)

        #endfunction

    def report_header(self, _file=0) -> None:
        """
         extern virtual function void report_header(UVM_FILE file = 0)
        Args:
            _file:
        """
        q = []
        args = []

        #srvr = UVMReportServer.get_server()
        clp = UVMCmdlineProcessor.get_inst()

        if clp.get_arg_matches("+UVM_NO_RELNOTES", args):
            return

        q.append("\n" + LINE + "\n")
        q.append(uvm_revision_string() + "\n")
        q.append(uvm_mgc_copyright + "\n")
        q.append(uvm_cdn_copyright + "\n")
        q.append(uvm_snps_copyright + "\n")
        q.append(uvm_cy_copyright + "\n")
        q.append(uvm_nv_copyright + "\n")
        q.append(uvm_tpoikela_copyright + "\n")
        q.append(LINE + "\n")

        if UVM_OBJECT_DO_NOT_NEED_CONSTRUCTOR == 0:
            if UVMRoot.m_relnotes_done is False:
                q.append("\n  ***********       IMPORTANT RELEASE NOTES         ************\n")
            q.append("\n  You are using a Python version of the UVM library which \n")
            q.append("  requires cocotb and an HDL simulator.\n")
            UVMRoot.m_relnotes_done = True

        if UVMRoot.m_relnotes_done is True:
            q.append("\n      (Specify +UVM_NO_RELNOTES to turn off this notice)\n")

        self.uvm_report_info("UVM/RELNOTES", UVM_STRING_QUEUE_STREAMING_PACK(q), UVM_LOW)


    #  // For error checking
    #  extern virtual task run_phase (uvm_phase phase)

    def phase_started(self, phase) -> None:
        """
        At end of elab phase we need to do tlm binding resolution.

        Args:
            phase (UVMPhase): Current phase for this callback.
        """
        eof_elab_phase = UVMEndOfElaborationPhase.get()
        uvm_debug(self, 'phase_started', phase.get_name())
        #if phase == end_of_elaboration_ph:
        if phase.get_name() == eof_elab_phase.get_name():
            uvm_debug(self, 'phase_started', "uvm_root resolving bindings now..")
            self.do_resolve_bindings()
            if self.enable_print_topology:
                self.print_topology()
            srvr = UVMReportServer.get_server()
            if srvr.get_severity_count(UVM_ERROR) > 0:
                self.uvm_report_fatal("BUILDERR", "stopping due to build errors", UVM_NONE)


    # function void end_of_elaboration_phase(uvm_phase phase);
    #	 uvm_component_proxy p = new("proxy")
    #	 uvm_top_down_visitor_adapter#(uvm_component) adapter = new("adapter")
    #	 uvm_coreservice_t cs = uvm_coreservice_t::get()
    #	 uvm_visitor#(uvm_component) v = cs.get_component_visitor()
    #	 adapter.accept(this, v, p)
    # endfunction


#----------------------------------------------------------------------------
# Group: Global Variables
#----------------------------------------------------------------------------

def get_report_server() -> 'UVMReportServer':
    from .uvm_report_server import UVMReportServer
    return UVMReportServer.get_server()

#------------------------------------------------------------------------------
# Variable: uvm_top
#
# This is the top-level that governs phase execution and provides component
# search interface. See <uvm_root> for more information.
#------------------------------------------------------------------------------
uvm_top: UVMRoot = UVMRoot.get()

#//-----------------------------------------------------------------------------
#// IMPLEMENTATION
#//-----------------------------------------------------------------------------
#
#
#
#
#// m_process_type_override
#// -----------------------
#
#function void uvm_root::m_process_type_override(string ovr)
#  string split_val[$]
#  int replace=1
#  uvm_coreservice_t cs = uvm_coreservice_t::get();
#  uvm_factory factory=cs.get_factory()
#
#  uvm_split_string(ovr, ",", split_val)
#
#  if(split_val.size() > 3 || split_val.size() < 2):
#    uvm_report_error("UVM_CMDLINE_PROC", {"Invalid setting for +uvm_set_type_override=", ovr,
#      ", setting must specify <requested_type>,<override_type>[,<replace>]"}, UVM_NONE)
#    return
#  end
#
#  // Replace arg is optional. If set, must be 0 or 1
#  if(split_val.size() == 3):
#    if(split_val[2]=="0") replace =  0
#    else if (split_val[2] == "1") replace = 1
#    else begin
#      uvm_report_error("UVM_CMDLINE_PROC", {"Invalid replace arg for +uvm_set_type_override=", ovr ," value must be 0 or 1"}, UVM_NONE)
#      return
#    end
#  end
#
#  self.uvm_report_info("UVM_CMDLINE_PROC", {"Applying type override from the command line: +uvm_set_type_override=", ovr}, UVM_NONE)
#  factory.set_type_override_by_name(split_val[0], split_val[1], replace)
#endfunction
#
#
#
#// m_process_default_sequence
#// ----------------
#
#function void uvm_root::m_process_default_sequence(string cfg)
#  string split_val[$]
#  uvm_coreservice_t cs = uvm_coreservice_t::get()
#  uvm_root m_uvm_top = cs.get_root();
#  uvm_factory f = cs.get_factory()
#  uvm_object_wrapper w
#
#  uvm_split_string(cfg, ",", split_val)
#  if(split_val.size() == 1):
#    uvm_report_error("UVM_CMDLINE_PROC", {"Invalid +uvm_set_default_sequence command\"", cfg,
#      "\" missing phase and type: sequencer is \"", split_val[0], "\""}, UVM_NONE)
#    return
#  end
#
#  if(split_val.size() == 2):
#    uvm_report_error("UVM_CMDLINE_PROC", {"Invalid +uvm_set_default_sequence command\"", cfg,
#      "\" missing type: sequencer is \"", split_val[0], "\"  phase is \"", split_val[1], "\""}, UVM_NONE)
#    return
#  end
#
#  if(split_val.size() > 3):
#    uvm_report_error("UVM_CMDLINE_PROC",
#      $sformatf("Invalid +uvm_set_default_sequence command\"%s\" : expected only 3 fields (sequencer, phase and type).", cfg), UVM_NONE)
#    return
#  end
#
#  w = f.find_wrapper_by_name(split_val[2])
#  if (w == None):
#      uvm_report_error("UVM_CMDLINE_PROC",
#                       $sformatf("Invalid type '%s' provided to +uvm_set_default_sequence", split_val[2]),
#                       UVM_NONE)
#      return
#  end
#  else begin
#      self.uvm_report_info("UVM_CMDLINE_PROC", {"Setting default sequence from the command line: +uvm_set_default_sequence=", cfg}, UVM_NONE)
#      uvm_config_db#(uvm_object_wrapper)::set(this, {split_val[0], ".", split_val[1]}, "default_sequence", w)
#  end
#
#endfunction : m_process_default_sequence
#
#
#
#
#// It is required that the run phase start at simulation time 0
#// TBD this looks wrong - taking advantage of uvm_root not doing anything else?
#// TBD move to phase_started callback?
#task uvm_root::run_phase (uvm_phase phase)
#  // check that the commandline are took effect
#  foreach(m_uvm_applied_cl_action[idx])
#	  if(m_uvm_applied_cl_action[idx].used==0):
#		    `uvm_warning("INVLCMDARGS",$sformatf("\"+uvm_set_action=%s\" never took effect due to a mismatching component pattern",m_uvm_applied_cl_action[idx].arg))
#	  end
#  foreach(m_uvm_applied_cl_sev[idx])
#	  if(m_uvm_applied_cl_sev[idx].used==0):
#		    `uvm_warning("INVLCMDARGS",$sformatf("\"+uvm_set_severity=%s\" never took effect due to a mismatching component pattern",m_uvm_applied_cl_sev[idx].arg))
#	  end
#
#  if($time > 0)
#    `uvm_fatal("RUNPHSTIME", {"The run phase must start at time 0, current time is ",
#       $sformatf("%0t", $realtime), ". No non-zero delays are allowed before ",
#       "run_test(), and pre-run user defined phases may not consume ",
#       "simulation time before the start of the run phase."})
#endtask
