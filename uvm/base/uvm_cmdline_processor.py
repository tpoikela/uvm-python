#
#------------------------------------------------------------------------------
#   Copyright 2011 Mentor Graphics Corporation
#   Copyright 2011 Cadence Design Systems, Inc.
#   Copyright 2011 Synopsys, Inc.
#   Copyright 2013 NVIDIA Corporation
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


import regex
import cocotb

from .uvm_report_object import UVMReportObject
from .uvm_debug import *
from ..macros import uvm_error
from .uvm_object_globals import *
from .uvm_globals import uvm_check_output_args


class UVMCmdLineVerb:
    def __init__(self):
        self.comp_path = ""
        self.id = ""
        self.verb = 0
        self.exec_time = 0

# Class: uvm_cmdline_processor
#
# This class provides an interface to the command line arguments that
# were provided for the given simulation.  The class is intended to be
# used as a singleton, but that isn't required.  The generation of the
# data structures which hold the command line argument information
# happens during construction of the class object.  A global variable
# called ~uvm_cmdline_proc~ is created at initialization time and may
# be used to access command line information.
#
# The uvm_cmdline_processor class also provides support for setting various UVM
# variables from the command line such as components' verbosities and configuration
# settings for integral types and strings.  Each of these capabilities is described
# in the Built-in UVM Aware Command Line Arguments section.
#

def uvm_dpi_get_tool_name():
    return "cocotb + iverilog"

def uvm_dpi_regcomp(match):
    rr = None
    try:
        rr = regex.compile(match)
    except:
        pass
    return rr


def uvm_dpi_regexec(exp_h, elem):
    if exp_h.match(elem) is not None:
        return 0
    return 1


