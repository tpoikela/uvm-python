#
#----------------------------------------------------------------------
#   Copyright 2019      Tuomas Poikela
#   
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#
#----------------------------------------------------------------------

import cocotb
from .uvm_queue import UVMQueue
from cocotb.triggers import Event, Timer
from .uvm_debug import *


def _uvm_debug(self, func, msg):
    # uvm_debug(self, func, msg)
    pass


class UVMMailbox():

    def __init__(self, size=0, name='mailbox'):
        self.max_size = size
        self.name = name
        self.m_queue = UVMQueue()
        self.m_read_event = Event('mailbox_read_event')
        self.m_write_event = Event('mailbox_write_event')

    @cocotb.coroutine
    def put(self, item):
        _uvm_debug(self, 'put', 'Starting to check can_put()')
        if not self.can_put():
            self.m_read_event.clear()
            yield self.m_read_event.wait()
            self.m_read_event.clear()
        _uvm_debug(self, 'put', 'Putting an event into item queue')
        self.m_queue.push_back(item)
        _uvm_debug(self, 'put', 'ZZZ pushed to queue, can_get is ' + str(self.can_get()))
        self.m_write_event.set()
        yield Timer(0)
        _uvm_debug(self, 'put', 'Finished')

    @cocotb.coroutine
    def get(self, itemq):
        if not self.can_get():
            _uvm_debug(self, 'get', 'waiting write event to get item')
            self.m_write_event.clear()
            yield self.m_write_event.wait()
            self.m_write_event.clear()
            _uvm_debug(self, 'get', 'event cleared, can_get ' + str(self.can_get()))

        _uvm_debug(self, 'get', 'wait write event DONE')
        if not self.can_get():
            raise Exception('can_get() should return True, but got false. q: ' +
                    str(self.m_queue))
        item = self.m_queue.pop_front()
        self.m_read_event.set()
        _uvm_debug(self, 'get', 'getting an item from mailbox now')
        itemq.append(item)
        yield Timer(0)

    @cocotb.coroutine
    def peek(self, itemq):
        """ Peeks (with blocking) next item from mailbox without removing it """
        if not self.can_get():
            _uvm_debug(self, 'get', 'waiting write event to get item')
            self.m_write_event.clear()
            yield self.m_write_event.wait()
            self.m_write_event.clear()
            _uvm_debug(self, 'get', 'event cleared, can_get ' + str(self.can_get()))
        item = self.m_queue.front()
        itemq.append(item)

    def try_put(self, item):
        _uvm_debug(self, 'try_put', 'Starting function')
        if self.can_put() is True:
            _uvm_debug(self, 'try_put', 'can_put is True')
            self.m_queue.push_back(item)
            _uvm_debug(self, 'try_put', 'pushed to queue, can_get is ' + str(self.can_get()))
            self.m_write_event.set()
            _uvm_debug(self, 'try_put', 'try_put finishing OK')
            return True
        return False

    # Tries to retrieve an item and append it to given list.
    # Returns True if success, False otherwise.
    def try_get(self, itemq):
        if self.can_get() is True:
            item = self.m_queue.pop_front()
            itemq.append(item)
            self.m_read_event.set()
            _uvm_debug(self, 'try_get', 'try_get finishing OK')
            return True
        return False

    def try_peek(self, itemq):
        if self.can_get() is True:
            item = self.m_queue.front()
            itemq.append(item)
            _uvm_debug(self, 'try_peek', 'try_peek finishing OK')
            return True
        return False

    def can_get(self):
        return self.m_queue.size() > 0

    def can_put(self):
        if self.max_size <= 0:
            return True
        return self.m_queue.size() < self.max_size

    def num(self):
        return self.m_queue.size() > 0

