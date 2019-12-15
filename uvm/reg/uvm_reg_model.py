#
#-------------------------------------------------------------
#   Copyright 2004-2009 Synopsys, Inc.
#   Copyright 2010-2011 Mentor Graphics Corporation
#   Copyright 2010 Cadence Design Systems, Inc.
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#-------------------------------------------------------------

#------------------------------------------------------------------------------
# TITLE: Global Declarations for the Register Layer
#------------------------------------------------------------------------------
#
# This section defines globally available types, enums, and utility classes.
#
#------------------------------------------------------------------------------

#-------------
# Group: Types
#-------------
#
# Type: uvm_reg_data_t
#
# 2-state data value with <`UVM_REG_DATA_WIDTH> bits
#
#typedef  bit unsigned [`UVM_REG_DATA_WIDTH-1:0]  uvm_reg_data_t ;

# Type: uvm_reg_data_logic_t
#
# 4-state data value with <`UVM_REG_DATA_WIDTH> bits
#
#typedef  logic unsigned [`UVM_REG_DATA_WIDTH-1:0]  uvm_reg_data_logic_t ;

# Type: uvm_reg_addr_t
#
# 2-state address value with <`UVM_REG_ADDR_WIDTH> bits
#
#typedef  bit unsigned [`UVM_REG_ADDR_WIDTH-1:0]  uvm_reg_addr_t ;

# Type: uvm_reg_addr_logic_t
#
# 4-state address value with <`UVM_REG_ADDR_WIDTH> bits
#
#typedef  logic unsigned [`UVM_REG_ADDR_WIDTH-1:0]  uvm_reg_addr_logic_t ;

# Type: uvm_reg_byte_en_t
#
# 2-state byte_enable value with <`UVM_REG_BYTENABLE_WIDTH> bits
#
#typedef  bit unsigned [`UVM_REG_BYTENABLE_WIDTH-1:0]  uvm_reg_byte_en_t ;

# Type: uvm_reg_cvr_t
#
# Coverage model value set with <`UVM_REG_CVR_WIDTH> bits.
#
# Symbolic values for individual coverage models are defined
# by the <uvm_coverage_model_e> type.
#
# The following bits in the set are assigned as follows
#
# 0-7     - UVM pre-defined coverage models
# 8-15    - Coverage models defined by EDA vendors,
#           implemented in a register model generator.
# 16-23   - User-defined coverage models
# 24..    - Reserved
#
#typedef  bit [`UVM_REG_CVR_WIDTH-1:0]  uvm_reg_cvr_t ;

# Type: uvm_hdl_path_slice
#
# Slice of an HDL path
#
# Struct that specifies the HDL variable that corresponds to all
# or a portion of a register.
#
# path    - Path to the HDL variable.
# offset  - Offset of the LSB in the register that this variable implements
# size    - Number of bits (toward the MSB) that this variable implements
#
# If the HDL variable implements all of the register, ~offset~ and ~size~
# are specified as -1. For example:
#|
#| r1.add_hdl_path('{ '{"r1", -1, -1} });
#|

#typedef struct {
class uvm_hdl_path_slice:
    def __init__(self):
        self.path = ""
        self.offset = -1
        self.size = -1
#} uvm_hdl_path_slice;
#
#typedef uvm_resource_db#(uvm_reg_cvr_t) uvm_reg_cvr_rsrc_db;


#--------------------
# Group: Enumerations
#--------------------
#
# Enum: uvm_status_e
#
# Return status for register operations
#
# UVM_IS_OK      - Operation completed successfully
# UVM_NOT_OK     - Operation completed with error
# UVM_HAS_X      - Operation completed successfully bit had unknown bits.
#
#
#   typedef enum {
UVM_IS_OK = 0
UVM_NOT_OK = 1
UVM_HAS_X = 2
#   } uvm_status_e;

# Enum: uvm_path_e
#
# Path used for register operation
#
# UVM_FRONTDOOR    - Use the front door
# UVM_BACKDOOR     - Use the back door
# UVM_PREDICT      - Operation derived from observations by a bus monitor via
#                    the <uvm_reg_predictor> class.
# UVM_DEFAULT_PATH - Operation specified by the context
#
#   typedef enum {
UVM_FRONTDOOR = 0
UVM_BACKDOOR = 1
UVM_PREDICT = 2
UVM_DEFAULT_PATH = 3
#   } uvm_path_e;

# Enum: uvm_check_e
#
# Read-only or read-and-check
#
# UVM_NO_CHECK   - Read only
# UVM_CHECK      - Read and check
#   
#   typedef enum {
UVM_NO_CHECK = 0
UVM_CHECK = 1
#   } uvm_check_e;

