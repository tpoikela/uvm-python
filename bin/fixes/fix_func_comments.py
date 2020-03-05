
"""Fixer that changes line comments preceding funcdef into a docstring
inside that function.

Example:
    # Returns some stuff.
    # No args accepted.
    def my_func():

Output:
    def my_func():
        "" Returns some stuff.
        No args accepted.
        ""

"""

import re
from lib2to3 import pytree, fixer_base
from lib2to3.pgen2 import token
from lib2to3.fixer_util import (Assign, Attr, Name, is_tuple, is_list, syms,
    String, Newline)
from lib2to3.pygram import python_symbols


def _debug(*args):
    print(*args)


def is_child_of(child, parent):
    curr_node = child
    print("child node is " + str(child))
    while curr_node is not None:
        curr_node = curr_node.getattr('parent')
        if curr_node == parent:
            return True
    return False


def lined(msg):
    return "|" + msg + "|"

class CommentStruct():

    def __init__(self, comm, no_funcs, node):
        self.comments = comm
        self.no_funcs = no_funcs.copy()
        self.node = node
        self.func_name = ""
        print("ComMStruct added no_funcs " + str(no_funcs) + ', node: '
                + str(node))

    def set_func(self, func):
        self.func_name = func


class FixFuncComments(fixer_base.BaseFix):

    explicit = False  # The user must ask for this fixers

    #PATTERN = """
    #any<(not(',') any)+ ',' ((not(',') any)+ ',')* [not(',') any]>
    #"""

    #PATTERN = """
    #suite<text=(any)+>
    #"""

    COMMA = pytree.Leaf(token.COMMA, ",")
    COLON = pytree.Leaf(token.COLON, ":")
    COMMENT = pytree.Leaf(token.COMMENT, '#')
    SEPS = (COMMA, COLON)

    comments = []
    re_comm = re.compile('#')

    printed = False

    has_def = False
    has_name = False
    def_name = ""
    func_name_seen = {}

    func_args = {}
    func_return = {}
    func_raises = {}
    func_indent = {}


    def reset_state(self):
        self.has_def = False
        self.has_name = False


    def get_func_name(self, node):
        for cc in node.children:
            if cc.type == token.NAME:
                if cc.value != 'def':
                    return cc.value
        raise Exception("No name found for " + str(node))


    def should_add_to(self, node):
        if node.type == self.syms.funcdef:
            func_name = self.get_func_name(node)
            return func_name in self.func_name_seen


    def match(self, node):
        prefix = node.prefix
        if len(prefix) > 0:
            _debug("[match]: prefix is now |" + prefix + "|")
        _debug("[match]: Full node is **>" + str(node) + "<**")

        # We detect function start here
        if node.type == token.NAME:
            if node.value == 'def':
                _debug("[match]: NAME with value |" + node.value + "|")
                self.has_def = True
            elif self.has_def is True and self.has_name is False:
                self.has_name = True
                self.def_name = node.value
                self.func_indent[self.def_name] = 0
                _debug("[match]: Function " + node.value + " BEGIN")
                # Check here if we have indent/dedent comment available
                self.func_name_seen[node.value] = True

        if node.type == self.syms.return_stmt:
            self.get_func_return(node)
        if node.type == self.syms.typedargslist:
            self.func_args[self.def_name] = self.get_func_args(node)
        if node.type == self.syms.raise_stmt:
            self.func_raises[self.def_name] = True


        # Discard previous comments if required
        if self.has_def is False and self.has_name is False:
            if node.type == self.syms.simple_stmt:
                if len(self.comments) > 0:
                    self.restore_last_comment()

        if self.has_def is True and self.has_name is True:
            if node.type == token.INDENT:
                self.func_indent[self.def_name] += 1
            if node.type == token.DEDENT:
                self.func_indent[self.def_name] -= 1

        # Store comments from prefix, if accepted token
        if len(prefix) > 0 and self.re_comm.search(prefix):
            if self.check_node_type_for_comments(node) is False:
                return False
            if self.has_def is True and self.has_name is True:
                if self.func_indent[self.def_name] != 0:
                    _debug("[match]: Discard prefix, no indent match: " +
                        str(prefix))
                    return False

            keep_prefix, comments = self.split_prefix(prefix)
            comm_struct = CommentStruct(comments,
                    list(self.func_name_seen.keys()), node)
            comm_struct.set_func(self.def_name)
            self.comments.append(comm_struct)  # TODO strip comment signs #
            node.prefix = keep_prefix
            _debug("[match] Stored comments: " + comments)
            _debug("[match] Preserved prefix: |" + keep_prefix + "|")
            return False
        elif self.should_add_to(node):  # TODO match function type
            _debug("[match] Found funcdef |" + str(node) + "|")
            return True
        return False

    count = 0

    def transform(self, func_node, results):
        #new = func_node.clone()
        new = func_node
        _debug('transform(): results is ' + str(results))
        _debug('transform(): call ' + str(self.count))
        self.count += 1
        indent = ""

        if len(self.comments) == 0:
            self.reset_state()
            return new

        for child in new.children:
            if child.type == self.syms.suite:
                suite_node = child
                _debug("Found suite! Indent is |" + indent + "|")
                found_ind = False

                for cc2 in suite_node.children:
                    # Need to skip first NEWLINE
                    if found_ind is False:
                        if cc2.type == token.INDENT:
                            indent = cc2.value  # Preserve correct indent
                            found_ind = True
                    else:
                        func_name = self.get_func_name(func_node)
                        comm_struct = self.comments[0]
                        curr_comments = comm_struct.comments
                        if func_name not in comm_struct.no_funcs:
                            indented_text = curr_comments.replace('\n    ', '\n' + indent)
                            indented_text = self.format_docstring(func_name,
                                    indented_text, indent)
                            comments = (indent + '""" ' + indented_text +
                                '\n' + indent + '"""')
                            suite_children = [String(comments), Newline()]
                            suite_node.insert_child(1,
                                    pytree.Node(syms.simple_stmt, suite_children))
                            self.comments.pop(0)
                        else:
                            # If comment was found after current func, we want
                            # to keep it for the next function, else restore
                            if comm_struct.func_name != func_name:
                                self.restore_last_comment()
                            self.reset_state()
                            return func_node
                        break
                _debug("Breaking outer for-loop after suite")
                break
        _debug("New node would be |" + str(new) + "|")
        self.reset_state()
        return new


    def split_prefix(self, prefix):
        """ Splits the prefix string in two parts, one will be preserved as
        original prefix, and 2nd part will be the new comments """
        keep_prefix = ""
        comments = ""
        lines = prefix.split("\n")
        _debug("split_prefix() lines are " + str(lines))
        before, after = self.split_empty(lines[0:-1])

        last_line = lines[-1]
        before.append('')
        before.append(last_line)

        keep_prefix = "\n".join(before)
        comments = self.join_comments(after)
        return keep_prefix, comments


    def split_empty(self, lines):
        """ If there are 2 sections of comments, need to split that into 2 or
        more parts. FInd the last empty line, then use that line as split
        point.
        """
        re_empty = re.compile(r'^\s*$')
        before = []
        after = []
        last_empty = -1
        for i, line in enumerate(lines):
            if re_empty.match(line):
                _debug("split_empty EMPTY LINE @" + str(i))
                last_empty = i

        if last_empty != -1:
            before = lines[0:last_empty]
            after = lines[last_empty:]
        else:
            after = lines
        return before, after


    def join_comments(self, lines):
        return "\n".join(lines)


    def check_node_type_for_comments(self, node):
        return (node.type == token.NAME or node.type == token.INDENT
            or node.type == token.DEDENT or node.type == token.AT)


    def restore_last_comment(self):
        comm_struct = self.comments.pop(0)
        node = comm_struct.node
        split = node.prefix.split("\n")
        print("restore() split before merge " + str(split))
        new_prefix = ("\n").join(split[0:-1])
        new_prefix += comm_struct.comments
        new_prefix += "\n" + split[-1]
        node.prefix = new_prefix
        _debug("Recreated node.prefix as " +
            lined(comm_struct.node.prefix))


    def get_func_args(self, node):
        res = []
        for child in node.children:
            if child.type == token.NAME and child.value != 'self':
                res.append(child.value)
        return res


    def get_func_return(self, node):
        res = []
        if self.def_name in self.func_return:
            res = self.func_return[self.def_name]
        else:
            self.func_return[self.def_name] = res
        res.append('Returns')


    def format_docstring(self, func_name, text, indent):
        indented_text = text.replace('# ', '')
        indented_text = indented_text.replace('//', '')
        split = indented_text.split("\n")

        if func_name in self.func_args:
            args = self.func_args[func_name]
            split.append(indent + "Args:")
            for arg in args:
                split.append(indent + "    " + arg + ": ")
        if func_name in self.func_return:
            split.append(indent + "Returns:")
        if func_name in self.func_raises:
            split.append(indent + "Raises:")
        return "\n".join(split)
