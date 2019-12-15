#
#------------------------------------------------------------------------------
#   Copyright 2007-2010 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http:#www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Title: Factory Component and Object Wrappers
#
# Topic: Intro
#
# This section defines the proxy component and object classes used by the
# factory. To avoid the overhead of creating an instance of every component
# and object that get registered, the factory holds lightweight wrappers,
# or proxies. When a request for a new object is made, the factory calls upon
# the proxy to create the object it represents.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#
# CLASS: uvm_component_registry #(T,Tname)
#
# The uvm_component_registry serves as a lightweight proxy for a component of
# type ~T~ and type name ~Tname~, a string. The proxy enables efficient
# registration with the <uvm_factory>. Without it, registration would
# require an instance of the component itself.
#
# See <Usage> section below for information on using uvm_component_registry.
#
#------------------------------------------------------------------------------

from .uvm_factory import UVMObjectWrapper
from .uvm_globals import uvm_report_warning, uvm_report_fatal
from .uvm_object_globals import UVM_NONE

class UVMComponentRegistry(UVMObjectWrapper):

    # dict of UVMComponentRegistry
    registry_db = {} #tname -> UVMComponentRegistry
    registered = {} #tname -> bool
    # Stores the actual constructors
    comps = {}

    def __init__(self, Constr, tname):
        self.Constr = Constr
        self.tname = tname
        self.type_name = tname
        if tname in UVMComponentRegistry.registry_db:
            uvm_report_warning("COMP_REGD", (tname + 'has already been'
                + 'added into the UVMComponentRegistry'))
        UVMComponentRegistry.comps[tname] = Constr
        UVMComponentRegistry.registered[tname] = False
        UVMComponentRegistry.registry_db[tname] = self.get()

    # Function: create_component
    #
    # Creates a component of type T having the provided ~name~ and ~parent~.
    # This is an override of the method in <uvm_object_wrapper>. It is
    # called by the factory after determining the type of object to create.
    # You should not call this method directly. Call <create> instead.
    def create_component(self, name, parent):
         return UVMComponentRegistry.comps[self.tname](name, parent)

    # Function: get_type_name
    #
    # Returns the value given by the string parameter, ~Tname~. This method
    # overrides the method in <uvm_object_wrapper>.
    def get_type_name(self):
        return self.tname

    # Function: get
    #
    # Returns the singleton instance of this type. Type-based factory operation
    # depends on there being a single proxy instance for each registered type.
    def get(self):
        if UVMComponentRegistry.registered[self.tname] is False:
            factory = get_factory()
            factory.register(self)
            UVMComponentRegistry.registered[self.tname] = True
        return self

    # Function: create
    #
    # Returns an instance of the component type, ~T~, represented by this proxy,
    # subject to any factory overrides based on the context provided by the
    # ~parent~'s full name. The ~contxt~ argument, if supplied, supersedes the
    # ~parent~'s context. The new instance will have the given leaf ~name~
    # and ~parent~.
    def create(self, name, parent, contxt=""):
        factory= get_factory()

        if contxt == "" and parent is not None:
            contxt = parent.get_full_name()
        obj = factory.create_component_by_type(self.get(),contxt,name,parent)
        if obj is not None:
            return obj

        # cast check removed, TSP
        msg = ("Factory did not return a component of type '" + self.type_name
          + "'. A component of type '")
        if obj is None:
            msg += "null"
        else:
            get_type_name_func = getattr(obj, "get_type_name", None)
            if callable(get_type_name_func):
                msg += obj.get_type_name()
            else:
                klass_name = obj.__class__
                raise Exception('No get_type_name in {}. Did you use uvm_componen_utils({})'.format(
                    klass_name, klass_name))

        msg += "' was returned instead. Name=" + name + " Parent="
        if parent is None:
            msg += 'null'
        else:
            msg += parent.get_type_name()
        msg +=  " contxt=" + contxt
        uvm_report_fatal("FCTTYP", msg, UVM_NONE);

    # Function: set_type_override
    #
    # Configures the factory to create an object of the type represented by
    # ~override_type~ whenever a request is made to create an object of the type,
    # ~T~, represented by this proxy, provided no instance override applies. The
    # original type, ~T~, is typically a super class of the override type.
    def set_type_override(self, override_type, replace=True):
        factory = get_factory()
        factory.set_type_override_by_type(self.get(),override_type,replace);

    # Function: set_inst_override
    #
    # Configures the factory to create a component of the type represented by
    # ~override_type~ whenever a request is made to create an object of the type,
    # ~T~, represented by this proxy,  with matching instance paths. The original
    # type, ~T~, is typically a super class of the override type.
    #
    # If ~parent~ is not specified, ~inst_path~ is interpreted as an absolute
    # instance path, which enables instance overrides to be set from outside
    # component classes. If ~parent~ is specified, ~inst_path~ is interpreted
    # as being relative to the ~parent~'s hierarchical instance path, i.e.
    # ~{parent.get_full_name(),".",inst_path}~ is the instance path that is
    # registered with the override. The ~inst_path~ may contain wildcards for
    # matching against multiple contexts.
    def set_inst_override(self, override_type, inst_path, parent=None):
        # full_inst_path = ""

        if parent is not None:
            if inst_path == "":
                inst_path = parent.get_full_name()
            else:
                inst_path = parent.get_full_name() + "." + inst_path

        factory = get_factory()
        factory.set_inst_override_by_type(self.get(),override_type,inst_path)


