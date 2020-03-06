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


    def triple_dedent_at_end(self):
        if 1 == 0:
            if 2 == 3:
                pass

    # Move this to docstring of 'must_comment' function
    def must_comment(self):
        pass

    # Misc trailing class comments, keep this

    # And also this

# KEEP1
# KEEP2
# KEEP3
