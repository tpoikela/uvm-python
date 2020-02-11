
import unittest

from uvm.base.uvm_resource_db import (UVMResourceDb, ResourceDbClassFactory)


class TestUVMResourceDb(unittest.TestCase):


    def test_create_class(self):
        DbInt = ResourceDbClassFactory('DbInt', ['_id', 'val2'], int)
        my_db = DbInt(_id=123, val2='name')
        self.assertEqual(my_db.T, int)
