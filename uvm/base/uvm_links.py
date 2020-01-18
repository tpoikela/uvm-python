#//
#//-----------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2013 NVIDIA Corporation
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

from .uvm_object import UVMObject
from uvm.macros import *

#// File: UVM Links
#//
#// The <UVMLinkBase> class, and its extensions, are provided as a mechanism
#// to allow for compile-time safety when trying to establish links between
#// records within a <uvm_tr_database>.
#//
#//

#//------------------------------------------------------------------------------
#//
#// CLASS: UVMLinkBase
#//
#// The ~UVMLinkBase~ class presents a simple API for defining a link between
#// any two objects.
#//
#// Using extensions of self class, a <uvm_tr_database> can determine the
#// type of links being passed, without relying on "magic" string names.
#//
#// For example:
#// |
#// | virtual def void do_establish_link(self,UVMLinkBase link):
#// |   UVMParentChildLink pc_link
#// |   UVMCauseEffectLink ce_link
#// |
#// |   if (sv.cast(pc_link, link)):
#// |      // Record the parent-child relationship
#// |   end
#// |   elif (sv.cast(ce_link, link)):
#// |      // Record the cause-effect relationship
#// |   end
#// |   else begin
#// |      // Unsupported relationship!
#// |   end
#// | endfunction : do_establish_link
#//

class UVMLinkBase(UVMObject):


    #   // Function: new
    #   // Constructor
    #   //
    #   // Parameters:
    #   // name - Instance name
    def __init__(self, name="unnamed-UVMLinkBase"):
        super().__init__(name)

    #   // Group:  Accessors
    #
    #   // Function: set_lhs
    #   // Sets the left-hand-side of the link
    #   //
    #   // Triggers the <do_set_lhs> callback.
    def set_lhs(self, lhs):
        self.do_set_lhs(lhs)

    #   // Function: get_lhs
    #   // Gets the left-hand-side of the link
    #   //
    #   // Triggers the <do_get_lhs> callback
    def get_lhs(self):
        return self.do_get_lhs()

    #   // Function: set_rhs
    #   // Sets the right-hand-side of the link
    #   //
    #   // Triggers the <do_set_rhs> callback.
    def set_rhs(self, rhs):
        self.do_set_rhs(rhs)


    #   // Function: get_rhs
    #   // Gets the right-hand-side of the link
    #   //
    #   // Triggers the <do_get_rhs> callback
    def get_rhs(self):
        return self.do_get_rhs()


    #   // Function: set
    #   // Convenience method for setting both sides in one call.
    #   //
    #   // Triggers both the <do_set_rhs> and <do_set_lhs> callbacks.
    def set(self, lhs, rhs):
        self.do_set_lhs(lhs)
        self.do_set_rhs(rhs)


    #   // Group: Implementation Callbacks
    #
    #   // Function: do_set_lhs
    #   // Callback for setting the left-hand-side
    #   pure virtual def void do_set_lhs(self,UVMObject lhs):
    #
    #   // Function: do_get_lhs
    #   // Callback for retrieving the left-hand-side
    #   pure virtual def UVMObject do_get_lhs(self):
    #
    #   // Function: do_set_rhs
    #   // Callback for setting the right-hand-side
    #   pure virtual def void do_set_rhs(self,UVMObject rhs):
    #
    #   // Function: do_get_rhs
    #   // Callback for retrieving the right-hand-side
    #   pure virtual def UVMObject do_get_rhs(self):
    #
    #endclass : UVMLinkBase

#//------------------------------------------------------------------------------
#//
#// CLASS: UVMParentChildLink
#//
#// The ~UVMParentChildLink~ is used to represent a Parent/Child relationship
#// between two objects.
#//


class UVMParentChildLink(UVMLinkBase):

    #   // Function: new
    #   // Constructor
    #   //
    #   // Parameters:
    #   // name - Instance name
    def __init__(self, name="unnamed-UVMParentChildLink"):
        super().__init__(name)
        self.m_lhs = None
        self.m_rhs = None


    #   // Function: get_link
    #   // Constructs a pre-filled link
    #   //
    #   // This allows for simple one-line link creations.
    #   // | my_db.establish_link(UVMParentChildLink::get_link(record1, record2))
    #   //
    #   // Parameters:
    #   // lhs - Left hand side reference
    #   // rhs - Right hand side reference
    #   // name - Optional name for the link object
    #   //
    @classmethod
    def get_link(cls, lhs, rhs, name="pc_link"):
        pc_link = UVMParentChildLink(name)
        pc_link.set(lhs, rhs)
        return pc_link


    #   // Group: Implementation Callbacks
    #
    #   // Function: do_set_lhs
    #   // Sets the left-hand-side (Parent)
    #   //
    def do_set_lhs(self, lhs):
        self.m_lhs = lhs

    #   // Function: do_get_lhs
    #   // Retrieves the left-hand-side (Parent)
    #   //
    def do_get_lhs(self):
        return self.m_lhs

    #   // Function: do_set_rhs
    #   // Sets the right-hand-side (Child)
    #   //
    def do_set_rhs(self, rhs):
        self.m_rhs = rhs


    #   // Function: do_get_rhs
    #   // Retrieves the right-hand-side (Child)
    #   //
    def do_get_rhs(self):
        return self.m_rhs

    #
    #endclass : UVMParentChildLink



