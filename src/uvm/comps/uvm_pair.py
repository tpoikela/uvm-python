#//
#//-----------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
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
#//-----------------------------------------------------------------------------
"""
Title: uvm_pair classes

This section defines container classes for handling value pairs.

"""

from uvm.base.sv import sv
from uvm.base.uvm_object import UVMObject
from uvm.macros import uvm_object_utils, uvm_error



class UVMClassPair(UVMObject):  # (type T1=int, T2=T1) extends uvm_object
    """
    Class: UVMClassPair #(T1,T2)

    Container holding handles to two objects whose types are specified by the
    type parameters, T1 and T2.
    """


    type_name = "UVMClassPair"

    #// Variable: T1 first
    #//
    #// The handle to the first object in the pair
    #
    #  T1 first
    #
    #// Variable: T2 second
    #//
    #// The handle to the second object in the pair
    #
    #  T2 second
    #

    #  // Function: new
    #  //
    #  // Creates an instance that holds a handle to two objects.
    #  // The optional name argument gives a name to the new pair object.
    def __init__(self, name="", f=None, s=None):
        super().__init__(name)
        self.first = f
        self.second = s

        #if f is None:
        #    self.first = new
        #else
        #  first = f
        #if (s is None)
        #    second = new
        #else
        #    second = s


    #  def get_type_name(self):
    #    return type_name
    #  endfunction

    def convert2string(self):
        s = sv.sformatf("pair : %s, %s",
             self.first.convert2string(), self.second.convert2string())
        return s


    #  def do_compare(self,uvm_object rhs, uvm_comparer comparer):
    #    this_type rhs_
    #    if(!sv.cast(rhs_,rhs)):
    #      uvm_error("WRONG_TYPE", {"do_compare: rhs argument is not of type '",get_type_name(),"'"})
    #      return 0
    #    end
    #    return first.compare(rhs_.first)  and  second.compare(rhs_.second)
    #  endfunction

    #  def do_copy(self,uvm_object rhs):
    #    this_type rhs_
    #    if(!sv.cast(rhs_,rhs))
    #      uvm_fatal("WRONG_TYPE", {"do_copy: rhs argument is not of type '",get_type_name(),"'"})
    #    first.copy(rhs_.first)
    #    second.copy(rhs_.second)
    #  endfunction


uvm_object_utils(UVMClassPair)


#//-----------------------------------------------------------------------------
#// CLASS: UVMBuiltInPair #(T1,T2)
#//
#// Container holding two variables of built-in types (int, string, etc.). The
#// types are specified by the type parameters, T1 and T2.
#//-----------------------------------------------------------------------------

class UVMBuiltInPair(UVMObject):


    type_name = "UVMBuiltInPair"

    #// Variable: T1 first
    #//
    #// The first value in the pair
    #
    #  T1 first

    #// Variable: T2 second
    #//
    #// The second value in the pair
    #  T2 second


    #  // Function: new
    #  //
    #  // Creates an instance that holds two built-in type values.
    #  // The optional name argument gives a name to the new pair object.
    #
    def __init__(self, name=""):
        super().__init__(name)
        self.first = 0
        self.seconds = 0


    def get_type_name(self):
        return UVMBuiltInPair.type_name


    def convert2string(self):
        return "built-in pair : {}, {}".format(self.first, self.second)


    def do_compare(self, rhs, comparer):
        rhs_ = []
        if not sv.cast(rhs_,rhs, UVMBuiltInPair):
            uvm_error("WRONG_TYPE", {"do_compare: rhs argument is not of type '",
                self.get_type_name(),"'"})
            return 0
        rhs_ = rhs[0]
        return self.first == rhs_.first and self.second == rhs_.second


    #  def do_copy(self,uvm_object rhs):
    #    this_type rhs_
    #    if(!sv.cast(rhs_,rhs))
    #      uvm_fatal("WRONG_TYPE", {"do_copy: rhs argument is not of type '",get_type_name(),"'"})
    #    first = rhs_.first
    #    second = rhs_.second

uvm_object_utils(UVMBuiltInPair)
