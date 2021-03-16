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


class vip_tx_if():

    def __init__(self, clk, Tx):
        self.clk = clk
        self.Tx = Tx

class vip_rx_if():

    def __init__(self, clk, Rx):
        self.clk = clk
        self.Rx = Rx

class vip_if():

    def __init__(self, clk, Tx, Rx):
        self.clk = clk
        self.Tx = Tx
        self.Rx = Rx

        self.tx = vip_tx_if(self.clk, self.Tx)
        self.rx = vip_rx_if(self.clk, self.Rx)
        self.tx_mon = vip_rx_if(self.clk, self.Tx)
