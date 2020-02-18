
import unittest

from uvm.reg.uvm_reg_predictor import UVMRegPredictor, UVMPredictS

from uvm.uvm_unit import (create_reg, create_reg_block, TestPacket,
    TestRegAdapter)


class TestUVMRegPredictor(unittest.TestCase):

    def test_create_predictor(self):
        predict = UVMRegPredictor("predictor_123", None)
        self.assertEqual(predict.get_name(), "predictor_123")

    def test_predict(self):
        predict = UVMRegPredictor("predictor_345", None)
        predict.adapter = TestRegAdapter()
        rg = create_reg_block('my_block')
        rg.lock_model()
        predict.map = rg.default_map
        predict.bus_in.write(TestPacket(123, 0x0))

    def test_check_phase(self):
        predict = UVMRegPredictor("predictor_567", None)
        predict.check_phase(phase=None)
        predict.m_pending[create_reg('test_reg')] = UVMPredictS()
        predict.check_phase(phase=None)


if __name__ == '__main__':
    unittest.main()
