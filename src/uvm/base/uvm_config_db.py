#//----------------------------------------------------------------------
#//   Copyright 2011 Cypress Semiconductor
#//   Copyright 2010-2011 Mentor Graphics Corporation
#//   Copyright 2014 NVIDIA Corporation
#//   Copyright 2019 Tuomas Poikela (tpoikela)
#//   All Rights Reserved Worldwide
#//
#//   Licensed under the Apache License, Version 2.0 (the
#//   "License"); you may not use this file except in
#//   compliance with the License.  You may obtain a copy of
#//   the License at
#//
#//       http://www.apache.org/licenses/LICENSE-2.0
#//
#//   Unless required by applicable law or agreed to in
#//   writing, software distributed under the License is
#//   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//   CONDITIONS OF ANY KIND, either express or implied.  See
#//   the License for the specific language governing
#//   permissions and limitations under the License.
#//----------------------------------------------------------------------

from cocotb.triggers import Event

from .uvm_resource import UVMResourceBase, UVMResource, UVMResourcePool, PRI_HIGH
from .uvm_resource_db import UVMResourceDb
from .uvm_pool import UVMPool
from .sv import uvm_re_match, uvm_glob_to_re
from .uvm_debug import uvm_debug

"""
Title: UVM Configuration Database

Topic: Intro

The `UVMConfigDb` class provides a convenience interface
on top of the `UVMResourceDb` to simplify the basic interface
that is used for configuring `UVMComponent` instances.

If the run-time `+UVM_CONFIG_DB_TRACE` command line option is specified,
all configuration DB accesses (read and write) are displayed.
"""

#//Internal class for config waiters


class m_uvm_waiter:

    def __init__(self, inst_name, field_name):
        """
        Args:
            inst_name:
            field_name:
        """
        self.inst_name = inst_name
        self.field_name = field_name
        self.trigger = Event()


