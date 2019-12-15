
import collections

from .uvm_object import UVMObject


class UVMPool(UVMObject):

    type_name = "uvm_pool"
    m_global_pool = None

    def __init__(self, name=""):
        UVMObject.__init__(self, name)
        self.pool = collections.OrderedDict()
        self.ptr = -1

    @classmethod
    def get_global_pool(cls):
        """ Returns the singleton global pool """
        if UVMPool.m_global_pool is None:
            UVMPool.m_global_pool = UVMPool("pool")
        return UVMPool.m_global_pool

    @classmethod
    def get_global(cls, key):
        gpool = UVMPool.get_global_pool()
        return gpool.get(key)

    def get(self, key):
        if key in self.pool:
            return self.pool[key]
        return None

    def add(self, key, item):
        self.pool[key] = item

    def num(self):
        return len(self.pool.keys())

    # len() operator
    def __len__(self):
        return self.num()

    # Implements X in Y operator
    def __contains__(self, key):
        return key in self.pool

    # Implements aa[x] = y
    def __setitem__(self, key, value):
        self.pool[key] = value

    # Implements aa[x]
    def __getitem__(self, key):
        return self.pool[key]

    def keys(self):
        return self.pool.keys()

    def delete(self, key=None):
        if key is None:
            self.pool = {}
        else:
            if key in self.pool:
                del self.pool[key]

    def exists(self, key):
        return key in self.pool

    def last(self):
        keys = self.pool.keys()
        if len(keys) > 0:
            self.ptr = self.num() - 1
            return next(reversed(self.pool))
        else:
            return False

    def has_first(self):
        return self.num() > 0

    def has_last(self):
        return self.num() > 0

    def first(self):
        # keys = self.pool.keys()
        for k in self.pool:
            self.ptr = 0
            return k
        return False

    def has_next(self):
        if self.ptr < (self.num() - 1):
            return True
        return False

    def next(self):
        if self.has_next() is True:
            self.ptr += 1
            key = list(self.pool.keys())[self.ptr]
            return key
        return None

    def has_prev(self):
        if self.ptr > 0:
            return True
        return False

    def prev(self):
        if self.has_prev() is True:
            self.ptr -= 1
            key = list(self.pool.keys())[self.ptr]
            return key
        return None

    def create(self, name=""):
        return UVMPool(name)

    def do_print(self, printer):
        while self.has_next():
            item = self.next()
            printer.print_generic(item)

#//------------------------------------------------------------------------------
#//
#// CLASS: uvm_object_string_pool #(T)
#//
#//------------------------------------------------------------------------------
#// This provides a specialization of the generic <uvm_pool #(KEY,T)> class for
#// an associative array of <uvm_object>-based objects indexed by string.
#// Specializations of this class include the ~uvm_event_pool~ (a
#// uvm_object_string_pool storing ~uvm_event#(uvm_object)~) and
#// ~uvm_barrier_pool~ (a uvm_obejct_string_pool storing <uvm_barrier>).
#//------------------------------------------------------------------------------

