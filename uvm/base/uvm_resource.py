#//----------------------------------------------------------------------
#//   Copyright 2011 Cypress Semiconductor
#//   Copyright 2010 Mentor Graphics Corporation
#//   Copyright 2011 Cadence Design Systems, Inc. 
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

from .uvm_object import UVMObject
from .sv import sv, uvm_re_match, uvm_glob_to_re
from ..uvm_macros import uvm_typename
from ..macros import uvm_info
from .uvm_globals import uvm_report_error
from .uvm_object_globals import UVM_NONE
from .uvm_spell_chkr import UVMSpellChkr
from .uvm_pool import UVMPool
from .uvm_printer import UVMLinePrinter
from .uvm_queue import UVMQueue

#//----------------------------------------------------------------------
#// Title: Resources
#//
#// Topic: Intro
#//
#// A resource is a parameterized container that holds arbitrary data.
#// Resources can be used to configure components, supply data to
#// sequences, or enable sharing of information across disparate parts of
#// a testbench.  They are stored using scoping information so their
#// visibility can be constrained to certain parts of the testbench.
#// Resource containers can hold any type of data, constrained only by
#// the data types available in SystemVerilog.  Resources can contain
#// scalar objects, class handles, queues, lists, or even virtual
#// interfaces.
#//
#// Resources are stored in a resource database so that each resource can
#// be retrieved by name or by type. The database has both a name table
#// and a type table and each resource is entered into both. The database
#// is globally accessible.
#//
#// Each resource has a set of scopes over which it is visible.  The set
#// of scopes is represented as a regular expression.  When a resource is
#// looked up the scope of the entity doing the looking up is supplied to
#// the lookup function.  This is called the ~current scope~.  If the
#// current scope is in the set of scopes over which a resource is
#// visible then the resource can be retuned in the lookup.
#//
#// Resources can be looked up by name or by type. To support type lookup
#// each resource has a static type handle that uniquely identifies the
#// type of each specialized resource container.
#//
#// Multiple resources that have the same name are stored in a queue.
#// Each resource is pushed into a queue with the first one at the front
#// of the queue and each subsequent one behind it.  The same happens for
#// multiple resources that have the same type.  The resource queues are
#// searched front to back, so those placed earlier in the queue have
#// precedence over those placed later.
#//
#// The precedence of resources with the same name or same type can be
#// altered.  One way is to set the ~precedence~ member of the resource
#// container to any arbitrary value.  The search algorithm will return
#// the resource with the highest precedence.  In the case where there
#// are multiple resources that match the search criteria and have the
#// same (highest) precedence, the earliest one located in the queue will
#// be one returned.  Another way to change the precedence is to use the
#// set_priority function to move a resource to either the front or back
#// of the queue.
#//
#// The classes defined here form the low level layer of the resource
#// database.  The classes include the resource container and the database
#// that holds the containers.  The following set of classes are defined
#// here:
#//
#// <uvm_resource_types>: A class without methods or members, only
#// typedefs and enums. These types and enums are used throughout the
#// resources facility.  Putting the types in a class keeps them confined
#// to a specific name space.
#//
#// <uvm_resource_options>: policy class for setting options, such
#// as auditing, which effect resources.
#//
#// <uvm_resource_base>: the base (untyped) resource class living in the
#// resource database.  This class includes the interface for setting a
#// resource as read-only, notification, scope management, altering
#// search priority, and managing auditing.
#//
#// <uvm_resource#(T)>: parameterized resource container.  This class
#// includes the interfaces for reading and writing each resource.
#// Because the class is parameterized, all the access functions are type
#// safe.
#//
#// <uvm_resource_pool>: the resource database. This is a singleton
#// class object.
#//----------------------------------------------------------------------

#----------------------------------------------------------------------
# Class: uvm_resource_types
#
# Provides typedefs and enums used throughout the resources facility.
# This class has no members or methods, only typedefs.  It's used in
# lieu of package-scope types.  When needed, other classes can use
# these types by prefixing their usage with uvm_resource_types::.  E.g.
#
#|  uvm_resource_types::rsrc_q_t queue
#
#----------------------------------------------------------------------
#class uvm_resource_types;
#
#  // types uses for setting overrides
#  typedef bit[1:0] override_t;
#  typedef enum override_t { TYPE_OVERRIDE = 2'b01,
#                            NAME_OVERRIDE = 2'b10 } override_e;
#
#   // general purpose queue of resourcex
#  typedef uvm_queue#(uvm_resource_base) rsrc_q_t;
#
#  // enum for setting resource search priority
#  typedef enum { PRI_HIGH, PRI_LOW } priority_e;
#
#  // access record for resources.  A set of these is stored for each
#  // resource by accessing object.  It's updated for each read/write.
#  typedef struct
#  {
#    time read_time;
#    time write_time;
#    int unsigned read_count;
#    int unsigned write_count;
#  } access_t;
#
#endclass

TYPE_OVERRIDE = 1
NAME_OVERRIDE = 2

