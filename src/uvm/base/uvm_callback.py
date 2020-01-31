#----------------------------------------------------------------------
#   Copyright 2007-2011 Mentor Graphics Corporation
#   Copyright 2007-2010 Cadence Design Systems, Inc.
#   Copyright 2010-2011 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#
#   uvm-python NOTE: All code ported from SystemVerilog UVM 1.2 to
#   python. Original code structures (including comments)
#   preserved where possible.
#----------------------------------------------------------------------

from .sv import sv
from .uvm_object import UVMObject
from .uvm_report_object import UVMReportObject
from .uvm_pool import UVMPool
from .uvm_queue import UVMQueue
from .uvm_misc import UVM_APPEND
from ..macros import (uvm_cb_trace_noobj, uvm_warning, uvm_info)
from ..uvm_macros import UVM_STRING_QUEUE_STREAMING_PACK
from .uvm_object_globals import UVM_NONE
from .uvm_globals import (uvm_report_warning, uvm_report_error,
    uvm_report_fatal)

ALL_TYPES = None

#------------------------------------------------------------------------------
# Title: Callbacks Classes
#
# This section defines the classes used for callback registration, management,
# and user-defined callbacks.
#------------------------------------------------------------------------------


def o2str(ordering):
    if ordering == UVM_APPEND:
        return "UVM_APPEND"
    return "<NO_ORDER_ADDED>"


#
# Class - UVMTypeIDBase
#
#------------------------------------------------------------------------------
# Simple typeid interface. Need this to set up the base-super mapping.
# This is similar to the factory, but much simpler. The idea of this
# interface is that each object type T has a typeid that can be
# used for mapping type relationships. This is not a user visible class.

class UVMTypeIDBase:
    typename = ""

    # UVMTypeIDBase -> uvm_callbacks
    typeid_map = {}

    # uvm_callbacks_base -> UVMTypeIDBase
    type_map = {}

#------------------------------------------------------------------------------
#
# Class - uvm_typeid#(T)
#
#------------------------------------------------------------------------------

class UVMTypeID(UVMTypeIDBase):
    m_b_inst = None

    @classmethod
    def get(cls):
        if UVMTypeID.m_b_inst is None:
            UVMTypeID.m_b_inst = UVMTypeID()
        return UVMTypeID.m_b_inst

#------------------------------------------------------------------------------
# Class - uvm_callbacks_base
#
# Base class singleton that holds generic queues for all instance
# specific objects. This is an internal class. This class contains a
# global pool that has all of the instance specific callback queues in it.
# All of the typewide callback queues live in the derivative class
# uvm_typed_callbacks#(T). This is not a user visible class.
#
# This class holds the class inheritance hierarchy information
# (super types and derivative types).
#
# Note, all derivative uvm_callbacks#() class singletons access this
# global m_pool object in order to get access to their specific
# instance queue.
#------------------------------------------------------------------------------


class UVMCallbacksBase(UVMObject):

    m_b_inst = None
    m_pool = UVMPool()  # uvm_object -> uvm_queue#(uvm_callback)
    m_tracing = True

    def __init__(self, name):
        super().__init__(name)
        #Type checking interface
        self.m_this_type = []     # one to many T->T/CB
        self.m_super_type = None       # one to one relation
        self.m_derived_types = []  # one to many relation, UVMTypeIDBase

    @classmethod
    def m_initialize(cls):
        if cls.m_b_inst is None:
            cls.m_b_inst = UVMCallbacksBase("callbacks_base")
            UVMCallbacksBase.m_pool = UVMPool()
        return UVMCallbacksBase.m_b_inst

    def m_am_i_a(self, obj):
        return 0

    def m_is_for_me(self, cb):
        return 0

    def m_is_registered(self, obj, cb):
        return True

    def m_get_tw_cb_q(self, obj, CB=None):
        return None

    def m_add_tw_cbs(self, cb, ordering):
        pass

    def m_delete_tw_cbs(self, cb):
        return 0

    # Check registration. To test registration, start at this class and
    # work down the class hierarchy. If any class returns true then
    # the pair is legal.
    def check_registration(self, obj, cb):
        st = None
        dt = None

        if self.m_is_registered(obj,cb):
            return True

        # Need to look at all possible T/CB pairs of this type
        for item in self.m_this_type:
            if (UVMCallbacksBase.m_b_inst != item and
                    item.m_is_registered(obj,cb)):
                return True

        if obj is None:
            for item in self.m_derived_types:
                dt = UVMTypeIDBase.typeid_map[item]
                if dt is not None and dt.check_registration(None,cb):
                    return True

        return False

    # Function: get_first
    #
    # Returns the first enabled callback of type CB which resides in the queue for ~obj~.
    # If ~obj~ is ~None~ then the typewide queue for T is searched. ~itr~ is the iterator
    # it will be updated with a value that can be supplied to <get_next> to get the next
    # callback object.
    #
    # If the queue is empty then ~None~ is returned.
    #
    # The iterator class <uvm_callback_iter> may be used as an alternative, simplified,
    # iterator interface.
    @classmethod
    def get_first(cls, itr, obj, CB=None):
        cb = None
        cls.get()
        q = cls.m_get_q(obj, CB)
        if q is not None:
            for i in range(len(q)):
                itr.m_i = i
                cb = q[i]
                if cb is not None and cb.callback_mode():
                    return cb
        return None
    #endclass

#------------------------------------------------------------------------------
#
# Class - uvm_typed_callbacks#(T)
#
#------------------------------------------------------------------------------

