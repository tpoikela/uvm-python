#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2013      NVIDIA Corporation
#//   Copyright 2013      Verilab, Inc.
#//   Copyright 2019 Tuomas Poikela (tpoikela)
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
#//------------------------------------------------------------------------------

from .sv import sv
from .uvm_queue import UVMQueue
from .uvm_pool import UVMPool
from .uvm_globals import (uvm_report_error, uvm_report_fatal, uvm_report_warning,
    uvm_is_match, uvm_report_info)
from .uvm_object_globals import UVM_NONE, UVM_MEDIUM
from ..macros import uvm_info
from ..uvm_macros import UVM_STRING_QUEUE_STREAMING_PACK



def m_has_wildcard(nm):
    """ Returns True if given string has wildcard * or ? """
    for char in nm:
        if char == "*" or char == "?":
            return True
    return False


class uvm_factory_queue_class:
    def __init__(self):
        self.queue = UVMQueue()

#------------------------------------------------------------------------------
#
# CLASS: uvm_factory
#
#------------------------------------------------------------------------------
#
# As the name implies, uvm_factory is used to manufacture (create) UVM objects
# and components. Object and component types are registered
# with the factory using lightweight proxies to the actual objects and
# components being created. The <uvm_object_registry #(T,Tname)> and
# <uvm_component_registry #(T,Tname)> class are used to proxy <uvm_objects>
# and <uvm_components>.
#
# The factory provides both name-based and type-based interfaces.
#
# type-based - The type-based interface is far less prone to errors in usage.
#   When errors do occur, they are caught at compile-time.
#
# name-based - The name-based interface is dominated
#   by string arguments that can be misspelled and provided in the wrong order.
#   Errors in name-based requests might only be caught at the time of the call,
#   if at all. Further, the name-based interface is not portable across
#   simulators when used with parameterized classes.
#
#
# The ~uvm_factory~ is an abstract class which declares many of its methods
# as ~pure virtual~.  The UVM uses the <uvm_default_factory> class
# as its default factory implementation.
#
# See <uvm_default_factory::Usage> section for details on configuring and using the factory.


class UVMFactory:

    #// Group: Retrieving the factory

    #// Function: get
    #// Static accessor for <uvm_factory>
    #//
    #// The static accessor is provided as a convenience wrapper
    #// around retrieving the factory via the <uvm_coreservice_t::get_factory>
    #// method.
    #//
    #// | // Using the uvm_coreservice_t:
    #// | uvm_coreservice_t cs;
    #// | uvm_factory f;
    #// | cs = uvm_coreservice_t::get();
    #// | f = cs.get_factory();
    #//
    #// | // Not using the uvm_coreservice_t:
    #// | uvm_factory f;
    #// | f = uvm_factory::get();
    #//
    @classmethod
    def get(cls):
        from uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        return cs.get_factory()

    # NOTE: SV virtual functions not added from original uvm_factory, not needed in python

#------------------------------------------------------------------------------
#
# CLASS: uvm_default_factory
#
#------------------------------------------------------------------------------
#
# Default implementation of the UVM factory.


