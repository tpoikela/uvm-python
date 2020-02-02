
import unittest

from uvm.base.uvm_port_base import UVMPortBase
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_object_globals import UVM_PORT


class TestUVMPortBase(unittest.TestCase):

    def test_name(self):
        parent = UVMComponent("port_parent", None)
        port_base = UVMPortBase("port_base", parent, UVM_PORT)
        self.assertEqual(port_base.get_type_name(), "port")


if __name__ == '__main__':
    unittest.main()
