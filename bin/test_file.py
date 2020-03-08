# File header
# Header row2

import_var = "ABC"

# Also move this as a comment
# for 'comment_this_func.
#
# With extra empty line
def comment_this_func(aaa):
    return aaa * 2

## Move this as class comment docstring
## Add this to class
class ABC():

    def do_not_comment_this(self):
        pass

    # Nothing to do here
    test_var = ""

    # Is this indent?
    def __init__(self, name):  # EOL ignored
        self.name = name

    # Floating comments, not included

    # Returns something.
    # Accepts nothing.
    async def my_func(self):
        return "Something"

    # Block before var, must preserve
    # var indent
    my_arr = []

    #def no_comments(self, ok):
    #    ok = 2 * ok
    #    return ok

    # This function does X and Y.
    # Plus Z also.
    @classmethod
    def static_func(cls, some_args):
        # Preserve this as line comment, DONT TOUCH
        return 2 * some_args

    def has_existing_comment(self, a1, a2):
        """ Already docstring, Should not do anything
        """
        pass

    # Should convert into docstring
    def gets_docstring_too(self):
        raise Exception("Not done")
        # Do not move this to next function
    # Nor this one

    def no_comments_here(self):
        pass

    # Should convert to docstring
    def receives_docstring(self, a, b, c):
        # Started comment
        if a > b:
            # Need to do something
            c = b * a
        # Closing comments
        return (c * c)

    # Get comment also
    def short_func(self, k):
        pass


    def triple_dedent_at_end(self):
        if 1 == 0:
            if 2 == 3:
                pass
    # Misc class comments

    # Move this to docstring of 'must_comment' function
    def must_comment(self):
        pass

    # Misc trailing class comments, keep this

    # And also this

# KEEP1
# KEEP2
# KEEP3

# KEEP 4
# KEEP 5
