
import unittest
import re
from uvm.base.uvm_printer import (UVMPrinter, UVMLinePrinter, UVMTreePrinter,
    UVMTablePrinter, UVMJSONPrinter)

from uvm.base.uvm_object import UVMObject
from uvm.base.uvm_object_globals import UVM_DEC


class TestUVMPrinter(unittest.TestCase):

    def test_printer_init(self):
        printer = UVMPrinter()

    def test_print_array_header(self):
        printer = UVMPrinter()
        printer.print_array_header("xxx", 10)
        row_info = printer.m_rows[0]


class TestUVMTablePrinter(unittest.TestCase):

    def test_print_field_int(self):
        tprinter = UVMTablePrinter()
        tprinter.print_field_int("my_number", 0x5678, 32)
        result = tprinter.emit()
        self.assertRegex(result, 'number.*5678')

    def test_table_printer(self):
        tprinter = UVMTablePrinter()
        tprinter.knobs.default_radix = UVM_DEC
        tprinter.print_field_int("number", 1234, 32)
        tprinter.print_string("my_string", "xxx yyy")
        tprinter.print_real("my_real", 1.2345)
        result = tprinter.emit()
        self.assertRegex(result, 'number.*1234')
        self.assertRegex(result, 'my_string.*xxx yyy')
        self.assertRegex(result, r'my_real.*real.*1\.2345')


class TestUVMLinePrinter(unittest.TestCase):

    def test_line_printer(self):
        lprinter = UVMLinePrinter()
        lprinter.knobs.default_radix = UVM_DEC
        lprinter.print_field_int("number", 1234, 32)
        lprinter.print_string("my_string", "xxx yyy")
        lprinter.print_real("my_real", 1.2345)
        obj = UVMObject("test obj123")
        lprinter.print_object(obj.get_name(), obj, ".")
        result = lprinter.emit()
        self.assertRegex(result, 'number.*1234')
        self.assertRegex(result, 'my_string.*xxx yyy')
        self.assertRegex(result, 'my_real: 1.2345')
        self.assertRegex(result, 'test obj123')


if __name__ == '__main__':
    unittest.main()
