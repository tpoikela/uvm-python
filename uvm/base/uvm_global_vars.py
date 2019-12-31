
from .uvm_printer import UVMTablePrinter, UVMTreePrinter
from .uvm_comparer import UVMComparer

uvm_default_table_printer = UVMTablePrinter()

uvm_default_tree_printer = UVMTreePrinter()

uvm_default_printer = uvm_default_table_printer

uvm_default_comparer = UVMComparer()
