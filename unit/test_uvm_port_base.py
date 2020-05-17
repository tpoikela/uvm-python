
import unittest

from uvm.base.uvm_port_base import UVMPortBase
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_object_globals import (UVM_PORT, UVM_EXPORT,
    UVM_IMPLEMENTATION)


class TestUVMPortBase(unittest.TestCase):

    def test_name(self):
        parent = UVMComponent("port_parent_123", None)
        port_base = UVMPortBase("port_base", parent, UVM_PORT)
        self.assertEqual(port_base.get_type_name(), "port")

    def test_connect(self):
        parent = UVMComponent("port_parent_456", None)
        child1 = UVMComponent("port_child_567", parent)
        port = UVMPortBase("port", parent, UVM_PORT)
        export = UVMPortBase("export", parent, UVM_EXPORT)
        export2 = UVMPortBase("export222", parent, UVM_EXPORT)
        port.connect(export)
        export2.connect(port)

        export3 = UVMPortBase('export3', child1, UVM_IMPLEMENTATION)
        export.connect(export3)

        conn_to = {}
        port.get_connected_to(conn_to)
        self.assertEqual(len(conn_to), 1)

        conn_to = {}
        export.get_provided_to(conn_to)
        self.assertEqual(len(conn_to), 1)

        port.resolve_bindings()

        # Just check there's no exceptions thrown
        str_conn_to = port.debug_connected_to()
        str_prov_to = export.debug_provided_to()

        # TODO disable reporting, check the returned strings
        self.assertRegex(str_conn_to, r'Resolved implementation')
        self.assertRegex(str_conn_to, r'port_child_567')

        self.assertRegex(str_prov_to, r'port_parent_456')

        export2.resolve_bindings()
        export2.debug_connected_to()


if __name__ == '__main__':
    unittest.main()
