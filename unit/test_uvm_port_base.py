
import unittest

from uvm.base.uvm_port_base import UVMPortBase
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_object_globals import (UVM_PORT, UVM_EXPORT)


class TestUVMPortBase(unittest.TestCase):

    def test_name(self):
        parent = UVMComponent("port_parent_123", None)
        port_base = UVMPortBase("port_base", parent, UVM_PORT)
        self.assertEqual(port_base.get_type_name(), "port")

    def test_connect(self):
        parent = UVMComponent("port_parent_456", None)
        port = UVMPortBase("port", parent, UVM_PORT)
        export = UVMPortBase("export", parent, UVM_EXPORT)
        export2 = UVMPortBase("export2", parent, UVM_EXPORT)
        port.connect(export)
        export2.connect(port)

        conn_to = {}
        port.get_connected_to(conn_to)
        self.assertEqual(len(conn_to), 1)

        conn_to = {}
        export.get_provided_to(conn_to)
        self.assertEqual(len(conn_to), 1)

        # Just check there's no exceptions thrown
        port.debug_connected_to()
        export.debug_provided_to()


if __name__ == '__main__':
    unittest.main()
