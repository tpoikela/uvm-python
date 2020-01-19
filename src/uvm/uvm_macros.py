
from .uvm_pkg import m_uvm_string_queue_join

def uvm_typename(obj):
    name = "<NO CLASS NAME>"
    if hasattr(obj, '__class__'):
        name = obj.__class__
    else:
        name = obj
    return name

def UVM_STRING_QUEUE_STREAMING_PACK(q):
    return m_uvm_string_queue_join(q)
