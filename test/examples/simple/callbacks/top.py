#//------------------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the "License"); you may not
#//   use this file except in compliance with the License.  You may obtain a copy
#//   of the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in writing, software
#//   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#//   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
#//   License for the specific language governing permissions and limitations
#//   under the License.
#//------------------------------------------------------------------------------


#//------------------------------------------------------------------------------
#// Title: Typical Callback Application
#//
#// This example demonstrates callback usage. The component developer defines a
#// driver and driver-specific callback class. The callback class defines the
#// hooks available for users to override. The component using the callbacks
#// (i.e. calling the callback methods) also defines corresponding virtual
#// methods for each callback hook. The developer implements each virtual methods
#// to call the corresponding callback method in all registered callback objects
#// using default algorithm. The end-user may then define either a callback or
#// driver subtype to extend driver behavior.
#//------------------------------------------------------------------------------


#//------------------------------------------------------------------------------
#//
#// Group: Component Developer Use Model
#//
#//------------------------------------------------------------------------------
#// Component developers defines transaction, driver, and callback classes.
#//------------------------------------------------------------------------------

import cocotb
from cocotb.triggers import Timer

from uvm.base.uvm_transaction import UVMTransaction
from uvm.base.uvm_callback import (UVMCallback, UVMCallbacks)
from uvm.base.uvm_component import *
from uvm.base.sv import sv
from uvm.base.uvm_report_server import UVMReportServer
from uvm.macros import *
from uvm.tlm1 import *

#//------------------------------------------------------------------------------
#//
#// CLASS: bus_tr
#//
#// A basic bus transaction.
#//------------------------------------------------------------------------------


class bus_tr(UVMTransaction):

    def __init__(self, name='trans'):
        super().__init__(name)
        self.addr = 0
        self.rand('addr', range(0, (1 << 32) - 1))
        self.data = 0
        self.rand('data', range(0, (1 << 32) - 1))

    def convert2string(self):
        return sv.sformatf("addr=%0h data=%0h", self.addr, self.data)


#//------------------------------------------------------------------------------
#//
#// CLASS: bus_driver_cb
#//
#//------------------------------------------------------------------------------
#// The callback class defines an interface consisting of one or more function
#// or task prototypes. The signatures of each method have no restrictions.
#// The component developer knows best the intended semantic of multiple
#// registered callbacks. Thus the algorithm for traversal the callback queue
#// should reside in the callback class itself. We could provide convenience
#// macros that implement the most common traversal methods, such as sequential
#// in-order execution.
#//------------------------------------------------------------------------------


class bus_driver_cb(UVMCallback):

    def trans_received(self, driver, tr):
        return 0

    #@cocotb.coroutine TODO fix this
    async def trans_executed(self, driver, tr):
        await Timer(0, "NS")

    def __init__(self, name="bus_driver_cb_inst"):
        super().__init__(name)

    type_name = "bus_driver_cb"

    def get_type_name(self):
        return bus_driver_cb.type_name


#//------------------------------------------------------------------------------
#//
#// CLASS: bus_driver
#//
#//------------------------------------------------------------------------------
#// With the following implementation of bus_driver, users can implement
#// the callback "hooks" by either...
#//
#// - extending bus_driver and overriding one or more of the virtual
#//   methods, trans_received or trans_executed. Then, configure the
#//   factory to use the new type via a type or instance override.
#//
#// - extending bus_driver_cb and overriding one or more of the virtual
#//   methods, trans_received or trans_executed. Then, register an
#//   instance of the new callback type with an instance of bus_driver.
#//   This requires access to the handle of the bus_driver.
#//------------------------------------------------------------------------------


class bus_driver(UVMComponent):

    #  uvm_blocking_put_imp #(bus_tr,bus_driver) in_port

    #
    def __init__(self, name, parent=None):
        super().__init__(name,parent)
        self.in_port = UVMBlockingPutImp("in",self)

    type_name = "bus_driver"

    def get_type_name(self):
        return bus_driver.type_name

    def trans_received(self, tr):
        uvm_do_callbacks_exit_on(self,bus_driver_cb, 'trans_received', 1, self, tr)


    
    async def trans_executed(self, tr):
        await Timer(0, "NS")
        return uvm_do_callbacks(self, bus_driver_cb, 'trans_executed', self, tr)

    
    async def put(self, t):
        uvm_report_info("bus_tr received",t.convert2string())
        if self.trans_received(t) is False:
            uvm_info("bus_tr dropped", "user callback indicated DROPPED\n")
            return

        await Timer(100, "NS")
        await self.trans_executed(t)
        uvm_info("bus_tr executed", t.convert2string() + "\n", UVM_LOW)


