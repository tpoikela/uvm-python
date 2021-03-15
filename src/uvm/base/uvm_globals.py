# ------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010-2011 Synopsys, Inc.
#   Copyright 2013-2014 NVIDIA Corporation
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
#
#   uvm-python NOTE: All code ported from SystemVerilog UVM 1.2 to
#   python. Original code structures (including comments)
#   preserved where possible.
# ------------------------------------------------------------------------------

import cocotb
from cocotb.triggers import Timer, Edge, ReadWrite
from cocotb.utils import get_sim_time, simulator

from .uvm_object_globals import (UVM_CALL_HOOK, UVM_COUNT, UVM_DISPLAY, UVM_ERROR, UVM_EXIT,
                                 UVM_FATAL, UVM_INFO, UVM_LOG, UVM_LOW, UVM_MEDIUM, UVM_NONE,
                                 UVM_NO_ACTION, UVM_RM_RECORD, UVM_STOP, UVM_WARNING)
from .sv import uvm_glob_to_re, uvm_re_match
from inspect import getframeinfo, stack

# from .uvm_scheduler import uvm_default_scheduler
# Title: Globals

# ------------------------------------------------------------------------------
#
# Group: Simulation Control
#
# ------------------------------------------------------------------------------


async def run_test(test_name="", dut=None):
    """
    Convenience function for uvm_top.run_test(). See `UVMRoot` for more
    information.

    Args:
        test_name (str): Name of the test to run.
        dut: DUT object from cocotb
    """
    cs = get_cs()
    top = cs.get_root()
    await top.run_test(test_name, dut)

#//----------------------------------------------------------------------------
#//
#// Group: Reporting
#//
#//----------------------------------------------------------------------------

#// Function: uvm_get_report_object
#//
#// Returns the nearest uvm_report_object when called.
#// For the global version, it returns uvm_root.
#//
#function uvm_report_object uvm_get_report_object()
#  uvm_root top
#  uvm_coreservice_t cs
#  cs = uvm_coreservice_t::get()
#  top = cs.get_root()
#  return top
#endfunction


def uvm_report_enabled(verbosity, severity=UVM_INFO, id=""):
    """
    Returns 1 if the configured verbosity in ~uvm_top~ for this
    severity/id is greater than or equal to ~verbosity~ else returns 0.

    See also `UVMReportObject.uvm_report_enabled`.

    Static methods of an extension of `UVMReportObject`, e.g. uvm_component-based
    objects, cannot call `uvm_report_enabled` because the call will resolve to
    the `UVMReportObject.uvm_report_enabled`, which is non-static.
    Static methods cannot call non-static methods of the same class.
    """
    cs = get_cs()
    top = cs.get_root()
    return top.uvm_report_enabled(verbosity,severity,id)


#// Function: uvm_report
#
#function void uvm_report( uvm_severity severity,
#                          string id,
#                          string message,
#                          int verbosity = (severity == uvm_severity'(UVM_ERROR)) ? UVM_LOW :
#                                          (severity == uvm_severity'(UVM_FATAL)) ? UVM_NONE : UVM_MEDIUM,
#                          string filename = "",
#                          int line = 0,
#                          string context_name = "",
#                          bit report_enabled_checked = 0)
#  uvm_root top
#  uvm_coreservice_t cs
#  cs = uvm_coreservice_t::get()
#  top = cs.get_root()
#  top.uvm_report(severity, id, message, verbosity, filename, line, context_name, report_enabled_checked)
#endfunction


def uvm_report_info(id, message, verbosity=UVM_MEDIUM, filename="", line=0,
        context_name="", report_enabled_checked=False):
    if uvm_report_enabled(verbosity, UVM_INFO, id):
        cs = get_cs()
        top = cs.get_root()
        # tpoikela: Do not refactor
        if filename == "":
            caller = getframeinfo(stack()[1][0])
            filename = caller.filename
        if line == 0:
            caller = getframeinfo(stack()[1][0])
            line = caller.lineno
        top.uvm_report_info(id, message, verbosity, filename, line, context_name,
                report_enabled_checked)


def uvm_report_error(id, message, verbosity=UVM_LOW, filename="", line=0,
        context_name="", report_enabled_checked=False):
    if uvm_report_enabled(verbosity, UVM_ERROR, id):
        cs = get_cs()
        top = cs.get_root()
        # tpoikela: Do not refactor
        if filename == "":
            caller = getframeinfo(stack()[1][0])
            filename = caller.filename
        if line == 0:
            caller = getframeinfo(stack()[1][0])
            line = caller.lineno
        top.uvm_report_error(id, message, verbosity, filename, line, context_name,
                report_enabled_checked)


def uvm_report_warning(id, message, verbosity=UVM_LOW, filename="", line=0,
        context_name="", report_enabled_checked=False):
    if uvm_report_enabled(verbosity, UVM_WARNING, id):
        cs = get_cs()
        top = cs.get_root()
        # tpoikela: Do not refactor
        if filename == "":
            caller = getframeinfo(stack()[1][0])
            filename = caller.filename
        if line == 0:
            caller = getframeinfo(stack()[1][0])
            line = caller.lineno
        top.uvm_report_warning(id, message, verbosity, filename, line, context_name,
                report_enabled_checked)


