
import cocotb
from cocotb.triggers import Timer, Join

from uvm_testlib import *

@cocotb.test(skip=False)
def test_tlm_nb_put_basic(dut):
    consumer = UVMTestConsumer('consumer', None)
    producer = UVMTestProducer('producer', None)

    producer.put_b_port.connect(consumer.put_b_imp)
    producer.get_b_port.connect(consumer.get_b_imp)
    producer.put_b_port.resolve_bindings()
    producer.get_b_port.resolve_bindings()

    producer.put_port.connect(consumer.put_imp)
    producer.get_port.connect(consumer.get_imp)
    producer.put_port.resolve_bindings()
    producer.get_port.resolve_bindings()

    if producer.put_b_port.m_if is None:
        raise Exception('put_b_port.m_if does not exist')

    pproc = cocotb.fork(producer.run_phase(None))
    #yield producer.run_phase(None)
    await consumer.wait_all_data()
    #yield [pproc.join(), wproc.join()]
    if consumer.count != 10:
        raise Exception('Consumer data count only {}'.format(consumer.count))

@cocotb.test(skip=False)
def test_tlm_exports(dut):
    producer = UVMTestProducer('producer', None)
    exporter = UVMTestExporter('exporter', None)
    exporter.connect_phase(None)
    producer.put_port.connect(exporter.put_export)
    producer.put_port.resolve_bindings()

    pproc = cocotb.fork(producer.run_phase(None))
    await exporter.wait_all_data()

@cocotb.test(skip=False)
def test_tlm_fifo(dut):
    fifo = UVMTLMAnalysisFIFO('fifo', None)
    fifo.write(1234);
    arr = []
    if not fifo.try_get(arr):
        raise Exception('FIFO try-get failed')