class UVMDefaultFactory(UVMFactory):

    m_debug_pass = False

    def __init__(self):
        self.m_override_info = UVMQueue()
        self.m_types = UVMPool()  # [uvm_object_wrapper] -> bit
        self.m_lookup_strs = UVMPool()
        self.m_type_names = UVMPool()
        self.m_type_overrides = UVMQueue()  # uvm_factory_override
        self.m_inst_override_queues = {}  # [uvm_object_wrapper] -> queue
        self.m_inst_override_name_queues = {}  # [string] -> queue
        self.m_wildcard_inst_overrides = UVMQueue()


    # Group: Registering Types
    #
    # Function: register
    #
    # Registers the given proxy object, ~obj~, with the factory.
    def register(self, obj):
        if obj is None:
            uvm_report_fatal("NULLWR", "Attempting to register a null object with the factory", UVM_NONE)

        if obj.get_type_name() != "" and obj.get_type_name() != "<unknown>":
            if self.m_type_names.exists(obj.get_type_name()):
                uvm_report_warning("TPRGED", ("Type name '" + obj.get_type_name()
                    + "' already registered with factory. No string-based lookup "
                    + "support for multiple types with the same type name."), UVM_NONE)
            else:
                self.m_type_names.add(obj.get_type_name(), obj)

        if self.m_types.exists(obj):
            if obj.get_type_name() != "" and obj.get_type_name() != "<unknown>":
                uvm_report_warning("TPRGED", ("Object type '" + obj.get_type_name()
                                 + "' already registered with factory. "), UVM_NONE)
        else:
            self.m_types.add(obj, 1)
            # If a named override happens before the type is registered, need to copy
            # the override queue.
            # Note:Registration occurs via static initialization, which occurs ahead of
            # procedural (e.g. initial) blocks. There should not be any preexisting overrides.
            if obj.get_type_name() in self.m_inst_override_name_queues:
                self.m_inst_override_queues[obj] = UVMQueue()
                self.m_inst_override_queues[obj] = self.m_inst_override_name_queues[obj.get_type_name()]
                self.m_inst_override_name_queues.delete(obj.get_type_name())
            if self.m_wildcard_inst_overrides.size():
                if not self.m_inst_override_queues.exists(obj):
                    self.m_inst_override_queues[obj] = UVMQueue()
                for i in range(0, self.m_wildcard_inst_overrides.size()):
                    if uvm_is_match(self.m_wildcard_inst_overrides[i].orig_type_name, obj.get_type_name()):
                        self.m_inst_override_queues[obj].push_back(self.m_wildcard_inst_overrides[i])

    # set_type_override_by_type
    # -------------------------
    # TODO
    # def set_type_override_by_type (self, original_type, override_type, bit replace=1)
    #  bit replaced
    #
    #  // check that old and new are not the same
    #  if (original_type == override_type) begin
    #    if (original_type.get_type_name() == "" || original_type.get_type_name() == "<unknown>")
    #      uvm_report_warning("TYPDUP", {"Original and override type ",
    #                                    "arguments are identical"}, UVM_NONE)
    #    else
    #      uvm_report_warning("TYPDUP", {"Original and override type ",
    #                                    "arguments are identical: ",
    #                                    original_type.get_type_name()}, UVM_NONE)
    #  end
    #
    #  // register the types if not already done so, for the benefit of string-based lookup
    #  if (!self.m_types.exists(original_type))
    #    register(original_type)
    #
    #  if (!self.m_types.exists(override_type))
    #    register(override_type)
    #
    #
    #  // check for existing type override
    #  foreach (self.m_type_overrides[index]) begin
    #    if (self.m_type_overrides[index].orig_type == original_type ||
    #        (self.m_type_overrides[index].orig_type_name != "<unknown>" &&
    #         self.m_type_overrides[index].orig_type_name != "" &&
    #         self.m_type_overrides[index].orig_type_name == original_type.get_type_name())) begin
    #      string msg
    #      msg = {"Original object type '",original_type.get_type_name(),
    #             "' already registered to produce '",
    #             self.m_type_overrides[index].ovrd_type_name,"'"}
    #      if (!replace) begin
    #        msg = {msg, ".  Set 'replace' argument to replace the existing entry."}
    #        uvm_report_info("TPREGD", msg, UVM_MEDIUM)
    #        return
    #      end
    #      msg = {msg, ".  Replacing with override to produce type '",
    #                  override_type.get_type_name(),"'."}
    #      uvm_report_info("TPREGR", msg, UVM_MEDIUM)
    #      replaced = 1
    #      self.m_type_overrides[index].orig_type = original_type
    #      self.m_type_overrides[index].orig_type_name = original_type.get_type_name()
    #      self.m_type_overrides[index].ovrd_type = override_type
    #      self.m_type_overrides[index].ovrd_type_name = override_type.get_type_name()
    #    end
    #  end
    #
    #  // make a new entry
    #  if (!replaced) begin
    #    uvm_factory_override override
    #    override = new(.orig_type(original_type),
    #                   .orig_type_name(original_type.get_type_name()),
    #                   .full_inst_path("*"),
    #                   .ovrd_type(override_type))
    #
    #    self.m_type_overrides.push_back(override)
    #  end
    #
    #endfunction

    # set_type_override_by_name
    # -------------------------
    def set_type_override_by_name(self, original_type_name, override_type_name,
            replace=True):
        replaced = False
        original_type = None
        override_type = None

        if self.m_type_names.exists(original_type_name):
            original_type = self.m_type_names.get(original_type_name)

        if self.m_type_names.exists(override_type_name):
            override_type = self.m_type_names.get(override_type_name)

        # check that type is registered with the factory
        if override_type is None:
            uvm_report_error("TYPNTF", ("Cannot register override for original type '"
            + original_type_name + "' because the override type '"
            + override_type_name + "' is not registered with the factory."), UVM_NONE)
            return

        # check that old and new are not the same
        if original_type_name == override_type_name:
            uvm_report_warning("TYPDUP", ("Requested and actual type name "
                + " arguments are identical: " + original_type_name
                + ". Ignoring this override."), UVM_NONE)
            return

        for index in range(0, self.m_type_overrides.size()):
            if self.m_type_overrides[index].orig_type_name == original_type_name:
                if not replace:
                    uvm_report_info("TPREGD", ("Original type '" + original_type_name
                      + "' already registered to produce '" + self.m_type_overrides[index].ovrd_type_name
                      + "'.  Set 'replace' argument to replace the existing entry."), UVM_MEDIUM)
                    return

                uvm_report_info("TPREGR", ("Original object type '" + original_type_name
                  + "' already registered to produce '" + self.m_type_overrides[index].ovrd_type_name
                  + "'.  Replacing with override to produce type '"
                  + override_type_name + "'."), UVM_MEDIUM)
                replaced = True
                self.m_type_overrides[index].ovrd_type = override_type
                self.m_type_overrides[index].ovrd_type_name = override_type_name

        if original_type is None:
            self.m_lookup_strs[original_type_name] = 1

        if not replaced:
            # uvm_factory_override override
            override = UVMFactoryOverride(orig_type=original_type,
                           orig_type_name=original_type_name,
                           full_inst_path="*",
                           ovrd_type=override_type)

            self.m_type_overrides.push_back(override)
            self.m_type_names.add(original_type_name, override.ovrd_type)

    # check_inst_override_exists
    # --------------------------
    # TODO
    #function bit uvm_default_factory::check_inst_override_exists (
    #    uvm_object_wrapper original_type,
    #                                      uvm_object_wrapper override_type,
    #                                      string full_inst_path)
    #  uvm_factory_override override
    #  uvm_factory_queue_class qc
    #
    #  if (m_inst_override_queues.exists(original_type))
    #    qc = m_inst_override_queues[original_type]
    #  else
    #    return 0
    #
    #  for (int index=0; index<qc.queue.size(); ++index) begin
    #
    #    override = qc.queue[index]
    #    if (override.full_inst_path == full_inst_path &&
    #        override.orig_type == original_type &&
    #        override.ovrd_type == override_type &&
    #        override.orig_type_name == original_type.get_type_name()) begin
    #    uvm_report_info("DUPOVRD",{"Instance override for '",
    #       original_type.get_type_name(),"' already exists: override type '",
    #       override_type.get_type_name(),"' with full_inst_path '",
    #       full_inst_path,"'"},UVM_HIGH)
    #      return 1
    #    end
    #  end
    #  return 0
    #endfunction

    # set_inst_override_by_type
    # -------------------------
    # TODO
    #function void uvm_default_factory::set_inst_override_by_type (
    #   uvm_object_wrapper original_type,
    #                                                      uvm_object_wrapper override_type,
    #                                                      string full_inst_path)
    #
    #  uvm_factory_override override
    #
    #  // register the types if not already done so
    #  if (!self.m_types.exists(original_type))
    #    register(original_type)
    #
    #  if (!self.m_types.exists(override_type))
    #    register(override_type)
    #
    #  if (check_inst_override_exists(original_type,override_type,full_inst_path))
    #    return
    #
    #  if(!m_inst_override_queues.exists(original_type))
    #    m_inst_override_queues[original_type] = new
    #
    #  override = new(.full_inst_path(full_inst_path),
    #                 .orig_type(original_type),
    #                 .orig_type_name(original_type.get_type_name()),
    #                 .ovrd_type(override_type))
    #
    #
    #  m_inst_override_queues[original_type].queue.push_back(override)
    #
    #endfunction

    # set_inst_override_by_name
    # -------------------------
    # TODO
    #function void uvm_default_factory::set_inst_override_by_name (
    # string original_type_name,
    #                                                      string override_type_name,
    #                                                      string full_inst_path)
    #
    #  uvm_factory_override override
    #  uvm_object_wrapper original_type
    #  uvm_object_wrapper override_type
    #
    #  if(self.m_type_names.exists(original_type_name))
    #    original_type = self.m_type_names[original_type_name]
    #
    #  if(self.m_type_names.exists(override_type_name))
    #    override_type = self.m_type_names[override_type_name]
    #
    #  // check that type is registered with the factory
    #  if (override_type == null) begin
    #    uvm_report_error("TYPNTF", {"Cannot register instance override with type name '",
    #    original_type_name,"' and instance path '",full_inst_path,"' because the type it's supposed ",
    #    "to produce, '",override_type_name,"', is not registered with the factory."}, UVM_NONE)
    #    return
    #  end
    #
    #  if (original_type == null)
    #      m_lookup_strs[original_type_name] = 1
    #
    #  override = new(.full_inst_path(full_inst_path),
    #                 .orig_type(original_type),
    #                 .orig_type_name(original_type_name),
    #                 .ovrd_type(override_type))
    #
    #  if(original_type != null) begin
    #    if (check_inst_override_exists(original_type,override_type,full_inst_path))
    #      return
    #    if(!m_inst_override_queues.exists(original_type))
    #      m_inst_override_queues[original_type] = new
    #    m_inst_override_queues[original_type].queue.push_back(override)
    #  end
    #  else begin
    #    if(m_has_wildcard(original_type_name)) begin
    #       foreach(self.m_type_names[i]) begin
    #         if(uvm_is_match(original_type_name,i)) begin
    #           this.set_inst_override_by_name(i, override_type_name, full_inst_path)
    #         end
    #       end
    #       m_wildcard_inst_overrides.push_back(override)
    #    end
    #    else begin
    #      if(!self.m_inst_override_name_queues.exists(original_type_name))
    #        self.m_inst_override_name_queues[original_type_name] = new
    #      self.m_inst_override_name_queues[original_type_name].queue.push_back(override)
    #    end
    #  end
    #
    #endfunction

    # create_object_by_name
    # ---------------------
    def create_object_by_name (self, requested_type_name, parent_inst_path="",
              name=""):
        wrapper = None
        inst_path = ""

        if parent_inst_path == "":
            inst_path = name
        elif name != "":
            inst_path = parent_inst_path + "." + name
        else:
            inst_path = parent_inst_path

        self.m_override_info.delete()
        wrapper = self.find_override_by_name(requested_type_name, inst_path)

        # if no override exists, try to use requested_type_name directly
        if wrapper is None:
            if not self.m_type_names.exists(requested_type_name):
                uvm_report_warning("BDTYP", ("Cannot create an object of type '"
                    + requested_type_name + "' because it is not registered with the factory.")
                    , UVM_NONE)
                return None
            wrapper = self.m_type_names.get(requested_type_name)
        return wrapper.create_object(name)

    # create_object_by_type
    # ---------------------
    def create_object_by_type(self, requested_type, parent_inst_path="", name=""):
        if requested_type is None:
            uvm_report_fatal("REQ_TYPE_NONE", "Requested type object was None")
        full_inst_path = ""
        if parent_inst_path == "":
            full_inst_path = name
        elif name != "":
            full_inst_path = parent_inst_path + "." + name
        else:
            full_inst_path = parent_inst_path

        self.m_override_info.delete()
        requested_type = self.find_override_by_type(requested_type, full_inst_path)
        if requested_type is None:
            uvm_report_fatal("REQ_TYPE_NONE", "Requested type object was None after override")
        return requested_type.create_object(name)

    # create_component_by_name
    # ------------------------
    def create_component_by_name(self, requested_type_name,
            parent_inst_path, name, parent):
        wrapper = None
        inst_path = ""

        if parent_inst_path == "":
            inst_path = name
        elif name != "":
          inst_path = parent_inst_path + "." + name
        else:
            inst_path = parent_inst_path

        self.m_override_info.delete()
        wrapper = self.find_override_by_name(requested_type_name, inst_path)

        # if no override exists, try to use requested_type_name directly
        if wrapper is None:
            if not self.m_type_names.exists(requested_type_name):
                uvm_report_warning("BDTYP", ("Cannot create a component of type '"
                    + requested_type_name + "' because it is not registered with the factory."
                    ), UVM_NONE)
                return None
            wrapper = self.m_type_names.get(requested_type_name)

        return wrapper.create_component(name, parent)

    # create_component_by_type
    # ------------------------
    def create_component_by_type (self, requested_type, parent_inst_path, name,
            parent):
        full_inst_path = ""
        if parent_inst_path == "":
            full_inst_path = name
        elif name != "":
            full_inst_path = parent_inst_path + "." + name
        else:
            full_inst_path = parent_inst_path

        self.m_override_info.delete()
        requested_type = self.find_override_by_type(requested_type, full_inst_path)
        return requested_type.create_component(name, parent)

    # find_wrapper_by_name
    # ------------
    # TODO
    #function uvm_object_wrapper uvm_default_factory::find_wrapper_by_name(string type_name)
    #
    #  if (self.m_type_names.exists(type_name))
    #    return self.m_type_names[type_name]
    #
    #  uvm_report_warning("UnknownTypeName", {"find_wrapper_by_name: Type name '",type_name,
    #      "' not registered with the factory."}, UVM_NONE)
    #
    #endfunction

    # find_override_by_name
    # ---------------------
    # @return uvm_object_wrapper
    def find_override_by_name (self, requested_type_name, full_inst_path):
        rtype = None
        qc = UVMQueue()
        lindex = None
        override = None

        if self.m_type_names.exists(requested_type_name):
            rtype = self.m_type_names.get(requested_type_name)

        if full_inst_path != "":
            if rtype is None:
                if requested_type_name in self.m_inst_override_name_queues:
                    qc = self.m_inst_override_name_queues[requested_type_name]
            else:
                if rtype in self.m_inst_override_queues:
                    qc = self.m_inst_override_queues[rtype]

            if qc is not None:
                for index in range(0, qc.size()):
                    match_ok = uvm_is_match(qc[index].orig_type_name, requested_type_name)
                    if match_ok and uvm_is_match(qc[index].full_inst_path, full_inst_path):
                        self.m_override_info.push_back(qc[index])
                        if UVMDefaultFactory.m_debug_pass:
                            if override is None:
                                override = qc[index].ovrd_type
                                qc[index].selected = 1
                                lindex=qc[index]
                        else:
                            qc[index].used += 1
                            if qc[index].ovrd_type.get_type_name() == requested_type_name:
                                return qc[index].ovrd_type
                            else:
                                return self.find_override_by_type(qc[index].ovrd_type,full_inst_path)

        ovrd_ok = not rtype in self.m_inst_override_queues and self.m_wildcard_inst_overrides.size() > 0
        if rtype is not None and ovrd_ok:
           self.m_inst_override_queues[rtype] = UVMQueue()
           for i in range(0, self.m_wildcard_inst_overrides.size()):
               if uvm_is_match(self.m_wildcard_inst_overrides.get(i).orig_type_name,
                       requested_type_name):
                   self.m_inst_override_queues[rtype].push_back(self.m_wildcard_inst_overrides.get(i))

        # type override - exact match
        for i in range(0, self.m_type_overrides.size()):
            if self.m_type_overrides[index].orig_type_name == requested_type_name:
                self.m_override_info.push_back(self.m_type_overrides[index])
                if UVMDefaultFactory.m_debug_pass:
                    if override is None:
                        override = self.m_type_overrides[index].ovrd_type
                        self.m_type_overrides[index].selected = 1
                        lindex=self.m_type_overrides[index]
                else:
                    self.m_type_overrides[index].used += 1
                    return self.find_override_by_type(self.m_type_overrides[index].ovrd_type,full_inst_path)

        if UVMDefaultFactory.m_debug_pass and override is not None:
            lindex.used += 1
            return self.find_override_by_type(override, full_inst_path)

        # No override found
        return None

    # find_override_by_type
    # ---------------------
    def find_override_by_type(self, requested_type, full_inst_path):
        override = None
        lindex = None
        qc = None
        if requested_type in self.m_inst_override_queues:
            qc = self.m_inst_override_queues[requested_type]

        for index in range(0, self.m_override_info.size()):
            if self.m_override_info[index].orig_type == requested_type:
                uvm_report_error("OVRDLOOP", "Recursive loop detected while finding override.", UVM_NONE)
                if UVMDefaultFactory.m_debug_pass is False:
                    self.debug_create_by_type(requested_type, full_inst_path)

                self.m_override_info[index].used += 1
                return requested_type

        # inst override; return first match; takes precedence over type overrides
        if full_inst_path != "" and qc is not None:
            for index in range(0, qc.size()):
                if self.are_args_ok(qc[index], requested_type, full_inst_path):
                    self.m_override_info.push_back(qc[index])
                    if UVMDefaultFactory.m_debug_pass:
                        if override is None:
                            override = qc[index].ovrd_type
                            qc[index].selected = 1
                            lindex = qc[index]
                    else:
                        qc[index].used += 1
                        if qc[index].ovrd_type == requested_type:
                            return requested_type
                        else:
                            return self.find_override_by_type(qc[index].ovrd_type,full_inst_path)

        # type override - exact match
        for index in range(0, self.m_type_overrides.size()):
            if self.args_are_ok_again(self.m_type_overrides[index],requested_type):
                self.m_override_info.push_back(self.m_type_overrides[index])
                if UVMDefaultFactory.m_debug_pass:
                    if override is None:
                        override = self.m_type_overrides[index].ovrd_type
                        self.m_type_overrides[index].selected = 1
                        lindex = self.m_type_overrides[index]
                else:
                    self.m_type_overrides[index].used += 1
                    if self.m_type_overrides[index].ovrd_type == requested_type:
                        return requested_type
                    else:
                        return self.find_override_by_type(self.m_type_overrides[index].ovrd_type,
                            full_inst_path)

        if UVMDefaultFactory.m_debug_pass and override is not None:
            lindex.used += 1
            if override == requested_type:
                return requested_type
            else:
                return self.find_override_by_type(override,full_inst_path)

        return requested_type
        #endfunction

    # print
    # -----
    def print(self, all_types=True):
        key = ""
        sorted_override_queues = {}  # uvm_factory_queue_class s[string]
        qs = UVMQueue()
        tmp = ""
        id = 0
        obj = None  # uvm_object_wrapper obj

        # sort the override queues
        for key in self.m_inst_override_queues:
            obj = self.m_inst_override_queues[key]
            tmp = obj.get_type_name()
            if tmp == "":
                sv.swrite(tmp, "__unnamed_id_%0d", id)
                id += 1
            sorted_override_queues[tmp] = self.m_inst_override_queues[key]

        for key in self.m_inst_override_name_queues:
            sorted_override_queues[key] = self.m_inst_override_name_queues[key]

        qs.push_back("\n#### Factory Configuration (*)\n\n")

        # print instance overrides
        if len(self.m_type_overrides) == 0 and len(sorted_override_queues) == 0:
            qs.push_back("  No instance or type overrides are registered with this factory\n")
        else:
            max1 = 0
            max2 = 0
            max3 = 0
            dash = "-" * 100
            space = " " * 100
            # print instance overrides
            if len(sorted_override_queues) == 0:
                qs.push_back("No instance overrides are registered with this factory\n")
            else:
                for qc in sorted_override_queues:
                    # qc = sorted_override_queues[j]
                    #for (int i=0; i<qc.queue.size(); ++i) begin
                    for i in range(len(qc.queue)):
                        if (qc.queue[i].orig_type_name.len() > max1):
                            max1 = len(qc.queue[i].orig_type_name)
                        if (qc.queue[i].full_inst_path.len() > max2):
                            max2 = len(qc.queue[i].full_inst_path)
                        if (qc.queue[i].ovrd_type_name.len() > max3):
                            max3 = len(qc.queue[i].ovrd_type_name)

                if (max1 < 14):
                    max1 = 14
                if (max2 < 13):
                    max2 = 13
                if (max3 < 13):
                    max3 = 13

                qs.push_back("Instance Overrides:\n\n")
                qs.push_back(sv.sformatf("  %0s%0s  %0s%0s  %0s%0s\n","Requested Type",
                    space[1:max1-14], "Override Path", space[1:max2-13],
                    "Override Type", space[1:max3-13]))
                qs.push_back(sv.sformatf("  %0s  %0s  %0s\n",dash[1:max1],
                    dash[1:max2], dash[1:max3]))

                for qc in sorted_override_queues:
                    # qc = sorted_override_queues[j]
                    for i in range(len(qc.queue)):
                        qs.push_back(sv.sformatf("  %0s%0s  %0s%0s",qc.queue[i].orig_type_name,
                            space[1:max1-len(qc.queue[i].orig_type_name)],
                            qc.queue[i].full_inst_path,
                            space[1:max2-len(qc.queue[i].full_inst_path)]))
                        qs.push_back(sv.sformatf("  %0s\n", qc.queue[i].ovrd_type_name))

            # print type overrides
            if len(self.m_type_overrides) == 0:
                qs.push_back("\nNo type overrides are registered with this factory\n")
            else:
                # Resize for type overrides
                if (max1 < 14):
                    max1 = 14
                if (max2 < 13):
                    max2 = 13
                if (max3 < 13):
                    max3 = 13

                for i in range(len(self.m_type_overrides)):
                    if len(self.m_type_overrides[i].orig_type_name) > max1:
                        max1 = len(self.m_type_overrides[i].orig_type_name)
                    if len(self.m_type_overrides[i].ovrd_type_name) > max2:
                        max2 = len(self.m_type_overrides[i].ovrd_type_name)
                if (max1 < 14):
                    max1 = 14
                if (max2 < 13):
                    max2 = 13
                qs.push_back("\nType Overrides:\n\n")
                qs.push_back(sv.sformatf("  %0s%0s  %0s%0s\n","Requested Type", space[1:max1-14],
                    "Override Type", space[1:max2-13]))
                qs.push_back(sv.sformatf("  %0s  %0s\n",dash[1:max1],
                    dash[1:max2]))
                for index in range(len(self.m_type_overrides)):
                    qs.push_back(sv.sformatf("  %0s%0s  %0s\n",
                             self.m_type_overrides[index].orig_type_name,
                             space[1:max1-len(self.m_type_overrides[index].orig_type_name)],
                             self.m_type_overrides[index].ovrd_type_name))

        # print all registered types, if all_types >= 1
        if all_types >= 1 and self.m_type_names.has_first():
            banner = False
            qs.push_back(sv.sformatf("\nAll types registered with the factory: %0d total\n",self.m_types.num()))
            key = self.m_type_names.first()
            while key is not None:
                # filter out uvm_ classes (if all_types<2) and non-types (lookup strings)
                if (not (all_types < 2 and uvm_is_match("uvm_*",
                       self.m_type_names[key].get_type_name())) and
                       key == self.m_type_names[key].get_type_name()):
                    if not banner:
                        qs.push_back("  Type Name\n")
                        qs.push_back("  ---------\n")
                        banner = True
                    qs.push_back(sv.sformatf("  %s\n", self.m_type_names[key].get_type_name()))
                if self.m_type_names.has_next():
                    key = self.m_type_names.next()
                else:
                    break
            # end while(self.m_type_names.next(key))

        qs.push_back("(*) Types with no associated type name will be printed as <unknown>\n\n####\n\n")
        uvm_info("UVM/FACTORY/PRINT", UVM_STRING_QUEUE_STREAMING_PACK(qs), UVM_NONE)

    # debug_create_by_name
    # --------------------
    # TODO
    #function void  uvm_default_factory::debug_create_by_name (string requested_type_name,
    #                                                  string parent_inst_path="",
    #                                                  string name="")
    #  m_debug_create(requested_type_name, null, parent_inst_path, name)
    #endfunction

    # debug_create_by_type
    # --------------------
    # TODO
    #function void  uvm_default_factory::debug_create_by_type (uvm_object_wrapper requested_type,
    #                                                  string parent_inst_path="",
    #                                                  string name="")
    #  m_debug_create("", requested_type, parent_inst_path, name)
    #endfunction

    # m_debug_create
    # --------------
    # TODO
    #function void  uvm_default_factory::m_debug_create (string requested_type_name,
    #                                            uvm_object_wrapper requested_type,
    #                                            string parent_inst_path,
    #                                            string name)
    #
    #  string full_inst_path
    #  uvm_object_wrapper result
    #
    #  if (parent_inst_path == "")
    #    full_inst_path = name
    #  else if (name != "")
    #    full_inst_path = {parent_inst_path,".",name}
    #  else
    #    full_inst_path = parent_inst_path
    #
    #  m_override_info.delete()
    #
    #  if (requested_type == null) begin
    #    if (!self.m_type_names.exists(requested_type_name) &&
    #      !m_lookup_strs.exists(requested_type_name)) begin
    #      uvm_report_warning("Factory Warning", {"The factory does not recognize '",
    #        requested_type_name,"' as a registered type."}, UVM_NONE)
    #      return
    #    end
    #    m_debug_pass = 1
    #
    #    result = find_override_by_name(requested_type_name,full_inst_path)
    #  end
    #  else begin
    #    m_debug_pass = 1
    #    if (!self.m_types.exists(requested_type))
    #      register(requested_type)
    #    result = find_override_by_type(requested_type,full_inst_path)
    #    if (requested_type_name == "")
    #      requested_type_name = requested_type.get_type_name()
    #  end
    #
    #  m_debug_display(requested_type_name, result, full_inst_path)
    #  m_debug_pass = 0
    #
    #  foreach (m_override_info[index])
    #    m_override_info[index].selected = 0
    #
    #endfunction

    # m_debug_display
    # ---------------
    # TODO
    #function void  uvm_default_factory::m_debug_display (string requested_type_name,
    #                                             uvm_object_wrapper result,
    #                                             string full_inst_path)
    #
    #  int    max1,max2,max3
    #  string dash = "---------------------------------------------------------------------------------------------------"
    #  string space= "                                                                                                   "
    #  string qs[$]
    #
    #  qs.push_back("\n#### Factory Override Information (*)\n\n")
    #  qs.push_back(
    #  	$sformatf("Given a request for an object of type '%s' with an instance\npath of '%s' the factory encountered\n\n",
    #  		requested_type_name,full_inst_path))
    #
    #  if (m_override_info.size() == 0)
    #    qs.push_back("no relevant overrides.\n\n")
    #  else begin
    #
    #    qs.push_back("the following relevant overrides. An 'x' next to a match indicates a\nmatch that was ignored.\n\n")
    #
    #    foreach (m_override_info[i]) begin
    #      if (m_override_info[i].orig_type_name.len() > max1)
    #        max1=m_override_info[i].orig_type_name.len()
    #      if (m_override_info[i].full_inst_path.len() > max2)
    #        max2=m_override_info[i].full_inst_path.len()
    #      if (m_override_info[i].ovrd_type_name.len() > max3)
    #        max3=m_override_info[i].ovrd_type_name.len()
    #    end
    #
    #    if (max1 < 13) max1 = 13
    #    if (max2 < 13) max2 = 13
    #    if (max3 < 13) max3 = 13
    #
    #    qs.push_back($sformatf("Original Type%0s  Instance Path%0s  Override Type%0s\n",
    #    	space.substr(1,max1-13),space.substr(1,max2-13),space.substr(1,max3-13)))
    #
    #    qs.push_back($sformatf("  %0s  %0s  %0s\n",dash.substr(1,max1),
    #                               dash.substr(1,max2),
    #                               dash.substr(1,max3)))
    #
    #    foreach (m_override_info[i]) begin
    #      qs.push_back($sformatf("%s%0s%0s\n",
    #             m_override_info[i].selected ? "  " : "x ",
    #             m_override_info[i].orig_type_name,
    #             space.substr(1,max1-m_override_info[i].orig_type_name.len())))
    #      qs.push_back($sformatf("  %0s%0s", m_override_info[i].full_inst_path,
    #             space.substr(1,max2-m_override_info[i].full_inst_path.len())))
    #      qs.push_back($sformatf("  %0s%0s", m_override_info[i].ovrd_type_name,
    #             space.substr(1,max3-m_override_info[i].ovrd_type_name.len())))
    #      if (m_override_info[i].full_inst_path == "*")
    #        qs.push_back("  <type override>")
    #      else
    #        qs.push_back("\n")
    #    end
    #    qs.push_back("\n")
    #  end
    #
    #
    #  qs.push_back("Result:\n\n")
    #  qs.push_back($sformatf("  The factory will produce an object of type '%0s'\n",
    #           result == null ? requested_type_name : result.get_type_name()))
    #
    #  qs.push_back("\n(*) Types with no associated type name will be printed as <unknown>\n\n####\n\n")
    #
    #  `uvm_info("UVM/FACTORY/DUMP",`UVM_STRING_QUEUE_STREAMING_PACK(qs),UVM_NONE)
    #endfunction

    # Internal helper functions

    def are_args_ok(self, qc_elem, requested_type, full_inst_path):
        name_ok = (qc_elem.orig_type == requested_type or
                   (qc_elem.orig_type_name != "<unknown>" and
                    qc_elem.orig_type_name != "" and
                    qc_elem.orig_type_name == requested_type.get_type_name()))
        return name_ok and uvm_is_match(qc_elem.full_inst_path, full_inst_path)

    def args_are_ok_again(self, type_override, requested_type):
        match_ok = (type_override.orig_type_name != "<unknown>" and
             type_override.orig_type_name != "" and
             requested_type is not None and
             type_override.orig_type_name == requested_type.get_type_name())
        return type_override.orig_type == requested_type or match_ok

