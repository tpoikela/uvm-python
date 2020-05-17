
import cocotb
from cocotb.triggers import Timer, Join

from uvm.tlm1.uvm_ports import *
from uvm.tlm1.uvm_imps import *
from uvm.base.uvm_component import UVMComponent
from uvm.base.uvm_event import UVMEvent
from uvm.macros.uvm_object_defines import *
from uvm.seq.uvm_sequence_item import UVMSequenceItem


class UVMTestProducer(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.put_b_port = UVMBlockingPutPort('put_b_port', self)
        self.get_b_port = UVMBlockingGetPort('get_b_port', self)
        self.put_port = UVMPutPort('put_port', self)
        self.get_port = UVMGetPort('get_port', self)


    async def run_phase(self, phase):
        for i in range(0, 10):
            seq_item = UVMSequenceItem('item')
            exp_id = 2 * i + 1
            seq_item.set_transaction_id(exp_id)
            await self.put_b_port.put(seq_item)
            await Timer(1)
            arr = []
            await self.get_b_port.get(arr)
            got_id = arr[0].get_transaction_id()
            if got_id != exp_id:
                raise Exception("Item ID error. Got: {}, Exp: {}".format(got_id,
                    exp_id))
uvm_component_utils(UVMTestProducer)


class UVMTestConsumer(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.put_b_imp = UVMBlockingPutImp('put_b_imp', self)
        self.count = 0
        self.wait_n = 10
        self.my_event = UVMEvent('wait data')
        self.get_b_imp = UVMBlockingGetImp('get_b_imp', self)
        self.curr_item = None
        self.get_imp = UVMGetImp('get_imp', self)
        self.put_imp = UVMGetImp('put_imp', self)


    async def put(self, item):
        self.count += 1
        if self.count % 2 == 0:
            await Timer(1)
        else:
            await Timer(2)
        self.curr_item = item
        if self.count == self.wait_n:
            self.my_event.trigger(self.count)


    async def get(self, item):
        await Timer(12)
        item.append(self.curr_item)


    async def wait_all_data(self, n=10):
        self.wait_n = n
        await self.my_event.wait_trigger()


uvm_component_utils(UVMTestConsumer)


class UVMTestExporter(UVMComponent):

    def __init__(self, name, parent):
        UVMComponent.__init__(self, name, parent)
        self.put_export = UVMPutExport('put_export', self)
        #self.fifo =
        self.consumer = UVMTestConsumer('child_cons', self)

    def connect_phase(self, phase):
        self.put_export.connect(self.consumer.put_imp)


    async def wait_all_data(self, n = 10):
        await consumer.wait_all_data(n)


uvm_component_utils(UVMTestExporter)