def uvm_report_fatal(id, message, verbosity=UVM_NONE, filename="", line=0,
        context_name="", report_enabled_checked=False):
    """
    These methods, defined in package scope, are convenience functions that
    delegate to the corresponding component methods in ~uvm_top~. They can be
    used in module-based code to use the same reporting mechanism as class-based
    components. See <uvm_report_object> for details on the reporting mechanism.

    *Note:* Verbosity is ignored for warnings, errors, and fatals to ensure users
    do not inadvertently filter them out. It remains in the methods for backward
    compatibility.
    """

    if uvm_report_enabled(verbosity, UVM_FATAL, id):
        cs = get_cs()
        top = cs.get_root()
        # tpoikela: Do not refactor
        if filename == "":
            caller = getframeinfo(stack()[1][0])
            filename = caller.filename
        if line == 0:
            caller = getframeinfo(stack()[1][0])
            line = caller.lineno
        top.uvm_report_fatal(id, message, verbosity, filename, line, context_name,
                report_enabled_checked)

#// Function: uvm_process_report_message
#//
#// This method, defined in package scope, is a convenience function that
#// delegate to the corresponding component method in ~uvm_top~. It can be
#// used in module-based code to use the same reporting mechanism as class-based
#// components. See <uvm_report_object> for details on the reporting mechanism.
#
#function void uvm_process_report_message(uvm_report_message report_message)
#  uvm_root top
#  uvm_coreservice_t cs
#  process p
#  p = process::self()
#  cs = uvm_coreservice_t::get()
#  top = cs.get_root()
#  top.uvm_process_report_message(report_message)
#endfunction


#// TODO merge with uvm_enum_wrapper#(uvm_severity)
def uvm_string_to_severity(sev_str, sev):
    if sev_str == "UVM_INFO":
        return UVM_INFO
    if sev_str == "UVM_WARNING":
        return UVM_WARNING
    if sev_str == "UVM_ERROR":
        return UVM_ERROR
    if sev_str == "UVM_FATAL":
        return UVM_FATAL
    return -1


def uvm_string_to_action(action_str, action):
    #  string actions[$]
    actions = action_str.split('|')  # uvm_split_string(action_str,"|",actions)
    action = 0x0
    for i in range(len(actions)):
        if actions[i] == "UVM_NO_ACTION":
            action |= UVM_NO_ACTION
        if actions[i] == "UVM_DISPLAY":
            action |= UVM_DISPLAY
        if actions[i] == "UVM_LOG":
            action |= UVM_LOG
        if actions[i] == "UVM_COUNT":
            action |= UVM_COUNT
        if actions[i] == "UVM_EXIT":
            action |= UVM_EXIT
        if actions[i] == "UVM_CALL_HOOK":
            action |= UVM_CALL_HOOK
        if actions[i] == "UVM_STOP":
            action |= UVM_STOP
        if actions[i] == "UVM_RM_RECORD":
            action |= UVM_RM_RECORD
    return action

#----------------------------------------------------------------------------
#
# Group: Miscellaneous
#
#----------------------------------------------------------------------------


# Function: uvm_is_match
#
# Returns 1 if the two strings match, 0 otherwise.
#
# The first string, ~expr~, is a string that may contain '*' and '?'
# characters. A * matches zero or more characters, and ? matches any single
# character. The 2nd argument, ~str~, is the string begin matched against.
# It must not contain any wildcards.
#
#----------------------------------------------------------------------------
def uvm_is_match(expr, _str):
    s = uvm_glob_to_re(expr)
    return uvm_re_match(s, _str) == 0


UVM_LINE_WIDTH = 120
UVM_NUM_LINES = 120
UVM_SMALL_STRING = UVM_LINE_WIDTH*8-1
UVM_LARGE_STRING = UVM_LINE_WIDTH*UVM_NUM_LINES*8-1

#//----------------------------------------------------------------------------
#//
#// Function: uvm_string_to_bits
#//
#// Converts an input string to its bit-vector equivalent. Max bit-vector
#// length is approximately 14000 characters.
#//----------------------------------------------------------------------------


def uvm_string_to_bits(string: str) -> int:
    bytearr = string.encode()
    result = 0
    shift = 0
    for bb in bytearr:
        result = (result << shift) | bb
        shift += 8
    return result


#//----------------------------------------------------------------------------
#//
#// Function: uvm_bits_to_string
#//
#// Converts an input bit-vector to its string equivalent. Max bit-vector
#// length is approximately 14000 characters.
#//----------------------------------------------------------------------------

#function string uvm_bits_to_string(logic [UVM_LARGE_STRING:0] str)
#  $swrite(uvm_bits_to_string, "%0s", str)
#endfunction