UVM_USE_RESOURCE_CONVERTER = False

PRI_HIGH = 0
PRI_LOW = 1


class Access_t:
    def __init__(self):
        self.read_time = 0
        self.write_time = 0
        self.read_count = 0
        self.write_count = 0

#----------------------------------------------------------------------
# Class: uvm_resource_options
#
# Provides a namespace for managing options for the
# resources facility.  The only thing allowed in this class is static
# local data members and static functions for manipulating and
# retrieving the value of the data members.  The static local data
# members represent options and settings that control the behavior of
# the resources facility.
#
# Options include:
#
#  * auditing:  on/off
#
#    The default for auditing is on.  You may wish to turn it off to
#    for performance reasons.  With auditing off memory is not
#    consumed for storage of auditing information and time is not
#    spent collecting and storing auditing information.  Of course,
#    during the period when auditing is off no audit trail information
#    is available
#
#----------------------------------------------------------------------


class UVMResourceOptions:

    auditing = True

    @classmethod
    def turn_on_auditing(cls):
        UVMResourceOptions.auditing = True

    @classmethod
    def turn_off_auditing(cls):
        UVMResourceOptions.auditing = False

    @classmethod
    def is_auditing(cls):
        return UVMResourceOptions.auditing


class get_t:
    def __init(self):
        self.name = ""
        self.scope = ""
        self.rsrc = None
        self.t = 0

#----------------------------------------------------------------------
# Class: uvm_resource_base
#
# Non-parameterized base class for resources.  Supports interfaces for
# scope matching, and virtual functions for printing the resource and
# for printing the accessor list
#----------------------------------------------------------------------


