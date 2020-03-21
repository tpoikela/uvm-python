
import cocotb
import re


class uvm_hdl():

    dut = None

    re_brackets = re.compile(r'(\w+)\[(\d+)\]')

    @classmethod
    def set_dut(cls, dut):
        cls.dut = dut
        cls.SIM_NAME = cocotb.SIM_NAME

    @classmethod
    def split_hdl_path(cls, path):
        if cls.SIM_NAME == 'Verilator':
            res = []
            spl = path.split('.')
            for name in spl:
                match = cls.re_brackets.search(name)
                if match is not None:
                    res.append(match[1])
                    # Throw exception if Conversion fails
                    res.append(int(match[2]))
                else:
                    res.append(name)
            return res
        else:
            return path.split('.')

    @classmethod
    def uvm_hdl_read(cls, path, value):
        if cls.dut is not None:
            curr_obj = cls.dut
            #split = path.split('.')
            split = cls.split_hdl_path(path)
            for spl in split:
                curr_obj = cls.get_next_obj(curr_obj, spl)
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
            #split = path.split('.')
            split = cls.split_hdl_path(path)
            for spl in split:
                curr_obj = cls.get_next_obj(curr_obj, spl)
                #if hasattr(curr_obj, spl):
                #    curr_obj = getattr(curr_obj, spl)
                #else:
                #    continue
            if curr_obj is not None:
                curr_obj.value = value
                return 1
            return 0
        else:
            raise Exception("dut is None. Use uvm_hdl.set_dut(dut) in your @cocotb.test()")


    @classmethod
    def get_next_obj(cls, curr_obj, spl):
        if isinstance(spl, int):
            #return curr_obj[spl]
            return curr_obj[spl]
        elif hasattr(curr_obj, spl):
            curr_obj = getattr(curr_obj, spl)
        return curr_obj
