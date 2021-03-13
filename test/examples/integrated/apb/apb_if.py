#//
#// -------------------------------------------------------------
#//    Copyright 2004-2011 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2010 Cadence Design Systems, Inc.
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//

import cocotb
from cocotb.triggers import *

from uvm.base.sv import sv_if


class apb_if(sv_if):
    #   wire [31:0] paddr
    #   wire        psel
    #   wire        penable
    #   wire        pwrite
    #   wire [31:0] prdata
    #   wire [31:0] pwdata

    def __init__(self, dut, bus_map=None, name="apb"):
        if bus_map is None:
            bus_map = {"clk": "pclk", "psel": "psel", "penable": "penable",
                    "pwrite": "pwrite", "prdata": "prdata", "pwdata": "pwdata",
                    "paddr": "paddr"}
        super().__init__(dut, name, bus_map)
        self.rst = dut.rst


    
    async def start(self):
        await Timer(0)

    #   clocking mck @(posedge pclk)
    #      output paddr, psel, penable, pwrite, pwdata
    #      input  prdata
    #
    #      sequence at_posedge
    #         1
    #      endsequence : at_posedge
    #   endclocking: mck
    #
    #   clocking sck @(posedge pclk)
    #      input  paddr, psel, penable, pwrite, pwdata
    #      output prdata
    #
    #      sequence at_posedge_; // FIXME todo review
    #         1
    #      endsequence : at_posedge_
    #   endclocking: sck
    #
    #   clocking pck @(posedge pclk)
    #      input paddr, psel, penable, pwrite, prdata, pwdata
    #   endclocking: pck
    #
    #   modport master(clocking mck)
    #   modport slave(clocking sck)
    #   modport passive(clocking pck)
    #
    #endinterface: apb_if
    #
    #`endif
