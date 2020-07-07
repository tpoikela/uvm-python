#//
#//-----------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2013 NVIDIA Corporation
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
#//-----------------------------------------------------------------------------

from ..dap import uvm_set_before_get_dap
from .uvm_object import UVMObject
from .uvm_object_globals import *
from .uvm_misc import uvm_bitstream_to_string, uvm_integral_to_string
from .sv import sv
from ..macros import uvm_object_utils, uvm_warning, uvm_error
from .uvm_scope_stack import UVMScopeStack
from .uvm_globals import uvm_string_to_bits


"""
File: UVM Recorders

The `UVMRecorder` class serves two purposes:
 - Firstly, it is an abstract representation of a record within a
   `UVMTrStream`.
 - Secondly, it is a policy object for recording fields ~into~ that
   record within the ~stream~.

"""



class UVMRecorder(UVMObject):
    """
    CLASS: UVMRecorder

    Abstract class which defines the ~recorder~ API.
    """

    #   // Variable- m_ids_by_recorder
    #   // A dict of integers, indexed by `UVMRecorder`s.  This
    #   // provides a unique 'id' or 'handle' for each recorder, which can be
    #   // used to identify the recorder.
    #   //
    #   // By default, neither ~m_ids_by_recorder~ or ~m_recorders_by_id~ are
    #   // used.  Recorders are only placed in the arrays when the user
    #   // attempts to determine the id for a recorder.
    #   local static integer m_ids_by_recorder[uvm_recorder]
    m_ids_by_recorder = {}

    def __init__(self, name="uvm_recorder"):
        UVMObject.__init__(self, name)
        #  // Variable- m_stream_dap
        #  // Data access protected reference to the stream
        #  uvm_set_before_get_dap#(uvm_tr_stream) m_stream_dap
        self.m_stream_dap = uvm_set_before_get_dap("stream_dap")
        #  // Variable- m_warn_null_stream
        #  // Used to limit the number of warnings
        self.m_warn_null_stream = True
        #
        #  // Variable- m_is_opened
        #  // Used to indicate recorder is open
        self.m_is_opened = False
        #
        #  // Variable- m_is_closed
        #  // Used to indicate recorder is closed
        self.m_is_closed = False
        #
        #  // !m_is_opened && !m_is_closed == m_is_freed
        #
        #  // Variable- m_open_time
        #  // Used to store the open_time
        self.m_open_time = 0
        #
        #  // Variable- m_close_time
        #  // Used to store the close_time
        self.m_close_time = 0
        #
        #  // Variable- recording_depth
        self.recording_depth = 0
        #
        #  // Variable: default_radix
        #  //
        #  // This is the default radix setting if <record_field> is called without
        #  // a radix.
        #
        self.default_radix = UVM_HEX

        #
        #  // Variable: physical
        #  //
        #  // This bit provides a filtering mechanism for fields.
        #  //
        #  // The <abstract> and physical settings allow an object to distinguish between
        #  // two different classes of fields.
        #  //
        #  // It is up to you, in the <uvm_object::do_record> method, to test the
        #  // setting of this field if you want to use the physical trait as a filter.
        #
        self.physical = True
        #
        #
        #  // Variable: abstract
        #  //
        #  // This bit provides a filtering mechanism for fields.
        #  //
        #  // The abstract and physical settings allow an object to distinguish between
        #  // two different classes of fields.
        #  //
        #  // It is up to you, in the <uvm_object::do_record> method, to test the
        #  // setting of this field if you want to use the abstract trait as a filter.
        #
        self.abstract = True
        #
        #
        #  // Variable: identifier
        #  //
        #  // This bit is used to specify whether or not an object's reference should be
        #  // recorded when the object is recorded.
        #
        self.identifier = 1
        #
        #
        #  // Variable: recursion_policy
        #  //
        #  // Sets the recursion policy for recording objects.
        #  //
        #  // The default policy is deep (which means to recurse an object).
        ##  uvm_recursion_policy_enum
        self.policy = UVM_DEFAULT_POLICY
        #

    def get_stream(self):
        """
        Group: Configuration API

        Function: get_stream
        Returns a reference to the stream which created
        this record.

        A warning will be asserted if get_stream is called prior
        to the record being initialized via `do_open`.

        Returns:
        """
        astr = []
        if not self.m_stream_dap.try_get(astr):
            if self.m_warn_null_stream == 1:
               uvm_warning("UVM/REC/NO_CFG",
                   sv.sformatf("attempt to retrieve STREAM from '%s' before it was set!",
                       self.get_name()))
            self.m_warn_null_stream = 0
        if len(astr):
            return astr[0]


    #   // Group: Transaction Recorder API
    #   //
    #   // Once a recorder has been opened via <uvm_tr_stream::open_recorder>, the user
    #   // can ~close~ the recorder.
    #   //
    #   // Due to the fact that many database implementations will require crossing
    #   // a language boundary, an additional step of ~freeing~ the recorder is required.
    #   //
    #   // A ~link~ can be established within the database any time between ~open~ and
    #   // ~free~, however it is illegal to establish a link after ~freeing~ the recorder.
    #   //


    def close(self, close_time=0):
        """
           Function: close
           Closes this recorder.

           Closing a recorder marks the end of the transaction in the stream.

           Parameters:
           close_time - Optional time to record as the closing time of this transaction.

           This method will trigger a `do_close` call.
        Args:
            close_time:
        """
        if (close_time == 0):
            close_time = sv.realtime()

        if self.is_open() is False:
            return

        self.do_close(close_time)

        self.m_is_opened = 0
        self.m_is_closed = 1
        self.m_close_time = close_time


    def free(self, close_time=0):
        """
        Function: free
        Frees this recorder

        Freeing a recorder indicates that the stream and database can release
        any references to the recorder.

        If a recorder has not yet been closed (via a call to `close`), then
        `close` will automatically be called, and passed the `close_time`.  If the recorder
        has already been closed, then the `close_time` will be ignored.

        This method will trigger a `do_free` call.

        Args:
            close_time (int): Optional time to record as the closing time of this transaction.
        """
        # process p=process::self()
        p = None
        s = ""
        stream = None  # uvm_tr_stream

        if not self.is_open() and not self.is_closed():
            return

        if self.is_open():
            self.close(close_time)

        self.do_free()

        # Clear out internal state
        stream = self.get_stream()

        self.m_is_closed = 0
        if p is not None:
            s = p.get_randstate()
        self.m_stream_dap = uvm_set_before_get_dap("stream_dap")
        if p is not None:
            p.set_randstate(s)
        self.m_warn_null_stream = 1
        if self in UVMRecorder.m_ids_by_recorder:
            UVMRecorder.m_free_id(UVMRecorder.m_ids_by_recorder[self])

        # Clear out stream state
        if stream is not None:
            stream.m_free_recorder(self)

    def is_open(self):
        """
           Function: is_open
           Returns true if this `uvm_recorder` was opened on its stream,
           but has not yet been closed.

        Returns:
        """
        return self.m_is_opened


    def get_open_time(self):
        """

           Function: get_open_time
           Returns the `open_time`

        Returns:
        """
        return self.m_open_time


    def is_closed(self):
        """
           Function: is_closed
           Returns true if this `uvm_recorder` was closed on its stream,
           but has not yet been freed.

        Returns:
        """
        return self.m_is_closed


    def get_close_time(self):
        """
           Function: get_close_time
           Returns the `close_time`

        Returns:
        """
        return self.m_close_time

    def m_do_open(self, stream, open_time, type_name):
        """
          Function- m_do_open
          Initializes the internal state of the recorder.

          Parameters:
          stream - The stream which spawned this recorder

          This method will trigger a `do_open` call.

          An error will be asserted if:
          - `m_do_open` is called more than once without the
           recorder being `freed` in between.
          - `stream` is `null`
        Args:
            stream:
            open_time:
            type_name:
        """
        m_stream = []
        if stream is None:
            uvm_error("UVM/REC/NULL_STREAM",
               sv.sformatf("Illegal attempt to set STREAM for '%s' to '<null>'",
                 self.get_name()))
            return

        if self.m_stream_dap.try_get(m_stream):
            uvm_error("UVM/REC/RE_INIT",
                sv.sformatf("Illegal attempt to re-initialize '%s'",
                self.get_name()))
            return

        self.m_stream_dap.set(stream)
        self.m_open_time = open_time
        self.m_is_opened = 1

        self.do_open(stream, open_time, type_name)


    #   // Group: Handles

    #   // Variable- m_recorders_by_id
    #   // A corollary to ~m_ids_by_recorder~, this indexes the recorders by their
    #   // unique ids.
    #   local static uvm_recorder m_recorders_by_id[integer]
    m_recorders_by_id = {}


    #   // Variable- m_id
    #   // Static int marking the last assigned id.
    #   local static integer m_id


    @classmethod
    def m_free_id(cls, id):
        """
           Function- m_free_id
           Frees the id/recorder link (memory cleanup)
        Args:
            cls:
            id:
        """
        recorder = None  # uvm_recorder
        if ((not sv.isunknown(id)) and (id in cls.m_recorders_by_id)):
            recorder = cls.m_recorders_by_id[id]

        if recorder is not None:
            del cls.m_recorders_by_id[id]
            del cls.m_ids_by_recorder[recorder]

    def get_handle(self):
        """
           Function: get_handle
           Returns a unique ID for this recorder.

           A value of `0` indicates that the recorder has been `freed`,
           and no longer has a valid ID.

        Returns:
        """
        if (self.is_open() is False and self.is_closed() is False):
            return 0
        else:
            handle = self.get_inst_id()

            m_ids_by_rec = UVMRecorder.m_ids_by_recorder
            # Check for the weird case where our handle changed.
            if self in m_ids_by_rec and m_ids_by_rec[self] != handle:
                this_id = UVMRecorder.m_ids_by_recorder[self]
                del UVMRecorder.m_recorders_by_id[this_id]

            UVMRecorder.m_recorders_by_id[handle] = self
            UVMRecorder.m_ids_by_recorder[self] = handle
            return handle
        #   endfunction : get_handle


    @classmethod
    def get_recorder_from_handle(cls, id):
        """
        Static accessor, returns a recorder reference for a given unique id.

        If no recorder exists with the given `id`, or if the
        recorder with that `id` has been freed, then `null` is
        returned.

        This method can be used to access the recorder associated with a
        call to `UVMTransaction.begin_tr` or `UVMComponent.begin_tr`.

        .. code-block:: python

           handle = tr.begin_tr()
           recorder = UVMRecorder.get_recorder_from_handle(handle)
           if recorder is not None:
               recorder.record_string("begin_msg", "Started recording transaction!")

        Args:
            cls:
            id:
        Returns:
            UVMRecorder:
        """
        if id == 0:
            return None
        if sv.isunknown(id) or id not in cls.m_recorders_by_id:
            return None
        return cls.m_recorders_by_id[id]


    #   // Group: Attribute Recording
    #
    #   // Function: record_field
    #   // Records an integral field (less than or equal to 4096 bits).
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Value of the field to record.
    #   // size - Number of bits of the field which apply (Usually obtained via $bits).
    #   // radix - The <uvm_radix_enum> to use.
    #   //
    #   // This method will trigger a <do_record_field> call.
    def record_field(self, name, value, size, radix=UVM_NORADIX):
        if self.get_stream() is None:
            return
        self.do_record_field(name, value, size, radix)


    #   // Function: record_field_int
    #   // Records an integral field (less than or equal to 64 bits).
    #   //
    #   // This optimized version of <record_field> is useful for sizes up
    #   // to 64 bits.
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Value of the field to record
    #   // size - Number of bits of the wfield which apply (Usually obtained via $bits).
    #   // radix - The <uvm_radix_enum> to use.
    #   //
    #   // This method will trigger a <do_record_field_int> call.
    def record_field_int(self,name, value, size, radix=UVM_NORADIX):
        if self.get_stream() is None:
            return
        self.do_record_field_int(name, value, size, radix)


    #   // Function: record_field_real
    #   // Records a real field.
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Value of the field to record
    #   //
    #   // This method will trigger a <do_record_field_real> call.
    #   function void record_field_real(string name,
    #                                   real value)
    #      if (get_stream() is None):
    #         return
    #      end
    #      do_record_field_real(name, value)
    #   endfunction : record_field_real


    #   // Function: record_object
    #   // Records an object field.
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Object to record
    #   //
    #   // The implementation must use the <recursion_policy> and <identifier> to
    #   // determine exactly what should be recorded.
    def record_object(self, name, value):
        if (self.get_stream() is None):
            return
        self.do_record_object(name, value)


    #   // Function: record_string
    #   // Records a string field.
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Value of the field
    #   //
    def record_string(self, name, value):
        if (self.get_stream() is None):
            return
        self.do_record_string(name, value)


    #   // Function: record_time
    #   // Records a time field.
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Value of the field
    #   //
    #   function void record_time(string name,
    #                             time value)
    #      if (get_stream() is None):
    #         return
    #      end
    #
    #      do_record_time(name, value)
    #   endfunction : record_time
    #
    #   // Function: record_generic
    #   // Records a name/value pair, where ~value~ has been converted to a string.
    #   //
    #   // For example:
    #   //| recorder.record_generic("myvar","var_type", sv.sformatf("%0d",myvar), 32)
    #   //
    #   // Parameters:
    #   // name - Name of the field
    #   // value - Value of the field
    #   // type_name - ~optional~ Type name of the field
    #   function void record_generic(string name,
    #                                string value,
    #                                string type_name="")
    #      if (get_stream() is None):
    #         return
    #      end
    #
    #      do_record_generic(name, value, type_name)
    #   endfunction : record_generic


    #  // Function: use_record_attribute
    #  //
    #  // Indicates that this recorder does (or does not) support usage of
    #  // the <`uvm_record_attribute> macro.
    #  //
    #  // The default return value is ~0~ (not supported), developers can
    #  // optionally extend ~uvm_recorder~ and set the value to ~1~ if they
    #  // support the <`uvm_record_attribute> macro.
    def use_record_attribute(self):
        return 0


    #   // Function: get_record_attribute_handle
    #   // Provides a tool-specific handle which is compatible with <`uvm_record_attribute>.
    #   //
    #   // By default, this method will return the same value as <get_handle>,
    #   // however tool vendors can override this method to provide tool-specific handles
    #   // which will be passed to the <`uvm_record_attribute> macro.
    #   //
    #   virtual function integer get_record_attribute_handle()
    #      return get_handle()
    #   endfunction : get_record_attribute_handle
    #
    #   // Group: Implementation Agnostic API
    #

    def do_open(self, stream, open_time, type_name):
        """
           Function: do_open
           Callback triggered via <uvm_tr_stream::open_recorder>.

           The `do_open` callback can be used to initialize any internal
           state within the recorder, as well as providing a location to
           record any initial information.
        Args:
            stream:
            open_time:
            type_name:
        """
        pass

    #
    #   // Function: do_close
    #   // Callback triggered via <close>.
    #   //
    #   // The ~do_close~ callback can be used to set internal state
    #   // within the recorder, as well as providing a location to
    #   // record any closing information.
    def do_close(self, close_time):
        pass

    #   // Function: do_free
    #   // Callback triggered via <free>.
    #   //
    #   // The ~do_free~ callback can be used to release the internal
    #   // state within the recorder, as well as providing a location
    #   // to record any "freeing" information.
    def do_free(self):
        pass


    #   // Function: do_record_field
    #   // Records an integral field (less than or equal to 4096 bits).
    #   //
    #   // ~Mandatory~ Backend implementation of <record_field>
    #   pure virtual protected function void do_record_field(string name,
    #                                                        uvm_bitstream_t value,
    #                                                        int size,
    #                                                        uvm_radix_enum radix)


    #   // Function: do_record_field_int
    #   // Records an integral field (less than or equal to 64 bits).
    #   //
    #   // ~Mandatory~ Backend implementation of <record_field_int>
    #   pure virtual protected function void do_record_field_int(string name,
    #                                                            uvm_integral_t value,
    #                                                            int          size,
    #                                                            uvm_radix_enum radix)
    #
    #   // Function: do_record_field_real
    #   // Records a real field.
    #   //
    #   // ~Mandatory~ Backend implementation of <record_field_real>
    #   pure virtual protected function void do_record_field_real(string name,
    #                                                             real value)
    #
    #   // Function: do_record_object
    #   // Records an object field.
    #   //
    #   // ~Mandatory~ Backend implementation of <record_object>
    #   pure virtual protected function void do_record_object(string name,
    #                                                         uvm_object value)
    #
    #   // Function: do_record_string
    #   // Records a string field.
    #   //
    #   // ~Mandatory~ Backend implementation of <record_string>
    #   pure virtual protected function void do_record_string(string name,
    #                                                         string value)
    #
    #   // Function: do_record_time
    #   // Records a time field.
    #   //
    #   // ~Mandatory~ Backend implementation of <record_time>
    #   pure virtual protected function void do_record_time(string name,
    #                                                       time value)
    #
    #   // Function: do_record_generic
    #   // Records a name/value pair, where ~value~ has been converted to a string.
    #   //
    #   // ~Mandatory~ Backend implementation of <record_generic>
    #   pure virtual protected function void do_record_generic(string name,
    #                                                          string value,
    #                                                          string type_name)
    #
    #
    #   // The following code is primarily for backwards compat. purposes.  "Transaction
    #   // Handles" are useful when connecting to a backend, but when passing the information
    #   // back and forth within simulation, it is safer to user the ~recorder~ itself
    #   // as a reference to the transaction within the database.
    #
    #   //------------------------------
    #   // Group- Vendor-Independent API
    #   //------------------------------
    #
    #
    #  // UVM provides only a text-based default implementation.
    #  // Vendors provide subtype implementations and overwrite the
    #  // <uvm_default_recorder> handle.
    #
    #
    #  // Function- open_file
    #  //
    #  // Opens the file in the <filename> property and assigns to the
    #  // file descriptor <file>.
    #  //
    #  virtual function bit open_file()
    #     return 0
    #  endfunction
    #
    #  // Function- create_stream
    #  //
    #  //
    #  virtual function integer create_stream (string name,
    #                                          string t,
    #                                          string scope)
    #     return -1
    #  endfunction
    #
    #
    #  // Function- m_set_attribute
    #  //
    #  //
    #  virtual function void m_set_attribute (integer txh,
    #                                 string nm,
    #                                 string value)
    #  endfunction
    #
    #
    #  // Function- set_attribute
    #  //
    #  virtual function void set_attribute (integer txh,
    #                               string nm,
    #                               logic [1023:0] value,
    #                               uvm_radix_enum radix,
    #                               integer numbits=1024)
    #  endfunction
    #
    #
    #  // Function- check_handle_kind
    #  //
    #  //
    #  virtual function integer check_handle_kind (string htype, integer handle)
    #     return 0
    #  endfunction
    #
    #
    #  // Function- begin_tr
    #  //
    #  //
    #  virtual function integer begin_tr(string txtype,
    #                                     integer stream,
    #                                     string nm,
    #                                     string label="",
    #                                     string desc="",
    #                                     time begin_time=0)
    #    return -1
    #  endfunction
    #
    #
    #  // Function- end_tr
    #  //
    #  //
    #  virtual function void end_tr (integer handle, time end_time=0)
    #  endfunction
    #
    #
    #  // Function- link_tr
    #  //
    #  //
    #  virtual function void link_tr(integer h1,
    #                                 integer h2,
    #                                 string relation="")
    #  endfunction
    #
    #
    #
    #  // Function- free_tr
    #  //
    #  //
    #  virtual function void free_tr(integer handle)
    #  endfunction
    #
    #endclass // uvm_recorder
