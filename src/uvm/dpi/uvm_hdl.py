

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
                    continue
            if curr_obj is not None:
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
            for spl in split:
                if hasattr(curr_obj, spl):
                    curr_obj = getattr(curr_obj, spl)
                else:
                    continue
            if curr_obj is not None:
                curr_obj.value = value
                return 1
            return 0
        else:
            raise Exception("dut is None. Use uvm_hdl.set_dut(dut) in your @cocotb.test()")
