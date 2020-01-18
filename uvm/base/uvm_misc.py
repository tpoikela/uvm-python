#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2014 NVIDIA Corporation
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
#
# File: Miscellaneous Structures
#
#------------------------------------------------------------------------------
#
# Class: uvm_void
#
# The ~uvm_void~ class is the base class for all UVM classes. It is an abstract
# class with no data members or functions. It allows for generic containers of
# objects to be created, similar to a void pointer in the C programming
# language. User classes derived directly from ~uvm_void~ inherit none of the
# UVM functionality, but such classes may be placed in ~uvm_void~-typed
# containers along with other UVM objects.
#
#------------------------------------------------------------------------------

import re
from .uvm_object_globals import *
from .uvm_scope_stack import UVMScopeStack


class UVMVoid(object):
    pass


UVM_APPEND = 0
UVM_PREPEND = 1

UVM_ENABLE_FIELD_CHECKS = 0


def isunknown(value):
    return False

# Function- uvm_get_array_index_string
#
#
def uvm_get_array_index_string(arg: str, is_wildcard: int) -> str:
    i = 0
    res = ""
    is_wildcard = 1
    i = len(arg) - 1
    if(arg[i] == "]"):
        while (i > 0 and (arg[i] != "[")):
            if ((arg[i] == "*") or (arg[i] == "?")):
                i = 0
            i -= 1

    if i > 0:
        res = arg[i+1: len(arg)-1]
        is_wildcard = 0
    return res

# Function- uvm_bitstream_to_string
#
#
def uvm_bitstream_to_string(value, size, radix=UVM_NORADIX, radix_str=""):
    # sign extend & don't show radix for negative values
    if radix == UVM_DEC: # and value[size-1] == 1: TODO
        return "{}".format(value)

    # TODO $countbits(value,'z) would be even better
    if isunknown(value):
        _t=0;
        for idx in range(0, size):
            _t[idx] = value[idx]
            value=_t
    else:
        value &= (1 << size) - 1
    return num_with_radix(radix, radix_str, value)

# Function- uvm_integral_to_string
#
#
def uvm_integral_to_string(value, size, radix=UVM_NORADIX, radix_str=""):
    # sign extend & don't show radix for negative values
    if radix == UVM_DEC and value[size-1] == 1:
        return "{}".format(value)

    # TODO $countbits(value,'z) would be even better
    if isunknown(value) is True:
        _t = 0
        for idx in range(0, size):
            _t[idx] = value[idx]
            value=_t;
    else:
        value &= (1 << size) - 1
    return num_with_radix(radix, radix_str, value)


# Function- uvm_object_value_str
#
def uvm_object_value_str(v):
    if v is None:
        return "<null>"
    res = "{}".format(v.get_inst_id())
    res = "@" + res
    return res

# Function- uvm_leaf_scope
#
#
def uvm_leaf_scope(full_name, scope_separator="."):
    bmatches = 0

    bracket_match = ""
    if scope_separator == "[":
        bracket_match = "]"
    if scope_separator == "(":
        bracket_match = ")"
    if scope_separator == "<":
        bracket_match = ">"
    if scope_separator == "{":
        bracket_match = "}"

    # Only use bracket matching if the input string has the end match
    if bracket_match != "" and bracket_match != full_name[-1]:
        bracket_match = ""

    if bracket_match == "":
        regex = re.compile(scope_separator)
        if scope_separator == ".":
            regex = re.compile("\.")
        if not regex.search(full_name):
            return full_name

    pos = 0
    for pos in range(len(full_name) - 1, 0, -1):
        if full_name[pos] == bracket_match:
            bmatches += 1
        elif full_name[pos] == scope_separator:
            bmatches -= 1
            if bmatches == 0 or bracket_match == "":
                break

    res = ""
    if pos > 0:
        max_pos = len(full_name)
        if scope_separator != ".":
            pos -= 1
            max_pos -= 1
            if full_name[pos+1] == scope_separator:
                pos += 1
        res = full_name[pos+1:max_pos]
    else:
        res = full_name
    return res


def num_with_radix(radix, radix_str, value):
    if radix == UVM_BIN:
        return "{}{}".format(radix_str, value)
    if radix == UVM_OCT:
        return "{}{}".format(radix_str, value)
    if radix == UVM_UNSIGNED:
        return "{}{}".format(radix_str, value)
    if radix == UVM_STRING:
        return "{}{}".format(radix_str, value)
    if radix == UVM_TIME:
        return "{}{}".format(radix_str, value)
    if radix == UVM_DEC:
        return "{}{}".format(radix_str, value)
    return "{}{}".format(radix_str, value)

