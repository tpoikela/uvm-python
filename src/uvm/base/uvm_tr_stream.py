#//
#//-----------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2013 NVIDIA Corporation
#//   Copyright 2019-2020 Tuomas Poikela
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


from .sv import sv
from ..dap.uvm_set_before_get_dap import uvm_set_before_get_dap
from .uvm_object import UVMObject
from ..macros.uvm_object_defines import uvm_object_utils
from ..macros.uvm_message_defines import uvm_error, uvm_warning
from .uvm_globals import uvm_sim_time

from .uvm_recorder import UVMTextRecorder

#//------------------------------------------------------------------------------
#// File: Transaction Recording Streams
#//
#
#// class- m_uvm_tr_stream_cfg
#// Undocumented helper class for storing stream
#// initialization values.

class m_uvm_tr_stream_cfg():
    def __init__(self):
        self.db = None  # uvm_tr_database db
        self.scope = ""
        self.stream_type_name = ""
#endclass : m_uvm_tr_stream_cfg

#
#typedef class uvm_set_before_get_dap
#typedef class uvm_text_recorder

#//------------------------------------------------------------------------------
#//
#// CLASS: UVMTrStream
#//
#// The ~UVMTrStream~ base class is a representation of a stream of records
#// within a <uvm_tr_database>.
#//
#// The record stream is intended to hide the underlying database implementation
#// from the end user, as these details are often vendor or tool-specific.
#//
#// The ~UVMTrStream~ class is pure virtual, and must be extended with an
#// implementation.  A default text-based implementation is provided via the
#// <UVMTextTrStream> class.
#//
#virtual class UVMTrStream extends uvm_object

