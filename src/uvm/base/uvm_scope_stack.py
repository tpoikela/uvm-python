# ------------------------------------------------------------------------------
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#   uvm-python NOTE: All code ported from SystemVerilog UVM 1.2 to
#   python. Original code structures (including comments)
#   preserved where possible.
# ------------------------------------------------------------------------------


class UVMScopeStack:
    def __init__(self):
        self.m_arg = ""
        self.m_stack = []

    def depth(self):
        return len(self.m_stack)

    def get(self):
        v = ""
        if len(self.m_stack) == 0:
            return self.m_arg
        get = self.m_stack[0]

        for i in range(1, len(self.m_stack)):
            v = self.m_stack[i]
            if v != "" and (v[0] == "[" or v[0] == "(" or v[0] == "{"):
                get = get + v
            else:
                get = get + "." + v

        if self.m_arg != "":
            if get != "":
                get = get + "." + self.m_arg
            else:
                get = self.m_arg
        return get

    def get_arg(self):
        return self.m_arg

    def set(self, s):
        self.m_stack = []
        self.m_stack.append(s)
        self.m_arg = ""

    def down(self, s):
        self.m_stack.append(s)
        self.m_arg = ""

    def down_element(self, element):
        _str = "[{}]".format(element)
        self.m_stack.append(_str)
        self.m_arg = ""

    def up_element(self):
        s = ""
        if len(self.m_stack) == 0:
            return
        s = self.m_stack.pop()
        if s != "" and s[0] != "[":
            self.m_stack.append(s)

    def up(self, separator="."):
        found = False
        s = ""
        while len(self.m_stack) > 0 and found is False:
            s = self. m_stack.pop()
            if separator == ".":
                if s == "" or (s[0] != "[" and s[0] != "(" and s[0] != "{"):
                    found = True
            else:
                if s != "" and s[0] == separator:
                    found = True
        self.m_arg = ""


    def set_arg(self, arg):
        if arg == "" or arg is None:
            return
        self.m_arg = arg

    def set_arg_element(self, arg, ele):
        tmp_value_str = str(ele)
        self.m_arg = {arg, "[", tmp_value_str, "]"}

    def unset_arg(self, arg):
        if arg == self.m_arg:
            self.m_arg = ""