class ProcessContainerC:
    def __init__(self, p_):
        self.p = p_

#//------------------------------------------------------------------------------
#//
#// CLASS- uvm_status_container
#//
#// Internal class to contain status information for automation methods.
#//
#//------------------------------------------------------------------------------
#
class UVMStatusContainer:

    #  static bit field_array[string];
    field_array = {}
    #  static bit print_matches;
    print_matches = False

    #  //The clone setting is used by the set/get config to know if cloning is on.
    def __init__(self):
        self.clone = True
        # Information variables used by the macro functions for storage.
        self.warning = False
        self.status = False
        self.bitstream = 0
        self.intv = 0
        self.element = 0
        self.stringv = ""
        self.scratch1 = ""
        self.scratch2 = ""
        self.key = ""
        self.object = None
        self.array_warning_done = False
        # The scope stack is used for messages that are emitted by policy classes.
        self.scope = UVMScopeStack()

        self.m_uvm_cycle_scopes = []  # uvm_object [$];

        #  //Used for checking cycles. When a data function is entered, if the depth is
        #  //non-zero, then then the existeance of the object in the map means that a
        #  //cycle has occured and the function should immediately exit. When the
        #  //function exits, it should reset the cycle map so that there is no memory
        #  //leak.
        self.cycle_check = {}  # bit cycle_check[uvm_object];

    def do_field_check(self, field, obj):
        if UVM_ENABLE_FIELD_CHECKS:
            if field in self.field_array:
                uvm_report_error("MLTFLD", "Field {} is defined multiple times in type '{}'".
                format(field, obj.get_type_name()), UVM_NONE)
        UVMStatusContainer.field_array[field] = 1

    def get_function_type(self, what):
        if what == UVM_COPY:
            return "copy"
        elif what == UVM_COMPARE:
            return "compare"
        elif what == UVM_PRINT:
            return "print"
        elif what == UVM_RECORD:
            return "record"
        elif what == UVM_PACK:
            return "pack"
        elif what == UVM_UNPACK:
            return "unpack"
        elif what == UVM_FLAGS:
            return "get_flags"
        elif what == UVM_SETINT:
            return "set"
        elif what == UVM_SETOBJ:
            return "set_object"
        elif what == UVM_SETSTR:
            return "set_string"
        else:
            return "unknown"
    #  endfunction

    #
    def get_full_scope_arg(self):
        return self.scope.get();


    #  //These are the policy objects currently in use. The policy object gets set
    #  //when a function starts up. The macros use this.
    #  uvm_comparer    comparer;
    #  uvm_packer      packer;
    #  uvm_recorder    recorder;
    #  uvm_printer     printer;

    #  // utility function used to perform a cycle check when config setting are pushed
    #  // to uvm_objects. the function has to look at the current object stack representing
    #  // the call stack of all __m_uvm_field_automation() invocations.
    #  // it is a only a cycle if the previous __m_uvm_field_automation call scope
    #  // is not identical with the current scope AND the scope is already present in the
    #  // object stack
    #  uvm_object m_uvm_cycle_scopes[$];

    def m_do_cycle_check(self, scope):
        ll = None
        #if m_uvm_cycle_scopes.size() == 0 ? null : m_uvm_cycle_scopes[$];
        if len(self.m_uvm_cycle_scopes) > 0:
            ll = self.m_uvm_cycle_scopes

        # we have been in this scope before (but actually right before so assuming a super/derived
        # context of the same object)
        if ll == scope:
            self.m_uvm_cycle_scopes.append(scope)
            return 0
        else:
            # now check if we have already been in this scope before
            idx = -1
            #uvm_object m[$] = m_uvm_cycle_scopes.find_first(item) with (item == scope);
            for i in range(len(self.m_uvm_cycle_scopes)):
                if self.m_uvm_cycle_scopes[i] == scope:
                    idx = i
                    break
            if idx != -1:
                return 1  # detected a cycle
            else:
                self.m_uvm_cycle_scopes.append(scope)
                return 0

        #  endfunction
    #endclass


def m_uvm_string_queue_join(i):
    res = ""
    for idx in range(len(i)):
        res = res + i[idx]
    return res


