
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

    comments = None
    re_comm = re.compile('#')

    printed = False

    def match(self, node):
        prefix = node.prefix
        _debug("prefix is now |" + prefix + "|")
        #_debug("type is now |" + self.syms[node.type] + "|")
        _debug("Full node is **>" + str(node) + "<**")

        if len(prefix) > 0 and self.re_comm.search(prefix):
            keep_prefix, comments = self.split_prefix(prefix)
            self.comments = comments  # TODO strip comment signs #
            node.prefix = keep_prefix + '\n'
            _debug("Stored comments: " + self.comments)
            _debug("Preserved prefix: " + keep_prefix)
            return False
        elif node.type == self.syms.funcdef:  # TODO match function type
            _debug("Found funcdef |" + str(node) + "|")
            return True

    count = 0

    def transform(self, node, results):
        new = node.clone()
        _debug('results is ' + str(results))
        _debug('transform() call ' + str(self.count))
        self.count += 1
        indent = ""

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
                        indented_text = self.comments.replace('\n    ', '\n' + indent)
                        comments = (indent + '""" ' + indented_text +
                            '\n' + indent + '"""')
                        suite_children = [String(comments), Newline()]
                        suite_node.insert_child(1,
                                pytree.Node(syms.simple_stmt, suite_children))
                        self.comments = ""
                        break
                _debug("Breaking outer for-loop after suite")
                break
        if self.comments != "":
            raise Exception("self.comments != '', something went wrong badly")
        _debug("New node would be |" + str(new) + "|")
        return new

    def split_prefix(self, prefix):
        """ Splits the prefix string in two parts, one will be preserved as
        original prefix, and 2nd part will be the new comments """
        keep_prefix = ""
        comments = ""
        lines = prefix.split("\n")
        _debug("split_prefix lines are " + str(lines))
        before, after = self.split_empty(lines[0:-1])
        keep_prefix = "\n".join(before)
        comments = self.format_comments(after)
        return keep_prefix, comments

    def split_empty(self, lines):
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

    def format_comments(self, lines):
        return "\n".join(lines)
