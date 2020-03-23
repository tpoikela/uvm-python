
import unittest

from uvm.tlm1.uvm_analysis_port import (UVMAnalysisImp, UVMAnalysisExport,
    UVMAnalysisPort)


class TestUVMAnalysisPort(unittest.TestCase):

    def test_ports(self):
        from uvm.base.uvm_domain import UVMDomain
        from uvm.base.uvm_component import UVMComponent
        domains = UVMDomain.get_common_domain()

        class MyComp(UVMComponent):
            def build(self):
                self.analysis_imp = UVMAnalysisImp('ap', self)

            def write(self, t):
                self.written = True
                self.t = t

        imp = UVMComponent("port_parent", None)
        analysis_port = UVMAnalysisPort('aport', None)
        analysis_export = UVMAnalysisExport('my_export_in_test1', imp)
        targetComp = MyComp('my_comp', None)
        targetComp.build()
        analysis_port.connect(analysis_export)
        analysis_export.connect(targetComp.analysis_imp)
        #analysis_port.connect(targetComp.analysis_imp)
        analysis_port.resolve_bindings()

        analysis_port.write(12345)
        self.assertEqual(targetComp.written, True)
        self.assertEqual(targetComp.t, 12345)


if __name__ == '__main__':
    unittest.main()
