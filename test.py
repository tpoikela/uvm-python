# File to run all unit tests for uvm-python

# Usage (from cmdline):
#  To run all tests: 
#    > python test.py
#  To run one file:
#    > python test.py TestUVMComponent
#  To run one test:
#    > python test.py TestUVMDomain.test_common

# Another way would be (this enables more complex setup):
#   suite = unittest.TestSuite()
#   suite.addTest(TestUVMDomain("test_common"))
#   runner = unittest.TextTestRunner()
#   runner.run(suite)


from uvm.base.uvm_component import TestUVMComponent
from uvm.base.uvm_domain import TestUVMDomain
from uvm.base.uvm_factory import TestUVMDefaultFactory
from uvm.base.uvm_globals import TestUVMGlobals
from uvm.base.uvm_mailbox import TestUVMMailbox
from uvm.base.uvm_misc import TestUVMMisc
from uvm.base.uvm_object import TestUVMObject
from uvm.base.uvm_phase import TestUVMPhase
from uvm.base.uvm_pool import TestUVMPool
from uvm.base.uvm_printer import TestUVMPrinter
from uvm.base.uvm_queue import TestUVMQueue
from uvm.base.uvm_registry import TestUVMRegistry
from uvm.base.uvm_report_catcher import TestUVMReportCatcher
from uvm.base.uvm_report_server import TestUVMReportServer
from uvm.base.uvm_topdown_phase import TestUVMTopdownPhase

from uvm.reg.uvm_reg_field import TestUVMRegField
from uvm.reg.uvm_reg import TestUVMReg
from uvm.reg.uvm_reg_map import TestUVMRegMap

from uvm.tlm1.uvm_sqr_connections import *
from uvm.tlm1.uvm_tlm_imps import *
from uvm.tlm1.uvm_analysis_port import *
from uvm.tlm1.uvm_ports import *
from uvm.tlm1.uvm_tlm_fifos import *

import unittest

unittest.main()
