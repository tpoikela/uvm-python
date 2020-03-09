#
#------------------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010 Synopsys, Inc.
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
from ..tlm1.uvm_sqr_connections import UVMSeqItemPullPort
from ..tlm1.uvm_analysis_port import UVMAnalysisPort


class UVMDriver(UVMComponent):
    """
    The base class for drivers that initiate requests for new transactions via
    a uvm_seq_item_pull_port. The ports are typically connected to the exports of
    an appropriate sequencer component.

    This driver operates in pull mode. Its ports are typically connected to the
    corresponding exports in a pull sequencer as follows:

    .. code-block:: python
        driver.seq_item_port.connect(sequencer.seq_item_export);
        driver.rsp_port.connect(sequencer.rsp_export);

    The ~rsp_port~ needs connecting only if the driver will use it to write
    responses to the analysis export in the sequencer.

    :ivar UVMSeqItemPullPort seq_item_port: Derived driver classes should use
        this port to request items from the sequencer. They may also use it to
        send responses back.

    :ivar UVMAnalysisPort rst_port: This port provides an alternate way of
        sending responses back to the originating sequencer. Which port to
        use depends on which export the sequencer provides for connection.
    """



    #uvm_analysis_port #(RSP) rsp_port;

    # Function: new
    #
    # Creates and initializes an instance of this class using the normal
    # constructor arguments for <uvm_component>: ~name~ is the name of the
    # instance, and ~parent~ is the handle to the hierarchical parent, if any.
    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.seq_item_port    = UVMSeqItemPullPort("seq_item_port", self)
        self.rsp_port         = UVMAnalysisPort("rsp_port", self)
        self.seq_item_prod_if = self.seq_item_port
        self.req = None
        self.rsp = None

    type_name = "uvm_driver #(REQ,RSP)"

    def get_type_name(self):
        return UVMDriver.type_name