class UVMResourceBase(UVMObject):

    #// variable: default_precedence
    #//
    #// The default precedence for an resource that has been created.
    #// When two resources have the same precedence, the first resource
    #// found has precedence.
    #//
    default_precedence = 1000

    #// Function: new
    #//
    #// constructor for uvm_resource_base.  The constructor takes two
    #// arguments, the name of the resource and a regular expression which
    #// represents the set of scopes over which this resource is visible.
    def __init__(self, name="", s="*"):
        UVMObject.__init__(self, name)
        #self.scope = ""
        self.set_scope(s)
        self.modified = False
        self.read_only = False
        self.access = {}  # uvm_resource_types::access_t access[string]
        # variable: precedence
        #
        # This variable is used to associate a precedence that a resource
        # has with respect to other resources which match the same scope
        # and name. Resources are set to the <default_precedence> initially,
        # and may be set to a higher or lower precedence as desired.
        self.precedence = UVMResourceBase.default_precedence

    #// Function: get_type_handle
    #//
    #// Pure virtual function that returns the type handle of the resource
    #// container.
    def get_type_handle(self):
        raise Exception('get_type_handle: pure virtual method')


    #//---------------------------
    #// Group: Read-only Interface
    #//---------------------------
    #
    #// Function: set_read_only
    #//
    #// Establishes this resource as a read-only resource.  An attempt
    #// to call <uvm_resource#(T)::write> on the resource will cause an error.

    def set_read_only(self):
        self.read_only = True

    #// function set_read_write
    #//
    #// Returns the resource to normal read-write capability.
    #
    #// Implementation question: Not sure if this function is necessary.
    #// Once a resource is set to read_only no one should be able to change
    #// that.  If anyone can flip the read_only bit then the resource is not
    #// truly read_only.

    def set_read_write(self):
        self.read_only = False

    #// Function: is_read_only
    #//
    #// Returns one if this resource has been set to read-only, zero
    #// otherwise
    def is_read_only(self):
        return self.read_only

    #//--------------------
    #// Group: Notification
    #//--------------------

    #// Task: wait_modified
    #//
    #// This task blocks until the resource has been modified -- that is, a
    #// <uvm_resource#(T)::write> operation has been performed.  When a 
    #// <uvm_resource#(T)::write> is performed the modified bit is set which 
    #// releases the block.  Wait_modified() then clears the modified bit so 
    #// it can be called repeatedly.

    #task wait_modified();
    #  wait (modified == 1);
    #  modified = 0;
    #endtask

    #//-----------------------
    #// Group: Scope Interface
    #//-----------------------
    #//
    #// Each resource has a name, a value and a set of scopes over which it
    #// is visible. A scope is a hierarchical entity or a context.  A scope
    #// name is a multi-element string that identifies a scope.  Each
    #// element refers to a scope context and the elements are separated by
    #// dots (.).
    #// 
    #//|    top.env.agent.monitor
    #// 
    #// Consider the example above of a scope name.  It consists of four
    #// elements: "top", "env", "agent", and "monitor".  The elements are
    #// strung together with a dot separating each element.  ~top.env.agent~
    #// is the parent of ~top.env.agent.monitor~, ~top.env~ is the parent of
    #// ~top.env.agent~, and so on.  A set of scopes can be represented by a
    #// set of scope name strings.  A very straightforward way to represent
    #// a set of strings is to use regular expressions.  A regular
    #// expression is a special string that contains placeholders which can
    #// be substituted in various ways to generate or recognize a
    #// particular set of strings.  Here are a few simple examples:
    #// 
    #//|     top\..*	                all of the scopes whose top-level component
    #//|                            is top
    #//|    top\.env\..*\.monitor	all of the scopes in env that end in monitor;
    #//|                            i.e. all the monitors two levels down from env
    #//|    .*\.monitor	            all of the scopes that end in monitor; i.e.
    #//|                            all the monitors (assuming a naming convention
    #//|                            was used where all monitors are named "monitor")
    #//|    top\.u[1-5]\.*	        all of the scopes rooted and named u1, u2, u3,
    #//                             u4, or u5, and any of their subscopes.
    #// 
    #// The examples above use POSIX regular expression notation.  This is
    #// a very general and expressive notation.  It is not always the case
    #// that so much expressiveness is required.  Sometimes an expression
    #// syntax that is easy to read and easy to write is useful, even if
    #// the syntax is not as expressive as the full power of POSIX regular
    #// expressions.  A popular substitute for regular expressions is
    #// globs.  A glob is a simplified regular expression. It only has
    #// three metacharacters -- *, +, and ?.  Character ranges are not
    #// allowed and dots are not a metacharacter in globs as they are in
    #// regular expressions.  The following table shows glob
    #// metacharacters.
    #// 
    #//|      char	meaning	                regular expression
    #//|                                    equivalent
    #//|      *	    0 or more characters	.*
    #//|      +	    1 or more characters	.+
    #//|      ?	    exactly one character	.
    #// 
    #// Of the examples above, the first three can easily be translated
    #// into globs.  The last one cannot.  It relies on notation that is
    #// not available in glob syntax.
    #// 
    #//|    regular expression	    glob equivalent
    #//|    ---------------------      ------------------
    #//|    top\..*	            top.*
    #//|    top\.env\..*\.monitor	    top.env.*.monitor
    #//|    .*\.monitor	            *.monitor
    #// 
    #// The resource facility supports both regular expression and glob
    #// syntax.  Regular expressions are identified as such when they 
    #// surrounded by '/' characters. For example, ~/^top\.*/~ is
    #// interpreted as the regular expression ~^top\.*~, where the
    #// surrounding '/' characters have been removed. All other expressions
    #// are treated as glob expressions. They are converted from glob 
    #// notation to regular expression notation internally.  Regular expression 
    #// compilation and matching as well as glob-to-regular expression 
    #// conversion are handled by two DPI functions:
    #// 
    #//|    function int uvm_re_match(string re, string str);
    #//|    function string uvm_glob_to_re(string glob);
    #// 
    #// uvm_re_match both compiles and matches the regular expression.
    #// All of the matching is done using regular expressions, so globs are
    #// converted to regular expressions and then processed.


    #// Function: set_scope
    #//
    #// Set the value of the regular expression that identifies the set of
    #// scopes over which this resource is visible.  If the supplied
    #// argument is a glob it will be converted to a regular expression
    #// before it is stored.
    #//
    def set_scope(self, s):
        scope = uvm_glob_to_re(s)
        self.scope = scope

    #// Function: get_scope
    #//
    #// Retrieve the regular expression string that identifies the set of
    #// scopes over which this resource is visible.
    #//
    def get_scope(self):
        return self.scope

    #// Function: match_scope
    #//
    #// Using the regular expression facility, determine if this resource
    #// is visible in a scope.  Return one if it is, zero otherwise.
    #//
    def match_scope(self, s):
        err = uvm_re_match(self.scope, s)
        return (err == 0)

    #//----------------
    #// Group: Priority
    #//----------------
    #//
    #// Functions for manipulating the search priority of resources.  The
    #// function definitions here are pure virtual and are implemented in
    #// derived classes.  The definitons serve as a priority management
    #// interface.

    #// Function: set priority
    #//
    #// Change the search priority of the resource based on the value of
    #// the priority enum argument.
    #//
    #pure virtual function void set_priority (uvm_resource_types::priority_e pri);

    #//-------------------------
    #// Group: Utility Functions
    #//-------------------------

    #// function convert2string
    #//
    #// Create a string representation of the resource value.  By default
    #// we don't know how to do this so we just return a "?".  Resource
    #// specializations are expected to override this function to produce a
    #// proper string representation of the resource value.

    #function string convert2string();
    #  return "?";
    #endfunction

    #// Function: do_print
    #//
    #// Implementation of do_print which is called by print().

    #function void do_print (uvm_printer printer);
    #  printer.print_string("",$sformatf("%s [%s] : %s", get_name(), get_scope(), convert2string()));
    #endfunction


    #//-------------------
    #// Group: Audit Trail
    #//-------------------
    #//
    #// To find out what is happening as the simulation proceeds, an audit
    #// trail of each read and write is kept. The <uvm_resource#(T)::read> and
    #// <uvm_resource#(T)::write> methods each take an accessor argument.  This is a
    #// handle to the object that performed that resource access.
    #//
    #//|    function T read(uvm_object accessor = None)
    #//|    function void write(T t, uvm_object accessor = None)
    #//
    #// The accessor can by anything as long as it is derived from
    #// uvm_object.  The accessor object can be a component or a sequence
    #// or whatever object from which a read or write was invoked.
    #// Typically the ~this~ handle is used as the
    #// accessor.  For example:
    #//
    #//|    uvm_resource#(int) rint
    #//|    int i
    #//|    ...
    #//|    rint.write(7, this)
    #//|    i = rint.read(this)
    #//
    #// The accessor's ~get_full_name()~ is stored as part of the audit trail.
    #// This way you can find out what object performed each resource access.
    #// Each audit record also includes the time of the access (simulation time)
    #// and the particular operation performed (read or write).
    #//
    #// Auditing is controlled through the <uvm_resource_options> class.
    #// function: record_read_access
    #function void record_read_access(uvm_object accessor = None)
    def record_read_access(self, accessor=None):
        str = ""
        access_record = None  # uvm_resource_types::access_t access_record
        #  // If an accessor object is supplied then get the accessor record.
        #  // Otherwise create a new access record.  In either case populate
        #  // the access record with information about this access.  Check
        #  // first to make sure that auditing is turned on.
        if not UVMResourceOptions.is_auditing():
            return

        # If an accessor is supplied, then use its name
        # as the database entry for the accessor record.
        #  Otherwise, use "<empty>" as the database entry.
        if accessor is not None:
            str = accessor.get_full_name()
        else:
            str = "<empty>"

        # Create a new accessor record if one does not exist
        if str in self.access:
            access_record = self.access[str]
        else:
            access_record = Access_t()
            self.init_access_record(access_record)

        # Update the accessor record
        access_record.read_count += 1
        # TODO access_record.read_time = $realtime
        self.access[str] = access_record

    #// function: record_write_access
    #
    def record_write_access(self, accessor=None):
        # If an accessor object is supplied then get the accessor record.
        # Otherwise create a new access record.  In either case populate
        # the access record with information about this access.  Check
        # first that auditing is turned on
        if UVMResourceOptions.is_auditing():
            if accessor is not None:
                access_record = None  # uvm_resource_types::access_t
                str = accessor.get_full_name()
                if str in self.access:
                    access_record = self.access[str]
                else:
                    access_record = Access_t()
                    self.init_access_record(access_record)
                access_record.write_count += 1
                # TODO access_record.write_time = $realtime
                self.access[str] = access_record

    #// Function: init_access_record
    #//
    #// Initialize a new access record
    #//
    def init_access_record(self, access_record):
        # inout uvm_resource_types::access_t access_record)
        access_record.read_time = 0
        access_record.write_time = 0
        access_record.read_count = 0
        access_record.write_count = 0


