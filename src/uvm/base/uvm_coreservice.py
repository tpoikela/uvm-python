#//----------------------------------------------------------------------
#//   Copyright 2013 Cadence Design Inc
#//   Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

from .uvm_factory import UVMDefaultFactory


class UVMCoreService:
    """
    Class: UVMCoreService

    UVMCoreService provides a default implementation of the
    UVMCoreService API. It instantiates uvm_default_factory, uvm_default_report_server,
    uvm_root.
    """

    m_inst: 'UVMCoreService' = None

    def __init__(self):
        self.report_server = None
        self.factory = None
        self.tr_database = None  # uvm_tr_database
        self._visitor = None

    @classmethod
    def get(cls):
        """

        Returns:
            UVMCoreService: Core service singleton.

        """
        if UVMCoreService.m_inst is None:
            UVMCoreService.m_inst = UVMCoreService()
        return UVMCoreService.m_inst

    @classmethod
    def reset(cls):
        """Reset the state of coreservices. Used for unit testing"""
        UVMCoreService.m_inst = None
        from .uvm_registry import UVMComponentRegistry, UVMObjectRegistry
        UVMComponentRegistry.reset()
        UVMObjectRegistry.reset()

    def get_root(self):
        """
        Returns:
            UVMRoot: Singleton instance of UVMRoot.
        """
        from .uvm_root import UVMRoot
        return UVMRoot.m_uvm_get_root()

    def get_factory(self):
        """
        Function: get_factory

        Returns the currently enabled uvm factory.
        When no factory has been set before, instantiates a uvm_default_factory

        Returns:
            UVMFactory: Enabled UVM factory.
        """
        if self.factory is None:
            self.factory = UVMDefaultFactory()
        return self.factory

    def set_factory(self, factory):
        """
        Sets the current uvm factory.
        Please note: it is up to the user to preserve the contents of the original factory or
        delegate calls to the original factory

        Args:
            factory (UVMFactory):
        """
        self.factory = factory

    def get_default_tr_database(self):
        """
        Returns the current default record database

        If no default record database has been set before this method
        is called, returns an instance of `UVMTextTrDatabase`

        Returns:
            UVMTrDatabase: Default transaction database
        """
        if self.tr_database is None:
            #process p = process::self();
            p = None
            tx_db = None  # UVMTextTrDatabase
            s = ""
            if p is not None:
                s = p.get_randstate()

            from .uvm_tr_database import UVMTextTrDatabase
            tx_db = UVMTextTrDatabase("default_tr_database")
            self.tr_database = tx_db

            if p is not None:
                p.set_randstate(s)
        return self.tr_database


    def set_default_tr_database(self, db):
        """
        Function: set_default_tr_database
        Sets the current default record database to `db`

        Args:
            db (UVMTrDatabase): Default transaction database to use
        """
        self.tr_database = db

    def get_report_server(self):
        """
        Returns:
            UVMReportServer: Report server singleton instance.
        """
        if self.report_server is None:
            from .uvm_report_server import UVMReportServer
            self.report_server = UVMReportServer()
        return self.report_server

    def set_report_server(self, server):
        self.report_server = server

    #// Function: set_component_visitor
    #// sets the component visitor to ~v~
    #// (this visitor is being used for the traversal at end_of_elaboration_phase
    #// for instance for name checking)
    #virtual function void set_component_visitor(uvm_visitor#(uvm_component) v);
    #        _visitor=v;
    #endfunction


    #// Function: get_component_visitor
    #// retrieves the current component visitor
    #// if unset(or ~null~) returns a <uvm_component_name_check_visitor> instance
    #virtual function uvm_visitor#(uvm_component) get_component_visitor();
    #        if(_visitor==null) begin
    #                uvm_component_name_check_visitor v = new("name-check-visitor");
    #                _visitor=v;
    #        end
    #        return _visitor;
    #endfunction
