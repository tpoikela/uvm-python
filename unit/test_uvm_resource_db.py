
import unittest

from uvm.base.uvm_resource_db import (UVMResourceDb, ResourceDbClassFactory)


class TestUVMResourceDb(unittest.TestCase):


    def test_create_class(self):
        DbInt = ResourceDbClassFactory('DbInt', ['_id', 'val2'], int)
        DbStr = ResourceDbClassFactory('DbStr', ['_id', 'val2'], str)
        my_db_int = DbInt(_id=123, val2='name')
        my_db_str = DbStr(_id=123, val2='name')
        self.assertEqual(my_db_int.T, int)
        self.assertEqual(my_db_str.T, str)
        my_db_int.set('*', 'value', 123)
        my_db_str.set('*', 'value', 'str_value')
        rsc_int = my_db_int.get_by_name('*', 'value')
        rsc_str = my_db_str.get_by_name('*', 'value')
        self.assertEqual(rsc_int.read(), 123)
        # TODO self.assertEqual(rsc_str.read(), 'str_value')
