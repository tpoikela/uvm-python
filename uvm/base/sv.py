""" Some SystemVerilog system functions mocked here """

import re
import random
import cocotb
import copy
from cocotb.triggers import Lock, Timer
from cocotb.utils import get_sim_time
from cocotb.bus import Bus

from constraint import Problem

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
        formats = ["%b", "%0b", "%0d", "%d", "%s", "%0s", "%h", "%0h", "%f", "%p", "%0t", "%t"]
        for s in formats:
            msg = msg.replace(s, "{}")
        return msg.format(*args)

    @classmethod
    def random(cls):
        return random.randint(0, SV_MAX_INT_VALUE)

    @classmethod
    def urandom(cls):
        return random.randint(0, SV_MAX_INT_VALUE)

random.seed(0)

SV_MAX_INT_VALUE = (1 << 31) - 1



#def process(func):
#    return cocotb.coroutine(func)

SV_MAX_RAND_TRIES = 10000

class sv_obj():
    """ sv_obj implement some basic features from SystemVerilog objects like 
    constrained randomisation """

    def __init__(self):
        self._sv_seed = sv.urandom()
        self._sv_attr_rand = []
        self._sv_attr_rand_list = []
        self.problem = None
        random.seed(self._sv_seed)
        self._sv_rand_state = random.getstate()

    def constraint(self, key, func):
        """ Adds a contraint into the object """
        if self.problem is None:
            self.problem = Problem()
        #if isinstance(key, str):
        #    key = [key]
        var_list = self._add_constraints(key, func)
        # Add variables to a list for randomization
        for vv in var_list:
            self.rand(vv)

    def _add_constraints(self, key, func):
        var_list = []
        if isinstance(key, dict):
            for prop in key:
                cvars = self._add_single_constraint(prop, key[prop])
                var_list.extend(cvars)
        elif isinstance(key, list):
            for constr in key:
                [key, func] = constr
                cvars = self._add_single_constraint(key, func)
                var_list.extend(cvars)
        else:
            cvars = self._add_single_constraint(key, func)
            var_list.extend(cvars)
        return var_list


    def _add_single_constraint(self, key, func):
        var_list = []
        if isinstance(key, str):
            self.problem.addVariable(key, func)
            var_list.append(key)
        elif isinstance(key, list):
            if callable(func):
                self.problem.addConstraint(func, key)
            else:
                self.problem.addVariables(key, func)
            var_list.extend(key)
        elif isinstance(key, tuple):
            if callable(func):
                self.problem.addConstraint(func, key)
            else:
                raise Exception("2nd arg must be lambda function. Got: " +
                    str(func))
            for tt in key:
                var_list.append(tt)
        return var_list

    def rand(self, key):
        if isinstance(key, str) is True:
            if key not in self._sv_attr_rand:
                self._sv_attr_rand.append(key)
            if isinstance(getattr(self, key), list):
                self._sv_attr_rand_list.append(key)
        else:
            raise Exception("Key error. Key to rand() must be string. Got: " +
                    str(key))


    def randomize(self):
        """ Randomizes the value in object marked with rand() or constraint()
        """
        ok = True
        chosen_sol = {}
        # Non-random part which generates all solutions
        if self.problem is not None:
            sols = self.problem.getSolutions()
            print("sols is now " + str(sols))
            if len(sols) == 0:
                return False
            else:
                # TODO choose solutions randomly
                chosen_sol = sols[0]
        random.setstate(self._sv_rand_state)
        #random.seed(self._sv_seed)
        for key in self._sv_attr_rand:
            prop = getattr(self, key)
            if key in chosen_sol:
                setattr(self, key, chosen_sol[key])
            else:
                if isinstance(prop, sv_obj):
                    ok = ok and prop.randomize()
                elif isinstance(prop, int):
                    setattr(self, key, sv.urandom())
        return ok

    # TODO add better support for constraints
    def randomize_with(self, constr):
        # Create new object with inline constraints, then randomize it
        my_obj = None
        try:
            my_obj = copy.deepcopy(self)
        except:
            return False
        my_obj._add_constraints(constr, None)
        ok = my_obj.randomize()
        # If OK, assign randomizes props. Note that this will work only
        # if original object has property marked with rand()
        if ok is True:
            for key in self._sv_attr_rand:
                setattr(self, key, getattr(my_obj, key))
        return ok


class semaphore():

    def __init__(self, count=1):
        self.max_count = count
        self.count = count
        self.lock = Lock("sem_lock")
        self.locked = False

    @cocotb.coroutine
    def get(self, count=1):
        if self.count > count:
            self.count -= count
            yield Timer(0, "NS")
        elif count > self.max_count:
            raise Exception("Tried to get {} > max count {}".format(count,
                self.max_count))
        else:
            yield self.lock.acquire()
            self.locked = True
            self.count -= count

    def put(self, count=1):
        if self.count < self.max_count:
            self.count += count
            if self.locked is True:
                self.locked = False
                self.lock.release()

    def try_get(self, count=1):
        if self.count >= count:
            self.count -= count
            return True
        return False


class sv_if(Bus):

    def __init__(self, entity, name, signals,
            optional_signals=[], bus_separator="_", array_idx=None):
        Bus.__init__(self, entity, name, signals, optional_signals,
                bus_separator, array_idx)


