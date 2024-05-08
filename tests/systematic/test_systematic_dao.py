'''
Created on 11.10.2015

@author: michael
'''
import unittest
import pytest

from alexandriabase.domain import Node, NoSuchNodeException
from daotests.test_base import DatabaseBaseTest
from alex_test_utils import load_table_data
from alexplugins.systematic.base import SystematicDao, SystematicIdentifier,\
    SystematicPoint


class TestSystematicDao(DatabaseBaseTest):
        
    def setUp(self):
        super().setUp()
        load_table_data(['systematik', 'sverweis'], self.engine)
        self.dao = SystematicDao(self.engine)
        
    def test_load_tree(self):
        tree = self.dao.get_tree()
        self.assertTrue(tree)
        self.assertEqual(len(tree.root_node.children), 2)
        eins = tree.root_node.children[0]
        zwei = tree.root_node.children[1]
        self.assertEqual("%s" % zwei, "2: 2")
        self.assertEqual(len(eins.children), 11)
        eins_eins = eins.children[0]
        eins_zwei = eins.children[1]
        eins_drei = eins.children[2]
        self.assertEqual(len(eins_eins.children), 2)
        self.assertEqual(len(eins_zwei.children), 0)
        self.assertEqual(len(eins_drei.children), 0)
        eins_eins_r_eins = eins_eins.children[0]
        eins_eins_r_zwei = eins_eins.children[1]
        self.assertEqual(len(eins_eins_r_eins.children), 0)
        self.assertEqual(len(eins_eins_r_zwei.children), 3)
        
    def test_get_node(self):
        identifier = SystematicIdentifier('1.1', 2, 3)
        node = self.dao.get_node(identifier)
        self.assertEqual("%s" % node, "1.1.II-3: 1.1.II-3")
        self.assertEqual(Node, node.__class__)

    def test_get_by_id(self):
        identifier = SystematicIdentifier('1.1', 2, 3)
        systematic_point = self.dao.get_by_id(identifier)
        self.assertEqual("%s" % systematic_point, "1.1.II-3: 1.1.II-3")
        self.assertEqual(SystematicPoint, systematic_point.__class__)

    def test_get_node_failing(self):
        identifier = SystematicIdentifier('1.1.4', 2, 3)
        with pytest.raises(NoSuchNodeException):
            self.dao.get_node(identifier)
            
    def test_update(self):
        identifier = SystematicIdentifier('1.1', 2, 3)
        node = SystematicPoint(identifier, "Completely new description")
        self.dao.save(node)
        node = self.dao.get_node(identifier)
        self.assertEqual("%s" % node, "1.1.II-3: Completely new description")
        
    def test_insert(self):
        parent_id = SystematicIdentifier('1.1', 2)
        parent_node = self.dao.get_node(parent_id)
        self.assertEqual(len(parent_node.children), 3)
        identifier = SystematicIdentifier('1.1', 2, 4)
        node = SystematicPoint(identifier, "Completely new node")
        self.dao.save(node)
        parent_node = self.dao.get_node(parent_id)
        self.assertEqual(len(parent_node.children), 4)
        self.assertEqual(identifier, parent_node.children[-1].id)

    def test_delete(self):
        parent_id = SystematicIdentifier('1.1', 2)
        parent_node = self.dao.get_node(parent_id)
        self.assertEqual(len(parent_node.children), 3)
        identifier = SystematicIdentifier('1.1', 2, 3)
        self.dao.delete(identifier)
        parent_node = self.dao.get_node(parent_id)
        self.assertEqual(len(parent_node.children), 2)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()