#----------------------------------------------------------------------------
#
# Task: uvm_wait_for_nba_region
#
# Callers of this task will not return until the NBA region, thus allowing
# other processes any number of delta cycles (#0) to settle out before
# continuing. See `UVMSequencerBase.wait_for_sequences` for example usage.
#
# TODO: Requires some work for cocotb. Right now, high enough
# UVM_POUND_ZERO_COUNT works, but it depends on number of components/processes.
# Also, putting very high number (> 1000) decreases simulation performance a
# lot (100 = runtime 5ns, 1500 = runtime 15ns).
#
#----------------------------------------------------------------------------

#verilator = True
verilator = False

sim_product = ''
if simulator.is_running():
    sim_product = simulator.get_simulator_product()
    print("uvm-python: SIM_PRODUCT IS |" + sim_product + "|")
    if sim_product == "Verilator":
        verilator = True

def uvm_has_verilator():
    return verilator

UVM_POUND_ZERO_COUNT = 1000
#UVM_NO_WAIT_FOR_NBA = True
UVM_NO_WAIT_FOR_NBA = False

UVM_AFTER_NBA_WAIT = 10

if hasattr(cocotb, 'SIM_NAME') and getattr(cocotb, 'SIM_NAME') == 'Verilator':
    UVM_POUND_ZERO_COUNT = 100


rw_event = ReadWrite()

async def uvm_wait_for_nba_region():
    if verilator is True:
        await rw_event
    else:
        if UVM_NO_WAIT_FOR_NBA is False:
            await rw_event
        else:
            for _ in range(0, UVM_POUND_ZERO_COUNT):
                await Timer(0)


# Returns UVM coreservice
def get_cs():
    from .uvm_coreservice import UVMCoreService
    return UVMCoreService.get()

#// Class: uvm_enum_wrapper#(T)
#//
#// The ~uvm_enum_wrapper#(T)~ class is a utility mechanism provided
#// as a convenience to the end user.  It provides a <from_name>
#// method which is the logical inverse of the System Verilog ~name~
#// method which is built into all enumerations.

#class uvm_enum_wrapper#(type T=uvm_active_passive_enum)
#
#    protected static T map[string]
#
#    // Function: from_name
#    // Attempts to convert a string ~name~ to an enumerated value.
#    //
#    // If the conversion is successful, the method will return
#    // 1, otherwise 0.
#    //
#    // Note that the ~name~ passed in to the method must exactly
#    // match the value which would be produced by ~enum::name~, and
#    // is case sensitive.
#    //
#    // For example:
#    //| typedef uvm_enum_wrapper#(uvm_radix_enum) radix_wrapper
#    //| uvm_radix_enum r_v
#    //|
#    //| // The following would return '0', as "foo" isn't a value
#    //| // in uvm_radix_enum:
#    //| radix_wrapper::from_name("foo", r_v)
#    //|
#    //| // The following would return '0', as "uvm_bin" isn't a value
#    //| // in uvm_radix_enum (although the upper case "UVM_BIN" is):
#    //| radix_wrapper::from_name("uvm_bin", r_v)
#    //|
#    //| // The following would return '1', and r_v would be set to
#    //| // the value of UVM_BIN
#    //| radix_wrapper::from_name("UVM_BIN", r_v)
#    //
#    static function bit from_name(string name, ref T value)
#        if (map.size() == 0)
#          m_init_map()
#
#        if (map.exists(name)) begin
#            value = map[name]
#            return 1
#        end
#        else begin
#            return 0
#        end
#    endfunction : from_name
#
#    // Function- m_init_map
#    // Initializes the name map, only needs to be performed once
#    protected static function void m_init_map()
#        T e = e.first()
#        do
#          begin
#            map[e.name()] = e
#            e = e.next()
#          end
#        while (e != e.first())
#    endfunction : m_init_map
#
#    // Function- new
#    // Prevents accidental instantiations
#    def __init__(self, arr):
#       self.arr = arr
#
#
#endclass : uvm_enum_wrapper

#----------------------------------------------------------------------------
#
# Group: uvm-python specific functions
#
#----------------------------------------------------------------------------

def uvm_is_sim_active():
    """
    Returns true if a simulator is active/attached. Returns False for example
    when running unit tests without cocotb Makefiles.
    """
    return simulator.is_running()


def uvm_sim_time(units='NS'):
    """
    Returns current simtime in the given units (default: NS)

    Args:
        units (str): PS, NS, US, MS or S
    Returns:
        int: Simulation time in specified units
    """
    if uvm_is_sim_active():
        return get_sim_time(units=units)
    return 0


rw_event2 = ReadWrite()
timer_zero = Timer(0, "NS")

async def uvm_zero_delay():
    if verilator is True:
        await rw_event2
    else:
        await timer_zero


def uvm_check_output_args(arr):
    """
    Check that all args in the arr are lists to emulate the SV inout/output/ref args

    Raises:
    """
    for item in arr:
        if not isinstance(item, list):
            raise Exception('All output args must be given as empty arrays. Got: '
                    + str(item))
        elif len(item) != 0:
            raise Exception('All output args must be given as empty arrays. Got: '
                    + str(item) + ' len: ' + str(len(item)))
