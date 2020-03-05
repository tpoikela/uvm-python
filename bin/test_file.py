# File header
# Header row2

import_var = "ABC"

class ABC():

    # Nothing to do here
    test_var = ""

    # Is this indent?
    def __init__(self, name):  # EOL ignored
        self.name = name

    # Floating comments, not included

    # Returns something.
    # Accepts nothing.
    async def my_func(self):
        pass

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
        return 2 * some_args


# KEEP1
# KEEP2
# KEEP3
