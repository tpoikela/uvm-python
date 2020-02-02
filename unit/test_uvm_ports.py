
import unittest

from uvm.base.uvm_component import UVMComponent
from uvm.tlm1.uvm_ports import (
    UVMBlockingPutPort, UVMNonBlockingPutPort,
    UVMBlockingGetPort, UVMNonBlockingGetPort,
)

from uvm.tlm1.uvm_imps import (
     UVMNonBlockingPutImp, UVMNonBlockingGetImp
)


class TestUVMPorts(unittest.TestCase):

    def test_non_blocking_put_port(self):
        source = UVMComponent('uvm_ports_comp', None)
        sink = UVMComponent('uvm_ports_comp2', None)

        def try_put(item):
            pass
        setattr(sink, 'try_put', try_put)

        put_port = UVMNonBlockingPutPort('my_port', source)
        put_imp = UVMNonBlockingPutImp('put_imp', sink)
        put_port.connect(put_imp)
        put_port.resolve_bindings()
        put_port.try_put(0x1234)
        # TODO add assert

    def test_blocking_put_port(self):
        comp = UVMComponent('comp', None)
        put_port = UVMBlockingPutPort('my_port', comp)
        self.assertEqual(put_port.is_port(), True)

if __name__ == '__main__':
    unittest.main()
