import unittest

from alexandriabase.base_exceptions import DataError
import pytest
from alexandriabase.domain import Tree
from alexplugins.systematic.base import systematic_string_to_identifier,\
    SystematicIdentifier, SystematicPoint


class SystematicIdFromStringTest(unittest.TestCase):

    def test_split_raw_systematic_id_simple(self):
        
        systematic_id = systematic_string_to_identifier("1.0.1")
        self.assertEqual(systematic_id, SystematicIdentifier('1.0.1'))
        
    def test_split_raw_systematic_id_roman(self):
        systematic_id = systematic_string_to_identifier("1.0.1.VII")
        self.assertEqual(systematic_id, SystematicIdentifier('1.0.1', 7))

    def test_split_raw_systematic_id_folder(self):
        systematic_id = systematic_string_to_identifier("1.0.1.VII-3")
        self.assertEqual(systematic_id, SystematicIdentifier('1.0.1', 7, 3))

    def test_split_raw_systematic_id_missing_roman(self):
        
        systematic_id = systematic_string_to_identifier("1.0-1")
        self.assertEqual(systematic_id, SystematicIdentifier('1.0', 0, 1))
        
        # Accept trailing dots
    def test_split_raw_systematic_id_trailing_dot(self):
        systematic_id = systematic_string_to_identifier("1.0.1.VII.")
        self.assertEqual(systematic_id, SystematicIdentifier('1.0.1', 7))
        
    def test_split_raw_systematic_id_empty_value(self):
        systematic_id = systematic_string_to_identifier(None)
        self.assertEqual(systematic_id, None)
    
    def test_split_raw_systematic_id_unparsable(self):
        exception_raised = False
        try:
            systematic_string_to_identifier("Hallo Welt")
        except DataError:
            exception_raised = True
        self.assertTrue(exception_raised)

