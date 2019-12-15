
import cocotb
import inspect
import re


class UVMDebug:
    DEBUG = False
    ONLY = ""
    INSPECT = False

    @classmethod
    def full_debug(cls):
        UVMDebug.ONLY = ""
        UVMDebug.INSPECT = True
        UVMDebug.DEBUG = True

    def debug_only(cls, name):
        UVMDebug.ONLY = name
        UVMDebug.INSPECT = False
        UVMDebug.DEBUG = True

    @classmethod
    def no_debug(cls):
        UVMDebug.ONLY = ""
        UVMDebug.INSPECT = False
        UVMDebug.DEBUG = False


def uvm_debug(self_or_cls, fname, msg):
    if UVMDebug.DEBUG is True:
        caller = ""
        if UVMDebug.INSPECT:
            curr_frame = inspect.currentframe()
            caller_frame = inspect.getouterframes(curr_frame, 2)
            #caller2_frame = inspect.getouterframes(caller_frame, 2)
            #print str(caller_frame).split()
            caller = ' - Caller: ' + caller_frame[1][3]
        name = ""
        if hasattr(self_or_cls, '__class__'):
            name = self_or_cls.__class__
        else:
            name = self_or_cls
        if UVMDebug.ONLY == "":
            #cocotb.log.info("[DEBUG] {} - {}() - {}".format(name, fname, msg) + caller)
            print("[DEBUG] {} - {}() - {}".format(name, fname, msg) + caller)
        else:
            if re.search(UVMDebug.ONLY, name):
                #cocotb.log.info("[DEBUG] {} - {}() - {}".format(name, fname, msg) + caller)
                print("[DEBUG] {} - {}() - {}".format(name, fname, msg) + caller)