#//------------------------------------------------------------------------------
#//
#// CLASS: UVMCauseEffectLink
#//
#// The ~UVMCauseEffectLink~ is used to represent a Cause/Effect relationship
#// between two objects.
#//


class UVMCauseEffectLink(UVMLinkBase):
    #
    #   // Variable- m_lhs,m_rhs
    #   // Implementation details
    #   local UVMObject m_lhs
    #   local UVMObject m_rhs
    #
    #   // Object utils
    #   `uvm_object_utils_begin(UVMCauseEffectLink)
    #   `uvm_object_utils_end
    #
    #   // Function: new
    #   // Constructor
    #   //
    #   // Parameters:
    #   // name - Instance name
    def __init__(self, name="unnamed-UVMCauseEffectLink"):
        super().__init__(name)


    #   // Function: get_link
    #   // Constructs a pre-filled link
    #   //
    #   // This allows for simple one-line link creations.
    #   // | my_db.establish_link(UVMCauseEffectLink::get_link(record1, record2))
    #   //
    #   // Parameters:
    #   // lhs - Left hand side reference
    #   // rhs - Right hand side reference
    #   // name - Optional name for the link object
    #   //
    @classmethod
    def get_link(cls, lhs, rhs, name="ce_link"):
        ce_link = UVMCauseEffectLink(name)
        ce_link.set(lhs, rhs)
        return ce_link


    #   // Group: Implementation Callbacks
    #
    #   // Function: do_set_lhs
    #   // Sets the left-hand-side (Cause)
    #   //
    def do_set_lhs(self, lhs):
        self.m_lhs = lhs

    #
    #   // Function: do_get_lhs
    #   // Retrieves the left-hand-side (Cause)
    #   //
    def do_get_lhs(self):
        return self.m_lhs

    #
    #   // Function: do_set_rhs
    #   // Sets the right-hand-side (Effect)
    #   //
    def do_set_rhs(self, rhs):
        self.m_rhs = rhs

    #
    #   // Function: do_get_rhs
    #   // Retrieves the right-hand-side (Effect)
    #   //
    def do_get_rhs(self):
        return self.m_rhs

    #
    #endclass : UVMCauseEffectLink
uvm_object_utils(UVMParentChildLink)

#//------------------------------------------------------------------------------
#//
#// CLASS: UVMRelatedLink
#//
#// The ~UVMRelatedLink~ is used to represent a generic "is related" link
#// between two objects.
#//


class UVMRelatedLink(UVMLinkBase):


    #   // Function: new
    #   // Constructor
    #   //
    #   // Parameters:
    #   // name - Instance name
    def __init__(self, name="unnamed-UVMRelatedLink"):
        super().__init__(name)
        self.m_lhs = None  # type: UVMObject
        self.m_rhs = None  # type: UVMObject


    #   // Function: get_link
    #   // Constructs a pre-filled link
    #   //
    #   // This allows for simple one-line link creations.
    #   // | my_db.establish_link(UVMRelatedLink::get_link(record1, record2))
    #   //
    #   // Parameters:
    #   // lhs - Left hand side reference
    #   // rhs - Right hand side reference
    #   // name - Optional name for the link object
    #   //
    @classmethod
    def get_link(cls, lhs, rhs, name="ce_link"):
        ce_link = UVMRelatedLink(name)
        ce_link.set(lhs, rhs)
        return ce_link


    #   // Group: Implementation Callbacks
    #
    #   // Function: do_set_lhs
    #   // Sets the left-hand-side
    #   //
    #   virtual def void do_set_lhs(self,UVMObject lhs):
    #      m_lhs = lhs
    #   endfunction : do_set_lhs

    #
    #   // Function: do_get_lhs
    #   // Retrieves the left-hand-side
    #   //
    #   virtual def UVMObject do_get_lhs(self):
    #      return m_lhs
    #   endfunction : do_get_lhs

    #
    #   // Function: do_set_rhs
    #   // Sets the right-hand-side
    #   //
    #   virtual def void do_set_rhs(self,UVMObject rhs):
    #      m_rhs = rhs
    #   endfunction : do_set_rhs

    #
    #   // Function: do_get_rhs
    #   // Retrieves the right-hand-side
    #   //
    #   virtual def UVMObject do_get_rhs(self):
    #      return m_rhs
    #   endfunction : do_get_rhs

    #
    #endclass : UVMRelatedLink
uvm_object_utils(UVMRelatedLink)
