
import unittest
from uvm.base.uvm_config_db import UVMConfigDb, UVMConfigDbOptions
from uvm.base.uvm_debug import UVMDebug

str1 = "uvm_test_top.ubus_example_tb0.ubus0.masters[0].monitor"

#UVMDebug.DEBUG = True


class TestUVMConfigDb(unittest.TestCase):

    def test_exists(self):
        pass
        # ok = True
        # self.assertEqual(ok, False)
        # ok = False
        # self.assertEqual(ok, True)

    def test_set_get(self):
        cntxt = None
        inst_name = "my_comp"
        field_name = "field1"
        value = 123
        UVMConfigDb.set(cntxt, "other_name", field_name, 666, T=None)
        UVMConfigDb.set(cntxt, inst_name, field_name, value, T=None)
        UVMConfigDb.set(cntxt, inst_name + ".*", field_name, 555, T=None)
        got_val = []
        ok = UVMConfigDb.get(cntxt, inst_name, field_name, got_val, T=None)
        self.assertEqual(ok, True)
        self.assertEqual(got_val[0], value)
        got_val = []
        ok = UVMConfigDb.get(cntxt, inst_name, "wrong_name", got_val, T=None)
        self.assertEqual(ok, False)
        self.assertEqual(len(got_val), 0)

        hier_name = inst_name + "." + "child"
        got_val = []
        ok = UVMConfigDb.get(cntxt, hier_name, field_name, got_val, T=None)
        self.assertEqual(ok, True)
        self.assertEqual(got_val[0], 555)


    def test_hier_set_get(self):
        UVMConfigDbOptions.tracing = True
        UVMConfigDb.set(None, str1, "master_id", 666, T=None)

        arr = []
        ok = UVMConfigDb.get(None, str1, "master_id", arr)
        self.assertEqual(ok, True)
        self.assertEqual(arr[0], 666)


    def test_set_override(self):
        pass
        # self.assertEqual(0, 1)


if __name__ == '__main__':
    unittest.main()