class UVMCmdlineProcessor(UVMReportObject):

    m_inst = None
    uvm_cmdline_proc = None

    # Used in unit tests
    m_test_mode = False
    m_test_plusargs = {}

    # Group: Singleton

    # Function: get_inst
    #
    # Returns the singleton instance of the UVM command line processor.

    @classmethod
    def get_inst(cls):
        if UVMCmdlineProcessor.m_inst is None:
           UVMCmdlineProcessor.m_inst = UVMCmdlineProcessor("uvm_cmdline_proc")
        return UVMCmdlineProcessor.m_inst

    # Group: Basic Arguments

    # Function: get_args
    #
    # This function returns a queue with all of the command line
    # arguments that were used to start the simulation. Note that
    # element 0 of the array will always be the name of the
    # executable which started the simulation.
    def get_args(self):
        return self.m_argv

    # Function: get_plusargs
    #
    # This function returns a queue with all of the plus arguments
    # that were used to start the simulation. Plusarguments may be
    # used by the simulator vendor, or may be specific to a company
    # or individual user. Plusargs never have extra arguments
    # (i.e. if there is a plusarg as the second argument on the
    # command line, the third argument is unrelated); this is not
    # necessarily the case with vendor specific dash arguments.
    def get_plusargs(self):
        return self.m_plus_argv

    # Function: get_uvmargs
    #
    # This function returns a queue with all of the uvm arguments
    # that were used to start the simulation. A UVM argument is
    # taken to be any argument that starts with a - or + and uses
    # the keyword UVM (case insensitive) as the first three
    # letters of the argument.
    def get_uvm_args(self):
        return self.m_uvm_argv

    # Function: get_arg_matches
    #
    # This function loads a queue with all of the arguments that
    # match the input expression and returns the number of items
    # that matched. If the input expression is bracketed
    # with #, then it is taken as an extended regular expression
    # otherwise, it is taken as the beginning of an argument to match.
    # For example:
    #
    #| string myargs[$]
    #| initial begin
    #|    void'(uvm_cmdline_proc.get_arg_matches("+foo",myargs)); #matches +foo, +foobar
    #|                                                            #doesn't match +barfoo
    #|    void'(uvm_cmdline_proc.get_arg_matches("/foo/",myargs)); #matches +foo, +foobar,
    #|                                                             #foo.sv, barfoo, etc.
    #|    void'(uvm_cmdline_proc.get_arg_matches("/^foo.*\.sv",myargs)); #matches foo.sv
    #|                                                                   #and foo123.sv,
    #|                                                                   #not barfoo.sv.
    def get_arg_matches(self, match, args):
        exp_h = None
        match_len = len(match)
        args.clear()
        if len(match) > 2 and match[0] == "/" and match[len(match)-1] == "/":
            match = match[1:len(match)-2]
            exp_h = uvm_dpi_regcomp(match)
            if exp_h is None:
                uvm_error("UVM_CMDLINE_PROC",
                        "Unable to compile the regular expression: " + match)
                return 0
        for i in range(len(self.m_argv)):
            if exp_h is not None:
                if uvm_dpi_regexec(exp_h, self.m_argv[i]) == 0:
                    args.append(self.m_argv[i])
            elif len(self.m_argv[i]) >= match_len:
                sub_argv = self.m_argv[i][0:match_len]
                if sub_argv == match:
                    args.append(self.m_argv[i])
        return len(args)

    # Group: Argument Values

    # Function: get_arg_value
    #
    # This function finds the first argument which matches the ~match~ arg and
    # returns the suffix of the argument. This is similar to the $value$plusargs
    # system task, but does not take a formatting string. The return value is
    # the number of command line arguments that match the ~match~ string, and
    # ~value~ is the value of the first match.
    def get_arg_value(self, match, value):
        uvm_check_output_args([value])
        chars = len(match)
        get_arg_value = 0
        for i in range(0, len(self.m_argv)):
            if len(self.m_argv[i]) >= chars:
                arg_to_try = self.m_argv[i][0:chars]

                if arg_to_try == match:
                    get_arg_value += 1
                    if get_arg_value == 1:
                        value.append(self.m_argv[i][chars:len(self.m_argv[i])])
        return get_arg_value

    # Function: get_arg_values
    #
    # This function finds all the arguments which matches the ~match~ arg and
    # returns the suffix of the arguments in a list of values. The return
    # value is the number of matches that were found (it is the same as
    # values.size() ).
    # For example if '+foo=1,yes,on +foo=5,no,off' was provided on the command
    # line and the following code was executed:
    #
    #| string foo_values[$]
    #| initial begin
    #|    void'(uvm_cmdline_proc.get_arg_values("+foo=",foo_values))
    #|
    #
    # The foo_values queue would contain two entries.  These entries are shown
    # here:
    #
    #   0 - "1,yes,on"
    #   1 - "5,no,off"
    #
    # Splitting the resultant string is left to user but using the
    # uvm_split_string() function is recommended.
    def get_arg_values(self, match, values):
        values.clear()
        #if match[0] == '+':
        #    match = match[1:]
        #if match[-1] == '=':
        #    match = match[:-1]

        chars = len(match)
        for i in range(len(self.m_argv)):
            if len(self.m_argv[i]) >= chars:
                argv_str = self.m_argv[i][0:chars]
                if argv_str == match:
                    val = self.m_argv[i][chars:len(self.m_argv[i])]
                    values.append(val)
            else:
                pass
        return len(values)

    # Group: Tool information

    # Function: get_tool_name
    #
    # Returns the simulation tool that is executing the simulation.
    # This is a vendor specific string.
    def get_tool_name(self):
        return uvm_dpi_get_tool_name()

    # Function: get_tool_version
    #
    # Returns the version of the simulation tool that is executing the simulation.
    # This is a vendor specific string.
    def get_tool_version(self):
        return uvm_dpi_get_tool_version()

    # constructor
    def __init__(self, name=""):
        UVMReportObject.__init__(self,name)
        self.m_argv = []
        self.m_plus_argv = []
        self.m_uvm_argv = []
        self.m_plus_arg_map = {}  # string -> []

        s = ""
        sub = ""

        ok = True
        plusarg_dict = cocotb.plusargs
        if UVMCmdlineProcessor.m_test_mode is True:
            plusarg_dict = UVMCmdlineProcessor.m_test_plusargs

        for name in plusarg_dict:
            uvm_debug(self, '__init__', "name is %s, val %s" % (name, plusarg_dict[name]))
            arg_val = plusarg_dict[name]
            s = name
            full_plus_arg = "+" + s + "=" + str(arg_val)
            if s != "":
                if name not in self.m_plus_arg_map:
                    self.m_plus_arg_map[name] = []
                self.m_plus_arg_map[name].append(arg_val)
                self.m_plus_argv.append(full_plus_arg)
                self.m_argv.append(full_plus_arg)
                uvm_debug(self, '__init__', "Added plusarg " + name + ' - ' +
                        full_plus_arg)
                if len(full_plus_arg) >= 4 and (full_plus_arg[0] == "-" or full_plus_arg[0] == "+"):
                    sub = full_plus_arg[1:4]
                    #sub = sub.toupper()
                    if sub == "UVM":
                        uvm_debug(self, '__init__', "Found UVM plusarg %s" % (full_plus_arg))
                        self.m_uvm_argv.append(full_plus_arg)
            ok = s != ""

        # Group: Command Line Debug

        # Variable: +UVM_DUMP_CMDLINE_ARGS
        #
        # ~+UVM_DUMP_CMDLINE_ARGS~ allows the user to dump all command line arguments to the
        # reporting mechanism.  The output in is tree format.

        # The implementation of this is in uvm_root.

        # Group: Built-in UVM Aware Command Line Arguments

        # Variable: +UVM_TESTNAME
        #
        # ~+UVM_TESTNAME=<class name>~ allows the user to specify which uvm_test (or
        # uvm_component) should be created via the factory and cycled through the UVM phases.
        # If multiple of these settings are provided, the first occurrence is used and a warning
        # is issued for subsequent settings.  For example:
        #
        #| <sim command> +UVM_TESTNAME=read_modify_write_test
        #

        # The implementation of this is in uvm_root since this is procedurally invoked via
        # ovm_root::run_test().

        # Variable: +UVM_VERBOSITY
        #
        # ~+UVM_VERBOSITY=<verbosity>~ allows the user to specify the initial verbosity
        # for all components.  If multiple of these settings are provided, the first occurrence
        # is used and a warning is issued for subsequent settings.  For example:
        #
        #| <sim command> +UVM_VERBOSITY=UVM_HIGH
        #

        # The implementation of this is in uvm_root since this is procedurally invoked via
        # ovm_root::new().

        # Variable: +uvm_set_verbosity
        #
        # ~+uvm_set_verbosity=<comp>,<id>,<verbosity>,<phase>~ and
        # ~+uvm_set_verbosity=<comp>,<id>,<verbosity>,time,<time>~ allow the users to manipulate the
        # verbosity of specific components at specific phases (and times during the "run" phases)
        # of the simulation.  The ~id~ argument can be either ~_ALL_~ for all IDs or a
        # specific message id.  Wildcarding is not supported for ~id~ due to performance concerns.
        # Settings for non-"run" phases are executed in order of occurrence on the command line.
        # Settings for "run" phases (times) are sorted by time and then executed in order of
        # occurrence for settings of the same time.  For example:
        #
        #| <sim command> +uvm_set_verbosity=uvm_test_top.env0.agent1.*,_ALL_,UVM_FULL,time,800
        #

        # Variable: +uvm_set_action
        #
        # ~+uvm_set_action=<comp>,<id>,<severity>,<action>~ provides the equivalent of
        # various uvm_report_object's set_report_*_action APIs.  The special keyword,
        # ~_ALL_~, can be provided for both/either the ~id~ and/or ~severity~ arguments.  The
        # action can be UVM_NO_ACTION or a | separated list of the other UVM message
        # actions.  For example:
        #
        #| <sim command> +uvm_set_action=uvm_test_top.env0.*,_ALL_,UVM_ERROR,UVM_NO_ACTION
        #

        # Variable: +uvm_set_severity
        #
        # ~+uvm_set_severity=<comp>,<id>,<current severity>,<new severity>~ provides the
        # equivalent of the various uvm_report_object's set_report_*_severity_override APIs. The
        # special keyword, ~_ALL_~, can be provided for both/either the ~id~ and/or
        # ~current severity~ arguments.  For example:
        #
        #| <sim command> +uvm_set_severity=uvm_test_top.env0.*,BAD_CRC,UVM_ERROR,UVM_WARNING
        #

        # Variable: +UVM_TIMEOUT
        #
        # ~+UVM_TIMEOUT=<timeout>,<overridable>~ allows users to change the global timeout of the UVM
        # framework.  The <overridable> argument ('YES' or 'NO') specifies whether user code can subsequently
        # change this value.  If set to 'NO' and the user code tries to change the global timeout value, an
        # warning message will be generated.
        #
        #| <sim command> +UVM_TIMEOUT=200000,NO
        #

        # The implementation of this is in uvm_root.

        # Variable: +UVM_MAX_QUIT_COUNT
        #
        # ~+UVM_MAX_QUIT_COUNT=<count>,<overridable>~ allows users to change max quit count for the report
        # server.  The <overridable> argument ('YES' or 'NO') specifies whether user code can subsequently
        # change this value.  If set to 'NO' and the user code tries to change the max quit count value, an
        # warning message will be generated.
        #
        #| <sim command> +UVM_MAX_QUIT_COUNT=5,NO
        #


        # Variable: +UVM_PHASE_TRACE
        #
        # ~+UVM_PHASE_TRACE~ turns on tracing of phase executions.  Users simply need to put the
        # argument on the command line.

        # Variable: +UVM_OBJECTION_TRACE
        #
        # ~+UVM_OBJECTION_TRACE~ turns on tracing of objection activity.  Users simply need to put the
        # argument on the command line.

        # Variable: +UVM_RESOURCE_DB_TRACE
        #
        # ~+UVM_RESOURCE_DB_TRACE~ turns on tracing of resource DB access.
        # Users simply need to put the argument on the command line.

        # Variable: +UVM_CONFIG_DB_TRACE
        #
        # ~+UVM_CONFIG_DB_TRACE~ turns on tracing of configuration DB access.
        # Users simply need to put the argument on the command line.

        # Variable: +uvm_set_inst_override

        # Variable: +uvm_set_type_override
        #
        # ~+uvm_set_inst_override=<req_type>,<override_type>,<full_inst_path>~ and
        # ~+uvm_set_type_override=<req_type>,<override_type>[,<replace>]~ work
        # like the name based overrides in the factory--factory.set_inst_override_by_name()
        #  and factory.set_type_override_by_name().
        # For uvm_set_type_override, the third argument is 0 or 1 (the default is
        # 1 if this argument is left off); this argument specifies whether previous
        # type overrides for the type should be replaced.  For example:
        #
        #| <sim command> +uvm_set_type_override=eth_packet,short_eth_packet
        #

        # The implementation of this is in uvm_root.

        # Variable: +uvm_set_config_int

        # Variable: +uvm_set_config_string
        #
        # ~+uvm_set_config_int=<comp>,<field>,<value>~ and
        # ~+uvm_set_config_string=<comp>,<field>,<value>~ work like their
        # procedural counterparts: set_config_int() and set_config_string(). For
        # the value of int config settings, 'b (0b), 'o, 'd, 'h ('x or 0x)
        # as the first two characters of the value are treated as base specifiers
        # for interpreting the base of the number. Size specifiers are not used
        # since SystemVerilog does not allow size specifiers in string to
        # value conversions.  For example:
        #
        #| <sim command> +uvm_set_config_int=uvm_test_top.soc_env,mode,5
        #
        # No equivalent of set_config_object() exists since no way exists to pass a
        # uvm_object into the simulation via the command line.
        #

        # The implementation of this is in uvm_root.

        # Variable: +uvm_set_default_sequence
        #
        # The ~+uvm_set_default_sequence=<seqr>,<phase>,<type>~ plusarg allows
        # the user to define a default sequence from the command line, using the
        # ~typename~ of that sequence.  For example:
        #
        #| <sim command> +uvm_set_default_sequence=path.to.sequencer,main_phase,seq_type
        #
        # This is functionally equivalent to calling the following in your
        # test:
        #
        #| uvm_coreservice_t cs = uvm_coreservice_t::get()
        #| uvm_factory f = cs.get_factory()
        #| uvm_config_db#(uvm_object_wrapper)::set(this,
        #|                                         "path.to.sequencer.main_phase",
        #|                                         "default_sequence",
        #|                                         f.find_wrapper_by_name("seq_type"))
        #
        # The implementation of this is in uvm_root.

    def m_convert_verb(self, verb_str):
        if verb_str == "NONE":
            return UVM_NONE
        if verb_str == "UVM_NONE":
            return UVM_NONE
        if verb_str == "LOW":
            return UVM_LOW
        if verb_str == "UVM_LOW":
            return UVM_LOW
        if verb_str == "MEDIUM":
            return UVM_MEDIUM
        if verb_str == "UVM_MEDIUM":
            return UVM_MEDIUM
        if verb_str == "HIGH":
            return UVM_HIGH
        if verb_str == "UVM_HIGH":
            return UVM_HIGH
        if verb_str == "FULL":
            return UVM_FULL
        if verb_str == "UVM_FULL":
            return UVM_FULL
        if verb_str == "DEBUG":
            return UVM_DEBUG
        if verb_str == "UVM_DEBUG":
            return UVM_DEBUG
        return 0

UVMCmdlineProcessor.uvm_cmdline_proc = UVMCmdlineProcessor.get_inst()
