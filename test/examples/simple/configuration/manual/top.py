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

from uvm import (UVMConfigDb, uvm_default_table_printer, uvm_default_printer,
    uvm_top, run_test)

from my_env_pkg import my_env


@cocotb.test()
async def module_top(dut):
    #  my_env topenv
    uvm_default_printer = uvm_default_table_printer
    uvm_top.enable_print_topology = 1

    # set configuration prior to creating the environment
    UVMConfigDb.set(None, "topenv.*.u1", "v", 30)
    UVMConfigDb.set(None, "topenv.inst2.u1", "v", 10)
    UVMConfigDb.set(None, "topenv.*", "debug", 1)
    UVMConfigDb.set(None, "*", "myaa[foo]", "hi")
    UVMConfigDb.set(None, "*", "myaa[bar]", "bye")
    UVMConfigDb.set(None, "*", "myaa[foobar]", "howdy")
    UVMConfigDb.set(None, "topenv.inst1.u1", "myaa[foo]", "boo")
    UVMConfigDb.set(None, "topenv.inst1.u1", "myaa[foobar]", "boobah")

    topenv = my_env("topenv", uvm_top)
    UVMConfigDb.set(topenv, "*.u1", "v", 30)
    UVMConfigDb.set(topenv, "inst2.u1", "v", 10)
    UVMConfigDb.set(topenv, "*", "debug", 1)
    UVMConfigDb.set(topenv, "*", "myaa[foo]", "hi")
    UVMConfigDb.set(topenv, "*", "myaa[bar]", "bye")
    UVMConfigDb.set(topenv, "*", "myaa[foobar]", "howdy")
    UVMConfigDb.set(topenv, "inst1.u1", "myaa[foo]", "boo")
    UVMConfigDb.set(topenv, "inst1.u1", "myaa[foobar]", "boobah")

    UVMConfigDb.set(uvm_top, "topenv", "should_match", 1234)

    await run_test()
