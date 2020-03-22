#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
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
File: Algorithmic Comparator

A common function of testbenches is to compare streams of transactions for
equivalence. For example, a testbench may compare a stream of transactions
from a DUT with expected results.

The UVM library provides a base class called
<uvm_in_order_comparator #(T,comp_type,convert,pair_type)> and two
derived classes, which are <uvm_in_order_built_in_comparator #(T)> for comparing
streams of built-in types and <UVMInOrderClassComparator #(T)> for comparing
streams of class objects.

The UVMAlgorithmicComparator also compares two streams of transactions;
however, the transaction streams might be of different type objects. This
device will use a user-written transformation function to convert one type
to another before performing a comparison.
"""

from uvm.base.uvm_component import UVMComponent
from uvm.macros import uvm_component_utils
from .uvm_in_order_comparator import UVMInOrderClassComparator
from ..tlm1 import UVMAnalysisImp, UVMAnalysisExport




class UVMAlgorithmicComparator(UVMComponent):
    """
    CLASS: UVMAlgorithmicComparator

    Compares two streams of data objects of different types.

    The algorithmic comparator is a wrapper around `UVMInOrderClassComparator`.
    Like the in-order comparator, the algorithmic comparator compares two streams
    of transactions, the ~BEFORE~ stream and the ~AFTER~ stream. It is often the case
    when two streams of transactions need to be compared that the two streams are
    in different forms. That is, the type of the ~BEFORE~ transaction stream is
    different than the type of the ~AFTER~ transaction stream.

    The UVMAlgorithmicComparator's ~TRANSFORMER~ type parameter specifies the
    class responsible for converting transactions of type ~BEFORE~ into those of
    type ~AFTER~. This transformer class must provide a transform() method with the
    following prototype::

      def transform(self, b):
          # Should return transformed transaction

    Matches and mismatches are reported in terms of the ~AFTER~ transactions.
    For more information, see the `UVMInOrderComparator` class.

    Port: before_export

    The export to which a data stream of type BEFORE is sent via a connected
    analysis port. Publishers (monitors) can send in an ordered stream of
    transactions against which the transformed BEFORE transactions will
    (be compared.

    Port: after_export

    The export to which a data stream of type AFTER is sent via a connected
    analysis port. Publishers (monitors) can send in an ordered stream of
    transactions to be transformed and compared to the AFTER transactions.
    """

    type_name = "UVMAlgorithmicComparator"


    #  // Function: new
    #  //
    #  // Creates an instance of a specialization of this class.
    #  // In addition to the standard uvm_component constructor arguments, ~name~
    #  // and ~parent~, the constructor takes a handle to a ~transformer~ object,
    #  // which must already be allocated (handles can't be ~null~) and must implement
    #  // the transform() method.
    #
    def __init__(self, name, parent=None, transformer=None):
        super().__init__(name, parent)

        self.m_transformer = transformer
        self.comp = UVMInOrderClassComparator("comp", self)

        self.before_export = UVMAnalysisImp("before_analysis_export", self)
        self.after_export = UVMAnalysisExport("after_analysis_export", self)


    def get_type_name(self):
        return UVMAlgorithmicComparator.type_name


    def connect_phase(self, phase):
        self.after_export.connect(self.comp.after_export)


    def write(self, b):
        self.comp.before_export.write(self.m_transformer.transform(b))


uvm_component_utils(UVMAlgorithmicComparator)
