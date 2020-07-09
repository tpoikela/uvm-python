#//
#//------------------------------------------------------------------------------
#//   Copyright 2007-2011 Mentor Graphics Corporation
#//   Copyright 2007-2010 Cadence Design Systems, Inc.
#//   Copyright 2010 Synopsys, Inc.
#//   Copyright 2019 Tuomas Poikela (tpoikela)
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
#//------------------------------------------------------------------------------

from typing import TypeVar, Dict, Generic, List, Optional, Any
import collections

from .uvm_object import UVMObject
from ..macros import uvm_warning

KEY = TypeVar('KEY')
VAL = TypeVar('VAL')

class UVMPool(UVMObject, Generic[KEY, VAL]):
    """
    Implements a class-based dynamic associative array. Allows sparse arrays to
    be allocated on demand, and passed and stored by reference.
    """

    type_name = "uvm_pool"
    m_global_pool = None


    def __init__(self, name="", T=None):
        UVMObject.__init__(self, name)
        self.pool = collections.OrderedDict()
        self.ptr = -1
        self.T = T

    @classmethod
    def get_global_pool(cls) -> 'UVMPool':
        """
        Returns the singleton global pool. Unlike in SV, uvm-python has only one
        global pool.

        This allows items to be shared amongst components throughout the
        verification environment.

        Returns:
            UVMPool: Single global pool
        """
        if UVMPool.m_global_pool is None:
            UVMPool.m_global_pool = UVMPool("pool")
        return UVMPool.m_global_pool

    @classmethod
    def get_global(cls, key) -> Any:
        """
        Returns the specified item instance from the global item pool.

        Args:
            key (str):
        Returns:
            any: Item matching the given key.
        """
        gpool = UVMPool.get_global_pool()
        return gpool.get(key)

    def get(self, key: KEY) -> VAL:
        """
        Function: get

        Returns the item with the given `key`.

        If no item exists by that key, a new item is created with that key
        and returned.
        Args:
            key:
        Returns:
        """
        if key in self.pool:
            return self.pool[key]
        elif self.T is not None:
            self.pool[key] = self.T()
            return self.pool[key]
        return None

    def add(self, key: KEY, item: VAL) -> None:
        self.pool[key] = item

    def num(self) -> int:
        return len(self.pool.keys())

    def keys(self):
        return self.pool.keys()

    def key_list(self) -> List[KEY]:
        return list(self.pool.keys())

    def delete(self, key=None) -> None:
        if key is None:
            self.pool = {}
        else:
            if key in self.pool:
                del self.pool[key]

    def exists(self, key: KEY) -> bool:
        return key in self.pool

    def last(self):
        keys = self.pool.keys()
        if len(keys) > 0:
            self.ptr = self.num() - 1
            return next(reversed(self.pool))  # type: ignore
        else:
            return False

    def has_first(self) -> bool:
        return self.num() > 0

    def has_last(self) -> bool:
        return self.num() > 0

    def first(self):
        # keys = self.pool.keys()
        for k in self.pool:
            self.ptr = 0
            return k
        return False

    def has_next(self) -> bool:
        if self.ptr < (self.num() - 1):
            return True
        return False

    def next(self) -> Optional[KEY]:
        if self.has_next() is True:
            self.ptr += 1
            key = list(self.pool.keys())[self.ptr]
            return key
        return None

    def has_prev(self) -> bool:
        if self.ptr > 0:
            return True
        return False

    def prev(self) -> Optional[KEY]:
        if self.has_prev() is True:
            self.ptr -= 1
            key = list(self.pool.keys())[self.ptr]
            return key
        return None

    def create(self, name="") -> 'UVMPool':
        return UVMPool(name, self.T)

    def do_print(self, printer) -> None:
        while self.has_next():
            key = self.next()
            item = self.pool[key]
            # print_generic(self, name, type_name, size, value, scope_separator="."):
            if hasattr(item, 'convert2string'):
                printer.print_string(item.get_name(), item.convert2string())
            else:
                name = ""
                if hasattr(key, 'get_name'):
                    name = key.get_name()
                printer.print_generic(name, '', 0, str(item))

    def __len__(self):
        """
        len() operator
        Returns:
        """
        return self.num()

    def __contains__(self, key) -> bool:
        """
        Implements X in Y operator
        Args:
            key:
        Returns:
        """
        return key in self.pool

    def __setitem__(self, key, value):
        """
        Implements aa[x] = y
        Args:
            key:
            value:
        """
        self.pool[key] = value

    def __getitem__(self, key):
        """
        Implements aa[x]
        Args:
            key:
        Returns:
        Raises:
        """
        if key in self.pool:
            return self.pool[key]
        else:
            raise IndexError('No key found')