class TestSystematicIdentifier(unittest.TestCase):
    
    def test_equality(self):
        
        self.assertEqual(SystematicIdentifier("1.2.3", 4, 5),
                         SystematicIdentifier("1.2.3", 4, 5))
        self.assertEqual(SystematicIdentifier("1.2.3", 4),
                         SystematicIdentifier("1.2.3", 4))
        self.assertEqual(SystematicIdentifier("1.2.3"),
                         SystematicIdentifier("1.2.3"))
        self.assertNotEqual(SystematicIdentifier("1.2.3", 4, 5),
                            SystematicIdentifier("1.2.3", 4, 6))
        self.assertNotEqual(SystematicIdentifier("1.2.3", 4, 5),
                            SystematicIdentifier("1.2.3", 4))
        self.assertNotEqual(SystematicIdentifier("1.2.3", 4, 5),
                            SystematicIdentifier("1.2.3", 5, 5))
        self.assertNotEqual(SystematicIdentifier("1.2.3", 4, 5),
                            SystematicIdentifier("1.2.3", None, 5))
        self.assertNotEqual(SystematicIdentifier("1.2.3", 4, 5),
                            SystematicIdentifier("1.2.4", 4, 5))

    def test_less_than(self):
        self.assertTrue(SystematicIdentifier("1") < SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1") < SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1", 2) < SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1", 2, 3) < SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1", 2) < SystematicIdentifier("1.1", 3))
        self.assertTrue(SystematicIdentifier("1.1") < SystematicIdentifier("1.1", 1))
        self.assertTrue(SystematicIdentifier("1.1", 2, 3) < SystematicIdentifier("1.1", 2, 4))
        self.assertTrue(SystematicIdentifier("1.1", 2) < SystematicIdentifier("1.1", 2, 1))

        self.assertFalse(SystematicIdentifier("1.1", 2, 3) < SystematicIdentifier("1.1", 2, 3))
        self.assertFalse(SystematicIdentifier("1.1", 2) < SystematicIdentifier("1.1", 2))
        self.assertFalse(SystematicIdentifier("1.1") < SystematicIdentifier("1.1"))

    def test_less_or_equal_than(self):
        self.assertTrue(SystematicIdentifier("1") <= SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1") <= SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1", 2) <= SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1", 2, 3) <= SystematicIdentifier("2"))
        self.assertTrue(SystematicIdentifier("1.1", 2) <= SystematicIdentifier("1.1", 3))
        self.assertTrue(SystematicIdentifier("1.1") <= SystematicIdentifier("1.1", 1))
        self.assertTrue(SystematicIdentifier("1.1", 2, 3) <= SystematicIdentifier("1.1", 2, 4))
        self.assertTrue(SystematicIdentifier("1.1", 2) <= SystematicIdentifier("1.1", 2, 1))

        self.assertTrue(SystematicIdentifier("1.1", 2, 3) <= SystematicIdentifier("1.1", 2, 3))
        self.assertTrue(SystematicIdentifier("1.1", 2) <= SystematicIdentifier("1.1", 2))
        self.assertTrue(SystematicIdentifier("1.1") <= SystematicIdentifier("1.1"))

    def test_greater_than(self):
        self.assertTrue(SystematicIdentifier("2") > SystematicIdentifier("1"))
        self.assertTrue(SystematicIdentifier("2") > SystematicIdentifier("1.1"))
        self.assertTrue(SystematicIdentifier("2") > SystematicIdentifier("1.1", 2))
        self.assertTrue(SystematicIdentifier("2") > SystematicIdentifier("1.1", 2, 3))
        self.assertTrue(SystematicIdentifier("1.1", 3) > SystematicIdentifier("1.1", 2))
        self.assertTrue(SystematicIdentifier("1.1", 1) > SystematicIdentifier("1.1"))
        self.assertTrue(SystematicIdentifier("1.1", 2, 4) > SystematicIdentifier("1.1", 2, 3))
        self.assertTrue(SystematicIdentifier("1.1", 2, 1) > SystematicIdentifier("1.1", 2))

        self.assertFalse(SystematicIdentifier("1.1", 2, 3) > SystematicIdentifier("1.1", 2, 3))
        self.assertFalse(SystematicIdentifier("1.1", 2) > SystematicIdentifier("1.1", 2))
        self.assertFalse(SystematicIdentifier("1.1") > SystematicIdentifier("1.1"))

    def test_greater_or_equal_than(self):
        self.assertTrue(SystematicIdentifier("2") >= SystematicIdentifier("1"))
        self.assertTrue(SystematicIdentifier("2") >= SystematicIdentifier("1.1"))
        self.assertTrue(SystematicIdentifier("2") >= SystematicIdentifier("1.1", 2))
        self.assertTrue(SystematicIdentifier("2") >= SystematicIdentifier("1.1", 2, 3))
        self.assertTrue(SystematicIdentifier("1.1", 3) >= SystematicIdentifier("1.1", 2))
        self.assertTrue(SystematicIdentifier("1.1", 1) >= SystematicIdentifier("1.1"))
        self.assertTrue(SystematicIdentifier("1.1", 2, 4) >= SystematicIdentifier("1.1", 2, 3))
        self.assertTrue(SystematicIdentifier("1.1", 2, 1) >= SystematicIdentifier("1.1", 2))

        self.assertTrue(SystematicIdentifier("1.1", 2, 3) >= SystematicIdentifier("1.1", 2, 3))
        self.assertTrue(SystematicIdentifier("1.1", 2) >= SystematicIdentifier("1.1", 2))
        self.assertTrue(SystematicIdentifier("1.1") >= SystematicIdentifier("1.1"))

    def test_subfolder_parent(self):
        
        identifier = SystematicIdentifier("1.2.3", "4", "5")
        self.assertEqual(identifier.parent_id, 
                         SystematicIdentifier("1.2.3", "4"))


    def test_roman_parent(self):
        
        identifier = SystematicIdentifier("1.2.3", "4")
        self.assertEqual(identifier.parent_id, 
                         SystematicIdentifier("1.2.3"))

    def test_normal_parent(self):
        
        identifier = SystematicIdentifier("1.2.3")
        self.assertEqual(identifier.parent_id, 
                         SystematicIdentifier("1.2"))

    def test_root_parent(self):
        
        identifier = SystematicIdentifier("1")
        self.assertEqual(identifier.parent_id, 
                         SystematicIdentifier(None))
        
    def test_get_next_sibling_1(self):
        identifier = SystematicIdentifier("1")
        self.assertEqual(identifier.get_next_sibling_identifier(),
                         SystematicIdentifier("2"))
        
    def test_get_next_sibling_2(self):
        identifier = SystematicIdentifier("1.1.7")
        self.assertEqual(identifier.get_next_sibling_identifier(),
                         SystematicIdentifier("1.1.8"))

    def test_get_next_sibling_3(self):
        identifier = SystematicIdentifier("1.1.7", 5)
        self.assertEqual(identifier.get_next_sibling_identifier(),
                         SystematicIdentifier("1.1.7", 6))

    def test_get_next_sibling_4(self):
        identifier = SystematicIdentifier("1.1.7", 5, 3)
        self.assertEqual(identifier.get_next_sibling_identifier(),
                         SystematicIdentifier("1.1.7", 5, 4))
        
    def test_to_string_1(self):
        identifier = SystematicIdentifier("1.1.7")
        self.assertEquals("%s" % identifier, "1.1.7")

    def test_to_string_2(self):
        identifier = SystematicIdentifier("1.1.7", 1)
        self.assertEquals("%s" % identifier, "1.1.7.I")

    def test_to_string_3(self):
        identifier = SystematicIdentifier("1.1.7", 1, 5)
        self.assertEquals("%s" % identifier, "1.1.7.I-5")

    def test_to_string_4(self):
        identifier = SystematicIdentifier("1.1.7", 0, 5)
        self.assertEquals("%s" % identifier, "1.1.7-5")

