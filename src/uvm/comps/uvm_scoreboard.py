#//
#//-----------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela
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

from ..base.uvm_component import UVMComponent


class UVMScoreboard(UVMComponent):
    """
    The `UVMScoreboard` class should be used as the base class for
    user-defined scoreboards.

    Deriving from `UVMScoreboard` will allow you to distinguish scoreboards from
    other component types inheriting directly from `UVMComponent`. Such
    scoreboards will automatically inherit and benefit from features that may be
    added to `UVMScoreboard` in the future.
    """

    #  // Function: new
    #  //
    #  // Creates and initializes an instance of this class using the normal
    #  // constructor arguments for `UVMComponent`: ~name~ is the name of the
    #  // instance, and ~parent~ is the handle to the hierarchical parent, if any.
    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)

    type_name = "uvm_scoreboard"

    def get_type_name(self):
        return UVMScoreboard.type_name
