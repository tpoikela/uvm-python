
import unittest
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
        self.tr_database = None # uvm_tr_database

    @classmethod
    def get(cls):
        if UVMCoreService.m_inst is None:
            UVMCoreService.m_inst = UVMCoreService()
        return UVMCoreService.m_inst

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
    # Please note: it is up to the user to preserve the contents of the original factory or delegate calls to the original factory
    def set_factory(self, factory):
        self.factory = factory

    #// Function: get_default_tr_database
    #// returns the current default record database
    #//
    #// If no default record database has been set before this method
    #// is called, returns an instance of <uvm_text_tr_database>
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
    #virtual function void set_default_tr_database(uvm_tr_database db);
    #   self.tr_database = db;
    #endfunction : set_default_tr_database

    def get_report_server(self):
        if self.report_server is None:
            self.report_server = UVMReportServer()
        return self.report_server

    def set_report_server(self, server):
        self.report_server = server


class TestUVMCoreService(unittest.TestCase):

    def test_name(self):
        cs = UVMCoreService()
        root = cs.get_root()
        self.assertEqual(root.get_full_name(), "__top__")


if __name__ == '__main__':
    unittest.main()
