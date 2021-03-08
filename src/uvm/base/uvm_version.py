#//----------------------------------------------------------------------
#//   Copyright 2007-2010 Mentor Graphics Corporation
#//   Copyright 2007-2011 Cadence Design Systems, Inc.
#//   Copyright 2010-2011 Synopsys, Inc.
#//   Copyright 2013-2014 NVIDIA Corporation
#//   Copyright 2019 Tuomas Poikela
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

from .. import version

uvm_mgc_copyright  = "(C) 2007-2014 Mentor Graphics Corporation"
uvm_cdn_copyright  = "(C) 2007-2014 Cadence Design Systems, Inc."
uvm_snps_copyright = "(C) 2006-2014 Synopsys, Inc."
uvm_cy_copyright   = "(C) 2011-2013 Cypress Semiconductor Corp."
uvm_nv_copyright   = "(C) 2013-2014 NVIDIA Corporation"
uvm_revision = "uvm-python {} (Ported from UVM 1.2)".format(version.__version__)
uvm_tpoikela_copyright = "(C) 2019-2021 Tuomas Poikela (tpoikela)"

def uvm_revision_string():
    return uvm_revision