class TreeTest(unittest.TestCase):
    
    def test_three_node_tree(self):
        
        node_list = []
        node_list.append(SystematicPoint(SystematicIdentifier("1.2"), "1.2"))
        node_list.append(SystematicPoint(SystematicIdentifier("1.1"), "1.1"))
        node_list.append(SystematicPoint(SystematicIdentifier("1"), "1"))
        node_list.append(SystematicPoint(SystematicIdentifier(None), "root"))
        
        tree = Tree(node_list)
        self.assertEqual(len(tree.root_node.children), 1)
        self.assertEqual(len(tree.root_node.children[0].children), 2)
        self.assertEqual("%s" % tree.root_node.children[0].children[0], "1.1: 1.1")
        
    def test_six_node_tree(self):
        
        node_list = []
        node_list.append(SystematicPoint(SystematicIdentifier("1.2"), "1.2"))
        node_list.append(SystematicPoint(SystematicIdentifier("1.1"), "1.1"))
        node_list.append(SystematicPoint(SystematicIdentifier("1"), "1"))
        node_list.append(SystematicPoint(SystematicIdentifier("2"), "2"))
        node_list.append(SystematicPoint(SystematicIdentifier("1.1", 2), "1.1.II"))
        node_list.append(SystematicPoint(SystematicIdentifier("1.1", 1), "1.1.I"))
        node_list.append(SystematicPoint(SystematicIdentifier(None), "root"))
        
        tree = Tree(node_list)
        self.assertEqual(len(tree.root_node.children), 2)
        self.assertEqual(len(tree.root_node.children[0].children), 2)
        self.assertEqual("%s" % tree.root_node.children[0].children[0], "1.1: 1.1")
        self.assertEqual("%s" % tree.root_node.children[0].children[0].children[1], "1.1.II: 1.1.II")
    
