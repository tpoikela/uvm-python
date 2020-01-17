#//
#//-----------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2013 NVIDIA Corporation
#//   Copyright 2020 Tuomas Poikela
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

from ..dap.uvm_simple_lock_dap import uvm_simple_lock_dap
from ..base.uvm_object import UVMObject
from ..base.sv import sv
from ..macros.uvm_object_defines import uvm_object_utils
from ..macros.uvm_message_defines import uvm_warning
from .uvm_tr_stream import uvm_text_tr_stream, uvm_tr_stream
from .uvm_recorder import UVMRecorder

NO_FILE_OPEN = 0

#//------------------------------------------------------------------------------
#// File: Transaction Recording Databases
#//
#// The UVM "Transaction Recording Database" classes are an abstract representation
#// of the backend tool which is recording information for the user.  Usually this
#// tool would be dumping information such that it can be viewed with the ~waves~
#// of the DUT.
#//


#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_tr_database
#//
#// The ~uvm_tr_database~ class is intended to hide the underlying database implementation
#// from the end user, as these details are often vendor or tool-specific.
#//
#// The ~uvm_tr_database~ class is pure virtual, and must be extended with an
#// implementation.  A default text-based implementation is provided via the
#// <uvm_text_tr_database> class.
#//

class uvm_tr_database(UVMObject):
    #
    #   // Variable- m_streams

    #   // Function: new
    #   // Constructor
    #   //
    #   // Parameters:
    #   // name - Instance name
    def __init__(self, name="unnamed-uvm_tr_database"):
        UVMObject.__init__(self, name)
        # Tracks the opened state of the database
        self.m_is_opened = False
        # Used for tracking streams which are between the open and closed states
        self.m_streams = {}  # bit m_streams[uvm_tr_stream]

    #   // Group: Database API
    #
    #   // Function: open_db
    #   // Open the backend connection to the database.
    #   //
    #   // If the database is already open, then this
    #   // method will return 1.
    #   //
    #   // Otherwise, the method will call <do_open_db>,
    #   // and return the result.
    def open_db(self):
        if self.m_is_opened is False:
            self.m_is_opened = self.do_open_db()
        return self.m_is_opened

    #
    #   // Function: close_db
    #   // Closes the backend connection to the database.
    #   //
    #   // Closing a database implicitly closes and
    #   // frees all <uvm_tr_streams> within the database.
    #   //
    #   // If the database is already closed, then this
    #   // method will return 1.
    #   //
    #   // Otherwise, this method will trigger a <do_close_db>
    #   // call, and return the result.
    def close_db(self):
        if self.m_is_opened:
            if self.do_close_db():
                self.m_is_opened = 0
        return self.m_is_opened == 0

    #   // Function: is_open
    #   // Returns the open/closed status of the database.
    #   //
    #   // This method returns 1 if the database has been
    #   // successfully opened, but not yet closed.
    #   //
    def is_open(self):
        return self.m_is_opened


    #   // Group: Stream API
    #

    #   // Function: open_stream
    #   // Provides a reference to a ~stream~ within the
    #   // database.
    #   //
    #   // Parameters:
    #   //   name - A string name for the stream.  This is the name associated
    #   //          with the stream in the database.
    #   //   scope - An optional scope for the stream.
    #   //   type_name - An optional name describing the type of records which
    #   //               will be created in this stream.
    #   //
    #   // The method returns a reference to a <uvm_tr_stream>
    #   // object if successful, ~null~ otherwise.
    #   //
    #   // This method will trigger a <do_open_stream> call, and if a
    #   // non ~null~ stream is returned, then <uvm_tr_stream::do_open>
    #   // will be called.
    #   //
    #   // Streams can only be opened if the database is
    #   // open (per <is_open>).  Otherwise the request will
    #   // be ignored, and ~null~ will be returned.
    #   function uvm_tr_stream open_stream(string name,
    #                                      string scope="",
    #                                      string type_name="")
    def open_stream(self, name, scope="", type_name=""):
        if not self.open_db():
            return None
        else:
            #process p = process::self()
            p = None
            s = ""

            if p is not None:
                s = p.get_randstate()

            open_stream = self.do_open_stream(name, scope, type_name)

            if open_stream is not None:
                self.m_streams[open_stream] = 1
                open_stream.m_do_open(self, scope, type_name)

            if p is not None:
                p.set_randstate(s)
            return open_stream


    #   // Function- m_free_stream
    #   // Removes stream from the internal array
    def m_free_stream(self, stream):
        if stream in self.m_streams:
            del self.m_streams[stream]
    #   endfunction : m_free_stream

    #
    #   // Function: get_streams
    #   // Provides a queue of all streams within the database.
    #   //
    #   // Parameters:
    #   // q - A reference to a queue of <uvm_tr_stream>s
    #   //
    #   // The ~get_streams~ method returns the size of the queue,
    #   // such that the user can conditionally process the elements.
    #   //
    #   // | uvm_tr_stream stream_q[$]
    #   // | if (my_db.get_streams(stream_q)) begin
    #   // |   // Process the queue...
    #   // | end
    #   function unsigned get_streams(ref uvm_tr_stream q[$])
    #      // Clear out the queue first...
    #      q.delete()
    #      // Then fill in the values
    #      foreach (m_streams[idx])
    #        q.push_back(idx)
    #      // Finally, return the size of the queue
    #      return q.size()
    #   endfunction : get_streams
    #
    #   // Group: Link API

    #   // Function: establish_link
    #   // Establishes a ~link~ between two elements in the database
    #   //
    #   // Links are only supported between ~streams~ and ~records~
    #   // within a single database.
    #   //
    #   // This method will trigger a <do_establish_link> call.
    def establish_link(self, link):
        s_lhs = []  # uvm_tr_stream 
        s_rhs = []  # uvm_tr_stream 
        r_lhs = []  # uvm_recorder 
        r_rhs = []  # uvm_recorder 
        lhs = link.get_lhs()
        rhs = link.get_rhs()
        db = None  # uvm_tr_database 

        if lhs is None:
            uvm_warning("UVM/TR_DB/BAD_LINK",
                "left hand side '<None>' is not supported in links for 'uvm_tr_database'")

        if rhs is None:
            uvm_warning("UVM/TR_DB/BAD_LINK",
                "right hand side '<None>' is not supported in links for 'uvm_tr_database'")
            return


        if (not sv.cast(s_lhs, lhs, uvm_tr_stream)) or (not sv.cast(r_lhs, lhs,
            UVMRecorder)):
            uvm_warning("UVM/TR_DB/BAD_LINK",
                sv.sformatf("left hand side of type '%s' not supported in links for 'uvm_tr_database'",
                lhs.get_type_name()))
            return
        else:
            s_lhs = s_lhs[0]
            r_lhs = r_lhs[0]

        if (not sv.cast(s_rhs, rhs, uvm_tr_stream)) or (not sv.cast(r_rhs, rhs, UVMRecorder)):
            uvm_warning("UVM/TR_DB/BAD_LINK",
                sv.sformatf("right hand side of type '%s' not supported in links for 'uvm_record_datbasae'",
                rhs.get_type_name()))
            return
        else:
            s_rhs = s_rhs[0]
            r_rhs = r_rhs[0]

        if r_lhs is not None:
            s_lhs = r_lhs.get_stream()

        if r_rhs is not None:
            s_rhs = r_rhs.get_stream()


        if ((s_lhs is not None) and (s_lhs.get_db() != self)):
            db = s_lhs.get_db()
            uvm_warning("UVM/TR_DB/BAD_LINK", sv.sformatf("attempt to link stream from '%s' into '%s'",
                db.get_name(), self.get_name()))
            return

        if ((s_rhs is not None) and (s_rhs.get_db() != self)):
            db = s_rhs.get_db()
            uvm_warning("UVM/TR_DB/BAD_LINK",
                sv.sformatf("attempt to link stream from '%s' into '%s'",
                db.get_name(), self.get_name()))
            return


        self.do_establish_link(link)
        #   endfunction : establish_link
        
    #
    #   // Group: Implementation Agnostic API
    #   //
    #
    #   // Function: do_open_db
    #   // Backend implementation of <open_db>
    #   pure virtual protected function bit do_open_db()
    #
    #   // Function: do_close_db
    #   // Backend implementation of <close_db>
    #   pure virtual protected function bit do_close_db()
    #
    #   // Function: do_open_stream
    #   // Backend implementation of <open_stream>
    #   pure virtual protected function uvm_tr_stream do_open_stream(string name,
    #                                                                string scope,
    #                                                                string type_name)
    #
    #   // Function: do_establish_link
    #   // Backend implementation of <establish_link>
    #   pure virtual protected function void do_establish_link(uvm_link_base link)
    #
    #endclass : uvm_tr_database
