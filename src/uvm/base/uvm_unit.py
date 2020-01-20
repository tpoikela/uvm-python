""" Common code used in unit testing """


class MockObj:
    inst_id = 0

    """ Mock object for unit testing to reduce import deps between files """
    def __init__(self, name, parent):
        self.m_parent = parent
        self.m_name = name
        self.m_typename = "MockObj"
        self.m_inst_id = MockObj.inst_id
        MockObj.inst_id += 1

    def get_name(self):
        """Get name of this object """
        return self.m_name

    def get_full_name(self):
        """Get full name of this object """
        if self.m_parent is not None:
            return self.m_parent.get_full_name() + "." + self.m_name
        return self.m_name

    def get_parent(self):
        """Get parent of this object """
        return self.m_parent

    def get_type_name(self):
        return self.m_typename

    def get_inst_id(self):
        return self.m_inst_id


class MockCb(MockObj):

    def __init__(self, name):
        super().__init__(name, None)
        self.m_enabled = True

    def callback_mode(self, on=-1):
        return self.m_enabled
