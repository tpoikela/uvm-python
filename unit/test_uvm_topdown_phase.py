
import unittest
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_topdown_phase import UVMTopdownPhase
from uvm.base.uvm_phase import UVMPhase
from uvm.base.uvm_object_globals import *


class TestUVMTopdownPhase(unittest.TestCase):


    def test_traverse(self):
        c1 = UVMComponent('uvm_test_top__test_uvm_topdown_phase', None)
        c2 = UVMComponent('sub_c1', c1)
        c3 = UVMComponent('sub_c2', c1)
        c4 = UVMComponent('sub_c2_c4', c2)
        td_phase = UVMTopdownPhase('MyPhase')
        states = [UVM_PHASE_STARTED, UVM_PHASE_READY_TO_END, UVM_PHASE_ENDED]
        phase = UVMPhase('MyActualPhase')
        for state in states:
            td_phase.traverse(c1, phase, state)

        children_c1 = []
        c1.get_children(children_c1)

        children_c2 = []
        c2.get_children(children_c2)
        self.assertEqual(len(children_c2), 1)
        self.assertEqual(children_c2[0].get_name(), c4.get_name())


if __name__ == '__main__':
    unittest.main()