class UVMResource(UVMResourceBase):

    my_type = None

    def __init__(self, name="", scope=""):
        UVMResourceBase.__init__(self, name, scope)
        self.val = None   # Resource value
        self.m_r2s = None  # Res2string converter
        self.modified = False

    def convert2string(self):
        if UVM_USE_RESOURCE_CONVERTER:
            self.m_get_converter()
            return self.m_r2s.convert2string(self.val)
        return sv.sformatf("(%s) %s", uvm_typename(self.val), self.val)


    @classmethod
    def get_type(cls):
        if UVMResource.my_type is None:
            UVMResource.my_type = UVMResource()
        else:
            return UVMResource.my_type

    def get_type_handle(self):
        return UVMResource.get_type()

    def set(self):
        """ Simply put this resource into the global resource pool"""
        pool = UVMResourcePool.get()
        pool.set(self)

    def set_override(self, override=NAME_OVERRIDE):
        rp = UVMResourcePool.get()
        rp.set(self, override)

    # Function: get_by_name
    #
    # looks up a resource by ~name~ in the name map. The first resource
    # with the specified name, whose type is the current type, and is
    # visible in the specified ~scope~ is returned, if one exists.  The
    # ~rpterr~ flag indicates whether or not an error should be reported
    # if the search fails.  If ~rpterr~ is set to one then a failure
    # message is issued, including suggested spelling alternatives, based
    # on resource names that exist in the database, gathered by the spell
    # checker.
    @classmethod
    def get_by_name(cls, scope, name, rpterr=True):
        rp = UVMResourcePool.get()
        rsrc = None
        rsrc_base = rp.get_by_name(scope, name, cls.get_type(), rpterr)
        if rsrc_base is None:
            return None
        return rsrc

    def read(self, accessor=None):
        """ Return the object stored in the resource container """
        self.record_read_access(accessor)
        return self.val

    # Function: write
    # Modify the object stored in this resource container.  If the
    # resource is read-only then issue an error message and return
    # without modifying the object in the container.  If the resource is
    # not read-only and an ~accessor~ object has been supplied then also
    # update the accessor record.  Lastly, replace the object value in
    # the container with the value supplied as the argument, ~t~, and
    # release any processes blocked on
    # <uvm_resource_base::wait_modified>.  If the value to be written is
    # the same as the value already present in the resource then the
    # write is not done.  That also means that the accessor record is not
    # updated and the modified bit is not set.
    def write(self, t, accessor=None):
        if self.is_read_only():
            uvm_report_error("resource", sv.sformatf("resource %s is read only -- cannot modify",
                self.get_name()))
            return

        # Set the modified bit and record the transaction only if the value
        # has actually changed.
        if self.val == t:
            return

        self.record_write_access(accessor)

        # set the value and set the dirty bit
        self.val = t
        self.modified = True

    #// Function: get_highest_precedence
    #//
    #// In a queue of resources, locate the first one with the highest
    #// precedence whose type is T.  This function is static so that it can
    #// be called from anywhere.
    #static function this_type get_highest_precedence(ref uvm_resource_types::rsrc_q_t q)
    @classmethod
    def get_highest_precedence(cls, q, T=None):
        rsrc = None
        r = None
        i = 0
        prec = 0
        first = 0

        if len(q) == 0:
            return None

        # Locate first resources in the queue whose type is T
        for i in range(len(q)):
            first = i
            q_val = q[first]
            if T is not None:
                if sv.cast(rsrc, q_val, T):
                    rsrc = q_val
                    break
            else:
                rsrc = q_val
                break

        # no resource in the queue whose type is T
        if rsrc is None:
            return None

        prec = rsrc.precedence

        # start searching from the next resource after the first resource
        # whose type is T
        # for(int i = first+1; i < q.size(); ++i) begin
        for i in range(first + 1, len(q)):
            if T is not None:
                if sv.cast(r, q[i], T):
                    r = q[i]
                    if r.precedence > prec:
                        rsrc = r
                        prec = r.precedence
            else:
                r = q[i]
                if r.precedence > prec:
                    rsrc = r
                    prec = r.precedence
        return rsrc

