#//----------------------------------------------------------------------
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------
"""
Contains SystemVerilog (SV) system functions mocked/added
to make the porting SV to Python faster. Also, some functions which are
originally implemented in C-code, are moved here to implement them in
Python. As the backdoor access is implemented via cocotb-object interface,
we don't want to compile vendor-specific C-code for using the backdoor
access. cocotb is already hiding these details from us.
"""

from inspect import getframeinfo, stack
import re
import random
from typing import List, Any

import cocotb

from cocotb_coverage import crv
from cocotb.triggers import Lock, Timer, Combine, First
from cocotb.utils import get_sim_time, simulator
from cocotb_bus.bus import Bus

from .uvm_exceptions import RandomizeError

RET_ERR = 1
RET_OK = 0


def uvm_re_match(rex, _str):
    m = re.search(rex, _str)
    if m is not None:
        return RET_OK
    return RET_ERR


def uvm_glob_to_re(_str: str) -> str:
    """
    Converts a glob-style pattern to Python
    regular expression syntax.

    Returns:
        str: Glob converted to regular expression syntax.
    """
    if _str is None or _str == "":
        return ""
    if _str[0] == "/" and _str[-1] == "/":
        return _str
    # TODO replace * with .*
    res = _str.replace('.', '\\.')
    res = res.replace('*', '.*')
    res = res.replace('[', '\\[')
    res = res.replace(']', '\\]')
    res = res.replace('?', '.')
    # TODO add more substitutions
    return res


def uvm_split_string(_str, sep: str, split_vals: List[str]) -> List[str]:
    res = _str.split(sep)
    for val in res:
        split_vals.append(val)
    return res


class process():

    FINISHED = 0
    RUNNING = 1
    WAITING = 2
    SUSPENDED = 3
    KILLED = 4

    def __init__(self):
        self.status = process.RUNNING
        self.pid = -1