# Another internal class. This contains the queue of typewide
# callbacks. It also contains some of the public interface methods,
# but those methods are accessed via the uvm_callbacks#() class
# so they are documented in that class even though the implementation
# is in this class.
#
# The <add>, <delete>, and <display> methods are implemented in this class.


class UVMTypedCallbacks(UVMCallbacksBase):  #(type T=uvm_object) extends uvm_callbacks_base

    #  static uvm_queue#(uvm_callback) m_tw_cb_q
    m_tw_cb_q = []

    #  static string m_typename
    m_typename = ""

    #  typedef uvm_typed_callbacks#(T) this_type
    #  typedef uvm_callbacks_base      super_type

    #  #The actual global object from the derivative class. Note that this is
    #  #just a reference to the object that is generated in the derived class.
    #  static this_type m_t_inst
    m_t_inst = None

    def __init__(self, name, T=ALL_TYPES):
        super().__init__(name)
        self.T = T

    @classmethod
    def m_initialize(cls):
        if cls.m_t_inst is None:
            super().m_initialize()
            cls.m_t_inst = UVMTypedCallbacks("typed_callbacks")
            cls.m_t_inst.m_tw_cb_q = []
        return cls.m_t_inst
        #  endfunction

    #
    #  #Type checking interface: is given ~obj~ of type T?
    def m_am_i_a(self, obj):
        if obj is None:
            return True
        arr = []
        if self.T is not ALL_TYPES:
            return sv.cast(arr, obj, self.T)
        return True
    #  endfunction


    #  #Getting the typewide queue
    def m_get_tw_cb_q(self, obj, CB=None):
        if self.m_am_i_a(obj):
            for i in range(len(self.m_derived_types)):
                #super_type dt
                dt = UVMTypeIDBase.typeid_map[self.m_derived_types[i]]
                if dt is not None and dt != self:
                    m_get_tw_cb_q = dt.m_get_tw_cb_q(obj, CB)
                    if m_get_tw_cb_q is not None:
                        return m_get_tw_cb_q
            return self.m_t_inst.m_tw_cb_q
        else:
            return None

    @classmethod
    def m_cb_find(cls, q, cb):
        for i in range(len(q)):
            if q[i] == cb:
                return i
        return -1
        #  endfunction


    #  static function int m_cb_find_name(uvm_queue#(uvm_callback) q, string name, string where)
    @classmethod
    def m_cb_find_name(cls, q, name, where):
        cb = None
        for i in range(len(q)):
            cb = q[i]
            if cb.get_name() == name:
                uvm_report_warning("UVM/CB/NAM/SAM", "A callback named \"" + name
                    + "\" is already registered with " + where)
                return 1
        return 0
        #  endfunction


    #  #For a typewide callback, need to add to derivative types as well.
    #  virtual function void m_add_tw_cbs(uvm_callback cb, uvm_apprepend ordering)
    #    super_type cb_pair
    #    uvm_object obj
    #    T me
    #    bit warned
    #    uvm_queue#(uvm_callback) q
    #    if(m_cb_find(m_t_inst.m_tw_cb_q,cb) == -1):
    #       warned = m_cb_find_name(m_t_inst.m_tw_cb_q, cb.get_name(), "type")
    #       if(ordering == UVM_APPEND)
    #          m_t_inst.m_tw_cb_q.push_back(cb)
    #       else
    #          m_t_inst.m_tw_cb_q.push_front(cb)
    #    end
    #    if(m_t_inst.m_pool.first(obj)):
    #      do begin
    #        if($cast(me,obj)):
    #          q = m_t_inst.m_pool.get(obj)
    #          if(qis None):
    #            q=new
    #            m_t_inst.m_pool.add(obj,q)
    #          end
    #          if(m_cb_find(q,cb) == -1):
    #            if (!warned):
    #               void'(m_cb_find_name(q, cb.get_name(), {"object instance ", me.get_full_name()}))
    #            end
    #            if(ordering == UVM_APPEND)
    #              q.push_back(cb)
    #            else
    #              q.push_front(cb)
    #          end
    #        end
    #      end while(m_t_inst.m_pool.next(obj))
    #    end
    #    foreach(m_derived_types[i]):
    #      cb_pair = UVMTypeIDBase::typeid_map[m_derived_types[i] ]
    #      if(cb_pair != this)
    #        cb_pair.m_add_tw_cbs(cb,ordering)
    #    end
    #  endfunction


    #  #For a typewide callback, need to remove from derivative types as well.
    #  virtual function bit m_delete_tw_cbs(uvm_callback cb)
    #    super_type cb_pair
    #    uvm_object obj
    #    uvm_queue#(uvm_callback) q
    #    int pos = m_cb_find(m_t_inst.m_tw_cb_q,cb)
    #
    #    if(pos != -1):
    #      m_t_inst.m_tw_cb_q.delete(pos)
    #      m_delete_tw_cbs = 1
    #    end
    #
    #    if(m_t_inst.m_pool.first(obj)):
    #      do begin
    #        q = m_t_inst.m_pool.get(obj)
    #        if(qis None):
    #          q=new
    #          m_t_inst.m_pool.add(obj,q)
    #        end
    #        pos = m_cb_find(q,cb)
    #        if(pos != -1):
    #          q.delete(pos)
    #          m_delete_tw_cbs = 1
    #        end
    #      end while(m_t_inst.m_pool.next(obj))
    #    end
    #    foreach(m_derived_types[i]):
    #      cb_pair = UVMTypeIDBase::typeid_map[m_derived_types[i] ]
    #      if(cb_pair != this)
    #        m_delete_tw_cbs |= cb_pair.m_delete_tw_cbs(cb)
    #    end
    #  endfunction


    #  static function void display(T obj=None)
    @classmethod
    def display(cls, obj=None):
        #    T me
        #    super_type ib = m_t_inst
        cbq = []  # string [$]
        inst_q = []  # string [$]
        mode_q = []  # string  [$]
        cb = None  # uvm_callback
        blanks = "                             "
        bobj = obj
        qs = []  # string[$]

        q = None  # uvm_queue#(uvm_callback)
        tname = ""
        strr = ""
        max_cb_name = 0
        max_inst_name= 0

        prev_trace = cls.m_tracing
        cls.m_tracing = False  # don't allow tracing during display

        if cls.m_typename != "":
            tname = cls.m_typename
        elif (obj is not None):
            tname = obj.get_type_name()
        else:
            tname = "*"

        q = cls.m_t_inst.m_tw_cb_q
        for i in range(len(q)):
            cb = q[i]
            cbq.append(cb.get_name())
            inst_q.append("(*)")
            if (cb.is_enabled()):
                mode_q.append("ON")
            else:
                mode_q.append("OFF")

            strr = cb.get_name()
            if max_cb_name <= strr.len():
                max_cb_name = strr.len()
            strr = "(*)"
            if max_inst_name <= strr.len():
                max_inst_name = strr.len()

        # tpoikela: TODO finalize this
        #    if(obj is None):
        #      if(m_t_inst.m_pool.first(bobj)):
        #        do
        #          if($cast(me,bobj)) break
        #        while(m_t_inst.m_pool.next(bobj))
        #      end
        #      if(me is not None || m_t_inst.m_tw_cb_q.size()):
        #        qs.push_back($sformatf("Registered callbacks for all instances of %s\n", tname))
        #        qs.push_back("---------------------------------------------------------------\n")
        #      end
        #      if(me is not None):
        #        do begin
        #          if($cast(me,bobj)):
        #            q = m_t_inst.m_pool.get(bobj)
        #            if (qis None):
        #              q=new
        #              m_t_inst.m_pool.add(bobj,q)
        #            end
        #            for(int i=0; i<q.size(); ++i):
        #              cb = q.get(i)
        #              cbq.push_back(cb.get_name())
        #              inst_q.push_back(bobj.get_full_name())
        #              if(cb.is_enabled()) mode_q.push_back("ON")
        #              else mode_q.push_back("OFF")
        #
        #              strr = cb.get_name()
        #              max_cb_name = max_cb_name > strr.len() ? max_cb_name : strr.len()
        #              strr = bobj.get_full_name()
        #              max_inst_name = max_inst_name > strr.len() ? max_inst_name : strr.len()
        #            end
        #          end
        #        end while (m_t_inst.m_pool.next(bobj))
        #      end
        #      else begin
        #        qs.push_back($sformatf("No callbacks registered for any instances of type %s\n", tname))
        #      end
        #    end
        #    else begin
        #      if(m_t_inst.m_pool.exists(bobj) || m_t_inst.m_tw_cb_q.size()):
        #       qs.push_back($sformatf("Registered callbacks for instance %s of %s\n", obj.get_full_name(), tname))
        #       qs.push_back("---------------------------------------------------------------\n")
        #      end
        #      if(m_t_inst.m_pool.exists(bobj)):
        #        q = m_t_inst.m_pool.get(bobj)
        #        if(qis None):
        #          q=new
        #          m_t_inst.m_pool.add(bobj,q)
        #        end
        #        for(int i=0; i<q.size(); ++i):
        #          cb = q.get(i)
        #          cbq.push_back(cb.get_name())
        #          inst_q.push_back(bobj.get_full_name())
        #          if(cb.is_enabled()) mode_q.push_back("ON")
        #          else mode_q.push_back("OFF")
        #
        #          str = cb.get_name()
        #          max_cb_name = max_cb_name > str.len() ? max_cb_name : str.len()
        #          str = bobj.get_full_name()
        #          max_inst_name = max_inst_name > str.len() ? max_inst_name : str.len()
        #        end
        #      end
        #    end
        #    if(!cbq.size()):
        #      if(obj is None) str = "*"
        #      else str = obj.get_full_name()
        #      qs.push_back($sformatf("No callbacks registered for instance %s of type %s\n", str, tname))
        #    end
        #
        for i in range(len(cbq)):
            padding = blanks[0:max_cb_name - len(cbq[i])]
            qs.append(sv.sformatf("%s  %s %s on %s  %s\n",
                cbq[i], padding, inst_q[i], blanks[0:max_inst_name - len(inst_q[i])-1],
                mode_q[i]))
        uvm_info("UVM/CB/DISPLAY", UVM_STRING_QUEUE_STREAMING_PACK(qs), UVM_NONE)
        cls.m_tracing = prev_trace  # allow tracing to be resumed
        #  endfunction
    #
    #endclass