#
#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_text_recorder
#//
#// The ~uvm_text_recorder~ is the default recorder implementation for the
#// <uvm_text_tr_database>.
#//

class UVMTextRecorder(UVMRecorder):

    def __init__(self, name="unnamed-uvm_text_recorder"):
        """
           Function: new
           Constructor

           Parameters:
           name - Instance name
        Args:
            name:
        """
        super().__init__(name)
        # Variable- m_text_db
        # Reference to the text database backend
        self.m_text_db = None  # #   uvm_text_tr_database

        # Variable- scope
        # Imeplementation detail
        self.scope = UVMScopeStack()


    def do_open(self, stream, open_time, type_name):
        """
           Group: Implementation Agnostic API

           Function: do_open
           Callback triggered via <uvm_tr_stream::open_recorder>.

           Text-backend specific implementation.
        Args:
            stream:
            open_time:
            type_name:
        """
        self. m_text_db = stream.get_db()
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                "    OPEN_RECORDER @%0t {{TXH:%0d STREAM:%0d NAME:%s TIME:%0t TYPE=\"%0s\"}}",
                sv.realtime(), self.get_handle(), stream.get_handle(),
                self.get_name(), open_time, type_name)


    def do_close(self, close_time):
        """
           Function: do_close
           Callback triggered via <uvm_recorder::close>.

           Text-backend specific implementation.
        Args:
            close_time:
        """
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                 "    CLOSE_RECORDER @%0t {{TXH:%0d TIME=%0t}}",
                 sv.realtime(),
                 self.get_handle(),
                 close_time)

    def do_free(self):
        """
        Function: do_free
        Callback triggered via <uvm_recorder::free>.

        Text-backend specific implementation.
        """
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                "    FREE_RECORDER @%0t {{TXH:%0d}}",
                sv.realtime(), self.get_handle())

        self.m_text_db = None


    #   // Function: do_record_field
    #   // Records an integral field (less than or equal to 4096 bits).
    #   //
    #   // Text-backend specific implementation.
    #   protected virtual function void do_record_field(string name,
    #                                                   uvm_bitstream_t value,
    #                                                   int size,
    #                                                   uvm_radix_enum radix)
    def do_record_field(self, name, value, size, radix):
        self.scope.set_arg(name)
        if not radix:
            radix = self.default_radix
        self.write_attribute(self.scope.get(), value, radix, size)


    #   // Function: do_record_field_int
    #   // Records an integral field (less than or equal to 64 bits).
    #   //
    #   // Text-backend specific implementation.
    def do_record_field_int(self, name, value, size, radix):
        self.scope.set_arg(name)
        if not radix:
            radix = self.default_radix
        self.write_attribute_int(self.scope.get(), value, radix, size)


    #   // Function: do_record_field_real
    #   // Record a real field.
    #   //
    #   // Text-backened specific implementation.
    #   protected virtual function void do_record_field_real(string name,
    #                                                        real value)
    #      bit [63:0] ival = $realtobits(value)
    #      scope.set_arg(name)
    #
    #      write_attribute_int(scope.get(),
    #                          ival,
    #                          UVM_REAL,
    #                          64)
    #   endfunction : do_record_field_real
    #


    #   // Function: do_record_object
    #   // Record an object field.
    #   //
    #   // Text-backend specific implementation.
    #   //
    #   // The method uses ~identifier~ to determine whether or not to
    #   // record the object instance id, and ~recursion_policy~ to
    #   // determine whether or not to recurse into the object.
    def do_record_object(self, name, value):
        v = 0
        _str = ""

        if self.identifier:
            if value is not None:
                _str = str(value.get_inst_id())
                v = int(_str)
            self.scope.set_arg(name)
            self.write_attribute_int(self.scope.get(), v, UVM_DEC, 32)

        if self.policy != UVM_REFERENCE:
            if value is not None:
                if value in value._m_uvm_status_container.cycle_check:
                    return
                value._m_uvm_status_container.cycle_check[value] = 1
                self.scope.down(name)
                value.record(self)
                self.scope.up()
                del value._m_uvm_status_container.cycle_check[value]


    #   // Function: do_record_string
    #   // Records a string field.
    #   //
    #   // Text-backend specific implementation.
    def do_record_string(self, name, value):
        self.scope.set_arg(name)
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                "      SET_ATTR @%0t {{TXH:%0d NAME:%s VALUE:%s   RADIX:%s BITS=%0d}}",
                sv.realtime(), self.get_handle(), self.scope.get(),
                value, "UVM_STRING", 8 + len(value))


    #   // Function: do_record_time
    #   // Records a time field.
    #   //
    #   // Text-backend specific implementation.
    def do_record_time(self, name,value):
        self.scope.set_arg(name)
        self.write_attribute_int(self.scope.get(), value, UVM_TIME, 64)


    #   // Function: do_record_generic
    #   // Records a name/value pair, where ~value~ has been converted to a string.
    #   //
    #   // Text-backend specific implementation.
    def do_record_generic(self, name, value, type_name):
        self.scope.set_arg(name)
        self.write_attribute(self.scope.get(), uvm_string_to_bits(value), UVM_STRING,
            8+len(value))


    #   // Group: Implementation Specific API


    #   // Function: write_attribute
    #   // Outputs an integral attribute to the textual log
    #   //
    #   // Parameters:
    #   // nm - Name of the attribute
    #   // value - Value
    #   // radix - Radix of the output
    #   // numbits - number of valid bits
    #   function void write_attribute(string nm,
    #                                 uvm_bitstream_t value,
    #                                 uvm_radix_enum radix,
    #                                 integer numbits=$bits(uvm_bitstream_t))
    def write_attribute(self, nm, value, radix, numbits=32):
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                "      SET_ATTR @%0t {{TXH:%0d NAME:%s VALUE:%s   RADIX:%s BITS=%0d}}",
                 sv.realtime(),
                 self.get_handle(),
                 nm,
                 uvm_bitstream_to_string(value, numbits, radix),
                 UVM_RADIX_TO_STRING_DICT[radix],
                 numbits)


    #   // Function: write_attribute_int
    #   // Outputs an integral attribute to the textual log
    #   //
    #   // Parameters:
    #   // nm - Name of the attribute
    #   // value - Value
    #   // radix - Radix of the output
    #   // numbits - number of valid bits
    def write_attribute_int(self, nm, value, radix, numbits=32):
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                "      SET_ATTR @%0t {{TXH:%0d NAME:%s VALUE:%s   RADIX:%s BITS=%0d}}",
                sv.realtime(), self.get_handle(), nm,
                uvm_integral_to_string(value, numbits, radix),
                UVM_RADIX_TO_STRING_DICT[radix], numbits)


    #  // UVM provides only a text-based default implementation.
    #  // Vendors provide subtype implementations and overwrite the
    #  // <uvm_default_recorder> handle.
    #
    #   string                                                   filename
    #   bit                                                      filename_set
    #
    #  // Function- open_file
    #  //
    #  // Opens the file in the <filename> property and assigns to the
    #  // file descriptor <file>.
    #  //
    #  virtual function bit open_file()
    #     if (!filename_set):
    #        m_text_db.set_file_name(filename)
    #     end
    #     return m_text_db.open_db()
    #  endfunction


    #  // Function- create_stream
    #  //
    #  //
    #  virtual function integer create_stream (string name,
    #                                          string t,
    #                                          string scope)
    #     uvm_text_tr_stream stream
    #     if (open_file()):
    #        $cast(stream,m_text_db.open_stream(name, scope, t))
    #        return stream.get_handle()
    #     end
    #     return 0
    #  endfunction


    #  // Function- m_set_attribute
    #  //
    #  //
    #  virtual function void m_set_attribute (integer txh,
    #                                 string nm,
    #                                 string value)
    #     if (open_file()):
    #        UVM_FILE file = m_text_db.m_file
    #        $fdisplay(file,"      SET_ATTR @%0t {TXH:%0d NAME:%s VALUE:%s}", $realtime,txh,nm,value)
    #     end
    #  endfunction

    #
    #
    #  // Function- set_attribute
    #  //
    #  //
    #  virtual function void set_attribute (integer txh,
    #                               string nm,
    #                               logic [1023:0] value,
    #                               uvm_radix_enum radix,
    #                               integer numbits=1024)
    #     if (open_file()):
    #        UVM_FILE file = m_text_db.m_file
    #         $fdisplay(file,
    #                   "      SET_ATTR @%0t {TXH:%0d NAME:%s VALUE:%s   RADIX:%s BITS=%0d}",
    #                   $realtime,
    #                   txh,
    #                   nm,
    #                   uvm_bitstream_to_string(value, numbits, radix),
    #                   radix.name(),
    #                   numbits)
    #
    #     end
    #  endfunction

    #
    #
    #  // Function- check_handle_kind
    #  //
    #  //
    #  virtual function integer check_handle_kind (string htype, integer handle)
    #     return ((uvm_recorder::get_recorder_from_handle(handle) != null) ||
    #             (uvm_tr_stream::get_stream_from_handle(handle) != null))
    #  endfunction


    #  // Function- begin_tr
    #  //
    #  //
    #  virtual function integer begin_tr(string txtype,
    #                                     integer stream,
    #                                     string nm,
    #                                     string label="",
    #                                     string desc="",
    #                                     time begin_time=0)
    #     if (open_file()):
    #        uvm_tr_stream stream_obj = uvm_tr_stream::get_stream_from_handle(stream)
    #        uvm_recorder recorder
    #
    #        if (stream_obj is None)
    #          return -1
    #
    #        recorder = stream_obj.open_recorder(nm, begin_time, txtype)
    #
    #        return recorder.get_handle()
    #     end
    #     return -1
    #  endfunction

    #
    #
    #  // Function- end_tr
    #  //
    #  //
    #  virtual function void end_tr (integer handle, time end_time=0)
    #     if (open_file()):
    #        uvm_recorder record = uvm_recorder::get_recorder_from_handle(handle)
    #        if (record != null):
    #           record.close(end_time)
    #        end
    #     end
    #  endfunction

    #
    #
    #  // Function- link_tr
    #  //
    #  //
    #  virtual function void link_tr(integer h1,
    #                                 integer h2,
    #                                 string relation="")
    #    if (open_file())
    #      $fdisplay(self.m_text_db.m_file,"  LINK @%0t {TXH1:%0d TXH2:%0d RELATION=%0s}", $realtime,h1,
    #          h2,relation)
    #  endfunction


    #  // Function- free_tr
    #  //
    #  //
    #  virtual function void free_tr(integer handle)
    #     if (open_file()):
    #        uvm_recorder record = uvm_recorder::get_recorder_from_handle(handle)
    #        if (record != null):
    #           record.free()
    #        end
    #     end
    #  endfunction // free_tr


uvm_object_utils(UVMTextRecorder)
