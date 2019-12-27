
import unittest
from ..base.uvm_registry import *


def uvm_object_utils(T):
    Ts = T.__name__
    m_uvm_object_registry_internal(T,Ts)
    m_uvm_object_create_func(T, Ts)
    m_uvm_get_type_name_func(T, Ts)


def uvm_component_utils(T):
    #if not __name__ in T:
    #    raise Exception("No __name__ found in {}".format(T))
    Ts = T.__name__
    m_uvm_component_registry_internal(T, Ts)
    m_uvm_get_type_name_func(T, Ts)


def m_uvm_get_type_name_func(T, Ts):
    setattr(T, 'type_name', Ts)

    def get_type_name(self):
        return Ts
    setattr(T, 'get_type_name', get_type_name)


def m_uvm_component_registry_internal(T,S):
    setattr(T, 'type_id', UVMComponentRegistry(T, S))

    def type_id():
        return T.type_id

    @classmethod
    def get_type(T):
        return T.type_id.get()
    setattr(T, 'get_type', get_type)

    def get_object_type(self):
        return T.type_id.get()
    setattr(T, 'get_object_type', get_object_type)


def m_uvm_object_registry_internal(T,S):
    setattr(T, 'type_id', UVMObjectRegistry(T, S))

    def type_id():
        return T.type_id

    @classmethod
    def get_type(T):
        return T.type_id.get()
    setattr(T, 'get_type', get_type)

    def get_object_type(self):
        return T.type_id.get()
    setattr(T, 'get_object_type', get_object_type)


def m_uvm_object_create_func(T,S):
    # pass
    def create(self, name=""):
        return T(name)
    setattr(T, 'create', create)