class UVMObjectStringPool(UVMPool[str, UVMObject]):
    """
    This provides a specialization of the generic `UVMPool` class for
    an associative array of `UVMObject`-based objects indexed by string.
    Specializations of this class include the `UVMEventPool` (a
    `UVMObjectStringPool` storing `UVMEvent` and
    `UVMBarrierPool` (a `UVMObjectStringPool` storing `UVMBarrier`).
    """

    m_global_pool = None
    type_name = "uvm_obj_str_pool"

    def __init__(self, name="", Constr=UVMObject):
        """
        Creates a new pool with the given `name`.

        Args:
            name (str): Name of the pool.
            Constr (class): Used for constructing default objects.
        """
        UVMPool.__init__(self, name)
        self.Constructor = Constr


    def get_type_name(self) -> str:
        """
        Returns the type name of this object.

        Returns:
            str: Type name of this object.
        """
        return UVMObjectStringPool.type_name


    @classmethod
    def get_global_pool(cls) -> 'UVMObjectStringPool':
        """
        Returns the singleton global pool.

        This allows objects to be shared amongst components throughout the
        verification environment.

        Returns:
            UVMObjectStringPool: Global pool
        """
        if UVMObjectStringPool.m_global_pool is None:
            UVMObjectStringPool.m_global_pool = UVMObjectStringPool("global_pool")
        return UVMObjectStringPool.m_global_pool


    @classmethod
    def get_global(cls, key: str) -> UVMObject:
        """
        Returns the specified item instance from the global item pool.

        Args:
            key (str): Key used for getting the item from global pool.

        Returns:
            any: Object matching the key in the global pool.
        """
        gpool = UVMObjectStringPool.get_global_pool()
        return gpool.get(key)


    def get(self, key: str) -> UVMObject:
        """
        Returns the object item at the given string `key`.

        If no item exists by the given `key`, a new item is created for that key
        and returned.

        Args:
            key (str): Key used for getting the item.
        Returns:
            any: Item matching the key. If no match, returns new object.
        """
        if key not in self.pool:
            self.pool[key] = self.Constructor(key)
        return self.pool[key]


    def delete(self, key: str) -> None:
        """
        Removes the item with the given string `key` from the pool.

        Args:
            key (str): Key used for removing the item.
        """
        if not self.exists(key):
            uvm_warning("POOLDEL", "delete: key '{}' doesn't exist".format(key))
            return
        self.delete(key)
    #  endfunction

    def do_print(self, printer) -> None:
        """
          Function- do_print

        Args:
            printer (UVMPrinter): Printer used for printing
        """
        key = ""
        num_keys = len(list(self.pool.keys()))
        printer.print_array_header("pool", num_keys,"aa_object_string")
        if self.has_first():
            key = self.first()
            while True:
                printer.print_object("[" + key + "]", self.pool[key],"[")
                if self.has_next():
                    key = self.next()
                else:
                    break
        printer.print_array_footer()
    # endfunction


class UVMEventPool(UVMObjectStringPool):
    def __init__(self, name=""):
        from .uvm_event import UVMEvent
        UVMObjectStringPool.__init__(self, name, UVMEvent)


class UVMBarrierPool(UVMObjectStringPool):
    def __init__(self, name=""):
        from .uvm_barrier import UVMBarrier
        UVMObjectStringPool.__init__(self, name, UVMBarrier)
