#------------------------------------------------------------------------------
#     Copyright 2007-2011 Mentor Graphics Corporation
#     Copyright 2007-2011 Cadence Design Systems, Inc.
#     Copyright 2010 Synopsys, Inc.
#     Copyright 2013 Cisco Systems, Inc.
#     Copyright 2019 Tuomas Poikela
#     All Rights Reserved Worldwide
#
#     Licensed under the Apache License, Version 2.0 (the "License"); you may not
#     use this file except in compliance with the License.    You may obtain a copy
#     of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#     WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    See the
#     License for the specific language governing permissions and limitations
#     under the License.
#------------------------------------------------------------------------------

from .uvm_component import UVMComponent
from .uvm_object_globals import (UVM_EXPORT, UVM_IMPLEMENTATION, UVM_NONE, UVM_PHASE_DONE,
                                 UVM_PHASE_EXECUTING, UVM_PORT)
from .uvm_domain import end_of_elaboration_ph
from .sv import sv
from ..macros.uvm_message_defines import uvm_report_fatal

UVM_UNBOUNDED_CONNECTIONS = -1
s_connection_error_id = "Connection Error"
s_connection_warning_id = "Connection Warning"
s_spaces = "                                             "

ERR_MSG2 = ("Port parent: {}. Cannot call an imp port's connect method. "
    + "An imp is connected only to the component passed in its constructor."
    + "(You attempted to bind this imp to {})")

ERR_MSG3 = ("Cannot connect exports to ports Try calling port.connect(export)"
    + " instead. (You attempted to bind this export to {}).")

## typedef uvm_port_component_base uvm_port_list[string]


class UVMPortComponentBase(UVMComponent):
    """
    This class defines an interface for obtaining a port's connectivity lists
    after or during the end_of_elaboration phase.    The sub-class,
    `UVMPortComponent` implements this interface.

    The connectivity lists are returned in the form of handles to objects of this
    type. This allowing traversal of any port's fan-out and fan-in network
    through recursive calls to <get_connected_to> and <get_provided_to>. Each
    port's full name and type name can be retrieved using ~get_full_name~ and
    ~get_type_name~ methods inherited from <uvm_component>.
    """


    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)

    # Function: get_connected_to
    #
    # For a port or export type, this function fills ~list~ with all
    # of the ports, exports and implementations that this port is
    # connected to.
    def get_connected_to(self, port_list):
        pass  # pure virtual

    # Function: get_provided_to
    #
    # For an implementation or export type, this function fills ~list~ with all
    # of the ports, exports and implementations that this port is
    # provides its implementation to.
    def get_provided_to(self, port_list):
        pass  # pure virtual

    def is_port(self):
        """
        Function: is_port

        """
        pass  # pure virtual

    def is_export(self):
        """
        Function: is_export

        """
        pass  # pure virtual

    # Function: is_imp
    #
    # These function determine the type of port. The functions are
    # mutually exclusive; one will return 1 and the other two will
    # return 0.
    def is_imp(self):
        pass  # pure virtual

    def build_phase(self, phase):
        """
        Turn off auto config by not calling build_phase()

        Args:
            phase:
        """
        self.build()  # for backward compat
        return

    def do_task_phase(self, phase):
        pass



class UVMPortComponent(UVMPortComponentBase):
    """
    See description of `UVMPortComponentBase` for information about this class
    """

    def __init__(self, name, parent, port):
        UVMPortComponentBase.__init__(self, name, parent)
        if port is None:
            uvm_report_fatal("Bad usage", "Null handle to port", UVM_NONE)
        self.m_port = port

    def get_type_name(self):
        if self.m_port is None:
            return "uvm_port_component"
        return self.m_port.get_type_name()

    def resolve_bindings(self):
        self.m_port.resolve_bindings()

    def get_port(self):
        """
        Function: get_port

        Retrieve the actual port object that this proxy refers to.
        Returns:
        """
        return self.m_port

    def get_connected_to(self, port_list):
        self.m_port.get_connected_to(port_list)

    def get_provided_to(self, port_list):
        self.m_port.get_provided_to(port_list)

    def is_port(self):
        return self.m_port.is_port()

    def is_export(self):
        return self.m_port.is_export()

    def is_imp(self):
        return self.m_port.is_imp()

## virtual class uvm_port_base #(type IF=uvm_void) extends IF


