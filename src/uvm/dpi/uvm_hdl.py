

class uvm_hdl():

    dut = None

    @classmethod
    def set_dut(cls, dut):
        cls.dut = dut

    @classmethod
    def uvm_hdl_read(cls, path, value):
        if cls.dut is not None:
            curr_obj = cls.dut
            split = path.split('.')
            for spl in split:
                if hasattr(curr_obj, spl):
                    curr_obj = getattr(curr_obj, spl)
                else:
                    print("uvm_hdl_read did not found " + spl)
                    continue
            if curr_obj is not None:
                print("uvm_hdl_read append result " + hex(int(curr_obj)))
                value.append(int(curr_obj))
                return 1
            return 0
        else:
            raise Exception("dut is None. Use uvm_hdl.set_dut(dut) in your @cocotb.test()")


    @classmethod
    def uvm_hdl_deposit(cls, path, value):
        if cls.dut is not None:
            curr_obj = cls.dut
            split = path.split('.')
            print("uvm_hdl_deposit path is " + path)
            for spl in split:
                if hasattr(curr_obj, spl):
                    curr_obj = getattr(curr_obj, spl)
                else:
                    print("uvm_hdl_deposit did not found " + spl)
                    continue
            if curr_obj is not None:
                curr_obj <= value
                return 1
            return 0
        else:
            raise Exception("dut is None. Use uvm_hdl.set_dut(dut) in your @cocotb.test()")
