
class RandomizeError(Exception):
    """
    Exception which is thrown when constrained randomization
    fails
    """
    pass


class TLMError(Exception):
    """
    Exception which is thrown when nonblocking TLM method fails
    fails
    """
    pass

class UVMFinishError(Exception):
    """
    Exception which is thrown when the test is finished
    """
    pass