#------------------------------------------------------------------------------
#
# CLASS: uvm_callbacks #(T,CB)
#
# The ~uvm_callbacks~ class provides a base class for implementing callbacks,
# which are typically used to modify or augment component behavior without
# changing the component class. To work effectively, the developer of the
# component class defines a set of "hook" methods that enable users to
# customize certain behaviors of the component in a manner that is controlled
# by the component developer. The integrity of the component's overall behavior
# is intact, while still allowing certain customizable actions by the user.
#
# To enable compile-time type-safety, the class is parameterized on both the
# user-defined callback interface implementation as well as the object type
# associated with the callback. The object type-callback type pair are
# associated together using the <`uvm_register_cb> macro to define
# a valid pairing; valid pairings are checked when a user attempts to add
# a callback to an object.
#
# To provide the most flexibility for end-user customization and reuse, it
# is recommended that the component developer also define a corresponding set
# of virtual method hooks in the component itself. This affords users the ability
# to customize via inheritance/factory overrides as well as callback object
# registration. The implementation of each virtual method would provide the
# default traversal algorithm for the particular callback being called. Being
# virtual, users can define subtypes that override the default algorithm,
# perform tasks before and/or after calling super.<method> to execute any
# registered callbacks, or to not call the base implementation, effectively
# disabling that particular hook. A demonstration of this methodology is
# provided in an example included in the kit.
#------------------------------------------------------------------------------

