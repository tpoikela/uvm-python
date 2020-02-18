from cocotb_test.run import run


def test_hello_world():
    run(
        verilog_sources=['../common_stub.v'],
        toplevel="common_stub",
        module="hello_world"
    )
