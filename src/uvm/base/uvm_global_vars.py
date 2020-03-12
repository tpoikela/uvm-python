
from .uvm_printer import UVMTablePrinter, UVMTreePrinter
from .uvm_comparer import UVMComparer
from .uvm_packer import UVMPacker

uvm_default_table_printer = UVMTablePrinter()

uvm_default_tree_printer = UVMTreePrinter()

uvm_default_printer = uvm_default_table_printer

uvm_default_comparer = UVMComparer()

uvm_default_packer = UVMPacker()
