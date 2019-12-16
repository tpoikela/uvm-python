# ------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010-2011 Synopsys, Inc.
#   Copyright 2013-2014 NVIDIA Corporation
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
# ------------------------------------------------------------------------------

import re
import cocotb
from cocotb.triggers import Timer
from cocotb.utils import get_sim_time, simulator
from .uvm_object_globals import *
from .sv import uvm_glob_to_re, uvm_re_match

UVM_POUND_ZERO_COUNT = 10
UVM_NO_WAIT_FOR_NBA = True


def uvm_sim_time(units='NS'):
    if simulator is not None:
        return get_sim_time(units=units)
    return 0

#----------------------------------------------------------------------------
#
# Group: Miscellaneous
#
#----------------------------------------------------------------------------
#
#
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

# Title: Globals

# ------------------------------------------------------------------------------
#
# Group: Simulation Control
#
# ------------------------------------------------------------------------------

# Task: run_test
#
# Convenience function for uvm_top.run_test(). See <uvm_root> for more
# information.


@cocotb.coroutine
def run_test(test_name=""):
    cs = get_cs()
    top = cs.get_root()
    yield top.run_test(test_name)


def uvm_info(id, message, verbosity):
    uvm_report_info(id, message, verbosity)


def uvm_report_info(id, message, verbosity = UVM_MEDIUM, filename = "", line = 0,
        context_name = "",  report_enabled_checked = False):
    cs = get_cs()
    top = cs.get_root();
    top.uvm_report_info(id, message, verbosity, filename, line, context_name,
            report_enabled_checked)


def uvm_report_error(id, message, verbosity = UVM_LOW, filename = "", line = 0,
        context_name = "",  report_enabled_checked = False):
    cs = get_cs()
    top = cs.get_root();
    top.uvm_report_error(id, message, verbosity, filename, line, context_name,
            report_enabled_checked)


def uvm_report_warning(id, message, verbosity = UVM_LOW, filename = "", line = 0,
        context_name = "",  report_enabled_checked = False):
    cs = get_cs()
    top = cs.get_root();
    top.uvm_report_warning(id, message, verbosity, filename, line, context_name,
            report_enabled_checked)


def uvm_report_fatal(id, message, verbosity = UVM_NONE, filename = "", line = 0,
        context_name = "",  report_enabled_checked = False):
    cs = get_cs()
    top = cs.get_root();
    top.uvm_report_fatal(id, message, verbosity, filename, line, context_name,
            report_enabled_checked)


#----------------------------------------------------------------------------
#
# Task: uvm_wait_for_nba_region
#
# Callers of this task will not return until the NBA region, thus allowing
# other processes any number of delta cycles (#0) to settle out before
# continuing. See <uvm_sequencer_base::wait_for_sequences> for example usage.
#
#----------------------------------------------------------------------------

@cocotb.coroutine
def uvm_wait_for_nba_region():
    s = ""
    nba = 0
    next_nba = 0
    
    #If `included directly in a program block, can't use a non-blocking assign,
    #but it isn't needed since program blocks are in a separate region.
    if UVM_NO_WAIT_FOR_NBA is False:
        next_nba += 1
        #nba <= next_nba;
        nba = next_nba
        #@(nba);
        yield Timer(0)
    else:
        for i in range(0, UVM_POUND_ZERO_COUNT):
            yield Timer(0)

# Function: uvm_report_enabled
#
# Returns 1 if the configured verbosity in ~uvm_top~ for this 
# severity/id is greater than or equal to ~verbosity~ else returns 0.
# 
# See also <uvm_report_object::uvm_report_enabled>.
#
# Static methods of an extension of uvm_report_object, e.g. uvm_component-based
# objects, cannot call ~uvm_report_enabled~ because the call will resolve to
# the <uvm_report_object::uvm_report_enabled>, which is non-static.
# Static methods cannot call non-static methods of the same class. 

def uvm_report_enabled(verbosity, severity=UVM_INFO, id=""):
    cs = get_cs()
    top = cs.get_root()
    return top.uvm_report_enabled(verbosity,severity,id)

# Returns UVM coreservice
def get_cs():
    from .uvm_coreservice import UVMCoreService
    return UVMCoreService.get()

import unittest

class TestUVMGlobals(unittest.TestCase):

    def test_run_test(self):
        pass

if __name__ == '__main__':
    unittest.main()
