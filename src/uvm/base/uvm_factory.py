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

# pytype: disable=attribute-error,not-writable

from typing import List, Optional

from .sv import sv
from .uvm_queue import UVMQueue
from .uvm_pool import UVMPool
from .uvm_globals import (uvm_report_error, uvm_report_fatal, uvm_report_warning,
    uvm_is_match, uvm_report_info)
from .uvm_object_globals import UVM_NONE, UVM_MEDIUM, UVM_HIGH
from ..macros import uvm_info
from ..uvm_macros import UVM_STRING_QUEUE_STREAMING_PACK



def m_has_wildcard(nm: str) -> bool:
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
# CLASS- UVMFactoryOverride
#
# Internal class. Data structure for factory overrides to store all override
# related information.
#------------------------------------------------------------------------------

class UVMFactoryOverride:


    def __init__(self, full_inst_path="", orig_type_name="", orig_type=None,
            ovrd_type=None):
        if ovrd_type is None:
            uvm_report_fatal("NULLWR",
                "Attempting to register a null override object with the factory", UVM_NONE)
        self.full_inst_path = full_inst_path
        self.orig_type_name = orig_type_name
        if orig_type is not None:
            self.orig_type_name  = orig_type.get_type_name()

        self.orig_type      = orig_type
        self.ovrd_type_name = ovrd_type.get_type_name()
        self.ovrd_type      = ovrd_type
        self.selected = False
        self.used = 0



