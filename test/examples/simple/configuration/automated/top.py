#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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
#//----------------------------------------------------------------------

import cocotb
from uvm import (UVMConfigDb, run_test, UVMObject)
from my_env_pkg import my_env

#//Begindoc: Automated Configuration
#//This test will focus on testing auto configurations using the uvm_component related config methods.


#//Walk through the test:
#//Configuration settings are stored in each component instance. 

#//Then a search is made to verify that those components full names match the field_name that had been set.


@cocotb.test()
async def module_top(dut):
    obj = UVMObject("my_conf_obj")

    # set configuration prior to creating the environment
    UVMConfigDb.set(None, "topenv.*.u1", "v", 30)
    UVMConfigDb.set(None, "topenv.inst2.u1", "v", 10)
    UVMConfigDb.set(None, "*", "recording_detail", 0)
    UVMConfigDb.set(None, "*", "myaa[foo]", "hi")
    UVMConfigDb.set(None, "*", "myaa[bar]", "bye")
    UVMConfigDb.set(None, "*", "myaa[foobar]", "howdy")
    UVMConfigDb.set(None, "topenv.inst1.u1", "myaa[foo]", "boo")
    UVMConfigDb.set(None, "topenv.inst1.u1", "myaa[foobar]", "boobah")
    UVMConfigDb.set(None, "topenv.inst1.u1", "my_conf_obj", obj)
    UVMConfigDb.set(None, "topenv.inst1.u1", "tag", 'I am tagged')
    topenv = my_env("topenv", None)
    await run_test()
