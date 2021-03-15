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


class vip_tr(UVMSequenceItem):

    def __init__(self, name="vip_tr"):
        super().__init__(name)
        self.chr = 0x0
        self.rand('chr', range(0, 256))


    def convert2string(self):
        return sv.sformatf("0x%0h", self.chr)


uvm_object_utils_begin(vip_tr)
uvm_field_int('vip_tr', UVM_ALL_ON)
uvm_object_utils_end(vip_tr)
