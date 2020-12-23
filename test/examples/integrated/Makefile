
test: test-ubus

test-ubus:
	make -C ubus/examples UVM_TEST=test_read_modify_write COCOTB_RESULTS_FILE=results_ubus.xml
	make -C ubus/examples UVM_TEST=test_2m_4s COCOTB_RESULTS_FILE=results_ubus_2m_4s.xml

# TODO
test-codec:
	make -C codec/