class UVMTrStream(UVMObject):
    #
    #   // Variable- m_cfg_dap
    #   // Data access protected reference to the DB
    #   local uvm_set_before_get_dap#(m_uvm_tr_stream_cfg) m_cfg_dap
    #
    #
    #   // Variable- m_warn_null_cfg
    #   // Used to limit the number of warnings
    #   local bit m_warn_null_cfg
    #
    #   // Variable- m_is_opened
    #   // Used to indicate stream is open
    #   local bit m_is_opened
    #
    #   // Variable- m_is_closed
    #   // Used to indicate stream is closed
    #   local bit m_is_closed
    #
    #   // !m_is_opened && !m_is_closed == m_is_freed
    #

    def __init__(self, name="unnamed-UVMTrStream"):
        """
           Function: new
           Constructor

           Parameters:
           name - Stream instance name
        Args:
            name:
        """
        UVMObject.__init__(self, name)
        self.m_cfg_dap = uvm_set_before_get_dap("cfg_dap")
        #   // Variable- m_records
        #   // Active records in the stream (active == open or closed)
        self.m_records = {}  # bit [uvm_recorder]
        self.m_warn_null_cfg = 0


    #   // Variable- m_ids_by_stream
    #   // An associative array of integers, indexed by uvm_tr_streams.  This
    #   // provides a unique 'id' or 'handle' for each stream, which can be
    #   // used to identify the stream.
    #   //
    #   // By default, neither ~m_ids_by_stream~ or ~m_streams_by_id~ are
    #   // used.  Streams are only placed in the arrays when the user
    #   // attempts to determine the id for a stream.
    #   local static integer m_ids_by_stream[UVMTrStream]
    m_ids_by_stream = {}

    def get_db(self):
        """

           Group: Configuration API

           Function: get_db
           Returns a reference to the database which contains this
           stream.

           A warning will be asserted if get_db is called prior to
           the stream being initialized via `do_open`.
        Returns:
        """
        m_cfg = []  # m_uvm_tr_stream_cfg m_cfg
        if not self.m_cfg_dap.try_get(m_cfg):
            if self.m_warn_null_cfg == 1:
                uvm_warning("UVM/REC_STR/NO_CFG",
                    sv.sformatf("attempt to retrieve DB from '%s' before it was set!",
                        self.get_name()))
            self.m_warn_null_cfg = 0
            return None
        return m_cfg[0].db


    #   // Function: get_scope
    #   // Returns the ~scope~ supplied when opening this stream.
    #   //
    #   // A warning will be asserted if get_scope is called prior to
    #   // the stream being initialized via <do_open>.
    #   function string get_scope()
    #      m_uvm_tr_stream_cfg m_cfg
    #      if (!m_cfg_dap.try_get(m_cfg)) begin
    #         if (m_warn_null_cfg == 1)
    #           `uvm_warning("UVM/REC_STR/NO_CFG",
    #                        $sformatf("attempt to retrieve scope from '%s' before it was set!",
    #                                  get_name()))
    #         m_warn_null_cfg = 0
    #         return ""
    #      end
    #      return m_cfg.scope
    #   endfunction : get_scope
    #
    #   // Function: get_stream_type_name
    #   // Returns a reference to the database which contains this
    #   // stream.
    #   //
    #   // A warning will be asserted if get_stream_type_name is called prior to
    #   // the stream being initialized via <do_open>.
    #   function string get_stream_type_name()
    #      m_uvm_tr_stream_cfg m_cfg
    #      if (!m_cfg_dap.try_get(m_cfg)) begin
    #         if (m_warn_null_cfg == 1)
    #           `uvm_warning("UVM/REC_STR/NO_CFG",
    #                        $sformatf("attempt to retrieve STREAM_TYPE_NAME from '%s' before it was set!",
    #                                  get_name()))
    #         m_warn_null_cfg = 0
    #         return ""
    #      end
    #      return m_cfg.stream_type_name
    #   endfunction : get_stream_type_name
    #
    #   // Group: Stream API
    #   //
    #   // Once a stream has been opened via <uvm_tr_database::open_stream>, the user
    #   // can ~close~ the stream.
    #   //
    #   // Due to the fact that many database implementations will require crossing
    #   // a language boundary, an additional step of ~freeing~ the stream is required.
    #   //
    #   // A ~link~ can be established within the database any time between "Open" and
    #   // "Free", however it is illegal to establish a link after "Freeing" the stream.
    #   //
    #

    #   // Function: close
    #   // Closes this stream.
    #   //
    #   // Closing a stream closes all open recorders in the stream.
    #   //
    #   // This method will trigger a <do_close> call, followed by
    #   // <uvm_recorder::close> on all open recorders within the
    #   // stream.
    #   function void close()
    #      if (!is_open())
    #        return
    #
    #      do_close()
    #
    #      foreach (m_records[idx])
    #        if (idx.is_open())
    #          idx.close()
    #
    #      m_is_opened = 0
    #      m_is_closed = 1
    #   endfunction : close
    #

    #   // Function: free
    #   // Frees this stream.
    #   //
    #   // Freeing a stream indicates that the database can free any
    #   // references to the stream (including references to records
    #   // within the stream).
    #   //
    #   // This method will trigger a <do_free> call, followed by
    #   // <uvm_recorder::free> on all recorders within the stream.
    #   function void free()
    #	   process p
    #	   string s
    #      uvm_tr_database db
    #      if (!is_open() && !is_closed())
    #        return
    #
    #      if (is_open())
    #        close()
    #
    #      do_free()
    #
    #      foreach (m_records[idx])
    #        idx.free()
    #
    #      // Clear out internal state
    #      db = get_db()
    #      m_is_closed = 0
    #      p = process::self()
    #      if(p != None)
    #      	s = p.get_randstate()
    #      m_cfg_dap = new("cfg_dap")
    #      if(p != None)
    #      	p.set_randstate(s)
    #      m_warn_null_cfg = 1
    #      if (m_ids_by_stream.exists(this))
    #        m_free_id(m_ids_by_stream[this])
    #
    #      // Clear out DB state
    #      if (db != None)
    #        db.m_free_stream(this)
    #   endfunction : free

    def m_do_open(self, db, scope="", stream_type_name=""):
        """
           Function- m_do_open
           Initializes the state of the stream

           Parameters-
           db - Database which the stream belongs to
           scope - Optional scope
           stream_type_name - Optional type name for the stream

           This method will trigger a `do_open` call.

           An error will be asserted if-
           - m_do_open is called more than once without the stream
             being `freed` between.
           - m_do_open is passed a `None` db
          function void m_do_open(uvm_tr_database db,
                                  string scope="",
                                  string stream_type_name="")
        Args:
            db:
            scope:
            stream_type_name:
        """
        m_cfg = []  # m_uvm_tr_stream_cfg
        m_db = None  # uvm_tr_database
        if db is None:
            uvm_error("UVM/REC_STR/NULL_DB",
                       sv.sformatf("Illegal attempt to set DB for '%s' to '<None>'",
                                 self.get_full_name()))
            return

        if self.m_cfg_dap.try_get(m_cfg):
            uvm_error("UVM/REC_STR/RE_CFG",
                       sv.sformatf("Illegal attempt to re-open '%s'",
                                 self.get_full_name()))
        else:
            # Never set before
            m_cfg = m_uvm_tr_stream_cfg()
            m_cfg.db = db
            m_cfg.scope = scope
            m_cfg.stream_type_name = stream_type_name
            self.m_cfg_dap.set(m_cfg)
            self.m_is_opened = True

            self.do_open(db, scope, stream_type_name)


    def is_open(self):
        """
        Function: is_open
        Returns true if this `UVMTrStream` was opened on the database,
        but has not yet been closed.

        Returns:
        """
        return self.m_is_opened

    def is_closed(self):
        """
           Function: is_closed
           Returns true if this `UVMTrStream` was closed on the database,
           but has not yet been freed.

        Returns:
        """
        return self.m_is_closed

    #   // Group: Transaction Recorder API
    #   //
    #   // New recorders can be opened prior to the stream being ~closed~.
    #   //
    #   // Once a stream has been closed, requests to open a new recorder
    #   // will be ignored (<open_recorder> will return ~None~).
    #   //
    #

    def open_recorder(self, name, open_time=0, type_name=""):
        """
           Function: open_recorder
           Marks the opening of a new transaction recorder on the stream.

           Parameters:
           name - A name for the new transaction
           open_time - Optional time to record as the opening of this transaction
           type_name - Optional type name for the transaction

           If `open_time` is omitted (or set to 0), then the stream will use
           the current time.

           This method will trigger a `do_open_recorder` call.  If `do_open_recorder`
           returns a non-`None` value, then the <uvm_recorder::do_open> method will
           be called in the recorder.

           Transaction recorders can only be opened if the stream is
           `open` on the database (per `is_open`).  Otherwise the
           request will be ignored, and `None` will be returned.
        Args:
            name:
            open_time:
            type_name:
        Returns:
        """
        m_time = open_time
        if open_time == 0:
            m_time = sv.time()

        # Check to make sure we're open
        if not self.is_open():
            return None
        else:
            #process p = process::self()
            p = None
            s = ""
            if p is not None:
                s = p.get_randstate()
            open_recorder = self.do_open_recorder(name, m_time, type_name)

            if open_recorder is not None:
                self.m_records[open_recorder] = 1
                open_recorder.m_do_open(self, m_time, type_name)

            if p is not None:
                p.set_randstate(s)
            return open_recorder
        #   endfunction : open_recorder


    def m_free_recorder(self, recorder):
        """
           Function- m_free_recorder
           Removes recorder from the internal array
        Args:
            recorder:
        """
        if recorder in self.m_records:
            del self.m_records[recorder]

    #
    #   // Function: get_recorders
    #   // Provides a queue of all transactions within the stream.
    #   //
    #   // Parameters:
    #   // q - A reference to the queue of <uvm_recorder>s
    #   //
    #   // The <get_recorders> method returns the size of the queue,
    #   // such that the user can conditionally process the elements.
    #   //
    #   // | uvm_recorder tr_q[$]
    #   // | if (my_stream.get_recorders(tr_q)) begin
    #   // |   // Process the queue...
    #   // | end
    #   //
    #   function unsigned get_recorders(ref uvm_recorder q[$])
    #      // Clear out the queue first...
    #      q.delete()
    #      // Fill in the values
    #      foreach (m_records[idx])
    #        q.push_back(idx)
    #      // Finally return the size of the queue
    #      return q.size()
    #   endfunction : get_recorders
    #

    #   // Group: Handles
    #
    #   // Variable- m_streams_by_id
    #   // A corollary to ~m_ids_by_stream~, this indexes the streams by their
    #   // unique ids.
    #   local static UVMTrStream m_streams_by_id[integer]
    m_streams_by_id = {}


    def get_handle(self):
        """
           Function: get_handle
           Returns a unique ID for this stream.

           A value of `0` indicates that the recorder has been `freed`,
           and no longer has a valid ID.

        Returns:
        """
        m_streams_by_id = UVMTrStream.m_streams_by_id
        m_ids_by_stream = UVMTrStream.m_ids_by_stream

        if self.is_open() is False and self.is_closed() is False:
            return 0
        else:
            handle = self.get_inst_id()

            # Check for the weird case where our handle changed.
            if self in m_ids_by_stream and m_ids_by_stream[self] != handle:
                key = m_ids_by_stream[self]
                del m_streams_by_id[key]

            m_streams_by_id[handle] = self
            m_ids_by_stream[self] = handle

            return handle
    #   endfunction : get_handle

    #
    #   // Function- m_get_handle
    #   // Provided to allow implementation-specific handles which are not
    #   // identical to the built-in handles.
    #   //
    #   // This is an implementation detail of the UVM library, which allows
    #   // for vendors to (optionally) put vendor-specific methods into the library.
    #   virtual function integer m_get_handle()
    #      return get_handle()
    #   endfunction : m_get_handle
    #

    #   // Function: get_stream_from_handle
    #   // Static accessor, returns a stream reference for a given unique id.
    #   //
    #   // If no stream exists with the given ~id~, or if the
    #   // stream with that ~id~ has been freed, then ~None~ is
    #   // returned.
    #   //
    #   static function UVMTrStream get_stream_from_handle(integer id)
    #      if (id == 0)
    #        return None
    #
    #      if ($isunknown(id) || !m_streams_by_id.exists(id))
    #        return None
    #
    #      return m_streams_by_id[id]
    #   endfunction : get_stream_from_handle
    #

    #   // Function- m_free_id
    #   // Frees the id/stream link (memory cleanup)
    #   //
    #   static function void m_free_id(integer id)
    #      UVMTrStream stream
    #      if (!$isunknown(id) && m_streams_by_id.exists(id))
    #        stream = m_streams_by_id[id]
    #
    #      if (stream != None) begin
    #         m_streams_by_id.delete(id)
    #         m_ids_by_stream.delete(stream)
    #      end
    #   endfunction : m_free_id
    #
    #   // Group: Implementation Agnostic API
    #   //
    #

    #   // Function: do_open
    #   // Callback triggered via <uvm_tr_database::open_stream>.
    #   //
    #   // Parameters:
    #   // db - Database which the stream belongs to
    #   // scope - Optional scope
    #   // stream_type_name - Optional type name for the stream
    #   //
    #   // The ~do_open~ callback can be used to initialize any internal
    #   // state within the stream, as well as providing a location to
    #   // record any initial information about the stream.
    #   protected virtual function void do_open(uvm_tr_database db,
    #                                           string scope,
    #                                           string stream_type_name)
    #   endfunction : do_open

    #
    #   // Function: do_close
    #   // Callback triggered via <close>.
    #   //
    #   // The ~do_close~ callback can be used to set internal state
    #   // within the stream, as well as providing a location to
    #   // record any closing information.
    #   protected virtual function void do_close()
    #   endfunction : do_close
    #

    #   // Function: do_free
    #   // Callback triggered via <free>.
    #   //
    #   // The ~do_free~ callback can be used to release the internal
    #   // state within the stream, as well as providing a location
    #   // to record any "freeing" information.
    #   protected virtual function void do_free()
    #   endfunction : do_free
    #

    #   // Function: do_open_recorder
    #   // Marks the beginning of a new record in the stream.
    #   //
    #   // Backend implementation of <open_recorder>
    #   protected virtual function uvm_recorder do_open_recorder(string name,
    #                                                            time   open_time,
    #                                                            string type_name)
    #      return None
    #   endfunction : do_open_recorder
    #
    #endclass : UVMTrStream
