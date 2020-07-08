#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
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
#//------------------------------------------------------------------------------
"""
Title: Comparators

The following classes define comparators for objects and built-in types.
"""

from ..base.uvm_component import UVMComponent
from ..base.uvm_object_globals import UVM_MEDIUM
from ..base.sv import sv
from ..macros import uvm_component_utils, uvm_error, uvm_info
from ..tlm1 import UVMAnalysisExport, UVMAnalysisPort, UVMTLMAnalysisFIFO
from .uvm_pair import UVMBuiltInPair, UVMClassPair
from .uvm_policies import (UVMBuiltInConverter, UVMBuiltInComp,
    UVMClassConverter, UVMClassComp)


class UVMInOrderComparator(UVMComponent):
    """
    CLASS: UVMInOrderComparator #(T,comp_type,convert,pair_type)

    Compares two streams of data objects of the type parameter, T.
    These transactions may either be classes or built-in types. To be
    successfully compared, the two streams of data must be in the same order.
    Apart from that, there are no assumptions made about the relative timing of
    the two streams of data.

    Type parameters

      T       - Specifies the type of transactions to be compared.

      comp_type - A policy class to compare the two
                  transaction streams. It must provide the static method
                  "function bit comp(T a, T b)" which returns ~TRUE~
                  if ~a~ and ~b~ are the same.

      convert - A policy class to convert the transactions being compared
                to a string. It must provide the static method
                "function string convert2string(T a)".

     pair_type - A policy class to allow pairs of transactions to be handled as
                 a single <uvm_object> type.

    Built in types (such as ints, bits, logic, and structs) can be compared using
    the default values for comp_type, convert, and pair_type. For convenience,
    you can use the subtype, <UVMInOrderBuiltInComparator #(T)>
    for built-in types.

    When T is a `UVMObject`, you can use the convenience subtype
    `UVMInOrderClassComparator`.

    Comparisons are commutative, meaning it does not matter which data stream is
    connected to which export, before_export or after_export.

    Comparisons are done in order and as soon as a transaction is received from
    both streams. Internal fifos are used to buffer incoming transactions on one
    stream until a transaction to compare arrives on the other stream.
    """


    #  #( type T = int ,
    #     type comp_type = uvm_built_in_comp #( T ) ,
    #     type convert = uvm_built_in_converter #( T ) ,
    #     type pair_type = uvm_built_in_pair #( T ) )
    #    extends uvm_component
    #

    type_name = "UVMInOrderComparator"

    #  // Port: before_export
    #  //
    #  // The export to which one stream of data is written. The port must be
    #  // connected to an analysis port that will provide such data.
    #
    #  uvm_analysis_export #(T) before_export


    #  // Port: after_export
    #  //
    #  // The export to which the other stream of data is written. The port must be
    #  // connected to an analysis port that will provide such data.
    #
    #  uvm_analysis_export #(T) after_export


    #  // Port: pair_ap
    #  //
    #  // The comparator sends out pairs of transactions across this analysis port.
    #  // Both matched and unmatched pairs are published via a pair_type objects.
    #  // Any connected analysis export(s) will receive these transaction pairs.
    #
    #  uvm_analysis_port   #(pair_type) pair_ap


    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.PairType = UVMBuiltInPair
        self.Convert = UVMBuiltInConverter
        self.CompType = UVMBuiltInComp

        self.before_export = UVMAnalysisExport("before_export", self)
        self.after_export  = UVMAnalysisExport("after_export", self)
        self.pair_ap       = UVMAnalysisPort("pair_ap", self)

        self.m_before_fifo = UVMTLMAnalysisFIFO("before", self)
        self.m_after_fifo  = UVMTLMAnalysisFIFO("after", self)
        self.m_matches = 0
        self.m_mismatches = 0


    def get_type_name(self):
        return UVMInOrderComparator.type_name


    def connect_phase(self, phase):
        self.before_export.connect(self.m_before_fifo.analysis_export)
        self.after_export.connect(self.m_after_fifo.analysis_export)



    #  // Task- run_phase
    #  //
    #  // Internal method.
    #  //
    #  // Takes pairs of before and after transactions and compares them.
    #  // Status information is updated according to the results of the comparison.
    #  // Each pair is published to the pair_ap analysis port.
    async def run_phase(self, phase):

        #    pair_type pair
        #    T b
        #    T a

        s = ""
        await super().run_phase(phase)  # Is this needed?
        while True:

            arr_b = []
            arr_a = []

            await self.m_before_fifo.get(arr_b)
            await self.m_after_fifo.get(arr_a)

            b = arr_b[0]
            a = arr_a[0]

            # pytype: disable=wrong-arg-types
            if self.CompType.comp(b, a) is False:
                s = sv.sformatf("%s differs from %s", self.Convert.convert2string(a),
                    self.Convert.convert2string(b))
                uvm_error("Comparator Mismatch", s)
                self.m_mismatches += 1

            else:
                s = self.Convert.convert2string(b)
                uvm_info("Comparator Match", s, UVM_MEDIUM)
                self.m_matches += 1

            # we make the assumption here that a transaction "sent for
            # analysis" is safe from being edited by another process.
            # Hence, it is safe not to clone a and b.

            pair = self.PairType("after/before")
            # pytype: enable=wrong-arg-types
            pair.first = a
            pair.second = b
            self.pair_ap.write(pair)


    #  // Function: flush
    #  //
    #  // This method sets m_matches and m_mismatches back to zero. The
    #  // `UVMTLMFIFO.flush` takes care of flushing the FIFOs.
    def flush(self):
        self.m_matches = 0
        self.m_mismatches = 0


uvm_component_utils(UVMInOrderComparator)


class UVMInOrderBuiltInComparator(UVMInOrderComparator):
    """
    CLASS: UVMInOrderBuiltInComparator

    This class uses the uvm_built_in_* comparison, converter, and pair classes.
    Use this class for built-in types (int, bit, string, etc.)
    """


    type_name = "UVMInOrderBuiltInComparator"

    def __init__(self, name, parent):
        super().__init__(name, parent)


    def get_type_name(self):
        return UVMInOrderBuiltInComparator.type_name


uvm_component_utils(UVMInOrderBuiltInComparator)


class UVMInOrderClassComparator(UVMInOrderComparator):
    """
    CLASS: UVMInOrderClassComparator #(T)

    This class uses the uvm_class_* comparison, converter, and pair classes.
    Use this class for comparing user-defined objects of type T, which must
    provide compare() and convert2string() method.
    """

    type_name = "UVMInOrderClassComparator"

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.PairType = UVMClassPair
        self.Convert = UVMClassConverter
        self.CompType = UVMClassComp


    def get_type_name(self):
        return UVMInOrderClassComparator.type_name


uvm_component_utils(UVMInOrderClassComparator)
