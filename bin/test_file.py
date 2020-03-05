

class ABC():

    def __init__(self, name):
        self.name = name

    # Floating comments, not included

    # Returns something.
    # Accepts nothing.
    def my_func(self):
        pass


    # This function does X and Y.
    # Plus Z also.
    @classmethod
    def static_func(cls, some_args):
        return 2 * some_args
