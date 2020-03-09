#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
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
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#------------------------------------------------------------------------------

from ..base.uvm_component import UVMComponent



class UVMEnv(UVMComponent):
    """
    The base class for hierarchical containers of other components that
    together comprise a complete environment. The environment may
    initially consist of the entire testbench. Later, it can be reused as
    a sub-environment in even larger system-level environments.
    """

    # Function: new
    #
    # Creates and initializes an instance of this class using the normal
    # constructor arguments for `UVMComponent`: ~name~ is the name of the
    # instance, and ~parent~ is the handle to the hierarchical parent, if any.
    def __init__(self, name="env", parent=None):
        UVMComponent.__init__(self, name, parent)

    type_name = "uvm_env"

    def get_type_name(self):
        return UVMEnv.type_name
