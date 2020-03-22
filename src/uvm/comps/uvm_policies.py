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
"""
Title: Policy Classes

Policy classes are used to implement polymorphic operations that
differ between built-in types and class-based types. Generic
components can then be built that work with either classes or 
built-in types, depending on what policy class is used.
"""

from ..base.sv import sv


#//----------------------------------------------------------------------
#// CLASS: UVMBuiltInComp #(T)
#// 
#// This policy class is used to compare built-in types.
#//
#// Provides a comp method that compares the built-in type,
#// T, for which the == operator is defined.
#//----------------------------------------------------------------------

class UVMBuiltInComp:  # (type T=int)

    @classmethod
    def comp(self, a, b):
        return a == b



#//----------------------------------------------------------------------
#// CLASS: UVMBuiltInConverter #(T)
#//
#// This policy class is used to convert built-in types to strings.
#//
#// Provides a convert2string method that converts the built-in type, T,
#// to a string using the %p format specifier.
#//----------------------------------------------------------------------


class UVMBuiltInConverter:  # (type T=int)
    @classmethod
    def convert2string(self, t):
        return sv.sformatf("%p", t)




#//----------------------------------------------------------------------
#// CLASS: UVMBuiltInClone #(T)
#//
#// This policy class is used to clone built-in types via the = operator.
#//
#// Provides a clone method that returns a copy of the built-in type, T.
#//----------------------------------------------------------------------


class UVMBuiltInClone:  # (type T=int)
    @classmethod
    def clone(self, from_):
        return from_


#//----------------------------------------------------------------------
#// CLASS: UVMClassComp #(T)
#//
#// This policy class is used to compare two objects of the same type.
#//
#// Provides a comp method that compares two objects of type T. The
#// class T must provide the method "function bit compare(T rhs)",
#// similar to the <uvm_object::compare> method.
#//----------------------------------------------------------------------

class UVMClassComp:  # (type T=int)
    @classmethod
    def comp(self, a, b):
        print("ASDA")
        return a.compare(b)


#//----------------------------------------------------------------------
#// CLASS: UVMClassConverter #(T)
#//
#// This policy class is used to convert a class object to a string.
#//
#// Provides a convert2string method that converts an instance of type T
#// to a string. The class T must provide the method
#// "function string convert2string()",
#// similar to the <uvm_object::convert2string> method.
#//----------------------------------------------------------------------

class UVMClassConverter:  # (type T=int)

    @classmethod
    def convert2string(self, t):
        return t.convert2string()


#//----------------------------------------------------------------------
#// CLASS: UVMClassClone #(T)
#//
#// This policy class is used to clone class objects.
#//
#// Provides a clone method that returns a copy of the built-in type, T.
#// The class T must implement the clone method, to which this class
#// delegates the operation. If T is derived from <uvm_object>, then
#// T must instead implement <uvm_object::do_copy>, either directly or
#// indirectly through use of the `uvm_field macros.
#//----------------------------------------------------------------------

class UVMClassClone:  # (type T=int)
    @classmethod
    def clone(self, from_):
        return from_.clone()