#------------------------------------------------------------------------------
#
# CLASS: uvm_object_wrapper
#
# The uvm_object_wrapper provides an abstract interface for creating object and
# component proxies. Instances of these lightweight proxies, representing every
# <uvm_object>-based and <uvm_component>-based object available in the test
# environment, are registered with the <uvm_factory>. When the factory is
# called upon to create an object or component, it finds and delegates the
# request to the appropriate proxy.
#
#------------------------------------------------------------------------------
class UVMObjectWrapper:

    # Function: create_object
    #
    # Creates a new object with the optional ~name~.
    # An object proxy (e.g., <uvm_object_registry #(T,Tname)>) implements this
    # method to create an object of a specific type, T.
    def create_object (self, name=""):
        return None

    # Function: create_component
    #
    # Creates a new component, passing to its constructor the given ~name~ and
    # ~parent~. A component proxy (e.g. <uvm_component_registry #(T,Tname)>)
    # implements this method to create a component of a specific type, T.
    def create_component(self,  name, parent):
        return None

    # Function: get_type_name
    #
    # Derived classes implement this method to return the type name of the object
    # created by <create_component> or <create_object>. The factory uses this
    # name when matching against the requested type in name-based lookups.
    def get_type_name(self):
        return "<unknown_type>"

#------------------------------------------------------------------------------
#
# CLASS- uvm_factory_override
#
# Internal class.
#------------------------------------------------------------------------------
class UVMFactoryOverride:
    #uvm_object_wrapper orig_type
    #uvm_object_wrapper ovrd_type
    def __init__(self, full_inst_path="", orig_type_name="", orig_type=None,
            ovrd_type = None):
        if ovrd_type is None:
            uvm_report_fatal ("NULLWR", "Attempting to register a null override object with the factory", UVM_NONE)
        self.full_inst_path= full_inst_path

        if orig_type is None:
            self.orig_type_name = orig_type_name
        else:
            self.orig_type_name  = orig_type.get_type_name()

        self.orig_type      = orig_type
        self.ovrd_type_name = ovrd_type.get_type_name()
        self.ovrd_type      = ovrd_type
        self.selected = False
        self.used = 0

