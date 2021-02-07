#//
#//--------------------------------------------------------------
#//    Copyright 2004-2009 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2019-2020 Tuomas Poikela
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
#//--------------------------------------------------------------
"""
Title: Generic Register Operation Descriptors

This section defines the abstract register transaction item. It also defines
a descriptor for a physical bus operation that is used by <uvm_reg_adapter>
subtypes to convert from a protocol-specific address/data/rw operation to
a bus-independent, canonical r/w operation.
"""


from ..seq.uvm_sequence_item import UVMSequenceItem
from ..macros.uvm_object_defines import uvm_object_utils
from ..macros.uvm_message_defines import uvm_error, uvm_fatal
from .uvm_reg_model import (UVM_READ, UVM_NOT_OK, UVM_MEM, UVM_FRONTDOOR,
    UVM_ACCESS_NAMES, UVM_ELEMENT_KIND_NAMES)
from ..base.uvm_object_globals import UVM_HIGH, UVM_INFO
from ..base.sv import sv
from ..base.uvm_globals import uvm_report_enabled
from typing import TypeVar, List

_T0 = TypeVar('_T0')


class UVMRegItem(UVMSequenceItem):
    """
    CLASS: uvm_reg_item

    Defines an abstract register transaction item. No bus-specific information
    is present, although a handle to a <uvm_reg_map> is provided in case a user
    wishes to implement a custom address translation algorithm.
    """

    #  // Variable: element_kind
    #  //
    #  // Kind of element being accessed: REG, MEM, or FIELD. See <uvm_elem_kind_e>.
    #  //
    #  uvm_elem_kind_e element_kind


    #  // TODO: parameterize
    #  constraint max_values { value.size() > 0 && value.size() < 1000; }
    #
    #  // Variable: offset
    #  //
    #  // For memory accesses, the offset address. For bursts,
    #  // the ~starting~ offset address.
    #  //
    #  rand uvm_reg_addr_t offset

    #  // Variable: status
    #  //
    #  // The result of the transaction: IS_OK, HAS_X, or ERROR.
    #  // See <uvm_status_e>.
    #  //
    #  uvm_status_e status

    #  // Variable: local_map
    #  //
    #  // The local map used to obtain addresses. Users may customize
    #  // address-translation using this map. Access to the sequencer
    #  // and bus adapter can be obtained by getting this map's root map,
    #  // then calling <uvm_reg_map::get_sequencer> and
    #  // <uvm_reg_map::get_adapter>.
    #  //
    #  uvm_reg_map local_map



    #  // Variable: parent
    #  //
    #  // The sequence from which the operation originated.
    #  //
    #  rand uvm_sequence_base parent

    #  // Variable: prior
    #  //
    #  // The priority requested of this transfer, as defined by
    #  // <uvm_sequence_base::start_item>.
    #  //
    #  int prior = -1

    #  // Variable: extension
    #  //
    #  // Handle to optional user data, as conveyed in the call to
    #  // write(), read(), mirror(), or update() used to trigger the operation.
    #  //
    #  rand uvm_object extension

    #  // Variable: bd_kind
    #  //
    #  // If path is UVM_BACKDOOR, this member specifies the abstraction
    #  // kind for the backdoor access, e.g. "RTL" or "GATES".
    #  //
    #  string bd_kind

    #  // Variable: fname
    #  //
    #  // The file name from where this transaction originated, if provided
    #  // at the call site.
    #  //
    #  string fname

    #  // Variable: lineno
    #  //
    #  // The file name from where this transaction originated, if provided
    #  // at the call site.
    #  //
    #  int lineno

    def __init__(self, name="") -> None:
        """
          Function: new

          Create a new instance of this type, giving it the optional `name`.

        Args:
            name:
        """
        UVMSequenceItem.__init__(self, name)
        #  // Variable: value
        #  //
        #  // The value to write to, or after completion, the value read from the DUT.
        #  // Burst operations use the <values> property.
        #  //
        self.value: List[int] = [0]  # rand uvm_reg_data_t value[]

        #  // Variable: path
        #  //
        #  // The path being used: <UVM_FRONTDOOR> or <UVM_BACKDOOR>.
        #  //
        #  uvm_path_e path
        self.path = UVM_FRONTDOOR

        self.status = 0
        self.fname = ""
        self.lineno = 0
        self.bd_kind = ""
        self.prior = -1
        self.extension = None
        self.parent = None
        self.offset = 0
        #  // Variable: kind
        #  //
        #  // Kind of access: READ or WRITE.
        #  //
        #  rand uvm_access_e kind
        self.kind = UVM_READ

        #  // Variable: element
        #  //
        #  // A handle to the RegModel model element associated with this transaction.
        #  // Use <element_kind> to determine the type to cast  to: <uvm_reg>,
        #  // <uvm_mem>, or <uvm_reg_field>.
        #  //
        self.element = None
        self.element_kind = -1

        #  // Variable: map
        #  //
        #  // The original map specified for the operation. The actual <map>
        #  // used may differ when a test or sequence written at the block
        #  // level is reused at the system level.
        #  //
        self.map = None

        self.local_map = None

    def convert2string(self) -> str:
        """
        Function: convert2string

        Returns a string showing the contents of this transaction.

        Returns:
            str: Reg item as string.
        """
        value_s = ""
        ele_name = "null"

        if self.element is not None:
            ele_name = self.element.get_full_name()

        kind_str         = UVM_ACCESS_NAMES[self.kind]
        element_kind_str = UVM_ELEMENT_KIND_NAMES[self.element_kind]

        s = ("kind="      + kind_str +
             " ele_kind=" + element_kind_str +
             " ele_name=" + ele_name)

        if (len(self.value) > 1 and uvm_report_enabled(UVM_HIGH, UVM_INFO, "RegModel")):
            value_s = "'{"
            for i in range(len(self.value)):
                value_s = value_s + sv.sformatf("%0h,", self.value[i])
            value_s = value_s[:-1] + "}"
        else:
            value_s = sv.sformatf("%0h", self.value[0])
        s = s + " value=" + value_s
        
        if self.element_kind == UVM_MEM:
            s = s + sv.sformatf(" offset=%0h", self.offset)

        map_name = "null"
        if self.map is not None:
            map_name = self.map.get_full_name()
        s = s + " map=" + map_name + " path=" + str(self.path)
        s = s + " status=" + str(self.status)
        return s


    def do_copy(self, rhs) -> None:
        """
        Function: do_copy

        Copy the ~rhs~ object into this object. The ~rhs~ object must
        derive from `UVMRegItem`.
        """
        if rhs is None:
            uvm_fatal("REG/NULL","do_copy: rhs argument is null")

        arr_rhs_ = []
        if not sv.cast(arr_rhs_, rhs, UVMRegItem):
            uvm_error("WRONG_TYPE","Provided rhs is not of type uvm_reg_item")
            return
        rhs_ = arr_rhs_[0]

        super().copy(rhs)
        self.element_kind = rhs_.element_kind
        self.element = rhs_.element
        self.kind = rhs_.kind
        self.value = rhs_.value
        self.offset = rhs_.offset
        self.status = rhs_.status
        self.local_map = rhs_.local_map
        self.map = rhs_.map
        self.path = rhs_.path
        self.extension = rhs_.extension
        self.bd_kind = rhs_.bd_kind
        self.parent = rhs_.parent
        self.prior = rhs_.prior
        self.fname = rhs_.fname
        self.lineno = rhs_.lineno



