
import unittest

from uvm.base.uvm_globals import (
    uvm_report_enabled,
    uvm_is_match
)

from uvm.base.uvm_object_globals import (
    UVM_INFO, UVM_MEDIUM, UVM_HIGH,
    UVM_FATAL
)


class TestUVMGlobals(unittest.TestCase):

    def test_uvm_report_enabled(self):
        # Default verbosity that is set
        self.assertTrue(uvm_report_enabled(UVM_MEDIUM, UVM_INFO))
        self.assertFalse(uvm_report_enabled(UVM_HIGH, UVM_INFO))
        self.assertTrue(uvm_report_enabled(UVM_MEDIUM, UVM_FATAL))


    def test_uvm_is_match(self):
        self.assertTrue(uvm_is_match("my_name*", "my_name.child1.c2"))
        self.assertFalse(uvm_is_match("your_name*", "my_name.child1.c2"))
        self.assertTrue(uvm_is_match("my_name????", "my_name.abc"))
        self.assertFalse(uvm_is_match("my_name??????", "my_name.abc"))
        self.assertTrue(uvm_is_match("zzz*www??yy", "zzz_abcdefg_wwwKKyy"))


if __name__ == '__main__':
    unittest.main()
