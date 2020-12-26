#
#------------------------------------------------------------------------------
# Copyright 2007-2011 Mentor Graphics Corporation
# Copyright 2017 Intel Corporation
# Copyright 2010 Synopsys, Inc.
# Copyright 2007-2018 Cadence Design Systems, Inc.
# Copyright 2010 AMD
# Copyright 2015-2018 NVIDIA Corporation
# Copyright 2020 Tuomas Poikela (tpoikela)
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
#------------------------------------------------------------------------------


from typing import Union, Generic, TypeVar, List, Optional, Any

from .uvm_object import UVMObject
from .uvm_globals import uvm_report_warning

T = TypeVar('T')


class UVMQueue(UVMObject, Generic[T]):

    type_name = "uvm_queue"
    m_global_queue: 'UVMQueue' = None

    def __init__(self, name=""):
        UVMObject.__init__(self, name)
        self.queue: List[T] = list()

    @classmethod
    def get_global_queue(cls) -> 'UVMQueue':
        """
        Function: get_global_queue

        Returns the singleton global queue.

        This allows items to be shared amongst components throughout the
        verification environment.

        Returns:
            UVMQueue: The global singleton queue
        """
        if UVMQueue.m_global_queue is None:
            UVMQueue.m_global_queue = UVMQueue("global_queue")
        return UVMQueue.m_global_queue

    @classmethod
    def get_global(cls, index) -> Any:
        """
        Function: get_global

        Returns the specified item instance from the global item queue.
        Args:
            cls:
            index:
        Returns:
        """
        gqueue = UVMQueue.get_global_queue()
        return gqueue.get(index)

    def get(self, index: int) -> T:
        """
        Function: get

        Returns the item at the given `index`.

        If no item exists by that key, a new item is created with that key
        and returned.
        Args:
            index:
        Returns:
        """
        default_value = 0
        if index >= self.size() or index < 0:
            uvm_report_warning("QUEUEGET",
                "get: given index out of range for queue of size {}. Ignoring get request"
                .format(self.size()))
            return default_value
        return self.queue[index]

    def size(self) -> int:
        """
        Function: size

        Returns the number of items stored in the queue.
        Returns:
        """
        return len(self.queue)

    def __len__(self) -> int:
        """
        len() operator
        Returns:
        """
        return self.size()

    def __setitem__(self, i: int, value):
        """
        Implements aa[x] = y
        Args:
            i:
            value:
        Raises:
        """
        if i < self.size():
            self.queue[i] = value
        else:
            raise Exception("UVMQueue set index {} ouf of bounds (size: {})".format(
                i, self.size()))


    def __getitem__(self, i: Union[int, slice]) -> Union[T, List[T]]:
        """
        Implements aa[x]
        Args:
            i:
        Returns:
        Raises:
        """
        if isinstance(i, slice):
            # TODO should handle slices like [:] and [:-1]
            res = []
            for i in range(slice.start, slice.stop):
                res.append(self.queue[i])
            return res
        elif i < self.size():
            return self.queue[i]
        else:
            raise IndexError("UVMQueue get index {} ouf of bounds (size: {})".format(
                i, self.size()))

    def insert(self, index: int, item: T) -> None:
        """
        Function: insert

        Inserts the item at the given `index` in the queue.
        Args:
            index:
            item:
        """
        if index >= self.size() or index < 0:
            uvm_report_warning("QUEUEINS",
                "insert: given index {} out of range for queue of size {}. Ignoring insert request"
                .format(index, self.size()))
            return
        self.queue.insert(index, item)

    def delete(self, index=-1) -> None:
        """
        Function: delete

        Removes the item at the given `index` from the queue; if `index` is
        not provided, the entire contents of the queue are deleted.
        Args:
            index:
        """
        if index >= self.size() or index < -1:
            uvm_report_warning("QUEUEDEL",
                "delete: given index out of range for queue of size {}. Ignoring delete request"
                .format(self.size()))
            return
        if index == -1:
            self.queue = list()
        else:
            self.queue.pop(index)

    def pop_front(self) -> T:
        """
        Function: pop_front

        Returns the first element in the queue (index=0),
        or `null` if the queue is empty.
        Returns:
        Raises:
        """
        if self.size() > 0:
            val = self.queue[0]
            del self.queue[0]
            return val
        else:
            raise Exception('pop_front() called on empty queue')

    def front(self) -> Optional[T]:
        if self.size() > 0:
            return self.queue[0]
        return None

    def back(self) -> Optional[T]:
        if self.size() > 0:
            return self.queue[len(self.queue) - 1]
        return None

    def pop_back(self) -> Optional[T]:
        """
        Function: pop_back

        Returns the last element in the queue (index=size()-1),
        or `null` if the queue is empty.
        Returns:
        """
        return self.queue.pop()

    def push_front(self, item: T) -> None:
        """
        Function: push_front

        Inserts the given `item` at the front of the queue.
        Args:
            item:
        """
        self.queue.insert(0, item)

    def push_back(self, item: T) -> None:
        """
        Function: push_back

        Inserts the given `item` at the back of the queue.
        Args:
            item:
        """
        self.queue.append(item)

    def create(self, name="") -> 'UVMQueue[T]':
        v = UVMQueue(name)
        return v

    def get_type_name(self) -> str:
        return UVMQueue.type_name

    def do_copy(self, rhs) -> None:
        if rhs is None:
            return
        UVMObject.do_copy(self, rhs)
        self.queue = rhs.queue

    def convert2string(self) -> str:
        return str(self.queue)

    def __str__(self) -> str:
        return self.convert2string()

    def find_with(self, find_func) -> 'UVMQueue[T]':
        """
        Group: find functions
        Added by tpoikela to mimic SystemVerilog find API
        Args:
            find_func:
        Returns:
        """
        qq = UVMQueue()
        for ee in self.queue:
            if find_func(ee):
                qq.push_back(ee)
        return qq

    def find_first_index(self, find_func) -> int:
        idx = -1
        for i in range(len(self.queue)):
            ee = self.queue[i]
            if find_func(ee):
                idx = i
                break
        return idx
