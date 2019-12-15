
class UVMDefaultServer:

    def __init__(self):
        self.m_quit_count = 0
        self.m_max_quit_count = 0
        self.max_quit_overridable = True
        self.m_severity_count = {}
        self.m_id_count = {}
        ## uvm_tr_database m_message_db;
        ## uvm_tr_stream m_streams[string][string]; // ro.name,rh.name