class UVMCallbacks(UVMTypedCallbacks):
    #(type T=uvm_object, type CB=uvm_callback) extends uvm_typed_callbacks#(T)

    # Singleton instance is used for type checking
    m_inst = None
    # typeinfo
    m_typeid = None  # UVMTypeIDBase
    m_cb_typeid = None  # UVMTypeIDBase

    m_typename = ''
    m_cb_typename = ''
    reporter = UVMReportObject("cb_tracer")
    m_base_inst = None  # uvm_callbacks#(T,uvm_callback)

    def __init__(self, name='uvm_callbacks', T=ALL_TYPES):
        super().__init__(name)
        self.m_registered = False
        self.T = T

    #  # get
    #  # ---
    #
    @classmethod
    def get(cls):

        if cls.m_inst is None:
            cb_base_type = UVMTypeIDBase()

            #void'(super_typ.:m_initialize())

            cb_base_type = UVMTypeID.get()
            cls.m_cb_typeid  = UVMTypeID.get()
            cls.m_typeid     = UVMTypeID.get()

            cls.m_inst = UVMCallbacks()

            if cb_base_type == UVMCallbacks.m_cb_typeid:
                #cast(m_base_inst, m_inst)
                cls.m_base_inst = UVMCallbacks.m_inst
                # The base inst in the super class gets set to this base inst
                cls.m_t_inst = UVMCallbacks.m_base_inst
                UVMTypeIDBase.typeid_map[UVMCallbacks.m_typeid] = UVMCallbacks.m_inst
                UVMTypeIDBase.type_map[UVMCallbacks.m_b_inst] = UVMCallbacks.m_typeid
            else:
                cls.m_base_inst = UVMCallbacks.get()
                cls.m_base_inst.m_this_type.append(UVMCallbacks.m_inst)

            if cls.m_inst is None:
                uvm_report_fatal("CB/INTERNAL","get(): m_inst is None")

        return cls.m_inst


    #  # m_register_pair
    #  # -------------
    #  # Register valid callback type
    #
    @classmethod
    def m_register_pair(cls, tname="", cbname="", T=ALL_TYPES):
        inst = cls.get()
        # tpoikela: mimics typed callbacks by creating one cbs-object
        # per registered pair
        cbs = UVMCallbacks(tname + "__" + cbname, T)

        cbs.m_typename = tname
        # TODO super_type.m_typename = tname
        cbs.m_typeid.typename = tname

        cbs.m_cb_typename = cbname
        cbs.m_cb_typeid.typename = cbname

        cbs.m_registered = True
        if cbs.get_name() not in inst._m_cb_table:
            inst._m_cb_table[cbs.get_name()] = cbs
        else:
            uvm_warning("CB_EXISTS", "Callback for " + cbs.get_name() + " already register")
        return True

    # tpoikela: Added for containig callbacks for each class
    _m_cb_table = {}
    @classmethod
    def _get_typed(cls, obj, CB):
        cb_table_key = cls._get_cb_table_key(obj, CB)
        if cb_table_key in cls._m_cb_table:
            return cls._m_cb_table[cb_table_key]
        return cls

    @classmethod
    def _get_cb_table_key(cls, obj, CB):
        if obj is not None:
            if CB is not None:
                return type(obj).__name__ + '__' + CB.__name__
            else:
                return type(obj).__name__
        return '__' + CB.__name__


    #  virtual function bit m_is_registered(uvm_object obj, uvm_callback cb)
    #    if(m_is_for_me(cb) && m_am_i_a(obj)):
    #      return m_registered
    #    end
    #  endfunction

    #  #Does type check to see if the callback is valid for this type
    #  virtual function bit m_is_for_me(uvm_callback cb)
    #    CB this_cb
    #    return($cast(this_cb,cb))
    #  endfunction

    # Group: Add/delete interface

    # Function: add
    #
    # Registers the given callback object, ~cb~, with the given
    # ~obj~ handle. The ~obj~ handle can be ~None~, which allows
    # registration of callbacks without an object context. If
    # ~ordering~ is UVM_APPEND (default), the callback will be executed
    # after previously added callbacks, else  the callback
    # will be executed ahead of previously added callbacks. The ~cb~
    # is the callback handle; it must be non-~None~, and if the callback
    # has already been added to the object instance then a warning is
    # issued. Note that the CB parameter is optional. For example, the
    # following are equivalent:
    #
    #| uvm_callbacks#(my_comp)::add(comp_a, cb)
    #| uvm_callbacks#(my_comp, my_callback)::add(comp_a,cb)
    #  static function void add(T obj, uvm_callback cb, uvm_apprepend ordering=UVM_APPEND)

    @classmethod
    def add(cls, obj, cb, ordering=UVM_APPEND):
        # pass
        q = []  # uvm_queue#(uvm_callback) q
        nm = ""
        tnm = ""
        cls.get()

        if cb is None:
            nm, tnm = cls.get_obj_and_typename(obj)

            uvm_report_error("CBUNREG",
                "None callback object cannot be registered with object "
                     + nm + " (" + tnm + ")", UVM_NONE)
            return


        if not cls.m_base_inst.check_registration(obj,cb):
            nm, tnm = cls.get_obj_and_typename(obj)

            uvm_report_warning("CBUNREG",
                "Callback " + cb.get_name() + " cannot be registered with object "
                + nm + " because callback type " + cb.get_type_name()
                + " is not registered with object type " + tnm, UVM_NONE)


        if obj is None:
            if cls.m_cb_find(cls.m_t_inst.m_tw_cb_q, cb) != -1:

                if cls.m_base_inst.m_typename != "":
                    tnm = cls.m_base_inst.m_typename
                else:
                    tnm = "uvm_object"

                uvm_report_warning("CBPREG",
                    "Callback object " + cb.get_name()
                    + " is already registered with type " + tnm, UVM_NONE)
            else:
                uvm_cb_trace_noobj(cb,sv.sformatf("Add (%s) typewide callback %0s for type %s",
                    o2str(ordering), cb.get_name(), cls.m_base_inst.m_typename))
                cls.m_t_inst.m_add_tw_cbs(cb, ordering)

        else:

            uvm_cb_trace_noobj(cb, sv.sformatf("Add (%s) callback %0s to object %0s ",
                o2str(ordering), cb.get_name(), obj.get_full_name()))

            q = cls.m_base_inst.m_pool.get(obj)

            if q is None:
                q = []
                cls.m_base_inst.m_pool.add(obj,q)

            if (len(q) == 0):
                # Need to make sure that registered report catchers are added. This
                # way users don't need to set up uvm_report_object as a super type.
                o = []  # uvm_report_object

                if (sv.cast(o,obj, UVMReportObject)):
                    # uvm_queue#(uvm_callback) qr
                    UVMCallbacks.get()
                    qr = UVMCallbacks.m_t_inst.m_tw_cb_q
                    for i in range(len(qr)):
                        q.append(qr[i])

                # for(int i=0; i<m_t_inst.m_tw_cb_q.size(); ++i)
                for i in range(len(cls.m_t_inst.m_tw_cb_q)):
                    q.append(cls.m_t_inst.m_tw_cb_q.get(i))


            #check if already exists in the queue
            if cls.m_cb_find(q,cb) != -1:
                uvm_report_warning("CBPREG", "Callback object " + cb.get_name()
                    + " is already registered with object " + obj.get_full_name(), UVM_NONE)
            else:
                cls.m_cb_find_name(q, cb.get_name(), "object instance " + obj.get_full_name())
                if ordering == UVM_APPEND:
                    q.append(cb)
                else:
                    q.insert(0, cb)

        #  endfunction

    @classmethod
    def get_obj_and_typename(cls, obj):
        nm = ""
        tnm = ""

        if obj is None:
            nm = "(*)"
        else:
            nm = obj.get_full_name()

        if cls.m_base_inst.m_typename != "":
            tnm = cls.m_base_inst.m_typename
        elif obj is not None:
            tnm = obj.get_type_name()
        else:
            tnm = "uvm_object"
        return nm, tnm


    #  # Function: add_by_name
    #  #
    #  # Registers the given callback object, ~cb~, with one or more uvm_components.
    #  # The components must already exist and must be type T or a derivative. As
    #  # with <add> the CB parameter is optional. ~root~ specifies the location in
    #  # the component hierarchy to start the search for ~name~. See <uvm_root::find_all>
    #  # for more details on searching by name.
    #
    #  static function void add_by_name(string name,
    #                                   uvm_callback cb,
    #                                   uvm_component root,
    #                                   uvm_apprepend ordering=UVM_APPEND)
    #    uvm_component cq[$]
    #    uvm_root top
    #    uvm_coreservice_t cs
    #    T t
    #    void'(get())
    #    cs = uvm_coreservice_t::get()
    #    top = cs.get_root()
    #
    #    if(cbis None):
    #       uvm_report_error("CBUNREG", { "None callback object cannot be registered with object(s) ",
    #         name }, UVM_NONE)
    #       return
    #    end
    #    `uvm_cb_trace_noobj(cb,$sformatf("Add (%s) callback %0s by name to object(s) %0s ",
    #                    ordering.name(), cb.get_name(), name))
    #    top.find_all(name,cq,root)
    #    if(cq.size() == 0):
    #      uvm_report_warning("CBNOMTC", { "add_by_name failed to find any components matching the name ",
    #        name, ", callback ", cb.get_name(), " will not be registered." }, UVM_NONE)
    #    end
    #    foreach(cq[i]):
    #      if($cast(t,cq[i])):
    #        add(t,cb,ordering)
    #      end
    #    end
    #  endfunction
    #
    #
    #  # Function: delete
    #  #
    #  # Deletes the given callback object, ~cb~, from the queue associated with
    #  #  the given ~obj~ handle. The ~obj~ handle can be ~None~, which allows
    #  # de-registration of callbacks without an object context.
    #  # The ~cb~ is the callback handle; it must be non-~None~, and if the callback
    #  # has already been removed from the object instance then a warning is
    #  # issued. Note that the CB parameter is optional. For example, the
    #  # following are equivalent:
    #  #
    #  #| uvm_callbacks#(my_comp)::delete(comp_a, cb)
    #  #| uvm_callbacks#(my_comp, my_callback)::delete(comp_a,cb)
    #
    #  static function void delete(T obj, uvm_callback cb)
    #    uvm_object b_obj = obj
    #    uvm_queue#(uvm_callback) q
    #    bit found
    #    int pos
    #    void'(get())
    #
    #    if(obj is None):
    #      `uvm_cb_trace_noobj(cb,$sformatf("Delete typewide callback %0s for type %s",
    #                       cb.get_name(), m_base_inst.m_typename))
    #      found = m_t_inst.m_delete_tw_cbs(cb)
    #    end
    #    else begin
    #      `uvm_cb_trace_noobj(cb,$sformatf("Delete callback %0s from object %0s ",
    #                      cb.get_name(), obj.get_full_name()))
    #      q = m_base_inst.m_pool.get(b_obj)
    #      pos = m_cb_find(q,cb)
    #      if(pos != -1):
    #        q.delete(pos)
    #        found = 1
    #      end
    #    end
    #    if(!found):
    #      string nm
    #      if(objis None) nm = "(*)"; else nm = obj.get_full_name()
    #      uvm_report_warning("CBUNREG", { "Callback ", cb.get_name(), " cannot be removed from object ",
    #        nm, " because it is not currently registered to that object." }, UVM_NONE)
    #    end
    #  endfunction
    #
    #

    #  # Function: delete_by_name
    #  #
    #  # Removes the given callback object, ~cb~, associated with one or more
    #  # uvm_component callback queues. As with <delete> the CB parameter is
    #  # optional. ~root~ specifies the location in the component hierarchy to start
    #  # the search for ~name~. See <uvm_root::find_all> for more details on searching
    #  # by name.
    #
    #  static function void delete_by_name(string name, uvm_callback cb,
    #     uvm_component root)
    #    uvm_component cq[$]
    #    uvm_root top
    #    T t
    #    uvm_coreservice_t cs
    #    void'(get())
    #    cs = uvm_coreservice_t::get()
    #    top = cs.get_root()
    #
    #    `uvm_cb_trace_noobj(cb,$sformatf("Delete callback %0s by name from object(s) %0s ",
    #                    cb.get_name(), name))
    #    top.find_all(name,cq,root)
    #    if(cq.size() == 0):
    #      uvm_report_warning("CBNOMTC", { "delete_by_name failed to find any components matching the name ",
    #        name, ", callback ", cb.get_name(), " will not be unregistered." }, UVM_NONE)
    #    end
    #    foreach(cq[i]):
    #      if($cast(t,cq[i])):
    #        delete(t,cb)
    #      end
    #    end
    #  endfunction


    #--------------------------
    # Group: Iterator Interface
    #--------------------------
    #
    # This set of functions provide an iterator interface for callback queues.
    # A facade class, <uvm_callback_iter> is also available, and is the generally
    # preferred way to iterate over callback queues.
    @classmethod
    def m_get_q(cls, obj, CB=None):
        q = None
        if not cls.m_base_inst.m_pool.exists(obj):  # no instance specific
            if obj is None:
                q = cls.m_t_inst.m_tw_cb_q
            else:
                q = cls.m_t_inst.m_get_tw_cb_q(obj, CB)
        else:
            q = cls.m_base_inst.m_pool.get(obj)
            if q is None:
                q = UVMQueue()
                cls.m_base_inst.m_pool.add(obj, q)
        return q

    #  # Function: get_first
    #  #
    #  # Returns the first enabled callback of type CB which resides in the queue for ~obj~.
    #  # If ~obj~ is ~None~ then the typewide queue for T is searched. ~itr~ is the iterator
    #  # it will be updated with a value that can be supplied to <get_next> to get the next
    #  # callback object.
    #  #
    #  # If the queue is empty then ~None~ is returned.
    #  #
    #  # The iterator class <uvm_callback_iter> may be used as an alternative, simplified,
    #  # iterator interface.
    #
    @classmethod
    def get_first(cls, itr, obj, CB=None):
        cls.get()
        # tpoikela: added to mimic typed cbs
        typed_cls = cls._get_typed(obj, CB)
        cls = typed_cls
        q = cls.m_get_q(obj, CB)
        for i in range(len(q)):
            itr.m_i = i
            cb = []
            if CB is not None:
                if sv.cast(cb, q[itr.m_i], CB) and cb[0].callback_mode():
                    return cb[0]
            else:
                return q[itr.m_i]  # Just return 1st index without type match
        return None
        #  endfunction


    #  # Function: get_last
    #  #
    #  # Returns the last enabled callback of type CB which resides in the queue for ~obj~.
    #  # If ~obj~ is ~None~ then the typewide queue for T is searched. ~itr~ is the iterator
    #  # it will be updated with a value that can be supplied to <get_prev> to get the previous
    #  # callback object.
    #  #
    #  # If the queue is empty then ~None~ is returned.
    #  #
    #  # The iterator class <uvm_callback_iter> may be used as an alternative, simplified,
    #  # iterator interface.
    #
    #  static function CB get_last (ref int itr, input T obj)
    #    uvm_queue#(uvm_callback) q
    #    CB cb
    #    void'(get())
    #    # tpoikela: added to mimic typed cbs
    #    typed_cls = cls._get_typed(obj, CB)
    #    cls = typed_cls
    #    q = m_get_q(obj)
    #    for(itr = q.size()-1; itr>=0; --itr)
    #      if ($cast(cb, q.get(itr)) && cb.callback_mode())
    #         return cb
    #    return None
    @classmethod
    def get_last(cls, itr, obj, CB=None):
        cls.get()
        # tpoikela: added to mimic typed cbs
        typed_cls = cls._get_typed(obj, CB)
        cls = typed_cls
        q = cls.m_get_q(obj, CB)
        for i in range(len(q)-1, -1, -1):
            itr.m_i = i
            cb = []
            if CB is not None:
                if sv.cast(cb, q[itr.m_i], CB) and cb[0].callback_mode():
                    return cb[0]
            else:
                return q[itr.m_i]  # Just return 1st index without type match
        return None

    #  # Function: get_next
    #  #
    #  # Returns the next enabled callback of type CB which resides in the queue for ~obj~,
    #  # using ~itr~ as the starting point. If ~obj~ is ~None~ then the typewide queue for T
    #  # is searched. ~itr~ is the iterator; it will be updated with a value that can be
    #  # supplied to <get_next> to get the next callback object.
    #  #
    #  # If no more callbacks exist in the queue, then ~None~ is returned. <get_next> will
    #  # continue to return ~None~ in this case until <get_first> or <get_last> has been used to reset
    #  # the iterator.
    #  #
    #  # The iterator class <uvm_callback_iter> may be used as an alternative, simplified,
    #  # iterator interface.
    #
    #  static function CB get_next (ref int itr, input T obj)
    @classmethod
    def get_next(cls, itr, obj, CB=None):
        cls.get()
        # tpoikela: added to mimic typed cbs
        typed_cls = cls._get_typed(obj, CB)
        cls = typed_cls
        q = cls.m_get_q(obj)
        for i in range(itr.m_i + 1, len(q)):
            itr.m_i = i
            cb = []
            if CB is not None:
                if sv.cast(cb, q[itr.m_i], CB) and cb[0].callback_mode():
                    return cb[0]
            else:
                return q[itr.m_i]
        return None
        #  endfunction

    #
    #
    #  # Function: get_prev
    #  #
    #  # Returns the previous enabled callback of type CB which resides in the queue for ~obj~,
    #  # using ~itr~ as the starting point. If ~obj~ is ~None~ then the typewide queue for T
    #  # is searched. ~itr~ is the iterator; it will be updated with a value that can be
    #  # supplied to <get_prev> to get the previous callback object.
    #  #
    #  # If no more callbacks exist in the queue, then ~None~ is returned. <get_prev> will
    #  # continue to return ~None~ in this case until <get_first> or <get_last> has been used to reset
    #  # the iterator.
    #  #
    #  # The iterator class <uvm_callback_iter> may be used as an alternative, simplified,
    #  # iterator interface.
    #
    #  static function CB get_prev (ref int itr, input T obj)
    @classmethod
    def get_prev(cls, itr, obj, CB=None):
        cls.get()
        # tpoikela: added to mimic typed cbs
        typed_cls = cls._get_typed(obj, CB)
        cls = typed_cls
        q = cls.m_get_q(obj)
        # for(itr = itr-1; itr>= 0; --itr)
        for i in range(itr.m_i - 1, -1, -1):
            itr.m_i = i
            cb = []
            if CB is not None:
                if sv.cast(cb, q[itr.m_i], CB) and cb[0].callback_mode():
                    return cb[0]
            else:
                return q[itr.m_i]
        return None


    #  #-------------
    #  # Group: Debug
    #  #-------------
    #
    #  # Function: display
    #  #
    #  # This function displays callback information for ~obj~. If ~obj~ is
    #  # ~None~, then it displays callback information for all objects
    #  # of type ~T~, including typewide callbacks.
    #
    #  static function void display(T obj=None)
    @classmethod
    def display(cls, obj=None):
        # For documentation purposes, need a function wrapper here.
        cls.get()
        super().display(obj)

    #endclass