class UVMFactory:
    """
    UVMFactory is used to create objects of type `UVMComponent` and
    `UVMObject` (and their derived user-defined types).
    Object and component types are registered
    with the factory using lightweight proxies to the actual objects and
    components being created. The `UVMObjectRegistry` and
    `UVMComponentRegistry` class are used to proxy `UVMObject`
    and `UVMComponent`.

    The factory provides both name-based and type-based interfaces.

    type-based - The type-based interface is far less prone to errors in usage.

    name-based - The name-based interface is dominated
      by string arguments that can be misspelled and provided in the wrong order.
      Errors in name-based requests might only be caught at the time of the call,
      if at all.

    The `UVMFactory` is an abstract class. The UVM uses the `UVMDefaultFactory` class
    as its default factory implementation.

    See `UVMDefaultFactory` section for details on configuring and using the factory.
    """

    #// Group: Retrieving the factory

    @classmethod
    def get(cls) -> 'UVMFactory':
        """
        Function: get
        Static accessor for `UVMFactory`

        The static accessor is provided as a convenience wrapper
        around retrieving the factory via the `UVMCoreService.get_factory`
        method.

        .. code-block:: python

            # Using the uvm_coreservice_t:
            cs = UVMCoreService.get()
            f = cs.get_factory()

        .. code-block:: python

            # Not using the uvm_coreservice_t:
            f = UVMFactory.get()

        Returns:
            UVMFactory: Singleton instace of the factory
        """
        from .uvm_coreservice import UVMCoreService
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
        self.m_override_info: List[UVMFactoryOverride] = []
        self.m_types = UVMPool()  # [uvm_object_wrapper] -> bit
        self.m_lookup_strs = UVMPool()
        self.m_type_names = UVMPool()
        self.m_type_overrides: List[UVMFactoryOverride] = []
        self.m_inst_override_queues = {}  # [uvm_object_wrapper] -> queue
        self.m_inst_override_name_queues = {}  # [string] -> queue
        self.m_wildcard_inst_overrides = UVMQueue()


    def register(self, obj) -> None:
        """
        Group: Registering Types

        Function: register

        Registers the given proxy object, `obj`, with the factory.
        Args:
            obj:
        """
        if obj is None:
            uvm_report_fatal("NULLWR",
                "Attempting to register a null object with the factory")

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
            tname = obj.get_type_name()
            if obj.get_type_name() in self.m_inst_override_name_queues:
                self.m_inst_override_queues[obj] = UVMQueue()
                self.m_inst_override_queues[obj] = self.m_inst_override_name_queues[tname]
                del self.m_inst_override_name_queues[tname]
            if self.m_wildcard_inst_overrides.size():
                if obj not in self.m_inst_override_queues:
                    self.m_inst_override_queues[obj] = UVMQueue()
                for i in range(0, self.m_wildcard_inst_overrides.size()):
                    wc_inst_override = self.m_wildcard_inst_overrides[i]
                    if uvm_is_match(wc_inst_override.orig_type_name, tname):
                        self.m_inst_override_queues[obj].push_back(wc_inst_override)

    def set_type_override_by_type(self, original_type, override_type,
            replace=True):
        """
        set_type_override_by_type
        -------------------------

        #def set_type_override_by_type (uvm_object_wrapper original_type,
                                                     uvm_object_wrapper override_type,
                                                     bit replace=1)
        Args:
            original_type:
            override_type:
            replace:
        """
        replaced = False

        # check that old and new are not the same
        if original_type == override_type:
            if original_type.get_type_name() == "" or original_type.get_type_name() == "<unknown>":
                uvm_report_warning("TYPDUP", "Original and override type "
                        + "arguments are identical", UVM_NONE)
            else:
                uvm_report_warning("TYPDUP", "Original and override type "
                        + "arguments are identical: "
                        + original_type.get_type_name(), UVM_NONE)

        # register the types if not already done so, for the benefit of string-based lookup
        if not self.m_types.exists(original_type):
            self.register(original_type)

        if not self.m_types.exists(override_type):
            self.register(override_type)

        # check for existing type override
        for index in range(len(self.m_type_overrides)):
            idx_orig_type = self.m_type_overrides[index].orig_type
            idx_type_name = self.m_type_overrides[index].orig_type_name
            if (idx_orig_type == original_type or
                    (idx_type_name != "<unknown>" and
                        idx_type_name != "" and
                        idx_type_name == original_type.get_type_name())):

                msg = ("Original object type '" + original_type.get_type_name()
                       + "' already registered to produce '"
                       + self.m_type_overrides[index].ovrd_type_name + "'")
                if replace is False:
                    msg = msg + ".  Set 'replace' argument to replace the existing entry."
                    uvm_report_info("TPREGD", msg, UVM_MEDIUM)
                    return

                msg = (msg + ".  Replacing with override to produce type '"
                    + override_type.get_type_name() + "'.")
                uvm_report_info("TPREGR", msg, UVM_MEDIUM)
                replaced = True
                self.m_type_overrides[index].orig_type = original_type
                self.m_type_overrides[index].orig_type_name = original_type.get_type_name()
                self.m_type_overrides[index].ovrd_type = override_type
                self.m_type_overrides[index].ovrd_type_name = override_type.get_type_name()



        #  make a new entry
        if replaced is False:
            # uvm_factory_override override
            override = UVMFactoryOverride(orig_type=original_type,
                           orig_type_name=original_type.get_type_name(),
                           full_inst_path="*",
                           ovrd_type=override_type)

            self.m_type_overrides.append(override)


    def set_type_override_by_name(self, original_type_name, override_type_name,
            replace=True):
        """
        set_type_override_by_name
        -------------------------
        Args:
            original_type_name:
            override_type_name:
            replace:
        """
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

        for index in range(0, len(self.m_type_overrides)):
            ovrd_type_name = self.m_type_overrides[index].ovrd_type_name
            if self.m_type_overrides[index].orig_type_name == original_type_name:
                if not replace:
                    uvm_report_info("TPREGD", ("Original type '" + original_type_name
                      + "' already registered to produce '" + ovrd_type_name
                      + "'.  Set 'replace' argument to replace the existing entry."), UVM_MEDIUM)
                    return

                uvm_report_info("TPREGR", ("Original object type '" + original_type_name
                  + "' already registered to produce '" + ovrd_type_name
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

            self.m_type_overrides.append(override)
            self.m_type_names.add(original_type_name, override.ovrd_type)

    def check_inst_override_exists(self, original_type, override_type,
            full_inst_path):
        """
        check_inst_override_exists
        --------------------------
        #def check_inst_override_exists (uvm_object_wrapper original_type,
                                             uvm_object_wrapper override_type,
                                             string full_inst_path)
        Args:
            original_type:
            override_type:
            full_inst_path:
        Returns:
        """
        override = None  # uvm_factory_override
        qc = None  # uvm_factory_queue_class

        if original_type in self.m_inst_override_queues:
            qc = self.m_inst_override_queues[original_type]
        else:
            return 0

        for index in range(len(qc.queue)):
            override = qc.queue[index]
            if (override.full_inst_path == full_inst_path and
                    override.orig_type == original_type and
                    override.ovrd_type == override_type and
                    override.orig_type_name == original_type.get_type_name()):
                uvm_report_info("DUPOVRD", "Instance override for '"
                    + original_type.get_type_name() + "' already exists: override type '"
                    + override_type.get_type_name() + "' with full_inst_path '"
                    + full_inst_path + "'", UVM_HIGH)
                return 1
        return 0


    def set_inst_override_by_type(self, original_type, override_type,
            full_inst_path):
        """
        set_inst_override_by_type
        -------------------------

        #def set_inst_override_by_type (uvm_object_wrapper original_type,
                                                             uvm_object_wrapper override_type,
                                                             string full_inst_path)
        Args:
            original_type:
            override_type:
            full_inst_path:
        """

        override = None  # uvm_factory_override

        # register the types if not already done so
        if not self.m_types.exists(original_type):
            self.register(original_type)

        if not self.m_types.exists(override_type):
            self.register(override_type)

        if self.check_inst_override_exists(original_type,override_type,full_inst_path):
            return

        if original_type not in self.m_inst_override_queues:
            self.m_inst_override_queues[original_type] = UVMQueue()

        override = UVMFactoryOverride(full_inst_path=full_inst_path,
                orig_type=original_type,
                orig_type_name=original_type.get_type_name(),
                ovrd_type=override_type)


        self.m_inst_override_queues[original_type].push_back(override)


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
    #  if (override_type  is None):
    #    uvm_report_error("TYPNTF", {"Cannot register instance override with type name '",
    #    original_type_name,"' and instance path '",full_inst_path,"' because the type it's supposed ",
    #    "to produce, '",override_type_name,"', is not registered with the factory."}, UVM_NONE)
    #    return
    #  end
    #
    #  if (original_type  is None)
    #      m_lookup_strs[original_type_name] = 1
    #
    #  override = new(.full_inst_path(full_inst_path),
    #                 .orig_type(original_type),
    #                 .orig_type_name(original_type_name),
    #                 .ovrd_type(override_type))
    #
    #  if(original_type != null):
    #    if (check_inst_override_exists(original_type,override_type,full_inst_path))
    #      return
    #    if(!m_inst_override_queues.exists(original_type))
    #      m_inst_override_queues[original_type] = new
    #    m_inst_override_queues[original_type].queue.push_back(override)
    #  end
    #  else:
    #    if(m_has_wildcard(original_type_name)):
    #       foreach(self.m_type_names[i]):
    #         if(uvm_is_match(original_type_name,i)):
    #           this.set_inst_override_by_name(i, override_type_name, full_inst_path)
    #         end
    #       end
    #       m_wildcard_inst_overrides.push_back(override)
    #    end
    #    else:
    #      if(!self.m_inst_override_name_queues.exists(original_type_name))
    #        self.m_inst_override_name_queues[original_type_name] = new
    #      self.m_inst_override_name_queues[original_type_name].queue.push_back(override)
    #    end
    #  end
    #
    #endfunction

    def create_object_by_name(self, requested_type_name, parent_inst_path="",
              name=""):
        """
        create_object_by_name
        ---------------------
        Args:
            requested_type_name:
            parent_inst_path:
            name:
        Returns:
        """
        inst_path = self._get_inst_path(parent_inst_path, name)

        self.m_override_info.clear()
        wrapper = self.find_override_by_name(requested_type_name, inst_path)

        # if no override exists, try to use requested_type_name directly
        if wrapper is None:
            if not self.m_type_names.exists(requested_type_name):
                uvm_report_warning("BDTYP", ("Cannot create an object of type '"
                    + requested_type_name + "' because it is not registered with the factory."),
                    UVM_NONE)
                return None
            wrapper = self.m_type_names.get(requested_type_name)
        return wrapper.create_object(name)

    def create_object_by_type(self, requested_type, parent_inst_path="", name=""):
        """
        create_object_by_type
        ---------------------
        Args:
            requested_type:
            parent_inst_path:
            name:
        Returns:
        """
        if requested_type is None:
            uvm_report_fatal("REQ_TYPE_NONE", "Requested type object was None")
        full_inst_path = self._get_inst_path(parent_inst_path, name)

        self.m_override_info.clear()
        requested_type = self.find_override_by_type(requested_type, full_inst_path)
        if requested_type is None:
            uvm_report_fatal("REQ_TYPE_NONE", "Requested type object was None after override")
        return requested_type.create_object(name)

    def _get_inst_path(self, parent_inst_path, name):
        inst_path = ""
        if parent_inst_path == "":
            inst_path = name
        elif name != "":
            inst_path = parent_inst_path + "." + name
        else:
            inst_path = parent_inst_path
        return inst_path

    def create_component_by_name(self, requested_type_name,
            parent_inst_path, name, parent):
        """
        create_component_by_name
        ------------------------
        Args:
            requested_type_name:
            parent_inst_path:
            name:
            parent:
        Returns:
        """

        inst_path = self._get_inst_path(parent_inst_path, name)

        self.m_override_info.clear()
        wrapper = self.find_override_by_name(requested_type_name, inst_path)

        # if no override exists, try to use requested_type_name directly
        if wrapper is None:
            if not self.m_type_names.exists(requested_type_name):
                uvm_report_warning("BDTYP", ("Cannot create a component of type '"
                    + requested_type_name + "' because it is not registered with the factory."),
                    UVM_NONE)
                return None
            wrapper = self.m_type_names.get(requested_type_name)

        return wrapper.create_component(name, parent)

    def create_component_by_type(self, requested_type, parent_inst_path, name,
            parent):
        """
        create_component_by_type
        ------------------------
        Args:
            requested_type:
            parent_inst_path:
            name:
            parent:
        Returns:
        """
        full_inst_path = self._get_inst_path(parent_inst_path, name)

        self.m_override_info.clear()
        requested_type = self.find_override_by_type(requested_type, full_inst_path)
        return requested_type.create_component(name, parent)

    # find_wrapper_by_name
    # ------------
    # TODO
    def find_wrapper_by_name(self, type_name: str) -> Optional['UVMObjectWrapper']:
        if self.m_type_names.exists(type_name):
            return self.m_type_names[type_name]
        uvm_report_warning("UnknownTypeName", ("find_wrapper_by_name: Type name '"
            + type_name + "' not registered with the factory."), UVM_NONE)

    def find_override_by_name(
            self, requested_type_name, full_inst_path) -> Optional['UVMObjectWrapper']:
        """
        find_override_by_name
        ---------------------
        Args:
            requested_type_name (str):
            full_inst_path (str):
        Returns:
            UVMObjectWrapper
        """
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
                        self.m_override_info.append(qc[index])
                        if UVMDefaultFactory.m_debug_pass:
                            if override is None:
                                override = qc[index].ovrd_type
                                qc[index].selected = 1
                                lindex = qc[index]
                        else:
                            qc[index].used += 1
                            if qc[index].ovrd_type.get_type_name() == requested_type_name:
                                return qc[index].ovrd_type
                            else:
                                return self.find_override_by_type(qc[index].ovrd_type,full_inst_path)

        ovrd_ok = rtype not in self.m_inst_override_queues and self.m_wildcard_inst_overrides.size() > 0
        if rtype is not None and ovrd_ok:
            self.m_inst_override_queues[rtype] = UVMQueue()
            for i in range(0, self.m_wildcard_inst_overrides.size()):
                if uvm_is_match(self.m_wildcard_inst_overrides.get(i).orig_type_name,
                        requested_type_name):
                    self.m_inst_override_queues[rtype].push_back(self.m_wildcard_inst_overrides.get(i))

        # type override - exact match
        for index in range(0, len(self.m_type_overrides)):
            if self.m_type_overrides[index].orig_type_name == requested_type_name:
                self.m_override_info.append(self.m_type_overrides[index])
                if UVMDefaultFactory.m_debug_pass:
                    if override is None:
                        override = self.m_type_overrides[index].ovrd_type
                        self.m_type_overrides[index].selected = 1
                        lindex = self.m_type_overrides[index]
                else:
                    self.m_type_overrides[index].used += 1
                    return self.find_override_by_type(self.m_type_overrides[index].ovrd_type,full_inst_path)

        if UVMDefaultFactory.m_debug_pass and override is not None:
            lindex.used += 1
            return self.find_override_by_type(override, full_inst_path)

        # No override found
        return None

    def find_override_by_type(self, requested_type, full_inst_path):
        """
        find_override_by_type
        ---------------------
        Args:
            requested_type:
            full_inst_path:
        Returns:
        """
        override = None
        lindex = None
        qc = None
        if requested_type in self.m_inst_override_queues:
            qc = self.m_inst_override_queues[requested_type]

        for index in range(0, len(self.m_override_info)):
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
                    self.m_override_info.append(qc[index])
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
        for index in range(0, len(self.m_type_overrides)):
            if self.args_are_ok_again(self.m_type_overrides[index],requested_type):
                self.m_override_info.append(self.m_type_overrides[index])
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

    def convert2string(self, all_types=True) -> str:
        """
        tpoikela: Added this to access factory string repr without print()

        Args:
            all_types (bool): If True, adds all possible types
        Returns:
            str: Factory converted to string
        """
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
                tmp = "__unnamed_id_" + str(id)
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
                for key, qc in sorted_override_queues.items():
                    for i in range(len(qc.queue)):
                        orig_type_name = qc.queue[i].orig_type_name
                        full_inst_path = qc.queue[i].full_inst_path
                        ovrd_type_name = qc.queue[i].ovrd_type_name
                        if len(orig_type_name) > max1:
                            max1 = len(orig_type_name)
                        if len(full_inst_path) > max2:
                            max2 = len(full_inst_path)
                        if len(ovrd_type_name) > max3:
                            max3 = len(ovrd_type_name)

                if max1 < 14:
                    max1 = 14
                if max2 < 13:
                    max2 = 13
                if max3 < 13:
                    max3 = 13

                qs.push_back("Instance Overrides:\n\n")
                qs.push_back(sv.sformatf("  %0s%0s  %0s%0s  %0s%0s\n","Requested Type",
                    space[1:max1-14], "Override Path", space[1:max2-13],
                    "Override Type", space[1:max3-13]))
                qs.push_back(sv.sformatf("  %0s  %0s  %0s\n",dash[1:max1],
                    dash[1:max2], dash[1:max3]))

                for key, qc in sorted_override_queues.items():
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
                if max1 < 14:
                    max1 = 14
                if max2 < 13:
                    max2 = 13
                if max3 < 13:
                    max3 = 13

                for i in range(len(self.m_type_overrides)):
                    if len(self.m_type_overrides[i].orig_type_name) > max1:
                        max1 = len(self.m_type_overrides[i].orig_type_name)
                    if len(self.m_type_overrides[i].ovrd_type_name) > max2:
                        max2 = len(self.m_type_overrides[i].ovrd_type_name)
                if max1 < 14:
                    max1 = 14
                if max2 < 13:
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
        return UVM_STRING_QUEUE_STREAMING_PACK(qs)

    def print_factory(self, all_types=True):
        """
        print
        -----
        Args:
            all_types:
        """
        fact_str = self.convert2string(all_types)
        uvm_info("UVM/FACTORY/PRINT", fact_str, UVM_NONE)

    # debug_create_by_name
    # --------------------
    # TODO
    def debug_create_by_name(self, requested_type_name, parent_inst_path="", name=""):
        self.m_debug_create(requested_type_name, None, parent_inst_path, name)

    # debug_create_by_type
    # --------------------

    def debug_create_by_type(self, requested_type, parent_inst_path="", name=""):
        self.m_debug_create("", requested_type, parent_inst_path, name)

    # m_debug_create
    # --------------
    # TODO
    def m_debug_create(self, requested_type_name, requested_type,
            parent_inst_path, name):
        full_inst_path = self._get_inst_path(parent_inst_path, name)
        result = None
        self.m_override_info.clear()

        if requested_type is None:
            if (not self.m_type_names.exists(requested_type_name) and
                    not self.m_lookup_strs.exists(requested_type_name)):
                uvm_report_warning("Factory Warning", {"The factory does not recognize '",
                    requested_type_name,"' as a registered type."}, UVM_NONE)
                return
            UVMDefaultFactory.m_debug_pass = 1
            result = self.find_override_by_name(requested_type_name,full_inst_path)
        else:
            UVMDefaultFactory.m_debug_pass = 1
            if not self.m_types.exists(requested_type):
                self.register(requested_type)
            result = self.find_override_by_type(requested_type,full_inst_path)
            if requested_type_name == "":
                requested_type_name = requested_type.get_type_name()
        self.m_debug_display(requested_type_name, result, full_inst_path)
        UVMDefaultFactory.m_debug_pass = 0
        for obj in self.m_override_info:
            obj.selected = 0

    # m_debug_display
    # ---------------
    # TODO
    def m_debug_display(self, requested_type_name, result, full_inst_path):
        pass
        max1 = 0
        max2 = 0
        max3 = 0
        dash = 100 * "-"
        space = 100 * " "
        qs = []

        qs.append("\n#### Factory Override Information (*)\n\n")
        qs.append(sv.sformatf("Given a request for an object of type '%s' with "
            + "an instance\npath of '%s' the factory encountered\n\n",
            requested_type_name,full_inst_path))

        if len(self.m_override_info) == 0:
            qs.append("no relevant overrides.\n\n")
        else:
            qs.append("the following relevant overrides. "
                + "An 'x' next to a match indicates a\nmatch that was ignored.\n\n")

            for i in range(len(self.m_override_info)):
                if (len(self.m_override_info[i].orig_type_name) > max1):
                    max1 = len(self.m_override_info[i].orig_type_name)
                if (len(self.m_override_info[i].full_inst_path) > max2):
                    max2 = len(self.m_override_info[i].full_inst_path)
                if (len(self.m_override_info[i].ovrd_type_name) > max3):
                    max3 = len(self.m_override_info[i].ovrd_type_name)

            if max1 < 13:
                max1 = 13
            if max2 < 13:
                max2 = 13
            if max3 < 13:
                max3 = 13

            qs.append(sv.sformatf("Original Type%0s  Instance Path%0s  Override Type%0s\n",
                space[1:max1-12],space[1:max2-12],space[1:max3-12]))
            #space.substr(1,max1-13),space.substr(1,max2-13),space.substr(1,max3-13)))

            qs.append(sv.sformatf("  %0s  %0s  %0s\n",
                dash[1:max1], dash[1:max2], dash[1:max3]))

            for i in range(len(self.m_override_info)):
                orig_type_len = len(self.m_override_info[i].orig_type_name)
                full_inst_path_len = len(self.m_override_info[i].full_inst_path)
                ovrd_type_len = len(self.m_override_info[i].ovrd_type_name)
                is_sel_str = "x "
                if self.m_override_info[i].selected:
                    is_sel_str = "  "

                qs.append(sv.sformatf("%s%0s%0s",
                    is_sel_str,
                    self.m_override_info[i].orig_type_name,
                    space[1:max1-orig_type_len]))
                qs.append(sv.sformatf("  %0s%0s", self.m_override_info[i].full_inst_path,
                    space[1:max2-full_inst_path_len]))
                qs.append(sv.sformatf("  %0s%0s", self.m_override_info[i].ovrd_type_name,
                    space[1:max3-ovrd_type_len]))
                if self.m_override_info[i].full_inst_path == "*":
                    qs.append("  <type override>")
                else:
                    qs.append("\n")
            qs.append("\n")

        qs.append("Result:\n\n")
        chosen_type_name = requested_type_name
        if result is not None:
            chosen_type_name = result.get_type_name()
        qs.append(sv.sformatf("  The factory will produce an object of type '%0s'\n",
            chosen_type_name))

        qs.append("\n(*) Types with no associated type name will be printed as <unknown>\n\n####\n\n")
        uvm_info("UVM/FACTORY/DUMP", UVM_STRING_QUEUE_STREAMING_PACK(qs),UVM_NONE)

    # Internal helper functions

    def are_args_ok(self, qc_elem, requested_type, full_inst_path) -> bool:
        name_ok = (qc_elem.orig_type == requested_type or
                   (qc_elem.orig_type_name != "<unknown>" and
                    qc_elem.orig_type_name != "" and
                    qc_elem.orig_type_name == requested_type.get_type_name()))
        return name_ok and uvm_is_match(qc_elem.full_inst_path, full_inst_path)

    def args_are_ok_again(self, type_override, requested_type) -> bool:
        match_ok = (type_override.orig_type_name != "<unknown>" and
             type_override.orig_type_name != "" and
             requested_type is not None and
             type_override.orig_type_name == requested_type.get_type_name())
        return type_override.orig_type == requested_type or match_ok



class UVMObjectWrapper:
    """
    The UVMObjectWrapper provides an abstract interface for creating object and
    component proxies. Instances of these lightweight proxies, representing every
    `UVMObject`-based and `UVMComponent`-based object available in the test
    environment, are registered with the `UVMFactory`. When the factory is
    called upon to create an object or component, it finds and delegates the
    request to the appropriate proxy.
    """

    def create_object(self, name=""):
        """
        Creates a new object with the optional `name`.
        An object proxy (e.g., <uvm_object_registry #(T,Tname)>) implements this
        method to create an object of a specific type, T.

        Args:
            name (str):
        Returns:
            UVMObject|None
        """
        return None

    def create_component(self, name, parent):
        """
        Function: create_component

        Creates a new component, passing to its constructor the given `name` and
        `parent`. A component proxy (e.g. <uvm_component_registry #(T,Tname)>)
        implements this method to create a component of a specific type, T.

        Args:
            name (str):
            parent (UVMComponent): Parent of the created component.
        Returns:
            UVMComponent|None
        """
        return None

    def get_type_name(self):
        """
        Derived classes implement this method to return the type name of the object
        created by `create_component` or `create_object`. The factory uses this
        name when matching against the requested type in name-based lookups.

        Returns:
            str: Name of the type
        """
        return "<unknown_type>"

# pytype: enable=attribute-error,not-writable