uvm_register_cb(bus_driver, bus_driver_cb)


#//------------------------------------------------------------------------------
#//
#// Group: End-User Use Model
#//
#//------------------------------------------------------------------------------
#// The end-user simply needs to extend the callback base class, overriding any or
#// all of the prototypes provided in the developer-supplied callback interface.
#// Then, register an instance of the callback class with any object designed to
#// use the base callback type.
#//------------------------------------------------------------------------------




#//------------------------------------------------------------------------------
#//
#// CLASS: my_bus_driver_cb
#//
#//------------------------------------------------------------------------------
#// This class defines a subtype of the driver developer's base callback class.
#// In this case, both available driver callback methods are defined. The
#// ~trans_received~ method randomly chooses whether to return 0 or 1. When 1,
#// the driver will "drop" the received transaction.
#//------------------------------------------------------------------------------


class my_bus_driver_cb(bus_driver_cb):
    drop = 0

    def __init__(self, name="bus_driver_cb_inst"):
        super().__init__(name)

    def trans_received(self, driver, tr):
        #static bit drop = 0
        driver.uvm_report_info("trans_received_cb",
          "  bus_driver=" + driver.get_full_name() + " tr=" + tr.convert2string())
        my_bus_driver_cb.drop = 1 - my_bus_driver_cb.drop
        return my_bus_driver_cb.drop

    #@cocotb.coroutine
    #@cocotb.coroutine TODO fix this
    def trans_executed(self, driver, tr):
        driver.uvm_report_info("trans_executed_cb",
            "  bus_driver=" + driver.get_full_name() + " tr=" + tr.convert2string())

    def get_type_name(self):
        return "my_bus_driver_cb"

#//------------------------------------------------------------------------------
#//
#// CLASS: my_bus_driver_cb2
#//
#//------------------------------------------------------------------------------
#// This class defines a subtype of the driver developer's base callback class.
#// In this case, only one of the two available methods are defined.
#//------------------------------------------------------------------------------


class my_bus_driver_cb2(bus_driver_cb):

    def __init__(self, name="bus_driver_cb_inst"):
        super().__init__(name)


    #@cocotb.coroutine TODO fix this
    def trans_executed(self, driver, tr):
        driver.uvm_report_info("trans_executed_cb2",
            "  bus_driver=" + driver.get_full_name() + " tr=" + tr.convert2string())

    def get_type_name(self):
        return "my_bus_driver_cb2"


#//------------------------------------------------------------------------------
#//
#// MODULE: top
#//
#//------------------------------------------------------------------------------
#// In this simple example, we don't build a complete environment, but this does
#// not detract from the example's purpose. In the top module, we instantiate
#// the bus_driver, and one instance each of our custom callback classes.
#// To register the callbacks with the driver, we get the global callback pool
#// that is typed to our specific driver-callback combination. We associate
#// (register) the callback objects with driver using the callback pool's
#// ~add_cb~ method. After calling ~display~ just to show that the
#// registration was successful, we push several transactions into the driver.
#// Our custom callbacks get called as the driver receives each transaction.
#//------------------------------------------------------------------------------

@cocotb.test()
async def module_top(dut):
    tr     = bus_tr()
    driver = bus_driver("driver")
    cb1    = my_bus_driver_cb("cb1")
    cb2    = my_bus_driver_cb2("cb2")

    UVMCallbacks.add(driver,cb1)
    UVMCallbacks.add(driver,cb2)
    UVMCallbacks.display()

    for i in range(5):
        tr.addr = i
        tr.data = 6-i
        await driver.in_port.put(tr)

    svr = UVMReportServer.get_server()
    svr.report_summarize()