#

#//------------------------------------------------------------------------------
#//
#// CLASS: UVMTextTrStream
#//
#// The ~UVMTextTrStream~ is the default stream implementation for the
#// <uvm_text_tr_database>.
#//
#//
#
#class UVMTextTrStream extends UVMTrStream
class UVMTextTrStream(UVMTrStream):

    def __init__(self, name="unnamed-UVMTextTrStream"):
        UVMTrStream.__init__(self, name)
        #   // Variable- m_text_db
        #   // Internal reference to the text-based backend
        self.m_text_db = None


    #   // Group: Implementation Agnostic API

    def do_open(self, db, scope, stream_type_name):
        """
           Function: do_open
           Callback triggered via <uvm_tr_database::open_stream>.

          protected virtual function void do_open(uvm_tr_database db,
                                                  string scope,
                                                  string stream_type_name)
        Args:
            db:
            scope:
            stream_type_name:
        """
        # $cast(m_text_db, db)
        self.m_text_db = db
        if self.m_text_db.open_db():
            sv.fdisplay(self.m_text_db.m_file,
                      "  CREATE_STREAM @%0t [NAME:%s T:%s SCOPE:%s STREAM:%0d]",
                      uvm_sim_time(),
                      self.get_name(),
                      stream_type_name,
                      scope,
                      self.get_handle())

    #   // Function: do_close
    #   // Callback triggered via <UVMTrStream::close>.
    #   protected virtual function void do_close()
    #      if (m_text_db.open_db())
    #        $fdisplay(m_text_db.m_file,
    #                  "  CLOSE_STREAM @%0t {NAME:%s T:%s SCOPE:%s STREAM:%0d}",
    #                  $time,
    #                  this.get_name(),
    #                  this.get_stream_type_name(),
    #                  this.get_scope(),
    #                  this.get_handle())
    #   endfunction : do_close
    #

    #   // Function: do_free
    #   // Callback triggered via <UVMTrStream::free>.
    #   //
    #   protected virtual function void do_free()
    #      if (m_text_db.open_db())
    #        $fdisplay(m_text_db.m_file,
    #                  "  FREE_STREAM @%0t {NAME:%s T:%s SCOPE:%s STREAM:%0d}",
    #                  $time,
    #                  this.get_name(),
    #                  this.get_stream_type_name(),
    #                  this.get_scope(),
    #                  this.get_handle())
    #      m_text_db = None
    #      return
    #   endfunction : do_free
    #

    def do_open_recorder(self, name, open_time, type_name):
        """
           Function: do_open_recorder
           Marks the beginning of a new record in the stream

           Text-backend specific implementation.
        Args:
            name:
            open_time:
            type_name:
        Returns:
        """
        if self.m_text_db.open_db():
            return UVMTextRecorder.type_id.create(name)
        return None


    #endclass : UVMTextTrStream
uvm_object_utils(UVMTextTrStream)