class sv:
    """ Namespace for SV functions """

    default_time_unit = "NS"

    @classmethod
    def clog2(cls, value):
        value = value - 1
        res = 0
        while value > 0:
            value = value >> 1
            res += 1
        return res

    @classmethod
    def is_simulator_active(cls):
        return simulator.is_running()

    @classmethod
    def display(cls, msg, *args):
        form_msg = sv.sformatf(msg, *args)
        print(form_msg)

    @classmethod
    def realtime(cls, unit=None):
        if cls.is_simulator_active() is False:
            return 0
        elif unit is None:
            return get_sim_time(cls.default_time_unit)
        else:
            return get_sim_time(unit)

    @classmethod
    def time(cls, unit=None):
        return cls.realtime(unit)

    @classmethod
    def fwrite(cls, fhandle, msg):
        if hasattr(fhandle, 'write'):
            fhandle.write(msg)
        else:
            print(msg)

    @classmethod
    def isunknown(cls, value):
        # TODO implement this properly
        return False

    @classmethod
    def bits(cls, var):
        if isinstance(var, int):
            return 32
        return 0

    @classmethod
    def fopen(cls, name, mode):
        return open(name, mode)

    @classmethod
    def fclose(cls, handle):
        handle.close()

    @classmethod
    def fdisplay(cls, fhandle, msg, *args):
        form_msg = sv.sformatf(msg, *args)
        form_msg += "\n"  # SV fdisplay behavior
        if fhandle != 0:
            if fhandle != 1:
                fhandle.write(form_msg)
            else:
                print(form_msg)

    @classmethod
    def cast(cls, dest: List, src: Any, T) -> bool:
        if isinstance(src, T):
            if hasattr(dest, 'append'):
                dest.append(src)
            return True
        return False

    STR_RE = re.compile(r'%(\d*[bdshxfpt])')
    formats = ["%b", "%0b", "%0d", "%d", "%s", "%0s", "%h", "%0h", "%f",
            "%p", "%0t", "%t", "%x"]

    @classmethod
    def sscanf(cls, scan_str: str, formats: str, *results):
        """
        Scans the input string with given format pattern.

        Args:
            scan_str (str): Input string to be scanned.

        Returns:
            list: List of matched strings
        """

        res = []
        re_list = get_regex_list(formats)
        acc = ""
        curr_match = ""
        for char in scan_str:
            acc += char
            prefix = re_list[0][2]
            if re_list[0][0].match(acc):
                # Keep adding chars while match holds
                curr_match += char
            elif len(curr_match) > 0:
                # When it stops matching, we're done for curr match
                value = re_list[0][1](curr_match)
                re_list.pop(0)  # Remove matched regex
                res.append(value)  # Append results
                curr_match = ""
                acc = ""
                if len(re_list) == 0:  # We're done, all matched
                    break
            elif (len(acc) >= len(prefix) and acc != prefix):
                acc = ""

        # Special case if last letter is a matching one
        if len(curr_match) > 0:
            # When it stops matching, we're done for curr match
            value = re_list[0][1](curr_match)
            re_list.pop(0)  # Remove matched regex
            res.append(value)  # Append results

        # TODO check from SV spec if all format specifiers must match
        if len(re_list) > 0:  # Regex left unmatched
            return []
        return res

    @classmethod
    def sformatf(cls, msg: str, *args) -> str:
        """
        This is to make porting faster, but should be switched to native python
        formatting inside UVM code

        Args:
            msg (str): String to format containing format specifiers.
            args (*any): Values that are used in formatting.
        Returns:
            str: Formatted string
        """
        #formats = {"%t": "%d", "%0t": "%0d"}
        #for s in formats:
        #    msg = msg.replace(s, formats[s])
        #return sformatf(msg, *args)
        # TODO substitute old types %s/%d etc with {}
        #new_msg = cls.STR_RE.sub(r'{:\1}', msg)
        #print("new_msg is " + new_msg)
        for s in cls.formats:
            if s == "%h" or s == "%0h":
                msg = msg.replace(s, "{:X}")
            else:
                msg = msg.replace(s, "{}")
        return msg.format(*args)

    @classmethod
    def random(cls):
        return random.randint(0, SV_MAX_INT_VALUE)

    @classmethod
    def urandom(cls):
        return random.randint(0, SV_MAX_INT_VALUE)

    @classmethod
    def urandom_range(cls, start, stop):
        return random.randint(start, stop)

    @classmethod
    def sv_assert(cls, val, msg=""):
        if not val:
            caller = getframeinfo(stack()[1][0])
            filename = caller.filename
            line = caller.lineno
            print("$error: {},{} Assertion failed. {}".format(filename, line, msg))

    @classmethod
    def test_plusargs(cls, name):
        arr = []
        sv.value_plusargs(name, arr)
        if len(arr) > 0:
            return True
        return False

    @classmethod
    def value_plusargs(cls, arg_str, arr):
        plusarg_dict = cocotb.plusargs
        for name in plusarg_dict:
            full_arg = name + '='
            for i in range(len(full_arg)):
                if full_arg[i] != arg_str[i]:
                    break
                elif i == len(full_arg) - 1:
                    arr.append(plusarg_dict[name])
                    return plusarg_dict[name]

    @classmethod
    async def fork_join(cls, forks):
        join_list = list(map(lambda t: t.join(), forks))
        await Combine(*join_list)

    @classmethod
    async def fork_join_any(cls, forks):
        join_list = list(map(lambda t: t.join(), forks))
        await First(*join_list)

    @classmethod
    async def fork_join_none(cls, procs):
        res = []
        for proc in procs:
            res.append(cocotb.fork(proc))
        return res


    @classmethod
    def set_bit(cls, int_val: int, idx: int, bit_val=1) -> int:
        if bit_val == 1:
            return int_val | (1 << idx)
        if bit_val == 0:
            return cls.clear_bit(int_val, idx)
        raise ValueError("bit_val must be 0/1. Got: " + str(bit_val))

    @classmethod
    def get_bit(cls, int_val: int, idx: int) -> int:
        return (int_val >> idx) & 0x1

    @classmethod
    def clear_bit(cls, int_val: int, idx: int) -> int:
        return int_val & ~(1 << idx)

    @classmethod
    def get_vector_of_ones(cls, width) -> int:
        return int(''.join(['1' for bit in range(width)]),2)


random.seed(0)

SV_MAX_INT_VALUE = (1 << 31) - 1