#------------------------------------------------------------------------------
#
# Class- uvm_derived_callbacks #(T,ST,CB)
#
#------------------------------------------------------------------------------
# This type is not really expected to be used directly by the user, instead they are
# expected to use the macro `uvm_set_super_type. The sole purpose of this type is to
# allow for setting up of the derived_type/super_type mapping.
#------------------------------------------------------------------------------

#class uvm_derived_callbacks#(type T=uvm_object, type ST=uvm_object, type CB=uvm_callback)
#    extends uvm_callbacks#(T,CB)
#
#  typedef uvm_derived_callbacks#(T,ST,CB) this_type
#  typedef uvm_callbacks#(T)            this_user_type
#  typedef uvm_callbacks#(ST)           this_super_type
#
#  # Singleton instance is used for type checking
#  static this_type m_d_inst
#  static this_user_type m_user_inst
#  static this_super_type m_super_inst
#
#  # typeinfo
#  static UVMTypeIDBase m_s_typeid
#
#  static function this_type get()
#    m_user_inst = this_user_type::get()
#    m_super_inst = this_super_type::get()
#    m_s_typeid = uvm_typeid#(ST)::get()
#    if(m_d_inst is None):
#      m_d_inst = new
#    end
#    return m_d_inst
#  endfunction
#
#  static function bit register_super_type(string tname="", sname="")
#    this_user_type u_inst = this_user_type::get()
#    this_type      inst = this_type::get()
#    uvm_callbacks_base s_obj
#
#    this_user_type::m_t_inst.m_typename = tname
#
#    if(sname != "") m_s_typeid.typename = sname
#
#    if(u_inst.m_super_type is not None):
#      if(u_inst.m_super_type == m_s_typeid) return 1
#      uvm_report_warning("CBTPREG", { "Type ", tname, " is already registered to super type ",
#        this_super_type::m_t_inst.m_typename, ". Ignoring attempt to register to super type ",
#        sname}, UVM_NONE)
#      return 1
#    end
#    if(this_super_type::m_t_inst.m_typename == "")
#      this_super_type::m_t_inst.m_typename = sname
#    u_inst.m_super_type = m_s_typeid
#    u_inst.m_base_inst.m_super_type = m_s_typeid
#    s_obj = UVMTypeIDBase::typeid_map[m_s_typeid]
#    s_obj.m_derived_types.push_back(m_typeid)
#    return 1
#  endfunction
#
#endclass

