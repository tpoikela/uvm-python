#//
#// -------------------------------------------------------------
#//    Copyright 2010-2011 Mentor Graphics Corporation
#//    Copyright 2019-2020 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//

import cocotb
from .uvm_reg import UVMReg
from .uvm_reg_field import UVMRegField
from .uvm_reg_model import (UVM_CHECK, UVM_DEFAULT_PATH, UVM_NOT_OK,
    UVM_PREDICT_WRITE, UVM_PREDICT_DIRECT, UVM_PREDICT_READ)
from ..macros import uvm_warning, uvm_error
from ..base.sv import sv



class UVMRegFIFO(UVMReg):
    """
    Class: UVMRegFIFO

    This special register models a DUT FIFO accessed via write/read,
    where writes push to the FIFO and reads pop from it.

    Backdoor access is not enabled, as it is not yet possible to force
    complete FIFO state, i.e. the write and read indexes used to access
    the FIFO data.
    """



    #    // Variable: fifo
    #    //
    #    // The abstract representation of the FIFO. Constrained
    #    // to be no larger than the size parameter. It is public
    #    // to enable subtypes to add constraints on it and randomize.
    #    //
    #    rand uvm_reg_data_t fifo[$]


    #    constraint valid_fifo_size {
    #      len(self.fifo) <= m_size
    #    }


    #    //----------------------
    #    // Group: Initialization
    #    //----------------------

    #    // Function: new
    #    //
    #    // Creates an instance of a FIFO register having ~size~ elements of
    #    // ~n_bits~ each.
    #    //
    def __init__(self, name, size, n_bits, has_cover):
        super().__init__(name,n_bits,has_cover)
        self.m_size = size
        self.fifo = []
        self.m_set_cnt = 0


    #    // Funtion: build
    #    //
    #    // Builds the abstract FIFO register object. Called by
    #    // the instantiating block, a `UVMRegBlock` subtype.
    #    //
    def build(self):
        self.value = UVMRegField.type_id.create("value")
        self.value.configure(self, self.get_n_bits(), 0, "RW", 0, 0x0, 1, 0, 1)


    #    // Function: set_compare
    #    //
    #    // Sets the compare policy during a mirror (read) of the DUT FIFO.
    #    // The DUT read value is checked against its mirror only when both the
    #    // ~check~ argument in the <mirror()> call and the compare policy
    #    // for the field is <UVM_CHECK>.
    #    //
    def set_compare(self, check=UVM_CHECK):
        self.value.set_compare(check)


    #    //---------------------
    #    // Group: Introspection
    #    //---------------------

    #    // Function: size
    #    //
    #    // The number of entries currently in the FIFO.
    #    //
    def size(self):
        return len(self.fifo)


    #    // Function: capacity
    #    //
    #    // The maximum number of entries, or depth, of the FIFO.
    #
    def capacity(self):
        return self.m_size


    #    //--------------
    #    // Group: Access
    #    //--------------

    #    //  Function: write
    #    //
    #    //  Pushes the given value to the DUT FIFO. If auto-prediction is enabled,
    #    //  the written value is also pushed to the abstract FIFO before the
    #    //  call returns. If auto-prediction is not enabled (via
    #    //  `UVMRegMap.set_auto_predict`), the value is pushed to abstract
    #    //  FIFO only when the write operation is observed on the target bus.
    #    //  This mode requires using the <uvm_reg_predictor> class.
    #    //  If the write is via an `UVMRegFIFO.update` operation, the abstract FIFO
    #    //  already contains the written value and is thus not affected by
    #    //  either prediction mode.


    #    //  Function: read
    #    //
    #    //  Reads the next value out of the DUT FIFO. If auto-prediction is
    #    //  enabled, the frontmost value in abstract FIFO is popped.


    #    // Function: set
    #    //
    #    // Pushes the given value to the abstract FIFO. You may call this
    #    // method several times before an <update()> as a means of preloading
    #    // the DUT FIFO. Calls to ~set()~ to a full FIFO are ignored. You
    #    // must call <update()> to update the DUT FIFO with your set values.
    #    //
    def set(self, value, fname="", lineno=0):
        # emulate write, with intention of update
        value &= ((1 << self.get_n_bits())-1)
        if len(self.fifo) == self.m_size:
            return
        super().set(value,fname,lineno)
        self.m_set_cnt += 1
        self.fifo.append(self.value.value)


    #    // Function: update
    #    //
    #    // Pushes (writes) all values preloaded using <set()> to the DUT.
    #    // You must ~update~ after ~set~ before any blocking statements,
    #    // else other reads/writes to the DUT FIFO may cause the mirror to
    #    // become out of sync with the DUT.
    #    //
    async def update(self, status, path=UVM_DEFAULT_PATH, map=None, parent=None,
            prior=-1, extension=None, fname="", lineno=0):
        upd = 0x0
        if self.m_set_cnt == 0 or len(self.fifo) == 0:
            return
        self.m_update_in_progress = 1
        i = len(self.fifo)-self.m_set_cnt
        #for (int i=fifo.size()-m_set_cnt; m_set_cnt > 0; i++, m_set_cnt--):
        while self.m_set_cnt > 0:
            # uvm_reg_data_t val = get();
            # super.update(status,path,map,parent,prior,extension,fname,lineno);
            if i >= 0:
                status.clear()
                await self.write(status, self.fifo[i], path, map, parent,prior,extension,fname,lineno)
            i += 1
            self.m_set_cnt -= 1
        self.m_update_in_progress = 0


    #    // Function: mirror
    #    //
    #    // Reads the next value out of the DUT FIFO. If auto-prediction is
    #    // enabled, the frontmost value in abstract FIFO is popped. If
    #    // the ~check~ argument is set and comparison is enabled with
    #    // <set_compare()>.


    #    // Function: get
    #    //
    #    // Returns the next value from the abstract FIFO, but does not pop it.
    #    // Used to get the expected value in a <mirror()> operation.
    #    //
    def get(self, fname="", lineno=0):
        #return fifo.pop(0)();
        val = self.fifo[0]
        return val


    #    // Function: do_predict
    #    //
    #    // Updates the abstract (mirror) FIFO based on <write()> and
    #    // <read()> operations.  When auto-prediction is on, this method
    #    // is called before each read, write, peek, or poke operation returns.
    #    // When auto-prediction is off, this method is called by a
    #    // `UVMRegPredictor` upon receipt and conversion of an observed bus
    #    // operation to this register.
    #    //
    #    // If a write prediction, the observed
    #    // write value is pushed to the abstract FIFO as long as it is
    #    // not full and the operation did not originate from an <update()>.
    #    // If a read prediction, the observed read value is compared
    #    // with the frontmost value in the abstract FIFO if <set_compare()>
    #    // enabled comparison and the FIFO is not empty.
    #    //
    #    virtual function void do_predict(uvm_reg_item      rw,
    #                                     uvm_predict_e     kind = UVM_PREDICT_DIRECT,
    #                                     uvm_reg_byte_en_t be = -1)
    def do_predict(self, rw, kind=UVM_PREDICT_DIRECT, be=-1):
        super().do_predict(rw,kind,be)

        if rw.status == UVM_NOT_OK:
            return

        if kind in [UVM_PREDICT_WRITE, UVM_PREDICT_DIRECT]:
            if (len(self.fifo) != self.m_size) and (not self.m_update_in_progress):
                self.fifo.append(self.value.value)
        elif kind == UVM_PREDICT_READ:
            value = rw.value[0] & ((1 << self.get_n_bits())-1)
            mirror_val = 0x0
            if (len(self.fifo) == 0):
                return
            mirror_val = self.fifo.pop(0)
            if (self.value.get_compare() == UVM_CHECK and mirror_val != value):
                uvm_warning("MIRROR_MISMATCH", sv.sformatf(
                    "Observed DUT read value 'h%0h != mirror value 'h%0h, FIFO: %s",
                    value, mirror_val, str(self.fifo)))


    #    // Group: Special Overrides

    #    // Task: pre_write
    #    //
    #    // Special pre-processing for a <write()> or <update()>.
    #    // Called as a result of a <write()> or <update()>. It is an error to
    #    // attempt a write to a full FIFO or a write while an update is still
    #    // pending. An update is pending after one or more calls to <set()>.
    #    // If in your application the DUT allows writes to a full FIFO, you
    #    // must override `UVMRegFIFO.pre_write` as appropriate.
    async def pre_write(self, rw):
        if self.m_set_cnt > 0 and not self.m_update_in_progress:
            uvm_error("Needs Update","Must call update() after set() and before write()")
            rw.status = UVM_NOT_OK
            return

        if (len(self.fifo) >= self.m_size and not self.m_update_in_progress):
            uvm_error("FIFO Full","Write to full FIFO ignored")
            rw.status = UVM_NOT_OK
            return


    #    // Task: pre_read
    #    //
    #    // Special post-processing for a <write()> or <update()>.
    #    // Aborts the operation if the internal FIFO is empty. If in your application
    #    // the DUT does not behave this way, you must override `UVMRegFIFO.pre_read` as
    #    // appropriate.
    async def pre_read(self, rw):
        # abort if fifo empty
        if len(self.fifo) == 0:
            rw.status = UVM_NOT_OK
            return


    def post_randomize(self):
        self.m_set_cnt = 0