class sv_obj(crv.Randomized):
    """ sv_obj implement some basic features from SystemVerilog objects like
    constrained randomisation """

    num_objs = 0

    def __init__(self):
        crv.Randomized.__init__(self)
        self._sv_seed = sv.urandom()
        self._sv_rand_obj = []
        random.seed(self._sv_seed)
        self._sv_rand_state = random.getstate()
        self._rand_mode = True
        sv_obj.num_objs += 1
        # print("Created SVObj@{}: Seed {}, State: {}".format(sv_obj.num_objs,
        # self._sv_seed, self._sv_rand_state))


    def constraint(self, c):
        """
        Adds a constraint into the object.

        Args:
            c (constraint): Lambda expression or function.

        """
        self.add_constraint(c)


    def rand_mode(self, mode):
        if mode:
            self._rand_mode = True
        else:
            self._rand_mode = False


    def rand(self, key, val_list=None):
        """
        Mark given class property as randomized. A call to `sv_obj.randomize()`
        will then randomize this value.

        Args:
            key (str): Name of the property.
            val_list (list|range): Optional constraints for randomisation.
        """
        if hasattr(key, "randomize"):
            if val_list is None:
                self._sv_rand_obj.append(key)
        elif hasattr(self, key) and val_list is None:
            if self.is_valid_rand_type(key):
                self._sv_rand_obj.append(key)
            else:
                raise TypeError('Attr {} of {} requires range or value list for rand()'
                    .format(key, type(getattr(self, key))))
        else:
            self.add_rand(key, val_list)

    def is_valid_rand_type(self, key):
        return not isinstance(getattr(self, key), (int, str, float))

    def pre_randomize(self):
        pass

    def post_randomize(self):
        pass

    def randomize(self, recurse=True):
        """
        Randomizes values in object marked with rand(). Recurses to sub-objects
        randomizing them as well.
        """
        if self._rand_mode is False:
            return True
        try:
            random.setstate(self._sv_rand_state)
            self.pre_randomize()
            ok = True
            if recurse:
                for entry in self._sv_rand_obj:
                    obj = entry
                    if hasattr(self, entry):
                        obj = getattr(self, entry)
                    ok = ok and obj.randomize()
            super().randomize()
            self.post_randomize()
            self._sv_rand_state = random.getstate()
            return True and ok
        except Exception as e:
            raise RandomizeError('randomize() failed for ' + str(self) + '\n' +
                    str(e))
            # return False


    def randomize_with(self, *constr):
        if self._rand_mode is False:
            return True
        try:
            self.pre_randomize()
            ok = True
            for entry in self._sv_rand_obj:
                obj = entry
                if hasattr(self, entry):
                    obj = getattr(self, entry)
                ok = ok and obj.randomize()
            super().randomize_with(*constr)
            self.post_randomize()
            return True and ok
        except Exception as e:
            raise RandomizeError('randomize() failed for ' + str(self) + '\n' + str(e))
            # return False


class semaphore():

    def __init__(self, count=1):
        self.max_count = count
        self.count = count
        self.lock = Lock("sem_lock")
        self.locked = False


    async def get(self, count=1):
        if self.count > count:
            self.count -= count
            await Timer(0, "NS")
        elif count > self.max_count:
            raise Exception("Tried to get {} > max count {}".format(count,
                self.max_count))
        else:
            await self.lock.acquire()
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


def sformatf(fmt, *args):
    return fmt % args


def cat(*args):
    ret = ""
    for a in args:
        ret += a

    return ret



async def wait(cond, ev):
    if not callable(cond):
        raise Exception("wait expects the first arguments to be callable")

    while True:
        if cond():
            break
        else:
            await ev.wait()
            ev.clear()

# Each letter matches a pair:
#   1. Regex to parse that value from string
#   2. Lambda function to convert the value
RE_FORMATS = {
    "d": [re.compile(r'^(-?[0-9_]+)$'), lambda s: int(s, 10), '-'],
    "h": [re.compile(r'^(0x[0-9a-fA-F_]+)$'), lambda s: int(s, 16), '0x'],
    "b": [re.compile(r'^([01_]+)$'), lambda s: int(s, 2), ''],
    "o": [re.compile(r'^(o[01_]+)$'), lambda s: int(s, 8), 'o'],
    "f": [re.compile(r'^(-?[0-9]*\.?[0-9]*)$'), float, '-'],
    "s": [re.compile(r'^(\w+)$'), lambda s: s, '']
}


def get_regex_list(formats):
    acc = ""
    re_format = re.compile("^%([dshbfo])$")
    results = []
    for char in formats:
        acc += char
        if len(acc) == 2:
            match = re_format.match(acc)
            if match:
                if match[1] in RE_FORMATS:
                    results.append(RE_FORMATS[match[1]])
                    acc = ""
                else:
                    raise Exception("Format spec {} not supported".format(match))
            else:
                acc = acc[1]  # Discard 1st character out of 2
    return results