class UVMConfigDb(UVMResourceDb):
    """
     All of the functions in UVMConfigDb are static, so they
     must be called using the classname.  For example::

     UVMConfigDb.set(self, "*", "A");

     The parameter value "int" identifies the configuration type as
     an int property.

     The `UVMConfigDb.set` and `UVMConfigDb.get` methods provide the same API and
     semantics as the set/get_config_* functions in `UVMComponent`.
    """

    #  // Internal lookup of config settings so they can be reused
    #  // The context has a pool that is keyed by the inst/field name.
    #  static uvm_pool#(string,uvm_resource#(T)) m_rsc[UVMComponent];
    m_rsc = {}

    #  // Internal waiter list for wait_modified
    #  static local uvm_queue#(m_uvm_waiter) m_waiters[string];
    m_waiters = {}

    @classmethod
    def get(cls, cntxt, inst_name, field_name, value, T=None):
        """
        Get the value for `field_name` in `inst_name`, using component `cntxt` as
        the starting search point. `inst_name` is an explicit instance name
        relative to `cntxt` and may be an empty string if the `cntxt` is the
        instance that the configuration object applies to. `field_name`
        is the specific field in the scope that is being searched for.

        The basic ~get_config_*~ methods from `UVMComponent` are mapped to
        this function as:

        .. code-block:: python

          get_config_int(...) => uvm_config_db#(uvm_bitstream_t)::get(cntxt,...)
          get_config_string(...) => uvm_config_db#(string)::get(cntxt,...)
          get_config_object(...) => uvm_config_db#(uvm_object)::get(cntxt,...)
          @classmethod
          def bit get(cls,  cntxt, inst_name, field_name, value):

        Args:
            cntxt:
            inst_name:
            field_name:
            value:
            T:
        Returns:
        Raises:
        """
        #//TBD: add file/line
        # p = 0
        r = None  # uvm_resource#(T) r, rt;
        # rt = None
        rp = UVMResourcePool.get()
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()

        if cntxt is None:
            cntxt = cs.get_root()
        if inst_name == "":
            inst_name = cntxt.get_full_name()
        elif cntxt.get_full_name() != "":
            inst_name = cntxt.get_full_name() + "." + inst_name

        #rq = rp.lookup_regex_names(inst_name, field_name, uvm_resource#(T)::get_type());
        rq = rp.lookup_regex_names(inst_name, field_name)
        uvm_debug(cls, 'get', 'rq size is ' + str(rq))
        r = UVMResource.get_highest_precedence(rq, T)

        if UVMConfigDbOptions.is_tracing():
            UVMResourceDb.m_show_msg("CFGDB/GET", "Configuration","read", inst_name,
                field_name, cntxt, r)
        if r is None:
            return False

        if hasattr(value, 'append'):
            value.append(r.read(cntxt))
        else:
            raise Exception('value must be a list-like with append')
        return True

    @classmethod
    def set(cls, cntxt, inst_name, field_name, value, T=None):
        """
        Create a new or update an existing configuration setting for
        `field_name` in `inst_name` from `cntxt`.
        The setting is made at `cntxt`, with the full scope of the set
        being {`cntxt`,".",`inst_name`}. If `cntxt` is `null` then `inst_name`
        provides the complete scope information of the setting.
        `field_name` is the target field. Both `inst_name` and `field_name`
        may be glob style or regular expression style expressions.

        If a setting is made at build time, the `cntxt` hierarchy is
        used to determine the setting's precedence in the database.
        Settings from hierarchically higher levels have higher
        precedence. Settings from the same level of hierarchy have
        a last setting wins semantic. A precedence setting of
        <uvm_resource_base::default_precedence>  is used for uvm_top, and
        each hierarchical level below the top is decremented by 1.

        After build time, all settings use the default precedence and thus
        have a last wins semantic. So, if at run time, a low level
        component makes a runtime setting of some field, that setting
        will have precedence over a setting from the test level that was
        made earlier in the simulation.

        The basic ~set_config_*~ methods from `UVMComponent` are mapped to
        this function as:

        .. code-block:: python

          set_config_int(...) => uvm_config_db#(uvm_bitstream_t)::set(cntxt,...)
          set_config_string(...) => uvm_config_db#(string)::set(cntxt,...)
          set_config_object(...) => uvm_config_db#(uvm_object)::set(cntxt,...)

        Args:
            cntxt:
            inst_name:
            field_name:
            value:
            T:
        """
        p = None
        curr_phase = None
        exists = False
        lookup = ""
        pool = None  # uvm_pool#(string,uvm_resource#(T)) pool;
        rstate = ""
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()

        # take care of random stability during allocation
        # process p = process::self();
        # if(p != null)
        # rstate = p.get_randstate();

        top = cs.get_root()
        curr_phase = top.m_current_phase

        if cntxt is None:
            cntxt = top
        if inst_name == "":
            inst_name = cntxt.get_full_name()
        elif cntxt.get_full_name() != "":
            inst_name = cntxt.get_full_name() + "." + inst_name

        if cntxt in UVMConfigDb.m_rsc:
            pass
        else:
            UVMConfigDb.m_rsc[cntxt] = UVMPool()
        pool = UVMConfigDb.m_rsc[cntxt]

        # Insert the token in the middle to prevent cache
        # oddities like i=foobar,f=xyz and i=foo,f=barxyz.
        # Can't just use '.', because '.' isn't illegal
        # in field names
        lookup = inst_name + "__M_UVM__" + field_name

        r = None  # uvm_resource#(T) r;
        if not pool.exists(lookup):
            r = UVMResource(field_name, inst_name)
            pool.add(lookup, r)
        else:
            r = pool.get(lookup)
            exists = True

        if curr_phase is not None and curr_phase.get_name() == "build":
            r.precedence = UVMResourceBase.default_precedence - cntxt.get_depth()
        else:
            r.precedence = UVMResourceBase.default_precedence

        r.write(value, cntxt)

        if exists:
            rp = UVMResourcePool.get()
            rp.set_priority_name(r, PRI_HIGH)
        else:
            # Doesn't exist yet, so put it in resource db at the head.
            r.set_override()

        # trigger any waiters
        if field_name in UVMConfigDb.m_waiters:
            w = None
            for i in range(len(UVMConfigDb.m_waiters[field_name])):
                w = UVMConfigDb.m_waiters[field_name].get(i)
                if uvm_re_match(uvm_glob_to_re(inst_name),w.inst_name) == 0:
                    w.trigger.set()

        if p is not None:
            p.set_randstate(rstate)

        if UVMConfigDbOptions.is_tracing():
            UVMResourceDb.m_show_msg("CFGDB/SET", "Configuration","set", inst_name, field_name, cntxt, r)

    @classmethod
    def exists(cls, cntxt, inst_name, field_name, spell_chk=False):
        """
        Check if a value for `field_name` is available in `inst_name`, using
        component `cntxt` as the starting search point. `inst_name` is an explicit
        instance name relative to `cntxt` and may be an empty string if the
        `cntxt` is the instance that the configuration object applies to.
        `field_name` is the specific field in the scope that is being searched for.
        The `spell_chk` arg can be set to 1 to turn spell checking on if it
        is expected that the field should exist in the database. The function
        returns 1 if a config parameter exists and 0 if it doesn't exist.

        Args:
            cntxt:
            inst_name:
            field_name:
            spell_chk:
        Returns:
        """
        from .uvm_coreservice import UVMCoreService
        cs = UVMCoreService.get()
        if cntxt is None:
            cntxt = cs.get_root()
        if inst_name == "":
            inst_name = cntxt.get_full_name()
        elif cntxt.get_full_name() != "":
            inst_name = cntxt.get_full_name() + "." + inst_name
        found_val = UVMResourceDb.get_by_name(inst_name,field_name,spell_chk)
        return found_val is not None

    #  // Function: wait_modified
    #  //
    #  // Wait for a configuration setting to be set for ~field_name~
    #  // in ~cntxt~ and ~inst_name~. The task blocks until a new configuration
    #  // setting is applied that effects the specified field.
    #
    #  static task wait_modified(UVMComponent cntxt, string inst_name,
    #      string field_name);
    #    process p = process::self();
    #    string rstate = p.get_randstate();
    #    m_uvm_waiter waiter;
    #    uvm_coreservice_t cs = uvm_coreservice_t::get();
    #
    #    if(cntxt == null)
    #      cntxt = cs.get_root();
    #    if(cntxt != cs.get_root()) begin
    #      if(inst_name != "")
    #        inst_name = {cntxt.get_full_name(),".",inst_name};
    #      else
    #        inst_name = cntxt.get_full_name();
    #    end
    #
    #    waiter = new(inst_name, field_name);
    #
    #    if(!m_waiters.exists(field_name))
    #      m_waiters[field_name] = new;
    #    m_waiters[field_name].push_back(waiter);
    #
    #    p.set_randstate(rstate);
    #
    #    // wait on the waiter to trigger
    #    @waiter.trigger;
    #
    #    // Remove the waiter from the waiter list
    #    for(int i=0; i<m_waiters[field_name].size(); ++i) begin
    #      if(m_waiters[field_name].get(i) == waiter) begin
    #        m_waiters[field_name].delete(i);
    #        break;
    #      end
    #    end
    #  endtask
    #
    #
    #endclass