#
#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_text_tr_database
#//
#// The ~uvm_text_tr_database~ is the default implementation for the
#// <uvm_tr_database>.  It provides the ability to store recording information
#// into a textual log file.
#//
#//

class uvm_text_tr_database(uvm_tr_database):
    #
    #   // Variable- m_filename_dap
    #   // Data Access Protected Filename
    #   local uvm_simple_lock_dap#(string) m_filename_dap
    #
    #   // Variable- m_file
    #   UVM_FILE m_file

    #   // Function: new
    #   // Constructor
    #   //
    #   // Parameters:
    #   // name - Instance name
    def __init__(self, name="unnamed-uvm_text_tr_database"):
        uvm_tr_database.__init__(self, name)
        self.m_filename_dap = uvm_simple_lock_dap("filename_dap")
        self.m_filename_dap.set("tr_db.log")
        self.m_file = NO_FILE_OPEN

    #   // Group: Implementation Agnostic API
    #
    #   // Function: do_open_db
    #   // Open the backend connection to the database.
    #   //
    #   // Text-Backend implementation of <uvm_tr_database::open_db>.
    #   //
    #   // The text-backend will open a text file to dump all records in to.  The name
    #   // of this text file is controlled via <set_file_name>.
    #   //
    #   // This will also lock the ~file_name~, so that it cannot be
    #   // modified while the connection is open.
    def do_open_db(self):
        if self.m_file == NO_FILE_OPEN:
            self.m_file = sv.fopen(self.m_filename_dap.get(), "a")
            if self.m_file != NO_FILE_OPEN:
                self.m_filename_dap.lock()
        return (self.m_file != NO_FILE_OPEN)

    #
    #   // Function: do_close_db
    #   // Close the backend connection to the database.
    #   //
    #   // Text-Backend implementation of <uvm_tr_database::close_db>.
    #   //
    #   // The text-backend will close the text file used to dump all records in to,
    #   // if it is currently opened.
    #   //
    #   // This unlocks the ~file_name~, allowing it to be modified again.
    def do_close_db(self):
        if self.m_file != NO_FILE_OPEN:
            #fork // Needed because $fclose is a task
            print("Closing the file now XXX")
            sv.fclose(self.m_file)
            #join_none
            self.m_filename_dap.unlock()
        return 1

    #   // Function: do_open_stream
    #   // Provides a reference to a ~stream~ within the
    #   // database.
    #   //
    #   // Text-Backend implementation of <uvm_tr_database::open_stream>
    #   protected virtual function uvm_tr_stream do_open_stream(string name,
    #                                                           string scope,
    #                                                           string type_name)
    def do_open_stream(self, name, scope, typename):
        # puvm_text_tr_stream 
        m_stream = uvm_text_tr_stream.type_id.create(name)
        return m_stream


    #   // Function: do_establish_link
    #   // Establishes a ~link~ between two elements in the database
    #   //
    #   // Text-Backend implementation of <uvm_tr_database::establish_link>.
    def do_establish_link(self, link):
        r_lhs = None
        r_rhs = None  # uvm_recorder 
        lhs = link.get_lhs()
        rhs = link.get_rhs()

        sv.cast(r_lhs, lhs, uvm_recorder)
        sv.cast(r_rhs, rhs, uvm_recorder)
        r_lhs = r_lhs[0]
        r_rhs = r_rhs[0]

        if (r_lhs is None  or r_rhs is None):
            return
        else:
            pc_link = None  # uvm_parent_child_link 
            re_link = None  # uvm_related_link 
            if sv.cast(pc_link, link, UVMParentChildLink):
                sv.fdisplay(self.m_file, "  LINK @%0t {{TXH1:%0d TXH2:%0d RELATION=%0s}}",
                    sv.time(), r_lhs.get_handle(), r_rhs.get_handle(), "child")

            elif sv.cast(re_link, link, UVMRelatedLink):
                sv.fdisplay(self.m_file, "  LINK @%0t {{TXH1:%0d TXH2:%0d RELATION=%0s}}",
                    sv.time(), r_lhs.get_handle(), r_rhs.get_handle(), "")
               
        #   endfunction : do_establish_link

    #
    #   // Group: Implementation Specific API
    #
    #   // Function: set_file_name
    #   // Sets the file name which will be used for output.
    #   //
    #   // The ~set_file_name~ method can only be called prior to ~open_db~.
    #   //
    #   // By default, the database will use a file named "tr_db.log".
    #   function void set_file_name(string filename)
    #      if (filename == "") begin
    #        `uvm_warning("UVM/TXT_DB/EMPTY_NAME",
    #                     "Ignoring attempt to set file name to ''!")
    #         return
    #      end
    #
    #      if (!m_filename_dap.try_set(filename)) begin
    #         `uvm_warning("UVM/TXT_DB/SET_AFTER_OPEN",
    #                      "Ignoring attempt to change file name after opening the db!")
    #         return
    #      end
    #   endfunction : set_file_name

    #
    #
    #endclass : uvm_text_tr_database
uvm_object_utils(uvm_text_tr_database)