class UVMPortBase():
    """
    Transaction-level communication between components is handled via its ports,
    exports, and imps, all of which derive from this class.

    The UVM provides a complete set of ports, exports, and imps for the OSCI-
    standard TLM interfaces. They can be found in the ../src/tlm/ directory.

    Just before `UVMComponent.end_of_elaboration_phase`, an internal
    `UVMComponent.resolve_bindings` process occurs, after which each port and
    export holds a list of all imps connected to it via hierarchical connections
    to other ports and exports. In effect, we are collapsing the port's fanout,
    which can span several levels up and down the component hierarchy, into a
    single array held local to the port. Once the list is determined, the port's
    min and max connection settings can be checked and enforced.

    uvm_port_base possesses the properties of components in that they have a
    hierarchical instance path and parent. Because SystemVerilog does not support
    multiple inheritance, uvm_port_base cannot extend both the interface it
    implements and <uvm_component>. Thus, uvm_port_base contains a local instance
    of uvm_component, to which it delegates such commands as get_name,
    get_full_name, and get_parent.
    """




    # Function: new
    #
    # The first two arguments are the normal <uvm_component> constructor
    # arguments.
    #
    # The ~port_type~ can be one of <UVM_PORT>, <UVM_EXPORT>, or
    # <UVM_IMPLEMENTATION>.
    #
    # The ~min_size~ and ~max_size~ specify the minimum and maximum number of
    # implementation (imp) ports that must be connected to this port base by the
    # end of elaboration. Setting ~max_size~ to ~UVM_UNBOUNDED_CONNECTIONS~ sets no
    # maximum, i.e., an unlimited number of connections are allowed.
    #
    # By default, the parent/child relationship of any port being connected to
    # this port is not checked. This can be overridden by configuring the
    # port's ~check_connection_relationships~ bit via ~uvm_config_int::set()~. See
    # <connect> for more information.
    def __init__(self, name, parent, port_type, min_size=0, max_size=1):
        self.m_port_type = port_type
        self.m_min_size    = min_size
        self.m_max_size    = max_size
        self.m_comp = UVMPortComponent(name, parent, self)
        self.m_resolved = False
        self.m_imp_list = {}
        self.m_if_mask = 0
        self.m_def_index = 0
        self.m_provided_by = {}
        self.m_provided_to = {}
        self.m_if = None
        self.m_imp = None
        #if (!uvm_config_int::get(m_comp, "", "check_connection_relationships",tmp))
        #   self.m_comp.set_report_id_action(s_connection_warning_id, UVM_NO_ACTION)

    def get_name(self):
        """ Returns the leaf name of this port. """
        return self.m_comp.get_name()

    def get_full_name(self):
        """ Returns the full hierarchical name of this port. """
        return self.m_comp.get_full_name()


    def get_parent(self):
        """ Returns the handle to this port's parent, or ~null~ if it has no
        parent. """
        return self.m_comp.get_parent()

    # Function: get_comp
    #
    # Returns a handle to the internal proxy component representing this port.
    #
    # Ports are considered components. However, they do not inherit
    # <uvm_component>. Instead, they contain an instance of
    # <uvm_port_component #(PORT)> that serves as a proxy to this port.
    def get_comp(self):
        return self.m_comp

    # Function: get_type_name
    #
    # Returns the type name to this port. Derived port classes must implement
    # this method to return the concrete type. Otherwise, only a generic
    # "uvm_port", "uvm_export" or "uvm_implementation" is returned.
    def get_type_name(self):
        if self.m_port_type == UVM_PORT:
            return "port"
        elif self.m_port_type == UVM_EXPORT:
            return "export"
        else:
            return "implementation"

    def max_size(self):
        """
        Function: max_size

        Returns the maximum number of implementation ports that must
        be connected to this port by the end_of_elaboration phase.
        Returns:
        """
        return self.m_max_size


    def min_size(self):
        """
        Function: min_size

        Returns the minimum number of implementation ports that must
        be connected to this port by the end_of_elaboration phase.
        Returns:
        """
        return self.m_min_size

    # Function: is_unbounded
    #
    # Returns 1 if this port has no maximum on the number of implementation
    # ports this port can connect to. A port is unbounded when the ~max_size~
    # argument in the constructor is specified as ~UVM_UNBOUNDED_CONNECTIONS~.
    def is_unbounded(self):
        return self.m_max_size == UVM_UNBOUNDED_CONNECTIONS

    # Function: is_port

    def is_port(self):
        return self.m_port_type == UVM_PORT

    # Function: is_export

    def is_export(self):
        return self.m_port_type == UVM_EXPORT

    # Function: is_imp
    #
    # Returns 1 if this port is of the type given by the method name,
    # 0 otherwise.
    def is_imp(self):
        return self.m_port_type == UVM_IMPLEMENTATION

    # Function: size
    #
    # Gets the number of implementation ports connected to this port. The value
    # is not valid before the end_of_elaboration phase, as port connections have
    # not yet been resolved.
    def size(self):
        return len(self.m_imp_list)

    def set_if(self, index=0):
        self.m_if = self.get_if(index)
        if self.m_if is not None:
            self.m_def_index = index

    def m_get_if_mask(self):
        return self.m_if_mask

    # Function: set_default_index
    #
    # Sets the default implementation port to use when calling an interface
    # method. This method should only be called on UVM_EXPORT types. The value
    # must not be set before the end_of_elaboration phase, when port connections
    # have not yet been resolved.
    def set_default_index(self, index):
        self.m_def_index = index

    def connect(self, provider):
        """
        Function: connect

        Connects this port to the given `provider` port. The ports must be
        compatible in the following ways

        - Their type parameters must match

        - The `provider`'s interface type (blocking, non-blocking, analysis, etc.)
            must be compatible. Each port has an interface mask that encodes the
            interface(s) it supports. If the bitwise AND of these masks is equal to
            the this port's mask, the requirement is met and the ports are
            compatible. For example, a uvm_blocking_put_port #(T) is compatible with
            a uvm_put_export #(T) and uvm_blocking_put_imp #(T) because the export
            and imp provide the interface required by the uvm_blocking_put_port.

        - Ports of type `UVM_EXPORT` can only connect to other exports or imps.

        - Ports of type `UVM_IMPLEMENTATION` cannot be connected, as they are
            bound to the component that implements the interface at time of
            construction.

        In addition to type-compatibility checks, the relationship between this
        port and the `provider` port will also be checked if the port's
        `check_connection_relationships` configuration has been set. (See `new`
        for more information.)

        Relationships, when enabled, are checked are as follows:

        - If this port is a UVM_PORT type, the `provider` can be a parent port,
            or a sibling export or implementation port.

        - If this port is a `UVM_EXPORT` type, the provider can be a child
            export or implementation port.

        If any relationship check is violated, a warning is issued.

        Note- the `UVMComponent.connect_phase` method is related to but not the same
        as this method. The component's `connect` method is a phase callback where
        port's `connect` method calls are made.
        Args:
            provider:
        """
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        top = cs.get_root()

        #if end_of_elaboration_ph.get_state() == UVM_PHASE_EXECUTING or end_of_elaboration_ph.get_state() == UVM_PHASE_DONE:
        #    self.m_comp.uvm_report_warning("Late Connection",
        #         ("Attempt to connect " + self.get_full_name()
        #             + " (of type " + self.get_type_name()
        #             + ") at or after end_of_elaboration phase. Ignoring."))
        #    return

        if provider is None:
            self.m_comp.uvm_report_error(s_connection_error_id,
                "Cannot connect to null port handle", UVM_NONE)
            return

        if provider == self:
            self.m_comp.uvm_report_error(s_connection_error_id,
               "Cannot connect a port instance to itself", UVM_NONE)
            return

        if (provider.m_if_mask & self.m_if_mask) != self.m_if_mask:
            print(sv.sformatf("provider: %h, m_if_mask: %h", provider.m_if_mask,
                    self.m_if_mask))
            self.m_comp.uvm_report_error(s_connection_error_id,
                 (provider.get_full_name()
                  + " (of type " + provider.get_type_name()
                  + ") doesn't provide the compl interface required of this port (type "
                  + self.get_type_name() + ")"), UVM_NONE)
            return

        # IMP.connect(anything) is illegal
        if self.is_imp() is True:
            parent_name = ""
            if self.m_comp.get_parent() is not None:
                parent_name = self.m_comp.get_full_name()
            self.m_comp.uvm_report_error(s_connection_error_id,
                 ERR_MSG2.format(parent_name, provider.get_full_name()), UVM_NONE)
            return

        # EXPORT.connect(PORT) are illegal
        if self.is_export() is True and provider.is_port() is True:
            self.m_comp.uvm_report_error(s_connection_error_id,
                 ERR_MSG3.format(provider.get_full_name()), UVM_NONE)
            return

        self.m_check_relationship(provider)

        self.m_provided_by[provider.get_full_name()] = provider
        provider.m_provided_to[self.get_full_name()] = self


    indent = ""
    save = ""

    # Function: debug_connected_to
    #
    # The ~debug_connected_to~ method outputs a visual text display of the
    # port/export/imp network to which this port connects (i.e., the port's
    # fanout).
    #
    # This method must not be called before the end_of_elaboration phase, as port
    # connections are not resolved until then.
    def debug_connected_to(self, level=0, max_level=-1):
        sz = 0
        num = 0
        curr_num = 0
        port = None
        # indent = ""

        if level < 0:
            level = 0
        if level == 0:
            UVMPortBase.save = ""
            UVMPortBase.indent = "    "

        if max_level != -1 and level >= max_level:
            return

        num = len(self.m_provided_by)

        if len(self.m_provided_by) != 0:
            for nm in self.m_provided_by:
                port = self.m_provided_by[nm]
                curr_num += 1
                UVMPortBase.save += UVMPortBase.indent + "    | \n"
                UVMPortBase.save += UVMPortBase.indent + "    |_" + nm + " (" + port.get_type_name() + ")\n"
                if num > 1 and curr_num != num:
                    UVMPortBase.indent += "    | "
                else:
                    UVMPortBase.indent += "        "
                port.debug_connected_to(level+1, max_level)
                #indent = indent.substr(0,indent.len()-4-1); TODO

        if level == 0:
            if UVMPortBase.save != "":
                UVMPortBase.save = ("This port's fanout network:\n\n    " + self.get_full_name()
                    + " (" + self.get_type_name() + ")\n" + UVMPortBase.save + "\n")
            if len(self.m_imp_list) == 0:
                from .uvm_coreservice import UVMCoreService
                cs = UVMCoreService.get()
                top = cs.get_root()
                if end_of_elaboration_ph is not None:
                    if (end_of_elaboration_ph.get_state() == UVM_PHASE_EXECUTING or
                            end_of_elaboration_ph.get_state() == UVM_PHASE_DONE):
                        UVMPortBase.save += "    Connected implementations: none\n"
                    else:
                        UVMPortBase.save += "    Connected implementations: not resolved until end-of-elab\n"
            else:
                UVMPortBase.save += "    Resolved implementation list:\n"
                for nm in self.m_imp_list:
                    port = self.m_imp_list[nm]
                    s_sz = str(sz)
                    UVMPortBase.save += (UVMPortBase.indent + s_sz + ": " + nm + " (" +
                        port.get_type_name() + ")\n")
                    sz += 1
            self.m_comp.uvm_report_info("debug_connected_to", UVMPortBase.save)
        return UVMPortBase.save

    # Function: debug_provided_to
    #
    # The ~debug_provided_to~ method outputs a visual display of the port/export
    # network that ultimately connect to this port (i.e., the port's fanin).
    #
    # This method must not be called before the end_of_elaboration phase, as port
    # connections are not resolved until then.
    def debug_provided_to(self, level=0, max_level=-1):
        nm = ""
        num = 0
        curr_num = 0
        port = None

        if level < 0:
            level = 0
        if level == 0:
            UVMPortBase.save = ""
            UVMPortBase.indent = "    "

        if max_level != -1 and level > max_level:
            return

        num = len(self.m_provided_to)

        if num != 0:
            for nm in self.m_provided_to:
                port = self.m_provided_to[nm]
                curr_num += 1
                UVMPortBase.save += UVMPortBase.indent + "    | \n"
                UVMPortBase.save += UVMPortBase.indent + "    |_" + nm + " (" + port.get_type_name() + ")\n"
                if num > 1 and curr_num != num:
                    UVMPortBase.indent += "    | "
                else:
                    UVMPortBase.indent += "        "
                port.debug_provided_to(level+1, max_level)
                # indent = indent.substr(0,indent.len()-4-1); #TODO

        if level == 0:
            if UVMPortBase.save != "":
                UVMPortBase.save = ("This port's fanin network:\n\n    "
                + self.get_full_name() + " (" + self.get_type_name()
                + ")\n" + UVMPortBase.save + "\n")
            if len(self.m_provided_to) == 0:
                UVMPortBase.save += UVMPortBase.indent + "This port has not been bound\n"
            self.m_comp.uvm_report_info("debug_provided_to", UVMPortBase.save)
        return UVMPortBase.save

    # get_connected_to
    # ----------------

    def get_connected_to(self, port_list):
        for name in self.m_provided_by:
            port = self.m_provided_by[name]
            port_list[name] = port.get_comp()

    # get_provided_to
    # ---------------

    def get_provided_to(self, port_list):
        for name in self.m_provided_to:
            port = self.m_provided_to[name]
            port_list[name] = port.get_comp()

    # m_check_relationship
    # --------------------

    def m_check_relationship(self, provider):
        s = ""
        res_from = None
        from_parent = None
        to_parent = None
        from_gparent = None
        to_gparent = None

        # Checks that the connection is between ports that are hierarchically
        # adjacent (up or down one level max, or are siblings),
        # and check for legal direction, requirer.connect(provider).

        # if we're an analysis port, allow connection to anywhere
        if self.get_type_name() == "uvm_analysis_port":
            return 1

        res_from        = self
        from_parent = self.get_parent()
        to_parent   = provider.get_parent()

        # skip check if we have a parentless port
        if from_parent is None or to_parent is None:
            return 1

        from_gparent = from_parent.get_parent()
        to_gparent     = to_parent.get_parent()

        # Connecting port-to-port: CHILD.port.connect(PARENT.port)
        #
        if res_from.is_port() and provider.is_port() and from_gparent != to_parent:
            s = (provider.get_full_name()
                + " (of type " + provider.get_type_name()
                + ") is not up one level of hierarchy from this port. "
                + "A port-to-port connection takes the form "
                + "child_component.child_port.connect(parent_port)")
            self.m_comp.uvm_report_warning(s_connection_warning_id, s, UVM_NONE)
            return 0

        # Connecting port-to-export: SIBLING.port.connect(SIBLING.export)
        # Connecting port-to-imp:        SIBLING.port.connect(SIBLING.imp)
        #
        elif res_from.is_port() and (provider.is_export() or provider.is_imp()) and from_gparent != to_gparent:
            s = (provider.get_full_name()
                + " (of type " + provider.get_type_name()
                + ") is not at the same level of hierarchy as this port. "
                + "A port-to-export connection takes the form "
                + "component1.port.connect(component2.export)")
            self.m_comp.uvm_report_warning(s_connection_warning_id, s, UVM_NONE)
            return 0

        # Connecting export-to-export: PARENT.export.connect(CHILD.export)
        # Connecting export-to-imp:        PARENT.export.connect(CHILD.imp)
        #
        elif res_from.is_export() and (provider.is_export() or provider.is_imp()) and from_parent != to_gparent:
            s = (provider.get_full_name()
                + " (of type " + provider.get_type_name()
                + ") is not down one level of hierarchy from this export. "
                + "An export-to-export or export-to-imp connection takes the form "
                + "parent_export.connect(child_component.child_export)")
            self.m_comp.uvm_report_warning(s_connection_warning_id, s, UVM_NONE)
            return 0
        return 1

    def m_add_list(self, provider):
        """
        m_add_list

        Internal method.
        Args:
            provider:
        """
        sz = ""
        for i in range(0, provider.size()):
            imp = provider.get_if(i)
            if not imp.get_full_name() in self.m_imp_list:
                self.m_imp_list[imp.get_full_name()] = imp

    # Function: resolve_bindings
    #
    # This callback is called just before entering the end_of_elaboration phase.
    # It recurses through each port's fanout to determine all the imp
    # destinations. It then checks against the required min and max connections.
    # After resolution, <size> returns a valid value and <get_if>
    # can be used to access a particular imp.
    #
    # This method is automatically called just before the start of the
    # end_of_elaboration phase. Users should not need to call it directly.
    def resolve_bindings(self):
        if self.m_resolved:  # don't repeat ourselves
            return

        if self.is_imp() is True:
            self.m_imp_list[self.get_full_name()] = self
        else:
            for nm in self.m_provided_by:
                port = self.m_provided_by[nm]
                port.resolve_bindings()
                self.m_add_list(port)

        self.m_resolved = 1

        if self.size() < self.min_size():
            self.m_comp.uvm_report_error(s_connection_error_id,
                "connection count of {} does not meet required minimum of {}"
                .format(self.size(), self.min_size()), UVM_NONE)

        if self.max_size() != UVM_UNBOUNDED_CONNECTIONS and self.size() > self.max_size():
            self.m_comp.uvm_report_error(s_connection_error_id,
                "connection count of {} exceeds maximum of {}".format(
                    self.size(), self.max_size()), UVM_NONE)

        if self.size() > 0:
            self.set_if(0)

    # Function: get_if
    #
    # Returns the implementation (imp) port at the given index from the array of
    # imps this port is connected to. Use <size> to get the valid range for index.
    # This method can only be called at the end_of_elaboration phase or after, as
    # port connections are not resolved before then.
    def get_if(self, index=0):
        s = ""
        if self.size() == 0:
            self.m_comp.uvm_report_warning("get_if",
                "Port size is zero; cannot get interface at any index", UVM_NONE)
            return None
        if index < 0 or index >= self.size():
            s = "Index {} out of range [0,{}]".format(index, self.size()-1)
            self.m_comp.uvm_report_warning(s_connection_error_id, s, UVM_NONE)
            return None
        for nm in self.m_imp_list:
            if index == 0:
                return self.m_imp_list[nm]
            index -= 1