uvm_object_utils(UVMRegItem)


class UVMRegBusOp():
    """
    CLASS: UVMRegBusOp

    Class that defines a generic bus transaction for register and memory accesses, having
    ~kind~ (read or write), ~address~, ~data~, and ~byte enable~ information.
    If the bus is narrower than the register or memory location being accessed,
    there will be multiple of these bus operations for every abstract
    `UVMRegItem` transaction. In this case, ~data~ represents the portion
    of <uvm_reg_item::value> being transferred during this bus cycle.
    If the bus is wide enough to perform the register or memory operation in
    a single cycle, ~data~ will be the same as <uvm_reg_item::value>.
    """

    #typedef struct {
    #
    #  // Variable: kind
    #  //
    #  // Kind of access: READ or WRITE.
    #  //
    #  uvm_access_e kind
    #
    #
    #  // Variable: addr
    #  //
    #  // The bus address.
    #  //
    #  uvm_reg_addr_t addr
    #
    #
    #  // Variable: data
    #  //
    #  // The data to write. If the bus width is smaller than the register or
    #  // memory width, ~data~ represents only the portion of ~value~ that is
    #  // being transferred this bus cycle.
    #  //
    #  uvm_reg_data_t data
    #
    #
    #  // Variable: n_bits
    #  //
    #  // The number of bits of <uvm_reg_item::value> being transferred by
    #  // this transaction.
    #
    #  int n_bits
    #
    #  /*
    #  constraint valid_n_bits {
    #     n_bits > 0
    #     n_bits <= `UVM_REG_DATA_WIDTH
    #  }
    #  */
    #
    #
    #  // Variable: byte_en
    #  //
    #  // Enables for the byte lanes on the bus. Meaningful only when the
    #  // bus supports byte enables and the operation originates from a field
    #  // write/read.
    #  //
    #  uvm_reg_byte_en_t byte_en
    #
    #
    #  // Variable: status
    #  //
    #  // The result of the transaction: UVM_IS_OK, UVM_HAS_X, UVM_NOT_OK.
    #  // See <uvm_status_e>.
    #  //
    #  uvm_status_e status
    #
    #} uvm_reg_bus_op

    def __init__(self) -> None:
        """
        Constructor
        """
        self.kind = UVM_READ
        self.addr = 0
        self.data = 0
        self.n_bits = 0
        self.byte_en = 0x0
        self.status = UVM_NOT_OK
