
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

DEBUG = False

re_empty = re.compile(r'^\s*$')
re_dedent = re.compile(r'\n    #')
re_dedent2 = re.compile(r'\n#')
re_code_block = re.compile(r'^\s+#?\|')
re_hash_only = re.compile('^\s+#$')

rst_code_block = '.. code-block:: python'

def _debug(*args):
    if DEBUG is True:
        print(*args)


def lined(msg):
    return "|" + msg + "|"


class CommentStruct():

    def __init__(self, comm, no_funcs, node):
        self.comments = comm
        self.no_funcs = no_funcs.copy()
        self.node = node
        self.func_name = ""
        _debug("ComMStruct added no_funcs " + str(no_funcs) + ', node: '
            + str(node))

    def set_func(self, func):
        self.func_name = func


class FixFuncComments(fixer_base.BaseFix):

    explicit = False  # The user must ask for this fixers
    printed = False

    COMMA = pytree.Leaf(token.COMMA, ",")
    COLON = pytree.Leaf(token.COLON, ":")
    COMMENT = pytree.Leaf(token.COMMENT, '#')
    SEPS = (COMMA, COLON)

    re_comm = re.compile('#')
    re_hash_space = re.compile(r'\n# ')
    re_link = re.compile(r'~(\w+)~')
    re_link2 = re.compile(r'<(\w+)>')

    comments = []
    has_def = False
    has_name = False
    def_name = ""
    func_name_seen = {}

    class_stack = []

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

        if node.type == self.syms.classdef:
            self.class_stack.pop()
            while len(self.comments) > 0:
                self.restore_last_comment()
            self.reset_func_data()
            return False

        # Ignore nested classes
        if len(self.class_stack) > 1:
            return False

        # We detect function start here
        if node.type == token.NAME:
            if node.value == 'class':
                # TODO extract name properly
                self.class_stack.append('class')
                if len(self.class_stack) > 1:
                    print("WARN. Ignoring nested classes")
            if self.has_def is False and node.value == 'def':
                _debug("[match]: NAME with value |" + node.value + "|")
                self.has_def = True
            elif node.value == 'class':
                if len(self.comments) > 0:
                    self.restore_last_comment()
                return False
            elif self.has_def is True and self.has_name is False:
                self.has_name = True
                self.def_name = node.value
                self.func_indent[self.def_name] = 0
                _debug("[match]: Function " + node.value + " BEGIN")
                # Check here if we have indent/dedent comment available
                self.func_name_seen[node.value] = True

        # Extract Returns/Args/Raises for the docstring
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

        # Keep track of function indent
        if self.has_def is True and self.has_name is True:
            if node.type == token.INDENT:
                self.func_indent[self.def_name] += 1
            if node.type == token.DEDENT:
                self.func_indent[self.def_name] -= 1

        # Store comments from prefix, if accepted token
        if len(prefix) > 0 and self.re_comm.search(prefix):
            if self.check_node_type_for_comments(node) is False:
                return False

            # We're inside a function
            if self.has_def is True and self.has_name is True:
                if (self.func_indent[self.def_name] != 0 and
                        not re_dedent.search(prefix)):
                    _debug("[match]: Discard prefix, no indent match: " +
                        str(prefix))
                    return False
                if len(self.class_stack) == 0:
                    if (self.func_indent[self.def_name] != 0 and
                            not re_dedent2.search(prefix)):
                        _debug("[match]: Discard prefix (not in class), no indent match: " +
                            str(prefix))
                        return False

            keep_prefix, comments = self.split_prefix(prefix)
            if len(comments) > 0:
                comm_struct = CommentStruct(comments,
                        list(self.func_name_seen.keys()), node)
                comm_struct.set_func(self.def_name)
                self.comments.append(comm_struct)  # TODO strip comment signs #
                node.prefix = keep_prefix
                _debug("[match] Stored comments: |" + comments + "|")
                _debug("[match] Preserved prefix: |" + keep_prefix + "|")
            else:
                _debug("[match] Ignored empty comments: |" + comments + "|")
            return False
        elif self.should_add_to(node):  # TODO match function type
            _debug("[match] Found funcdef |" + str(node) + "|")
            return True
        return False


    def transform(self, func_node, results):
        #new = func_node.clone()
        new = func_node
        _debug('transform(): Started for function ' + lined(self.def_name))
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
                    # Need to skip first NEWLINE token
                    if found_ind is False:
                        if cc2.type == token.INDENT:
                            indent = cc2.value  # Preserve correct indent
                            _debug("In suite.children! Updated indent to |" + indent + "|")
                            found_ind = True
                    else:
                        func_name = self.get_func_name(func_node)
                        comm_struct = self.comments[0]
                        curr_comments = comm_struct.comments
                        if func_name not in comm_struct.no_funcs:

                            if self.re_hash_space.search(curr_comments):
                                indented_text = curr_comments.replace('# ', indent)
                            else:
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
        _debug("restore() split before merge " + str(split))
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
        indented_text = text.replace('//', '')
        indented_text = indented_text.replace('# ', '')
        split = indented_text.split("\n")

        new_split = []
        in_code_block = False
        for i, line in enumerate(split):
            split[i] = self.re_link.sub(r'`\1`', line)
            split[i] = self.re_link2.sub(r'`\1`', split[i])

            if re_code_block.search(split[i]):
                split[i] = split[i].replace('#|', '')
                if in_code_block is False:
                    in_code_block = True
                    new_split.append(indent + rst_code_block)
                    new_split.append('')
            else:
                in_code_block = False

            if len(split[i]) < len(indent):
                split[i] = indent + split[i]
            split[i] = re_hash_only.sub('', split[i])
            new_split.append(split[i])

        if func_name in self.func_args:
            args = self.func_args[func_name]
            new_split.append(indent + "Args:")
            for arg in args:
                if arg not in ['None', 'True', 'False']:
                    new_split.append(indent + "    " + arg + ": ")
        if func_name in self.func_return:
            new_split.append(indent + "Returns:")
        if func_name in self.func_raises:
            new_split.append(indent + "Raises:")
        return "\n".join(new_split)


    def reset_func_data(self):
        """ Resets all collected function data """
        self.comments = []
        self.reset_state()
        self.def_name = ""
        self.func_name_seen = {}
        self.func_args = {}
        self.func_return = {}
        self.func_raises = {}
        self.func_indent = {}