class UVMObjectRegistry(UVMObjectWrapper):

    # dict of UVMObjectRegistry
    registry_db = {}  # tname -> UVMObjectRegistry
    registered = {}  # tname -> bool
    # Stores the actual constructors
    objs = {}

    def __init__(self, Constr, tname):
        self.Constr = Constr
        self.tname = tname
        self.type_name = tname
        if tname in UVMObjectRegistry.registry_db:
            uvm_report_warning("COMP_REGD", (tname + 'has already been'
                + 'added into the UVMComponentRegistry'))
        UVMObjectRegistry.objs[tname] = Constr
        UVMObjectRegistry.registered[tname] = False
        UVMObjectRegistry.registry_db[tname] = self.get()

    # Function: create_object
    #
    # Creates an object of type ~T~ and returns it as a handle to a
    # <uvm_object>. This is an override of the method in <uvm_object_wrapper>.
    # It is called by the factory after determining the type of object to create.
    # You should not call this method directly. Call <create> instead.

    def create_object(self, name=""):
        return UVMObjectRegistry.objs[self.tname](name)

    # Function: get_type_name
    #
    # Returns the value given by the string parameter, ~Tname~. This method
    # overrides the method in <uvm_object_wrapper>.
    def get_type_name(self):
        return self.type_name

    # Function: get
    #
    # Returns the singleton instance of this type. Type-based factory operation
    # depends on there being a single proxy instance for each registered type.
    def get(self):
        if UVMObjectRegistry.registered[self.tname] is False:
            factory = get_factory()
            factory.register(self)
            UVMObjectRegistry.registered[self.tname] = True
        return self

    # Function: create
    #
    # Returns an instance of the object type, ~T~, represented by this proxy,
    # subject to any factory overrides based on the context provided by the
    # ~parent~'s full name. The ~contxt~ argument, if supplied, supersedes the
    # ~parent~'s context. The new instance will have the given leaf ~name~,
    # if provided.
    def create(self, name, parent = None, contxt=""):
        factory = get_factory()

        if contxt == "" and parent is not None:
            contxt = parent.get_full_name()
        obj = factory.create_object_by_type(self.get(),contxt,name)
        if obj is not None:
            return obj
        create = obj
        return create
        #if (!$cast(create, obj)) begin
        #    string msg;
        #    msg = {"Factory did not return an object of type '",type_name,
        #      "'. A component of type '",obj == null ? "null" : obj.get_type_name(),
        #      "' was returned instead. Name=",name," Parent=",
        #      parent==null?"null":parent.get_type_name()," contxt=",contxt};
        #    uvm_report_fatal("FCTTYP", msg, UVM_NONE);

    # Function: set_type_override
    #
    # Configures the factory to create an object of the type represented by
    # ~override_type~ whenever a request is made to create an object of the type
    # represented by this proxy, provided no instance override applies. The
    # original type, ~T~, is typically a super class of the override type.
    def set_type_override(self, override_type, replace=True):
        factory = get_factory()
        factory.set_type_override_by_type(get(),override_type,replace);

    # Function: set_inst_override
    #
    # Configures the factory to create an object of the type represented by
    # ~override_type~ whenever a request is made to create an object of the type
    # represented by this proxy, with matching instance paths. The original
    # type, ~T~, is typically a super class of the override type.
    #
    # If ~parent~ is not specified, ~inst_path~ is interpreted as an absolute
    # instance path, which enables instance overrides to be set from outside
    # component classes. If ~parent~ is specified, ~inst_path~ is interpreted
    # as being relative to the ~parent~'s hierarchical instance path, i.e.
    # ~{parent.get_full_name(),".",inst_path}~ is the instance path that is
    # registered with the override. The ~inst_path~ may contain wildcards for
    # matching against multiple contexts.
    def set_inst_override(self, override_type, inst_path, parent=None):
        full_inst_path = ""
        factory = get_factory()

        if parent is not None:
            if inst_path == "":
                inst_path = parent.get_full_name()
            else:
                inst_path = parent.get_full_name() + "." + inst_path
        factory.set_inst_override_by_type(get(),override_type,inst_path);
    #endclass

def get_factory():
    from .uvm_coreservice import UVMCoreService
    cs = UVMCoreService.get()
    return cs.get_factory()

import unittest
import sys
#sys.path.insert(0, './macros')

class TestUVMRegistry(unittest.TestCase):

    def test_registry(self):
        class ABC:
            def __init__(self, name, parent):
                self.name = name
                self.parent = parent
        from ..macros.uvm_object_defines import uvm_component_utils
        uvm_component_utils(ABC)
        reg = UVMComponentRegistry(ABC, 'ABC')
        abc_comp = reg.create('inst_name', None)
        self.assertEqual(abc_comp.name, 'inst_name')
        self.assertEqual(abc_comp.parent, None)

if __name__ == '__main__':
    unittest.main()
