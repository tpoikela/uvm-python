
from ..base.uvm_registry import UVMComponentRegistry, UVMObjectRegistry, uvm_report_warning
from ..base.sv import sv

from ..base.uvm_object_globals import (UVM_CHECK_FIELDS, UVM_COMPARE, UVM_COPY, UVM_DEFAULT,
                                       UVM_LOW, UVM_NOCOMPARE, UVM_NOCOPY, UVM_NONE, UVM_NOPACK,
                                       UVM_NOPRINT, UVM_NORECORD, UVM_PACK, UVM_PRINT, UVM_RADIX,
                                       UVM_READONLY, UVM_RECORD, UVM_REFERENCE, UVM_SETINT,
                                       UVM_SETOBJ, UVM_SETSTR, UVM_UNPACK)
from ..base.uvm_globals import uvm_report_info
from ..base.uvm_globals import uvm_is_match


def uvm_object_utils(T):
    Ts = T.__name__
    m_uvm_object_registry_internal(T,Ts)
    m_uvm_object_create_func(T, Ts)
    m_uvm_get_type_name_func(T, Ts)
    m_uvm_object_repr_func(T, Ts)
    return T


def uvm_component_utils(T):
    #if not __name__ in T:
    #    raise Exception("No __name__ found in {}".format(T))
    Ts = T.__name__
    m_uvm_component_registry_internal(T, Ts)
    m_uvm_get_type_name_func(T, Ts)
    return T


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


def m_uvm_object_repr_func(T,S):
    def __repr__(self):
        return T.convert2string(self)
    if hasattr(T, 'convert2string'):
        setattr(T, '__repr__', __repr__)


# Needed to make uvm_field_* macros work with similar args as in SV,
# stores the class object of last uvm_object_utils_begin(...)
__CURR_OBJ = None


def uvm_component_utils_begin(T):
    global __CURR_OBJ
    __CURR_OBJ = T
    uvm_component_utils(T)
    uvm_field_utils_start(T)

def uvm_component_utils_end(T):
    global __CURR_OBJ
    if __CURR_OBJ is not T:
        raise Exception('Expected: ' + str(__CURR_OBJ) + ' Got: ' + str(T))
    else:
        __CURR_OBJ = None
    uvm_field_utils_end(T)


def uvm_object_utils_begin(T):
    global __CURR_OBJ
    __CURR_OBJ = T
    uvm_object_utils(T)
    uvm_field_utils_start(T)


def uvm_object_utils_end(T):
    global __CURR_OBJ
    if __CURR_OBJ is not T:
        raise Exception('Expected: ' + str(__CURR_OBJ) + ' Got: ' + str(T))
    else:
        __CURR_OBJ = None
    uvm_field_utils_end(T)