# Enum: uvm_endianness_e
#
# Specifies byte ordering
#
# UVM_NO_ENDIAN      - Byte ordering not applicable
# UVM_LITTLE_ENDIAN  - Least-significant bytes first in consecutive addresses
# UVM_BIG_ENDIAN     - Most-significant bytes first in consecutive addresses
# UVM_LITTLE_FIFO    - Least-significant bytes first at the same address
# UVM_BIG_FIFO       - Most-significant bytes first at the same address
#   
#   typedef enum {
UVM_NO_ENDIAN = 0
UVM_LITTLE_ENDIAN = 1
UVM_BIG_ENDIAN = 2
UVM_LITTLE_FIFO = 3
UVM_BIG_FIFO = 4
#   } uvm_endianness_e;

# Enum: uvm_elem_kind_e
#
# Type of element being read or written
#
# UVM_REG      - Register
# UVM_FIELD    - Field
# UVM_MEM      - Memory location
#
#   typedef enum {
UVM_REG = 0
UVM_FIELD = 1
UVM_MEM = 2
#   } uvm_elem_kind_e;

# Enum: uvm_access_e
#
# Type of operation begin performed
#
# UVM_READ     - Read operation
# UVM_WRITE    - Write operation
#
#   typedef enum {
UVM_READ = 0
UVM_WRITE = 1
UVM_BURST_READ = 2
UVM_BURST_WRITE = 3
#   } uvm_access_e;

# Enum: uvm_hier_e
#
# Whether to provide the requested information from a hierarchical context.
#
# UVM_NO_HIER - Provide info from the local context
# UVM_HIER    - Provide info based on the hierarchical context
#
#   typedef enum {
UVM_NO_HIER = 0
UVM_HIER = 1
#   } uvm_hier_e;

# Enum: uvm_predict_e
#
# How the mirror is to be updated
#
# UVM_PREDICT_DIRECT  - Predicted value is as-is
# UVM_PREDICT_READ    - Predict based on the specified value having been read
# UVM_PREDICT_WRITE   - Predict based on the specified value having been written
#
#   typedef enum {
UVM_PREDICT_DIRECT = 0
UVM_PREDICT_READ = 1
UVM_PREDICT_WRITE = 2
#   } uvm_predict_e;

# Enum: uvm_coverage_model_e
#
# Coverage models available or desired.
# Multiple models may be specified by bitwise OR'ing individual model identifiers.
#
# UVM_NO_COVERAGE      - None
# UVM_CVR_REG_BITS     - Individual register bits
# UVM_CVR_ADDR_MAP     - Individual register and memory addresses
# UVM_CVR_FIELD_VALS   - Field values
# UVM_CVR_ALL          - All coverage models
#
#typedef enum uvm_reg_cvr_t {
UVM_NO_COVERAGE      = 0x0000
UVM_CVR_REG_BITS     = 0x0001
UVM_CVR_ADDR_MAP     = 0x0002
UVM_CVR_FIELD_VALS   = 0x0004
UVM_CVR_ALL          = -1
#} uvm_coverage_model_e;

# Enum: uvm_reg_mem_tests_e
#
# Select which pre-defined test sequence to execute.
#
# Multiple test sequences may be selected by bitwise OR'ing their
# respective symbolic values.
#
# UVM_DO_REG_HW_RESET      - Run <uvm_reg_hw_reset_seq>
# UVM_DO_REG_BIT_BASH      - Run <uvm_reg_bit_bash_seq>
# UVM_DO_REG_ACCESS        - Run <uvm_reg_access_seq>
# UVM_DO_MEM_ACCESS        - Run <uvm_mem_access_seq>
# UVM_DO_SHARED_ACCESS     - Run <uvm_reg_mem_shared_access_seq>
# UVM_DO_MEM_WALK          - Run <uvm_mem_walk_seq>
# UVM_DO_ALL_REG_MEM_TESTS - Run all of the above
#
# Test sequences, when selected, are executed in the
# order in which they are specified above.
#
#typedef enum bit [63:0] {
UVM_DO_REG_HW_RESET      = 0x0000000000000001
UVM_DO_REG_BIT_BASH      = 0x0000000000000002
UVM_DO_REG_ACCESS        = 0x0000000000000004
UVM_DO_MEM_ACCESS        = 0x0000000000000008
UVM_DO_SHARED_ACCESS     = 0x0000000000000010
UVM_DO_MEM_WALK          = 0x0000000000000020
UVM_DO_ALL_REG_MEM_TESTS = 0xffffffffffffffff
#} uvm_reg_mem_tests_e;
#

