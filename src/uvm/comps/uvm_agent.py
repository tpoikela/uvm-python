#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2011 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela (tpoikela)
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

from ..base.uvm_object_globals import UVM_ACTIVE
from ..base.uvm_component import UVMComponent
from ..base.uvm_resource import UVMResourcePool
from ..base.uvm_queue import UVMQueue



class UVMAgent(UVMComponent):
    """
    The `UVMAgent` virtual class should be used as the base class for the user-
    defined agents. Deriving from `UVMAgent` will allow you to distinguish agents
    from other component types also using its inheritance. Such agents will
    automatically inherit features that may be added to `UVMAgent` in the future.
    
    While an agent's build function, inherited from `UVMComponent`, can be
    implemented to define any agent topology, an agent typically contains three
    subcomponents: a driver, sequencer, and monitor. If the agent is active,
    subtypes should contain all three subcomponents. If the agent is passive,
    subtypes should contain only the monitor.
    """

    # Function: new
    #
    # Creates and initializes an instance of this class using the normal
    # constructor arguments for <uvm_component>: ~name~ is the name of the
    # instance, and ~parent~ is the handle to the hierarchical parent, if any.
    #
    # The int configuration parameter is_active is used to identify whether this
    # agent should be acting in active or passive mode. This parameter can
    # be set by doing:
    #
    #| uvm_config_int::set(this, "<relative_path_to_agent>,
    #|   "is_active", UVM_ACTIVE)
    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.is_active = UVM_ACTIVE


    def build_phase(self, phase):
        self.active = 0
        rp = None  # uvm_resource_pool
        rq = UVMQueue()  # uvm_resource_types::rsrc_q_t

        UVMComponent.build_phase(self, phase)
        # is_active is treated as if it were declared via `uvm_field_enum,
        # which means it matches against uvm_active_passive_enum, int,
        # int unsigned, uvm_integral_t, uvm_bitstream_t, and string.
        rp = UVMResourcePool.get()
        rq = rp.lookup_name(self.get_full_name(), "is_active", None, 0)
        rq = UVMResourcePool.sort_by_precedence(rq)
        for i in range(len(rq)):
            rsrc = rq[i]  # uvm_resource_base
            rap = rsrc
            self.is_active = rap.read(self)

    type_name = "uvm_agent"

    def get_type_name(self):
        return UVMAgent.type_name

    # Function: get_is_active
    #
    # Returns UVM_ACTIVE is the agent is acting as an active agent and
    # UVM_PASSIVE if it is acting as a passive agent. The default implementation
    # is to just return the is_active flag, but the component developer may
    # override this behavior if a more complex algorithm is needed to determine
    # the active/passive nature of the agent.
    def get_is_active(self):
        return self.is_active
