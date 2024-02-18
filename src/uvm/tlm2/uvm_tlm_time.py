#//----------------------------------------------------------------------
#// Copyright 2011-2014 Mentor Graphics Corporation
#// Copyright 2014 Semifore
#// Copyright 2014 Intel Corporation
#// Copyright 2010-2017 Synopsys, Inc.
#// Copyright 2011-2018 Cadence Design Systems, Inc.
#// Copyright 2014-2018 NVIDIA Corporation
#// Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

from ..macros.uvm_message_defines import (uvm_error, uvm_fatal)

#// CLASS -- NODOCS -- UVMTLMTime
#// Canonical time type that can be used in different timescales
#//
#// This time type is used to represent time values in a canonical
#// form that can bridge initiators and targets located in different
#// timescales and time precisions.
#//
#// For a detailed explanation of the purpose for this class,
#// see <Why is this necessary>.


class UVMTime:

    #   static local real m_resolution = 1.0e-12; // ps by default
    m_resolution = 1.0e-12
    #   local time m_time;  // Number of 'm_res' time units,
    #   local string m_name
    #
    #   // Function -- NODOCS -- set_time_resolution
    #   // Set the default canonical time resolution.
    #   //
    #   // Must be a power of 10.
    #   // When co-simulating with SystemC, it is recommended
    #   // that default canonical time resolution be set to the
    #   // SystemC time resolution.
    #   //
    #   // By default, the default resolution is 1.0e-12 (ps)
    #   //

    @classmethod
    def set_time_resolution(cls, res):
        # // Actually, it does not *really* need to be a power of 10.
        cls.m_resolution = res


    #   // Function -- NODOCS -- new
    #   // Create a new canonical time value.
    #   //
    #   // The new value is initialized to 0.
    #   // If a resolution is not specified,
    #   // the default resolution,
    #   // as specified by <set_time_resolution()>,
    #   // is used.

    def __init__(self, name="UVMTLMTime", res=0):
        self.m_name = name
        self.m_res = res
        self.m_time = 0
        if res == 0:
            self.m_res = UVMTime.m_resolution
        self.reset()

    #   // Function -- NODOCS -- get_name
    #   // Return the name of this instance
    #   //
    #   def string get_name(self):
    #      return m_name
    #   endfunction
    #
    #
    #   // Function -- NODOCS -- reset
    #   // Reset the value to 0
    def reset(self):
        self.m_time = 0

    #   // Scale a timescaled value to 'm_res' units,
    #   // the specified scale
    def to_m_res(self, t, scaled, secs):
        # ToDo: Check resolution
        return (t/scaled) * (secs/self.m_res)  # cast to 'real' removed
    #   endfunction


    #   // Function -- NODOCS -- get_realtime
    #   // Return the current canonical time value,
    #   // scaled for the caller's timescale
    #   //
    #   // ~scaled~ must be a time literal value that corresponds
    #   // to the number of seconds specified in ~secs~ (1ns by default).
    #   // It must be a time literal value that is greater or equal
    #   // to the current timescale.
    #   //
    #   //| #(delay.get_realtime(1ns));
    #   //| #(delay.get_realtime(1fs, 1.0e-15));
    #   //
    def get_realtime(self, scaled, secs=1.0e-9):
        return self.m_time * float(scaled) * self.m_res / secs

    #   // Function -- NODOCS -- incr
    #   // Increment the time value by the specified number of scaled time unit
    #   //
    #   // ~t~ is a time value expressed in the scale and precision
    #   // of the caller.
    #   // ~scaled~ must be a time literal value that corresponds
    #   // to the number of seconds specified in ~secs~ (1ns by default).
    #   // It must be a time literal value that is greater or equal
    #   // to the current timescale.
    #   //
    #   //| delay.incr(1.5ns, 1ns);
    #   //| delay.incr(1.5ns, 1ps, 1.0e-12);
    #   //
    def incr(self, t, scaled, secs=1.0e-9):
        if t < 0.0:
            uvm_error("UVM/TLM/TIMENEG", "Cannot increment UVMTLMTime variable "
                    + self.m_name + " by a negative value")
            return

        if scaled == 0:
            uvm_fatal("UVM/TLM/BADSCALE",
                "UVMTLMTime::incr() called with a scaled time literal that is smaller than the current timescale")


        self.m_time += self.to_m_res(t, scaled, secs)

    #
    #   // Function -- NODOCS -- decr
    #   // Decrement the time value by the specified number of scaled time unit
    #   //
    #   // ~t~ is a time value expressed in the scale and precision
    #   // of the caller.
    #   // ~scaled~ must be a time literal value that corresponds
    #   // to the number of seconds specified in ~secs~ (1ns by default).
    #   // It must be a time literal value that is greater or equal
    #   // to the current timescale.
    #   //
    #   //| delay.decr(200ps, 1ns);
    #   //
    #   def void decr(self,real t, time scaled, real secs):
    #      if (t < 0.0):
    #         `uvm_error("UVM/TLM/TIMENEG", {"Cannot decrement UVMTLMTime variable ", m_name, " by a negative value"})
    #         return
    #      end
    #      if (scaled == 0):
    #         `uvm_fatal("UVM/TLM/BADSCALE",
    #                    "UVMTLMTime::decr() called with a scaled time literal that is smaller than the current timescale")
    #      end
    #
    #      m_time -= to_m_res(t, scaled, secs)
    #
    #      if (m_time < 0.0):
    #         `uvm_error("UVM/TLM/TOODECR", {"Cannot decrement UVMTLMTime variable ", m_name, " to a negative value"})
    #         reset()
    #      end
    #   endfunction
    #
    #
    #   // Function -- NODOCS -- get_abstime
    #   // Return the current canonical time value,
    #   // in the number of specified time unit, regardless of the
    #   // current timescale of the caller.
    #   //
    #   // ~secs~ is the number of seconds in the desired time unit
    #   // e.g. 1e-9 for nanoseconds.
    #   //
    #   //| $write("%.3f ps\n", delay.get_abstime(1e-12));
    #   //
    #   def real get_abstime(self,real secs):
    #      return m_time*m_res/secs
    #   endfunction
    #
    #
    #   // Function -- NODOCS -- set_abstime
    #   // Set the current canonical time value,
    #   // to the number of specified time unit, regardless of the
    #   // current timescale of the caller.
    #   //
    #   // ~secs~ is the number of seconds in the time unit in the value ~t~
    #   // e.g. 1e-9 for nanoseconds.
    #   //
    #   //| delay.set_abstime(1.5, 1e-12));
    #   //
    #   def void set_abstime(self,real t, real secs):
    #      m_time = t*secs/m_res
    #   endfunction
    #endclass