#// Section: Types
#
#//----------------------------------------------------------------------
#// Topic: uvm_config_int
#//
#// Convenience type for uvm_config_db#(uvm_bitstream_t)
#//
#//| typedef uvm_config_db#(uvm_bitstream_t) uvm_config_int;
#typedef uvm_config_db#(uvm_bitstream_t) uvm_config_int;
#
#//----------------------------------------------------------------------
#// Topic: uvm_config_string
#//
#// Convenience type for uvm_config_db#(string)
#//
#//| typedef uvm_config_db#(string) uvm_config_string;
#typedef uvm_config_db#(string) uvm_config_string;
#
#//----------------------------------------------------------------------
#// Topic: uvm_config_object
#//
#// Convenience type for uvm_config_db#(uvm_object)
#//
#//| typedef uvm_config_db#(uvm_object) uvm_config_object;
#typedef uvm_config_db#(uvm_object) uvm_config_object;
#
#//----------------------------------------------------------------------
#// Topic: uvm_config_wrapper
#//
#// Convenience type for uvm_config_db#(uvm_object_wrapper)
#//
#//| typedef uvm_config_db#(uvm_object_wrapper) uvm_config_wrapper;
#typedef uvm_config_db#(uvm_object_wrapper) uvm_config_wrapper;


class UVMConfigDbOptions:
    """
     Class: uvm_config_db_options

     Provides a namespace for managing options for the
     configuration DB facility.  The only thing allowed in this class is static
     local data members and static functions for manipulating and
     retrieving the value of the data members.  The static local data
     members represent options and settings that control the behavior of
     the configuration DB facility.

     Options include:

      * tracing:  on/off

        The default for tracing is off.
    """

    #  static local bit ready;
    ready = False
    #  static local bit tracing;
    tracing = False

    @classmethod
    def turn_on_tracing(cls):
        """
        Turn tracing on for the configuration database. This causes all
        reads and writes to the database to display information about
        the accesses. Tracing is off by default.

        This method is implicitly called by the `+UVM_CONFIG_DB_TRACE`.
        """
        if not UVMConfigDbOptions.ready:
            UVMConfigDbOptions.init()
        UVMConfigDbOptions.tracing = True

    @classmethod
    def turn_off_tracing(cls):
        """
        Turn tracing off for the configuration database.
        """
        if not UVMConfigDbOptions.ready:
            UVMConfigDbOptions.init()
        UVMConfigDbOptions.tracing = False

    @classmethod
    def is_tracing(cls):
        """
        Returns: 1 if the tracing facility is on and 0 if it is off.
        """
        if not UVMConfigDbOptions.ready:
            UVMConfigDbOptions.init()
        return UVMConfigDbOptions.tracing


    @classmethod
    def init(cls):
        trace_args = []  # string trace_args[$];
        from .uvm_cmdline_processor import UVMCmdlineProcessor
        clp = UVMCmdlineProcessor.get_inst()
        if clp.get_arg_matches("+UVM_CONFIG_DB_TRACE", trace_args) > 0:
            UVMConfigDbOptions.tracing = 1
        if clp.get_arg_matches("+UVM_CONFIG_DB_TRACE=", trace_args) > 0:
            UVMConfigDbOptions.tracing = 1
        UVMConfigDbOptions.ready = 1