#-----------------------
# Group: Utility Classes
#-----------------------

#------------------------------------------------------------------------------
# Class: uvm_hdl_path_concat
#
# Concatenation of HDL variables
#
# A dArray of <uvm_hdl_path_slice> specifying a concatenation
# of HDL variables that implement a register in the HDL.
#
# Slices must be specified in most-to-least significant order.
# Slices must not overlap. Gaps may exist in the concatenation
# if portions of the registers are not implemented.
#
# For example, the following register
#|
#|        1 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0
#| Bits:  5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
#|       +-+---+-------------+---+-------+
#|       |A|xxx|      B      |xxx|   C   |
#|       +-+---+-------------+---+-------+
#|
#
# If the register is implemented using a single HDL variable,
# The array should specify a single slice with its ~offset~ and ~size~
# specified as -1. For example:
#
#| concat.set('{ '{"r1", -1, -1} });
#
#------------------------------------------------------------------------------

class uvm_hdl_path_concat:

    def __init__(self):
        self.slices = []
    
    # Variable: slices
    # Array of individual slices,
    # stored in most-to-least significant order
    #uvm_hdl_path_slice slices[];
    
    # Function: set
    # Initialize the concatenation using an array literal
    def set(self, t):
        self.slices = t;
    
    # Function: add_slice
    # Append the specified ~slice~ literal to the path concatenation
    def add_slice(self, slice):
        self.slices.append(slice)
    
    # Function: add_path
    # Append the specified ~path~ to the path concatenation,
    # for the specified number of bits at the specified ~offset~.
    def add_path(self, path, offset = -1, size = -1):
        t = uvm_hdl_path_slice()
        t.offset = offset
        t.path   = path
        t.size   = size
        self.add_slice(t);
    #endclass

# concat2string
#
def uvm_hdl_concat2string(concat):
    image = "{"
    
    if (len(concat.slices) == 1 and
        concat.slices[0].offset == -1 and
        concat.slices[0].size == -1):
        return concat.slices[0].path

    i = 0
    for sli in concat.slices:
        if i == 0:
            image = image + "" + sli.path
        else:
            image = image +  ", " + sli.path
        if sli.offset >= 0:
            image = image + "@" + "[{} +: {}]".format(sli.offset, sli.size)
        i += 1

    image = image + "}"
    return image

class uvm_reg_map_addr_range:
    def __init__(self):
        self.min = 0
        self.max = 0
        self.stride = 0

#`include "reg/uvm_reg_item.svh"
#`include "reg/uvm_reg_adapter.svh"
#`include "reg/uvm_reg_predictor.svh"
#`include "reg/uvm_reg_sequence.svh"
#`include "reg/uvm_reg_cbs.svh"
#`include "reg/uvm_reg_backdoor.svh"
#`include "reg/uvm_reg_field.svh"
#`include "reg/uvm_vreg_field.svh"
#`include "reg/uvm_reg.svh"
#`include "reg/uvm_reg_indirect.svh"
#`include "reg/uvm_reg_fifo.svh"
#`include "reg/uvm_reg_file.svh"
#`include "reg/uvm_mem_mam.svh"
#`include "reg/uvm_vreg.svh"
#`include "reg/uvm_mem.svh"
#`include "reg/uvm_reg_map.svh"
#`include "reg/uvm_reg_block.svh"
#
#`include "reg/sequences/uvm_reg_hw_reset_seq.svh"
#`include "reg/sequences/uvm_reg_bit_bash_seq.svh"
#`include "reg/sequences/uvm_mem_walk_seq.svh"
#`include "reg/sequences/uvm_mem_access_seq.svh"
#`include "reg/sequences/uvm_reg_access_seq.svh"
#`include "reg/sequences/uvm_reg_mem_shared_access_seq.svh"
#`include "reg/sequences/uvm_reg_mem_built_in_seq.svh"
#`include "reg/sequences/uvm_reg_mem_hdl_paths_seq.svh"

import unittest

class TestUVMRegModel(unittest.TestCase):

    def test_concat2string(self):
        concat = uvm_hdl_path_concat()
        path_sli = uvm_hdl_path_slice()
        path_sli.path = "dut"
        concat.add_path(path_sli.path)
        str_path = uvm_hdl_concat2string(concat)
        self.assertEqual(str_path, "dut")
        concat.add_path("test_reg")
        str_path = uvm_hdl_concat2string(concat)
        self.assertEqual(str_path, "{dut, test_reg}")

if __name__ == '__main__':
    unittest.main()