UVMTLMTime = UVMTime

#// Group -- NODOCS -- Why is this necessary
#//
#// Integers are not sufficient, on their own,
#// to represent time without any ambiguity:
#// you need to know the scale of that integer value.
#// That scale is information conveyed outside of that integer.
#// In SystemVerilog, it is based on the timescale
#// that was active when the code was compiled.
#// SystemVerilog properly scales time literals, but not integer values.
#// That's because it does not know the difference between an integer
#// that carries an integer value and an integer that carries a time value.
#// The 'time' variables are simply 64-bit integers,
#// they are not scaled back and forth to the underlying precision.
#//
#//| `timescale 1ns/1ps
#//|
#//| module m();
#//|
#//| time t;
#//|
#//| initial
#//| begin
#//|    #1.5;
#//|    $write("T=%f ns (1.5)\n", $realtime());
#//|    t = 1.5;
#//|    #t;
#//|    $write("T=%f ns (3.0)\n", $realtime());
#//|    #10ps;
#//|    $write("T=%f ns (3.010)\n", $realtime());
#//|    t = 10ps;
#//|    #t;
#//|    $write("T=%f ns (3.020)\n", $realtime());
#//| end
#//| endmodule
#//
#// yields
#//
#//| T=1.500000 ns (1.5)
#//| T=3.500000 ns (3.0)
#//| T=3.510000 ns (3.010)
#//| T=3.510000 ns (3.020)
#//
#// Within SystemVerilog, we have to worry about
#// - different time scale
#// - different time precision
#//
#// Because each endpoint in a socket
#// could be coded in different packages
#// and thus be executing under different timescale directives,
#// a simple integer cannot be used to exchange time information
#// across a socket.
#//
#// For example
#//
#//| `timescale 1ns/1ps
#//|
#//| package a_pkg;
#//|
#//| class a;
#//|    function void f(inout time t);
#//|       t += 10ns;
#//|    endfunction
#//| endclass
#//|
#//| endpackage
#//|
#//|
#//| `timescale 1ps/1ps
#//|
#//| program p;
#//|
#//| import a_pkg::*;
#//|
#//| time t;
#//|
#//| initial
#//| begin
#//|    a A = new;
#//|    A.f(t);
#//|    #t;
#//|    $write("T=%0d ps (10,000)\n", $realtime());
#//| end
#//| endprogram
#//
#// yields
#//
#//| T=10 ps (10,000)
#//
#// Scaling is needed every time you make a procedural call
#// to code that may interpret a time value in a different timescale.
#//
#// Using the UVMTLMTime type
#//
#//| `timescale 1ns/1ps
#//|
#//|    package a_pkg;
#//|
#//| import uvm_pkg::*;
#//|
#//| class a;
#//|    function void f(UVMTLMTime t);
#//|       t.incr(10ns, 1ns);
#//|    endfunction
#//| endclass
#//|
#//| endpackage
#//|
#//|
#//| `timescale 1ps/1ps
#//|
#//| program p;
#//|
#//| import uvm_pkg::*;
#//| import a_pkg::*;
#//|
#//| UVMTLMTime t = new;
#//|
#//| initial
#//|    begin
#//|       a A = new;
#//|       A.f(t);
#//|       #(t.get_realtime(1ns));
#//|       $write("T=%0d ps (10,000)\n", $realtime());
#//| end
#//| endprogram
#//
#// yields
#//
#//| T=10000 ps (10,000)
#//
#// A similar procedure is required when crossing any simulator
#// or language boundary,
#// such as interfacing between SystemVerilog and SystemC.
