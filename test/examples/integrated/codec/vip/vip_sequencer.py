

from uvm import *

class vip_sequencer(UVMSequencer):

    def __init__(self, name, parent):
        super().__init__(name, parent)

uvm_component_utils(vip_sequencer)