import unittest

class TestUVMDefaultFactory(unittest.TestCase):

    def test_override(self):
        fact = UVMDefaultFactory()
        fact.set_type_override_by_name('XXX', 'YYY')
        ovrd = fact.find_override_by_type(requested_type='XXX', full_inst_path='')

    def test_create_component_by_name(self):
        from ..comps.uvm_test import UVMTest
        from ..macros.uvm_object_defines import uvm_component_utils
        class MyTest123(UVMTest):
            def __init__(self, name, parent):
                UVMTest.__init__(self, name, parent)
        uvm_component_utils(MyTest123)
        factory = UVMFactory.get()
        test_name = 'MyTest123'
        uvm_test_top = factory.create_component_by_name(test_name,
            "", "uvm_test_top", None)
        self.assertEqual(uvm_test_top.get_full_name(), "uvm_test_top")

    def test_create_object_by_name(self):
        from ..macros.uvm_object_defines import uvm_object_utils
        from uvm_object import UVMObject
        class MyObj(UVMObject):
            def __init__(self, name):
                UVMObject.__init__(self, name)
        uvm_object_utils(MyObj)
        factory = UVMFactory.get()
        new_obj = factory.create_object_by_name('MyObj', "", "my_obj_name")
        self.assertEqual(new_obj.get_name(), 'my_obj_name')

if __name__ == '__main__':
    unittest.main()


