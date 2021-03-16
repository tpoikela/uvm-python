
import unittest
from uvm.base import (UVMComponent, UVMObjection)

class SubChild(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)

class Child(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.subchild = SubChild("subchild1", self)


class Parent(UVMComponent):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.child = Child("child", self)
        self.child2 = Child("child2", self)


class TestUVMObjection(unittest.TestCase):


    def test_hier_obj(self):
        objection = UVMObjection("test_objection")
        parent = Parent("parent_objection_test", None)

        subchild1 = parent.child.subchild
        objection.raise_objection(subchild1, "subchild objection raised")
        self.assertEqual(objection.get_objection_count(subchild1), 1)
        self.assertEqual(objection.get_objection_total(parent.child), 1)
        self.assertEqual(objection.get_objection_total(parent), 1)

        objection.raise_objection(parent.child, "child objection raised")
        self.assertEqual(objection.get_objection_total(parent.child), 2)
        self.assertEqual(objection.get_objection_total(parent), 2)

        objection.raise_objection(parent.child2, "child2 objection raised")
        self.assertEqual(objection.get_objection_total(parent), 3)
        objection.raise_objection(parent, "parent objection raised")
        self.assertEqual(objection.get_objection_total(parent), 4)

        # Dropping the objections

        objection.drop_objection(subchild1, "subchild objection dropped")
        self.assertEqual(objection.get_objection_count(subchild1), 0)
        print(objection.convert2string())
        # self.assertEqual(objection.get_objection_total(parent.child), 1)
        # self.assertEqual(objection.get_objection_total(parent), 3)

        objection.drop_objection(parent, "parent objection dropped")
        self.assertEqual(objection.get_objection_count(parent), 0)

        objection.drop_objection(parent.child2, "child2 objection dropped")
        self.assertEqual(objection.get_objection_count(parent.child2), 0)

        objection.drop_objection(parent.child, "child objection dropped")
        self.assertEqual(objection.get_objection_count(parent.child), 0)
        # self.assertEqual(objection.get_objection_total(parent), 0)
