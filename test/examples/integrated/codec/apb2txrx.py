#// 
#// -------------------------------------------------------------
#//    Copyright 2011 Synopsys, Inc.
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

from uvm import *
from apb.apb_rw import *
from vip import *


class apb2txrx(UVMComponent):
    #
    #   uvm_analysis_imp#(apb_rw, apb2txrx) apb
    #
    #   uvm_analysis_port#(vip_tr) tx_ap
    #   uvm_analysis_port#(vip_tr) rx_ap
    #

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.apb   = UVMAnalysisImp("apb", self)
        self.tx_ap = UVMAnalysisPort("tx_ap", self)
        self.rx_ap = UVMAnalysisPort("rx_ap", self)
        self.radd =  0x0100
        self.wadd =  0x0100


    def build_phase(self, phase):
        arr = []
        if UVMConfigDb.get(self, "", "radd", arr):
            self.radd = arr[0]
        arr = []
        if UVMConfigDb.get(self, "", "wadd", arr):
            self.wadd = arr[0]


    def write(self, rw):
        # R from 'radd' are Rx characters
        if (rw.kind == apb_rw.READ and rw.addr == self.radd):
            tr = vip_tr.type_id.create("rx",None,self.get_full_name())
            tr.chr = rw.data
            self.rx_ap.write(tr)
        
        # W from 'wadd' are Tx characters
        if (rw.kind == apb_rw.WRITE  and  rw.addr == self.wadd):
            tr = vip_tr.type_id.create("tx",None,self.get_full_name())
            tr.chr = rw.data
            self.tx_ap.write(tr)


uvm_component_utils(apb2txrx)