#------------------------------------------------------------------------------
#
# CLASS: uvm_callback_iter
#
#------------------------------------------------------------------------------
# The ~uvm_callback_iter~ class is an iterator class for iterating over
# callback queues of a specific callback type. The typical usage of
# the class is:
#
#| uvm_callback_iter#(mycomp,mycb) iter = new(this)
#| for(mycb cb = iter.first(); cb is not None; cb = iter.next())
#|    cb.dosomething()
#
# The callback iteration macros, <`uvm_do_callbacks> and
# <`uvm_do_callbacks_exit_on> provide a simple method for iterating
# callbacks and executing the callback methods.
#------------------------------------------------------------------------------
class UVMCallbackIter:  # (type T = uvm_object, type CB = uvm_callback)

    # Function: new
    #
    # Creates a new callback iterator object. It is required that the object
    # context be provided.

    def __init__(self, obj, CB=None):
        self.m_i = 0
        self.m_cb = None  # UVMCallback
        self.m_obj = obj
        self.CB = CB

    # Function: first
    #
    # Returns the first valid (enabled) callback of the callback type (or
    # a derivative) that is in the queue of the context object. If the
    # queue is empty then ~None~ is returned.

    def first(self):
        self.m_cb = UVMCallbacks.get_first(self, self.m_obj, self.CB)
        return self.m_cb

    # Function: last
    #
    # Returns the last valid (enabled) callback of the callback type (or
    # a derivative) that is in the queue of the context object. If the
    # queue is empty then ~None~ is returned.
    def last(self):
        self.m_cb = UVMCallbacks.get_last(self, self.m_obj, self.CB)
        return self.m_cb

    # Function: next
    #
    # Returns the next valid (enabled) callback of the callback type (or
    # a derivative) that is in the queue of the context object. If there
    # are no more valid callbacks in the queue, then ~None~ is returned.
    def next(self):
        self.m_cb = UVMCallbacks.get_next(self, self.m_obj, self.CB)
        return self.m_cb

    # Function: prev
    #
    # Returns the previous valid (enabled) callback of the callback type (or
    # a derivative) that is in the queue of the context object. If there
    # are no more valid callbacks in the queue, then ~None~ is returned.
    def prev(self):
        self.m_cb = UVMCallbacks.get_prev(self, self.m_obj, self.CB)
        return self.m_cb

    # Function: get_cb
    #
    # Returns the last callback accessed via a first() or next()
    # call.
    def get_cb(self):
        return self.m_cb

    #function void trace(uvm_object obj = None)
    #   if (m_cb is not None && T::cbs::get_debug_flags() & UVM_CALLBACK_TRACE):
    #      uvm_report_object reporter = None
    #      string who = "Executing "
    #      void'($cast(reporter, obj))
    #      if (reporter is None) void'($cast(reporter, m_obj))
    #      if (reporter is None) reporter = uvm_top
    #      if (obj is not None) who = {obj.get_full_name(), " is executing "}
    #      elif (m_obj is not None) who = {m_obj.get_full_name(), " is executing "}
    #      reporter.uvm_report_info("CLLBK_TRC", {who, "callback ", m_cb.get_name()}, UVM_LOW)
    #   end
    #endfunction
    #endclass