#//----------------------------------------------------------------------
#// Class: uvm_resource_pool
#//
#// The global (singleton) resource database.
#//
#// Each resource is stored both by primary name and by type handle.  The
#// resource pool contains two associative arrays, one with name as the
#// key and one with the type handle as the key.  Each associative array
#// contains a queue of resources.  Each resource has a regular
#// expression that represents the set of scopes over which it is visible.
#//
#//|  +------+------------+                          +------------+------+
#//|  | name | rsrc queue |                          | rsrc queue | type |
#//|  +------+------------+                          +------------+------+
#//|  |      |            |                          |            |      |
#//|  +------+------------+                  +-+-+   +------------+------+
#//|  |      |            |                  | | |<--+---*        |  T   |
#//|  +------+------------+   +-+-+          +-+-+   +------------+------+
#//|  |  A   |        *---+-->| | |           |      |            |      |
#//|  +------+------------+   +-+-+           |      +------------+------+
#//|  |      |            |      |            |      |            |      |
#//|  +------+------------+      +-------+  +-+      +------------+------+
#//|  |      |            |              |  |        |            |      |
#//|  +------+------------+              |  |        +------------+------+
#//|  |      |            |              V  V        |            |      |
#//|  +------+------------+            +------+      +------------+------+
#//|  |      |            |            | rsrc |      |            |      |
#//|  +------+------------+            +------+      +------------+------+
#//
#// The above diagrams illustrates how a resource whose name is A and
#// type is T is stored in the pool.  The pool contains an entry in the
#// type map for type T and an entry in the name map for name A.  The
#// queues in each of the arrays each contain an entry for the resource A
#// whose type is T.  The name map can contain in its queue other
#// resources whose name is A which may or may not have the same type as
#// our resource A.  Similarly, the type map can contain in its queue
#// other resources whose type is T and whose name may or may not be A.
#//
#// Resources are added to the pool by calling <set>; they are retrieved
#// from the pool by calling <get_by_name> or <get_by_type>.  When an object
#// creates a new resource and calls <set> the resource is made available to be
#// retrieved by other objects outside of itself; an object gets a
#// resource when it wants to access a resource not currently available
#// in its scope.
#//
#// The scope is stored in the resource itself (not in the pool) so
#// whether you get by name or by type the resource's visibility is
#// the same.
#//
#// As an auditing capability, the pool contains a history of gets.  A
#// record of each get, whether by <get_by_type> or <get_by_name>, is stored
#// in the audit record.  Both successful and failed gets are recorded. At
#// the end of simulation, or any time for that matter, you can dump the
#// history list.  This will tell which resources were successfully
#// located and which were not.  You can use this information
#// to determine if there is some error in name, type, or
#// scope that has caused a resource to not be located or to be incorrectly
#// located (i.e. the wrong resource is located).
#//
#//----------------------------------------------------------------------
class UVMResourcePool:

    rp = None

    def __init__(self):
        self.rtab = UVMPool()
        self.ttab = {}
        self.get_record = []  # History of gets

    @classmethod
    def get(cls):
        if UVMResourcePool.rp is None:
            UVMResourcePool.rp = UVMResourcePool()
        return UVMResourcePool.rp

    def spell_check(self, s):
        return UVMSpellChkr.check(self.rtab, s)

    #-----------
    # Group: Set
    #-----------

    # Function: set
    #
    # Add a new resource to the resource pool.  The resource is inserted
    # into both the name map and type map so it can be located by
    # either.
    #
    # An object creates a resources and ~sets~ it into the resource pool.
    # Later, other objects that want to access the resource must ~get~ it
    # from the pool
    #
    # Overrides can be specified using this interface.  Either a name
    # override, a type override or both can be specified.  If an
    # override is specified then the resource is entered at the front of
    # the queue instead of at the back.  It is not recommended that users
    # specify the override parameter directly, rather they use the
    # <set_override>, <set_name_override>, or <set_type_override>
    # functions.
    #
    def set(self, rsrc, override=False):
        rq = list()
        name = ""
        type_handle = None
        # If resource handle is ~None~ then there is nothing to do.
        if rsrc is None:
            return
        # insert into the name map.  Resources with empty names are
        # anonymous resources and are not entered into the name map
        name = rsrc.get_name()
        if name != "":
            if name in self.rtab:
                rq = self.rtab[name]
            else:
                rq = list()

        # Insert the resource into the queue associated with its name.
        # If we are doing a name override then insert it in the front of
        # the queue, otherwise insert it in the back.
        if override & NAME_OVERRIDE:
            rq.insert(0, rsrc)
        else:
            rq.append(rsrc)

        self.rtab[name] = rq

        # insert into the type map
        type_handle = rsrc.get_type_handle()
        if type_handle in self.ttab:
            rq = self.ttab[type_handle]
        else:
            rq = list()

        # insert the resource into the queue associated with its type.  If
        # we are doing a type override then insert it in the front of the
        # queue, otherwise insert it in the back of the queue.
        if override & TYPE_OVERRIDE:
            rq.insert(0, rsrc)
        else:
            rq.append(rsrc)
        self.ttab[type_handle] = rq


    #--------------
    # Group: Lookup
    #--------------
    #
    # This group of functions is for finding resources in the resource database.
    #
    # <lookup_name> and <lookup_type> locate the set of resources that
    # matches the name or type (respectively) and is visible in the
    # current scope.  These functions return a queue of resources.
    #
    # <get_highest_precedence> traverse a queue of resources and
    # returns the one with the highest precedence -- i.e. the one whose
    # precedence member has the highest value.
    #
    # <get_by_name> and <get_by_type> use <lookup_name> and <lookup_type>
    # (respectively) and <get_highest_precedence> to find the resource with
    # the highest priority that matches the other search criteria.


    # Function: lookup_name
    #
    # Lookup resources by ~name~.  Returns a queue of resources that
    # match the ~name~, ~scope~, and ~type_handle~.  If no resources
    # match the queue is returned empty. If ~rpterr~ is set then a
    # warning is issued if no matches are found, and the spell checker is
    # invoked on ~name~.  If ~type_handle~ is ~None~ then a type check is
    # not made and resources are returned that match only ~name~ and
    # ~scope~.

    def lookup_name(self, scope, name, type_handle=None, rpterr=True):
        rq = list()
        q = list()
        # rsrc = None
        r = None

        # ensure rand stability during lookup
        # process p = process::self()
        # string s
        # if(p!=None) s=p.get_randstate()
        # q=new()
        # if(p!=None) p.set_randstate(s)

        # resources with empty names are anonymous and do not exist in the name map
        if name == "":
            return q

        # Does an entry in the name map exist with the specified name?
        # If not, then we're done
        if not (name in self.rtab):
            if rpterr:
                self.spell_check(name)
            return q

        rq = self.rtab[name]
        for i in range(0, len(rq)):
            r = rq[i]
            # does the type and scope match?
            handle_ok = type_handle is None or (r.get_type_handle() == type_handle)
            if handle_ok and r.match_scope(scope):
                q.append(r)

        return q

    #// Function: get_highest_precedence
    #//
    #// Traverse a queue, ~q~, of resources and return the one with the highest
    #// precedence.  In the case where there exists more than one resource
    #// with the highest precedence value, the first one that has that
    #// precedence will be the one that is returned.
    #
    #function uvm_resource_base get_highest_precedence(ref uvm_resource_types::rsrc_q_t q)
    #
    #  uvm_resource_base rsrc
    #  uvm_resource_base r
    #  int unsigned i
    #  int unsigned prec
    #
    #  if(q.size() == 0)
    #    return None
    #
    #  // get the first resources in the queue
    #  rsrc = q.get(0)
    #  prec = rsrc.precedence
    #
    #  // start searching from the second resource
    #  for(int i = 1; i < q.size(); ++i) begin
    #    r = q.get(i)
    #    if(r.precedence > prec) begin
    #      rsrc = r
    #      prec = r.precedence
    #    end
    #  end
    #
    #  return rsrc
    #
    #endfunction

    #// Function: sort_by_precedence
    #//
    #// Given a list of resources, obtained for example from <lookup_scope>,
    #// sort the resources in  precedence order. The highest precedence
    #// resource will be first in the list and the lowest precedence will
    #// be last. Resources that have the same precedence and the same name
    #// will be ordered by most recently set first.
    #static function queue sort_by_precedence(ref uvm_resource_types::rsrc_q_t q)
    @classmethod
    def sort_by_precedence(cls, q):
        #  uvm_resource_types::rsrc_q_t all[int]
        _all = {}
        r = None  # uvm_resource_base

        for i in range(len(q)):
            r = q[i]
            if r.precedence not in _all:
                _all[r.precedence] = UVMQueue()
            _all[r.precedence].push_front(r)  # since we will push_front in the final
        qq = []
        for key in _all:
            for j in range(len(_all[key])):
                r = _all[key].get(j)
                #qq.push_front(r)
                qq.insert(0, r)
        return qq
        #endfunction

    #// Function: get_by_name
    #//
    #// Lookup a resource by ~name~, ~scope~, and ~type_handle~.  Whether
    #// the get succeeds or fails, save a record of the get attempt.  The
    #// ~rpterr~ flag indicates whether to report errors or not.
    #// Essentially, it serves as a verbose flag.  If set then the spell
    #// checker will be invoked and warnings about multiple resources will
    #// be produced.
    #
    #function uvm_resource_base get_by_name(string scope = "",
    #                                       string name,
    #                                       uvm_resource_base type_handle,
    #                                       bit rpterr = 1)
    def get_by_name(self, scope, name, type_handle, rpterr=True):
        q = []  # uvm_resource_types::rsrc_q_t q
        rsrc = None  # uvm_resource_base rsrc
        q = self.lookup_name(scope, name, type_handle, rpterr)
        #
        if(len(q) == 0):
            self.push_get_record(name, scope, None)
            return None

        rsrc = self.get_highest_precedence(q)
        self.push_get_record(name, scope, rsrc)
        return rsrc
        #endfunction

    #
    #// Function: lookup_type
    #//
    #// Lookup resources by type. Return a queue of resources that match
    #// the ~type_handle~ and ~scope~.  If no resources match then the returned
    #// queue is empty.
    #
    #function uvm_resource_types::rsrc_q_t lookup_type(string scope = "",
    #                                                  uvm_resource_base type_handle)
    #
    #  uvm_resource_types::rsrc_q_t q = new()
    #  uvm_resource_types::rsrc_q_t rq
    #  uvm_resource_base r
    #  int unsigned i
    #
    #  if(type_handle == None || !ttab.exists(type_handle)) begin
    #    return q
    #  end
    #
    #  rq = ttab[type_handle]
    #  for(int i = 0; i < rq.size(); ++i) begin 
    #    r = rq.get(i)
    #    if(r.match_scope(scope))
    #      q.push_back(r)
    #  end
    #
    #  return q
    #
    #endfunction
    #
    #// Function: get_by_type
    #//
    #// Lookup a resource by ~type_handle~ and ~scope~.  Insert a record into
    #// the get history list whether or not the get succeeded.
    #
    #function uvm_resource_base get_by_type(string scope = "",
    #                                       uvm_resource_base type_handle)
    #
    #  uvm_resource_types::rsrc_q_t q
    #  uvm_resource_base rsrc
    #
    #  q = lookup_type(scope, type_handle)
    #
    #  if(q.size() == 0) begin
    #    push_get_record("<type>", scope, None)
    #    return None
    #  end
    #
    #  rsrc = q.get(0)
    #  push_get_record("<type>", scope, rsrc)
    #  return rsrc
    #  
    #endfunction


    #// Function: lookup_regex_names
    #//
    #// This utility function answers the question, for a given ~name~,
    #// ~scope~, and ~type_handle~, what are all of the resources with requested name,
    #// a matching scope (where the resource scope may be a
    #// regular expression), and a matching type?
    #// ~name~ and ~scope~ are explicit values.
    #function uvm_resource_types::rsrc_q_t lookup_regex_names(string scope,
    #                                                         string name,
    #                                                         uvm_resource_base type_handle = None)
    def lookup_regex_names(self, scope, name, type_handle=None):
        return self.lookup_name(scope, name, type_handle, 0)

    #// Function: lookup_regex
    #//
    #// Looks for all the resources whose name matches the regular
    #// expression argument and whose scope matches the current scope.
    #
    #function uvm_resource_types::rsrc_q_t lookup_regex(string re, scope)
    #
    #  uvm_resource_types::rsrc_q_t rq
    #  uvm_resource_types::rsrc_q_t result_q
    #  int unsigned i
    #  uvm_resource_base r
    #
    #  re = uvm_glob_to_re(re)
    #  result_q = new()
    #
    #  foreach (rtab[name]) begin
    #    if(uvm_re_match(re, name))
    #      continue
    #    rq = rtab[name]
    #    for(i = 0; i < rq.size(); i++) begin
    #      r = rq.get(i)
    #      if(r.match_scope(scope))
    #        result_q.push_back(r)
    #    end
    #  end
    #
    #  return result_q
    #endfunction

    #// Function: lookup_scope
    #//
    #// This is a utility function that answers the question: For a given
    #// ~scope~, what resources are visible to it?  Locate all the resources
    #// that are visible to a particular scope.  This operation could be
    #// quite expensive, as it has to traverse all of the resources in the
    #// database.
    #function uvm_resource_types::rsrc_q_t lookup_scope(string scope)
    def lookup_scope(self, scope):
        rq = None  # uvm_resource_types::rsrc_q_t rq
        r = None  # uvm_resource_base r
        i = 0
        q = UVMQueue()  # uvm_resource_types::rsrc_q_t q = new()
        # iterate in reverse order for the special case of autoconfig
        # of arrays. The array name with no [] needs to be higher priority.
        # This has no effect an manual accesses.
        name = ""
        if self.rtab.has_last():
            name = self.rtab.last()
            while (True):
                rq = self.rtab[name]
                for i in range(len(rq)):
                    r = rq[i]
                    if r.match_scope(scope):
                        q.push_back(r)
                if self.rtab.has_prev():
                    name = self.rtab.prev()
                else:
                    break
        return q

    #// Function: print_resources
    #//
    #// Print the resources that are in a single queue, ~rq~.  This is a utility
    #// function that can be used to print any collection of resources
    #// stored in a queue.  The ~audit~ flag determines whether or not the
    #// audit trail is printed for each resource along with the name,
    #// value, and scope regular expression.
    #function void print_resources(uvm_resource_types::rsrc_q_t rq, bit audit = 0)
    def print_resources(self, rq, audit=False):
        i = 0
        r = None  # uvm_resource_base r
        pass
        UVMResourcePool.printer = UVMLinePrinter()
        printer = UVMResourcePool.printer
        printer.knobs.separator=""
        printer.knobs.full_name=0
        printer.knobs.identifier=0
        printer.knobs.type_name=0
        printer.knobs.reference=0

        if rq is None or len(rq) == 0:
            uvm_info("UVM/RESOURCE/PRINT","<none>",UVM_NONE)
            return

        for i in range(len(rq)):
            r = rq[i]
            r.print(printer)
            if audit is True:
                r.print_accessors()


