
import unittest
from uvm.base.uvm_resource import UVMResource, UVMResourcePool


class TestUVMResource(unittest.TestCase):

    def test_scope_match(self):
        nname1 = "my_comp.field1"
        nname2 = "my_comp.*.field1"
        rr = UVMResource("fname", "my_comp.field1")
        self.assertEqual(True, rr.match_scope(nname1))
        self.assertEqual(False, rr.match_scope(nname2))


    def test_write_read(self):
        rsc = UVMResource("rname", "scope_name")
        rsc.write(123, accessor=None)
        val = rsc.read()
        self.assertEqual(val, 123)


class TestUVMResourcePool(unittest.TestCase):

    def test_get(self):
        pool = UVMResourcePool.get()

    def test_regex_lookup(self):
        # pool = UVMPool()
        field_name = "field"
        inst_re_name = "globbed_name.*"
        r = UVMResource(field_name, inst_re_name)
        r.write(666)
        # lookup = inst_re_name + "__M_UVM__" + field_name
        # pool.add(lookup, r)
        inst_name = "globbed_name.child"
        rp = UVMResourcePool.get()
        rp.set(r)
        rq = rp.lookup_regex_names(inst_name, field_name)
        self.assertEqual(len(rq), 1)

        # Add another resource and make sure we're not getting it
        r2 = UVMResource('field_xxx', 'inst_yyy')
        r2.write(444)
        rp.set(r2)
        rq = rp.lookup_regex_names(inst_name, field_name)
        self.assertEqual(len(rq), 1)

        nname1 = "my_comp.field1"
        nname2 = "my_comp.*.field1"
        rn1 = UVMResource(field_name, nname1)
        rn1.write(111)
        rn2 = UVMResource(field_name, nname2)
        rn2.write(222)
        rp.set(rn1)
        rp.set(rn2)
        rq = rp.lookup_regex_names("my_comp.field1", field_name)
        self.assertEqual(rq[0].read(), 111)


    def test_set_get(self):
        rsrc = UVMResource("name_xxx", "scope_yyy")
        rsrc.write(567, accessor=None)
        pool = UVMResourcePool.get()
        pool.set(rsrc, False)
        rq = pool.lookup_name("scope_yyy", "name_xxx")
        self.assertEqual(len(rq), 1)
        self.assertEqual(rq[0].read(), 567)


if __name__ == '__main__':
    unittest.main()