#------------------------------------------------------------------------------
# CLASS: uvm_callback
#
# The ~uvm_callback~ class is the base class for user-defined callback classes.
# Typically, the component developer defines an application-specific callback
# class that extends from this class. In it, he defines one or more virtual
# methods, called a ~callback interface~, that represent the hooks available
# for user override.
#
# Methods intended for optional override should not be declared ~pure.~ Usually,
# all the callback methods are defined with empty implementations so users have
# the option of overriding any or all of them.
#
# The prototypes for each hook method are completely application specific with
# no restrictions.
#------------------------------------------------------------------------------


class UVMCallback(UVMObject):

    reporter = UVMReportObject("cb_tracer")

    # Function: new
    #
    # Creates a new uvm_callback object, giving it an optional ~name~.
    def __init__(self, name="uvm_callback"):
        UVMObject.__init__(self, name)
        self.m_enabled = True

    # Function: callback_mode
    #
    # Enable/disable callbacks (modeled like rand_mode and constraint_mode).
    def callback_mode(self, on=-1):
        if on == 0 or on == 1:
            is_en = "DISABLED"
            if on == 1:
                is_en = "ENABLED"
            uvm_cb_trace_noobj(self,sv.sformatf("Setting callback mode for %s to %s",
                  self.get_name(), is_en))
        else:
            is_en = "DISABLED"
            if self.m_enabled is True:
                is_en = "ENABLED"
            uvm_cb_trace_noobj(self, sv.sformatf("Callback mode for %s is %s",
                self.get_name(), is_en))
        callback_mode = self.m_enabled
        if on == 0:
            self.m_enabled = False
        if on == 1:
            self.m_enabled = True
        return callback_mode

    # Function: is_enabled
    #
    # Returns 1 if the callback is enabled, 0 otherwise.
    def is_enabled(self):
        return self.callback_mode()


    type_name = "uvm_callback"

    # Function: get_type_name
    #
    # Returns the type name of this callback object.

    def get_type_name(self):
        return UVMCallback.type_name