import unittest


class TestUVMResource(unittest.TestCase):

    def test_scope_match(self):
        nname1 = "my_comp.field1"
        nname2 = "my_comp.*.field1"
        rr = UVMResource("fname", "my_comp.field1")
        self.assertEqual(True, rr.match_scope(nname1))
        self.assertEqual(False, rr.match_scope(nname2))


    def test_write_read(self):
        rsc = UVMResource("rname", "scope_name")
        rsc.write(123, accessor=None)
        val = rsc.read()
        self.assertEqual(val, 123)


class TestUVMResourcePool(unittest.TestCase):

    def test_get(self):
        pool = UVMResourcePool.get()

    def test_regex_lookup(self):
        # pool = UVMPool()
        field_name = "field"
        inst_re_name = "globbed_name.*"
        r = UVMResource(field_name, inst_re_name)
        r.write(666)
        # lookup = inst_re_name + "__M_UVM__" + field_name
        # pool.add(lookup, r)
        inst_name = "globbed_name.child"
        rp = UVMResourcePool.get()
        rp.set(r)
        rq = rp.lookup_regex_names(inst_name, field_name)
        self.assertEqual(len(rq), 1)

        # Add another resource and make sure we're not getting it
        r2 = UVMResource('field_xxx', 'inst_yyy')
        r2.write(444)
        rp.set(r2)
        rq = rp.lookup_regex_names(inst_name, field_name)
        self.assertEqual(len(rq), 1)

        nname1 = "my_comp.field1"
        nname2 = "my_comp.*.field1"
        rn1 = UVMResource(field_name, nname1)
        rn1.write(111)
        rn2 = UVMResource(field_name, nname2)
        rn2.write(222)
        rp.set(rn1)
        rp.set(rn2)
        rq = rp.lookup_regex_names("my_comp.field1", field_name)
        self.assertEqual(rq[0].read(), 111)


    def test_set_get(self):
        return
        rsrc = UVMResource("name_xxx", "scope_yyy")
        rsrc.write(567, accessor=None)
        pool = UVMResourcePool.get()
        pool.set(rsrc, False)
        rq = pool.lookup_name("scope_yyy", "name_xxx")
        self.assertEqual(len(rq), 1)
        self.assertEqual(rq[0].read(), 567)

if __name__ == '__main__':
    unittest.main()