class UVMObjectStringPool(UVMPool):  # (type T=uvm_object) extends uvm_pool #(string,T);
    #  typedef uvm_object_string_pool #(T) this_type;
    m_global_pool = None
    #  const static string type_name = {"uvm_obj_str_pool"};
    type_name = "uvm_obj_str_pool"

    #  // Function: new
    #  //
    #  // Creates a new pool with the given ~name~.
    def __init__(self, name="", Constr=UVMObject):
        UVMPool.__init__(self, name)
        self.Constructor = Constr
    #  endfunction

    #  // Function: get_type_name
    #  //
    #  // Returns the type name of this object.
    #
    def get_type_name(self):
        return UVMObjectStringPool.type_name
    # endfunction

    #  // Function: get_global_pool
    #  //
    #  // Returns the singleton global pool for the item type, T.
    #  //
    #  // This allows items to be shared amongst components throughout the
    #  // verification environment.
    @classmethod
    def get_global_pool(cls):
        if UVMObjectStringPool.m_global_pool is None:
            UVMObjectStringPool.m_global_pool = UVMObjectStringPool("global_pool")
        return UVMObjectStringPool.m_global_pool
    #  endfunction

    #  // Function: get_global
    #  //
    #  // Returns the specified item instance from the global item pool.
    @classmethod
    def get_global(cls, key):
        gpool = UVMObjectStringPool.get_global_pool()
        return gpool.get(key)
    # endfunction

    #
    #  // Function: get
    #  //
    #  // Returns the object item at the given string ~key~.
    #  //
    #  // If no item exists by the given ~key~, a new item is created for that key
    #  // and returned.
    #
    def get(self, key):
        if not key in self.pool:
            self.pool[key] = self.Constructor(key)
        return self.pool[key]
    #  endfunction

    #  // Function: delete
    #  //
    #  // Removes the item with the given string ~key~ from the pool.
    #
    def delete(self, key):
        if not self.exists(key):
            uvm_report_warning("POOLDEL", "delete: key '{}' doesn't exist".format(key))
            return
        self.delete(key)
    #  endfunction

    #  // Function- do_print
    def do_print(self, printer):
        key = ""
        num_keys = len(list(self.pool.keys()))
        printer.print_array_header("pool", num_keys,"aa_object_string")
        if self.has_first():
            key = self.first()
            while (True):
                printer.print_object("[" + key + "]", self.pool[key],"[")
                if self.has_next():
                    key = self.next()
                else:
                    break
        printer.print_array_footer()
    # endfunction
#endclass


class UVMEventPool(UVMObjectStringPool):
    def __init__(self, name=""):
        from .uvm_event import UVMEvent
        UVMObjectStringPool.__init__(self, name, UVMEvent)


class UVMBarrierPool(UVMObjectStringPool):
    def __init__(self, name=""):
        from .uvm_barrier import UVMBarrier
        UVMObjectStringPool.__init__(self, name, UVMBarrier)

import unittest

class TestUVMPool(unittest.TestCase):

    def test_global_pool(self):
        gpool = UVMPool.get_global_pool()
        gpool.add('abc', 879)
        g_val = UVMPool.get_global('abc')
        self.assertEqual(g_val, 879)

    def test_pool(self):
        pool = UVMPool()
        pool.add('xxx', 123)
        self.assertEqual(pool.num(), 1)
        self.assertEqual(pool.get('xxx'), 123)
        first_key = pool.first()
        last_key = pool.last()
        self.assertEqual(first_key, 'xxx')
        self.assertEqual(first_key, last_key)

    def test_pool_iter(self):
        pool = UVMPool()
        pool.add('a', 1)
        pool.add('b', 2)
        pool.add('c', 3)
        self.assertEqual(pool.num(), 3)
        self.assertEqual(pool.has_prev(), False)
        self.assertEqual(pool.has_next(), True)
        self.assertEqual(pool.last(), 'c')
        self.assertEqual(pool.first(), 'a')
        self.assertEqual(pool.last(), 'c')
        self.assertEqual(pool.prev(), 'b')
        self.assertEqual(pool.prev(), 'a')
        self.assertEqual(pool.next(), 'b')
        self.assertEqual(pool.next(), 'c')

    def test_len_and_in(self):
        pool = UVMPool()
        self.assertEqual('xxx' in pool, False)
        self.assertEqual(len(pool), 0)
        pool.add('xxx', 1234)
        self.assertEqual('xxx' in pool, True)
        self.assertEqual(len(pool), 1)

    def test_while_has_next(self):
        pool = UVMPool()
        pool.add(1, 2)
        pool.add(4, 8)
        pool.add(8, 16)
        while (pool.has_next()):
            val = pool.next()

class TestUVMEventPool(unittest.TestCase):

    def test_event_pool(self):
        event_pool = UVMEventPool('event_pool')
        evt_start = event_pool.get('start')
        evt_end = event_pool.get('end')

if __name__ == '__main__':
    unittest.main()