def uvm_field_utils_start(T):
    # Create static member containers for var names and masks
    if not hasattr(T, "_m_uvm_field_names"):
        setattr(T, "_m_uvm_field_names", [])
    if not hasattr(T, "_m_uvm_field_masks"):
        setattr(T, "_m_uvm_field_masks", {})

    def _m_uvm_field_automation(self, rhs, what__, str__):
        from ..base.uvm_object import UVMObject
        bases = T.__bases__
        for Base in bases:
            if hasattr(Base, "_m_uvm_field_automation"):
                Base._m_uvm_field_automation(self, rhs, what__, str__)
        vals = T._m_uvm_field_names
        masks = T._m_uvm_field_masks
        _current_scopes = []  # uvm_object[$]

        T_cont = T._m_uvm_status_container
        T_cont_obj = UVMObject._m_uvm_status_container

        if what__ in [UVM_SETINT, UVM_SETSTR, UVM_SETOBJ]:
            if T_cont.m_do_cycle_check(self):
                return
            else:
                _current_scopes = T_cont.m_uvm_cycle_scopes
        # This part does the actual work
        if what__ == UVM_COPY:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOCOPY) and (mask_v & UVM_COPY != 0):
                    v_attr = getattr(rhs, v)
                    if hasattr(v_attr, "clone"):
                        setattr(self, v, v_attr.clone())
                    else:
                        setattr(self, v, v_attr)
        elif what__ == UVM_COMPARE:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOCOMPARE) and (mask_v & UVM_COMPARE != 0):
                    v_attr_rhs = getattr(rhs, v)
                    v_attr_self = getattr(self, v)
                    # Try simple equality first
                    if v_attr_rhs != v_attr_self:
                        if isinstance(v_attr_self, int):
                            T_cont.comparer.compare_field(v,
                                v_attr_self, v_attr_rhs, 0)
                        elif isinstance(v_attr_self, str):
                            T_cont.comparer.compare_string(v,
                                v_attr_self, v_attr_rhs, 0)
                        elif hasattr(v_attr_self, "compare"):
                            T_cont.comparer.compare_object(v,
                                v_attr_self, v_attr_rhs)

                        if (T_cont.comparer.result and
                                T_cont.comparer.show_max <= T_cont.comparer.result):
                            return
        elif what__ == UVM_PRINT:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOPRINT) and (mask_v & UVM_PRINT != 0):
                    v_attr_self = getattr(self, v)
                    if v_attr_self is None:
                        continue

                    if isinstance(v_attr_self, int):
                        T_cont.printer.print_field(v, v_attr_self,
                            sv.bits(v_attr_self), (what__ & UVM_RADIX))
                    elif isinstance(v_attr_self, UVMObject):
                        if mask_v & UVM_REFERENCE:
                            T_cont.printer.print_object_header(v, v_attr_self)
                        else:
                            T_cont.printer.print_object(v, v_attr_self)
                    elif isinstance(v_attr_self, str):
                        T_cont.printer.print_string(v, v_attr_self)
                    else:
                        raise Exception(
                            "Print not implemented yet with field macros. val: " + str(v_attr_self))
        elif what__ == UVM_SETINT:
            for v in vals:
                mask_v = masks[v]
                matched = False
                T_cont.scope.set_arg(v)
                matched = uvm_is_match(str__, T_cont.scope.get())
                if matched:
                    if mask_v & UVM_READONLY:
                        uvm_report_warning("RDONLY", sv.sformatf("Readonly argument match %s is ignored",
                         T_cont.get_full_scope_arg()), UVM_NONE)
                    else:
                        if T_cont.print_matches:
                            uvm_report_info("STRMTC", "set_int()" + ": Matched string "
                                + str__ + " to field " + T_cont.get_full_scope_arg(), UVM_LOW)
                        val = UVMObject._m_uvm_status_container.bitstream
                        setattr(self, v, val)
                        T_cont.status = 1
                T_cont.scope.unset_arg(v)
        elif what__ == UVM_SETSTR:
            for v in vals:
                mask_v = masks[v]
                T_cont.scope.set_arg(v)
                matched = uvm_is_match(str__, T_cont.scope.get())
                if matched:
                    if mask_v & UVM_READONLY:
                        uvm_report_warning("RDONLY", sv.sformatf("Readonly argument match %s is ignored",
                         T_cont.get_full_scope_arg()), UVM_NONE)
                    else:
                        if T_cont.print_matches:
                            uvm_report_info("STRMTC", "set_int()" + ": Matched string "
                                + str__ + " to field " + T_cont.get_full_scope_arg(), UVM_LOW)
                        val = UVMObject._m_uvm_status_container.stringv
                        setattr(self, v, val)
                        T_cont.status = 1
        elif what__ == UVM_SETOBJ:
            for v in vals:
                mask_v = masks[v]
                ARG = getattr(self, v)
                T_cont.scope.set_arg(v)
                if uvm_is_match(str__, T_cont.scope.get()):
                    if mask_v & UVM_READONLY:
                        uvm_report_warning("RDONLY", sv.sformatf("Readonly argument match %s is ignored",
                            T_cont.get_full_scope_arg()), UVM_NONE)
                    else:
                        if T_cont.print_matches:
                            uvm_report_info("STRMTC", "set_object()" + ": Matched string "
                                + str__ + " to field " + T_cont.get_full_scope_arg(), UVM_LOW)
                        #if sv.cast(ARG, T_cont_obj.object):
                        if T_cont_obj.object is None:
                            uvm_report_warning("UVM_SETOBJ NULL", sv.sformatf("Tried to set null obj to %s",
                                T_cont.get_full_scope_arg()), UVM_NONE)
                        setattr(self, v, T_cont_obj.object)
                        T_cont_obj.status = True
                elif ARG is not None and (mask_v & UVM_READONLY == 0):
                    cnt = 0
                    # Only traverse if there is a possible match.
                    while cnt < len(str__):
                        if (str__[cnt] == "." or str__[cnt] == "*"):
                            break
                        cnt += 1
                    if cnt != len(str__):
                        T_cont.scope.down(v)
                        ARG._m_uvm_field_automation(None, UVM_SETOBJ, str__)
                        T_cont.scope.up()

        elif what__ == UVM_CHECK_FIELDS:
            for v in vals:
                T_cont.do_field_check(v, self)
                mask_v = masks[v]
                ARG = getattr(self, v)
        elif what__ == UVM_PACK:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOPACK):
                    val = getattr(self, v)
                    if isinstance(val, int):
                        T_cont.packer.pack_field_int(val, sv.bits(val))
                    elif isinstance(val, UVMObject):
                        T_cont.packer.pack_object(val)
                    elif isinstance(val, str):
                        T_cont.packer.pack_string(val)
                    else:
                        raise TypeError("Unsupported type " + str(type(val)) + " for field automation")
        elif what__ == UVM_UNPACK:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOPACK):
                    val = getattr(self, v)
                    if isinstance(val, int):
                        rhs = T_cont.packer.unpack_field_int(sv.bits(val))
                    elif isinstance(val, UVMObject):
                        T_cont.packer.unpack_object(val)
                        rhs = val
                    elif isinstance(val, str):
                        rhs = T_cont.packer.unpack_string()
                    else:
                        raise TypeError("Unsupported type " + str(type(val)) + " for field automation")
                    setattr(self, v, rhs)
        elif what__ == UVM_RECORD:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NORECORD):
                    print("Recording now attr " + v)
                    val = getattr(self, v)
                    if isinstance(val, int):
                        T_cont.recorder.record_field(v, val, 32)
                    elif isinstance(val, UVMObject):
                        T_cont.recorder.record_object(v, val)
                    elif isinstance(val, str):
                        T_cont.recorder.record_string(v, val)
                    else:
                        raise TypeError("Unsupported type " + str(type(val)) + " for field automation")

        if what__ in [UVM_SETINT, UVM_SETSTR, UVM_SETOBJ]:
            _current_scopes.pop()
            T_cont.uvm_cycle_scopes = _current_scopes

    setattr(T, "_m_uvm_field_automation", _m_uvm_field_automation)


def uvm_field_utils_end(T):
    pass


def uvm_field_val(name, mask):
    if not hasattr(__CURR_OBJ, name):
        vals = getattr(__CURR_OBJ, "_m_uvm_field_names")
        masks = getattr(__CURR_OBJ, "_m_uvm_field_masks")
        vals.append(name)
        masks[name] = mask
    else:
        raise Exception('uvm_field_val(): ' + str(__CURR_OBJ) +
            ' does not have property named ' + name)


def uvm_field_int(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)


def uvm_field_string(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)


def uvm_field_object(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)


def uvm_field_aa(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)


def uvm_field_aa_string_string(name, mask=UVM_DEFAULT):
    uvm_field_aa(name, mask)
