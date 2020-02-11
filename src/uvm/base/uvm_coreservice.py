
from .uvm_factory import UVMDefaultFactory
from .uvm_report_server import UVMReportServer


#//----------------------------------------------------------------------
#// Class: uvm_default_coreservice_t
#//
#// uvm_default_coreservice_t provides a default implementation of the
#// uvm_coreservice_t API. It instantiates uvm_default_factory, uvm_default_report_server,
#// uvm_root.
#//----------------------------------------------------------------------
class UVMCoreService:

    m_inst = None

    def __init__(self):
        self.report_server = None
        self.factory = None
        self.tr_database = None  # uvm_tr_database
        self._visitor = None

    @classmethod
    def get(cls):
        if UVMCoreService.m_inst is None:
            UVMCoreService.m_inst = UVMCoreService()
        return UVMCoreService.m_inst
    
    @staticmethod
    def reset():
        """Reset the state of coreservices. Used for unit testing"""
        UVMCoreService.m_inst = None
        from .uvm_registry import UVMComponentRegistry, UVMObjectRegistry
        UVMComponentRegistry.reset()
        UVMObjectRegistry.reset()

    def get_root(self):
        from .uvm_root import UVMRoot
        return UVMRoot.m_uvm_get_root()

    # Function: get_factory
    #
    # Returns the currently enabled uvm factory.
    # When no factory has been set before, instantiates a uvm_default_factory
    def get_factory(self):
        if self.factory is None:
            self.factory = UVMDefaultFactory()
        return self.factory

    # Function: set_factory
    #
    # Sets the current uvm factory.
    # Please note: it is up to the user to preserve the contents of the original factory or
    # delegate calls to the original factory
    def set_factory(self, factory):
        self.factory = factory

    # Function: get_default_tr_database
    # returns the current default record database
    #
    # If no default record database has been set before this method
    # is called, returns an instance of <uvm_text_tr_database>
    def get_default_tr_database(self):
        if self.tr_database is None:
            #process p = process::self();
            p = None
            tx_db = None  # uvm_text_tr_database
            s = ""
            if p is not None:
                s = p.get_randstate()

            from .uvm_tr_database import uvm_text_tr_database
            tx_db = uvm_text_tr_database("default_tr_database")
            self.tr_database = tx_db

            if p is not None:
                p.set_randstate(s)
        return self.tr_database
        #endfunction : get_default_tr_database

    #// Function: set_default_tr_database
    #// Sets the current default record database to ~db~
    def set_default_tr_database(self, db):
        self.tr_database = db

    def get_report_server(self):
        if self.report_server is None:
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
