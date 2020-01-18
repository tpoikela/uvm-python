
import unittest
from uvm import (UVM_IMP_COMMON, UVM_TLM_NONBLOCKING_PUT_MASK)


class TestUVMTLMImps(unittest.TestCase):

    def test_uvm_imp_common(self):
        from uvm.base.uvm_port_base import UVMPortBase
        from uvm.base.uvm_component import UVMComponent

        class MyTest():
            pass
        MyTest = UVM_IMP_COMMON(MyTest, UVM_TLM_NONBLOCKING_PUT_MASK, 'MyTest')
        obj = MyTest('MyPort', UVMComponent('xxx', None))
        self.assertEqual(obj.get_type_name(), 'MyTest')
        self.assertEqual(obj.is_imp(), True)
        self.assertEqual(isinstance(obj, UVMPortBase), True)


if __name__ == '__main__':
    unittest.main()