class SystematicNodeTest(unittest.TestCase):
    
    def test_comparison_lt(self):
        one = SystematicPoint(SystematicIdentifier("1.2"), "Description")
        other = SystematicPoint(SystematicIdentifier("1.2.3"), "Description")
        third = SystematicPoint(SystematicIdentifier("1.2"), "Description")
        fourth = None
        self.assertTrue(one < other)
        self.assertFalse(one > other)
        self.assertTrue(one >= third)
        self.assertTrue(one <= third)
        self.assertTrue(one == third)
        self.assertTrue(other >= third)
        self.assertFalse(other == third)
        self.assertFalse(one == fourth)
        
    def test_to_string_1(self):
        node = SystematicPoint(SystematicIdentifier("1.2"), "Description")
        self.assertEqual("%s" % node, "1.2: Description")
        
    def test_to_string_2(self):
        # Root node
        node = SystematicPoint(SystematicIdentifier(None), "Description")
        self.assertEqual("%s" % node, "Description")

class SystematicIdentifierTests(unittest.TestCase):
    
    def test_get_parent_identifier_with_root_node(self):
        
        identifier = SystematicIdentifier(None)
        self.assertEqual(None, identifier.parent_id)
        
    def test_identifier_to_string_root_node(self):
        self.assertEqual("%s" % SystematicIdentifier(None), "Root node!")
    
    def test_identifier_to_string_simple_node(self):
        self.assertEqual("%s" % SystematicIdentifier("1.2"), "1.2")

    def test_identifier_to_string_roman_node(self):
        self.assertEqual("%s" % SystematicIdentifier("1.2", 20), "1.2.XX")

    def test_identifier_to_string_folder_node(self):
        self.assertEqual("%s" % SystematicIdentifier("1.2", 20, 17), "1.2.XX-17")

    def test_comparison_lt_with_none(self):
        identifier = SystematicIdentifier("1.2")
        other = None
        exception_raised = False
        try:
            identifier < other  # @NoEffect
        except Exception as e:
            exception_raised = True
            self.assertEqual(e.args[0], "Invalid comparison with None type.")
        self.assertTrue(exception_raised)

    def test_comparison_gt_with_none(self):
        identifier = SystematicIdentifier("1.2")
        other = None
        exception_raised = False
        try:
            identifier > other  # @NoEffect
        except Exception as e:
            exception_raised = True
            self.assertEqual(e.args[0], "Invalid comparison with None type.")
        self.assertTrue(exception_raised)

    def test_comparison_le_with_none(self):
        identifier = SystematicIdentifier("1.2")
        other = None
        exception_raised = False
        try:
            identifier <= other  # @NoEffect
        except Exception as e:
            exception_raised = True
            self.assertEqual(e.args[0], "Invalid comparison with None type.")
        self.assertTrue(exception_raised)

    def test_comparison_ge_with_none(self):
        identifier = SystematicIdentifier("1.2")
        other = None
        exception_raised = False
        try:
            identifier >= other  # @NoEffect
        except Exception as e:
            exception_raised = True
            self.assertEqual(e.args[0], "Invalid comparison with None type.")
        self.assertTrue(exception_raised)

    def test_comparison_different_node_id_length_1(self):
        identifier = SystematicIdentifier("1.2")
        other = SystematicIdentifier("1")
        self.assertTrue(identifier > other)

    def test_comparison_different_node_id_length_2(self):
        identifier = SystematicIdentifier("1.2")
        other = SystematicIdentifier("1.2.3")
        self.assertTrue(identifier < other)

    def test_comparison_same_node_id_length(self):
        identifier = SystematicIdentifier("1.3")
        other = SystematicIdentifier("1.3")
        self.assertTrue(identifier <= other)
        self.assertTrue(identifier >= other)

    def test_comparison_with_root_node_1(self):
        identifier = SystematicIdentifier(None)
        other = SystematicIdentifier("1.2.3")
        self.assertTrue(identifier < other)

    def test_comparison_with_root_node_2(self):
        identifier = SystematicIdentifier("1")
        other = SystematicIdentifier(None)
        self.assertTrue(identifier > other)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
