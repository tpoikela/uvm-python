""" Some SystemVerilog system functions mocked here """

import re
import random
import cocotb
from cocotb.triggers import Lock, Timer
from cocotb.utils import get_sim_time

RET_ERR = 1
RET_OK = 0


def uvm_re_match(rex, _str):
    m = re.search(rex, _str)
    if m is not None:
        return RET_OK
    return RET_ERR


def uvm_glob_to_re(_str):
    if _str is None or _str == "":
        return ""
    if _str[0] == "/" and _str[-1] == "/":
        return _str
    # TODO replace * with .*
    res = _str.replace('.', '\\.')
    res = res.replace('*', '.*')
    # TODO add more substitutions
    return res


class process():

    FINISHED = 0
    RUNNING = 1
    WAITING = 2
    SUSPENDED = 3
    KILLED = 4

    def __init__(self):
        self.status = process.RUNNING


class sv:

    @classmethod
    def realtime(cls, unit=None):
        if unit is None:
            return get_sim_time()
        else:
            return get_sim_time(unit)

    @classmethod
    def fwrite(cls, fhandle, msg):
        if hasattr(fhandle, 'write'):
            fhandle.write(msg)
        else:
            print(msg)

    @classmethod
    def fopen(cls, name, mode):
        return open(name, mode)

    @classmethod
    def fclose(handle):
        handle.close()

    @classmethod
    def fdisplay(cls, fhandle, msg, *args):
        form_msg = sv.sformatf(msg, *args)
        if fhandle != 0:
            if fhandle != 1:
                fhandle.write(form_msg)
            else:
                print(form_msg)

    @classmethod
    def cast(cls, dest, src, T):
        if isinstance(src, T):
            if hasattr(dest, 'append'):
                dest.append(src)
            return True
        return False

    @classmethod
    def sformatf(cls, msg, *args):
        # TODO substitute old types %s/%d etc with {}
        formats = ["%0d", "%d", "%s", "%0s", "%h", "%f", "%p", "%0t", "%t"]
        for s in formats:
            msg = msg.replace(s, "{}")
        return msg.format(*args)

random.seed(0)

SV_MAX_INT_VALUE = (1 << 31) - 1

def urandom():
    return random.randint(0, SV_MAX_INT_VALUE)


#def process(func):
#    return cocotb.coroutine(func)


class sv_obj():

    def __init__(self):
        self._sv_seed = urandom()
        self._sv_attr_rand = []

    def constraint(self, key, func):
        self._sv_attr_rand_constr.append(key)

    def rand(self, key):
        self._sv_attr_rand.append(key)

    def randomize(self):
        random.seed(self._sv_seed)
        for key in self._sv_attr_rand:
            setattr(self, key, urandom())

class semaphore():

    def __init__(self, count=1):
        self.count = count
        self.lock = Lock("sem_lock")

    @cocotb.coroutine
    def get(self, count=1):
        if self.count > 0:
            self.count -= 1
            yield Timer(0, "NS")
        else:
            yield self.lock.acquire()
            self.count -= 1

    def put(self, count=1):
        self.count += 1
        if self.count == 1:
            self.lock.release()


import unittest

class TestSV(unittest.TestCase):

    def test_uvm_glob_to_re(self):
        str1 = "uvm_*"
        res1 = uvm_glob_to_re(str1)
        self.assertEqual(res1, 'uvm_.*')
        str2 = "uvm_*xxx*yyy"
        res2 = uvm_glob_to_re(str2)
        self.assertEqual(res2, 'uvm_.*xxx.*yyy')
        str3 = "my_top.xxx*"
        res3 = uvm_glob_to_re(str3)
        self.assertEqual(res3, 'my_top\\.xxx.*')

    def test_cast(self):
        pass

    def test_sformatf(self):
        str1 = sv.sformatf("Number: %0d, String: %s", 555, "xxx")
        self.assertRegex(str1, "Number: 555")
        self.assertRegex(str1, "String: xxx")


if __name__ == '__main__':
    unittest.main()
