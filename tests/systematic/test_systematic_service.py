'''
Created on 18.10.2015

@author: michael
'''
import unittest
from unittest.mock import MagicMock

from alexandriabase.daos import DocumentDao, DocumentEventRelationsDao
from alexandriabase.domain import Document, Node, NoSuchNodeException, AlexDate,\
    EventFilter
from alexplugins.systematic.base import SystematicIdentifier, SystematicPoint,\
    QualifiedSystematicPoint, SystematicDao, DocumentSystematicRelationsDao,\
    SystematicService, systematic_string_to_identifier

class QualifiedSystematicNodeTest(unittest.TestCase):
    
    def no_test_string_for_physical_node(self):
        identifier = SystematicIdentifier("1.2", 3, 4)
        node = SystematicPoint(identifier, "Description")
        qualified_node = QualifiedSystematicPoint(node, True)
        node_as_string = "%s" % qualified_node
        self.assertEqual(node_as_string, "1.2.III-4*: Description")

    def no_test_string_for_relation_node(self):
        identifier = SystematicIdentifier("1.2", 3, 4)
        node = SystematicPoint(identifier, "Description")
        qualified_node = QualifiedSystematicPoint(node, False)
        node_as_string = "%s" % qualified_node
        self.assertEqual(node_as_string, "1.2.III-4: Description")

    def no_test_hash(self):
        dictionary = {}
        identifier = SystematicIdentifier("1.2", 3, 4)
        node = SystematicPoint(identifier, "Description")
        qualified_node = QualifiedSystematicPoint(node, False)
        dictionary[qualified_node] = None
        
class ServiceTest(unittest.TestCase):
    
    def setUp(self):
        self.systematic_dao = MagicMock(spec=SystematicDao)
        self.document_dao = MagicMock(spec=DocumentDao)
        self.document_systematic_references_dao = MagicMock(spec=DocumentSystematicRelationsDao)
        self.document_event_references_dao = MagicMock(spec=DocumentEventRelationsDao)
        self.service = SystematicService(self.systematic_dao,
                                         self.document_dao, 
                                         self.document_systematic_references_dao,
                                         self.document_event_references_dao)

    def no_test_fetch_systematic_entry_for_id_string(self):
        
        identifier = SystematicIdentifier("1.2", 3, 4)
        self.systematic_dao.get_node = MagicMock(return_value=SystematicPoint(identifier, "description"))
        entry = self.service.fetch_systematic_entry_for_id_string("1.2.III-4")
        self.systematic_dao.get_node.assert_called_once_with(identifier)
        self.assertEqual(entry.id, identifier)
        self.assertEqual(entry.description, "description")

    def no_testFetchSystematicEntriesForDocument(self):
        
        # Setup
        document = Document(25)
        signature = systematic_string_to_identifier("1.2.IV-3")
        identifier1 = SystematicIdentifier("2.3", 5, 6)
        identifier2 = SystematicIdentifier("3.4", 7, 8)
        self.document_systematic_references_dao.fetch_systematik_ids_for_document_id = MagicMock(return_value=[identifier1, identifier2])
        self.document_systematic_references_dao.fetch_signature_for_document_id = MagicMock(return_value=signature)
        
        values = {signature: SystematicPoint(signature, "signature"),
                  identifier1: SystematicPoint(identifier1, "identifier1"),
                  identifier2: SystematicPoint(identifier2, "identifier2")}

        def side_effect(arg):
            return values[arg]

        self.systematic_dao.get_by_id = MagicMock(side_effect=side_effect)

        # Execution
        result = self.service.fetch_systematic_entries_for_document(document)

        # Assertion
        self.assertEqual(len(result), 3)

        self.assertIn(QualifiedSystematicPoint(values[signature], True), result)
        self.assertIn(QualifiedSystematicPoint(values[identifier1], False), result)
        self.assertIn(QualifiedSystematicPoint(values[identifier2], False), result)
        
    def no_testFetchSystematicEntriesForDocumentWithNone(self):
        
        # Execution
        result = self.service.fetch_systematic_entries_for_document(None)

        # Assertion
        self.assertEqual(len(result), 0)

    def no_testAddSystematicEntryToDocumentWithoutLocation(self):
        # Setup
        document = Document(56)
        systematic_node = SystematicPoint(SystematicIdentifier("1.2", 3, 4), "Description")
        self.document_systematic_references_dao.fetch_signature_for_document_id = MagicMock(return_value=None)
        
        # Execution        
        self.service.add_systematic_entry_to_document(document, systematic_node)
        
        # Assertion
        self.document_systematic_references_dao.set_signature_for_document_id.assert_called_once_with(document.id, systematic_node)
    
    def no_testAddSystematicEntryToDocumentWithLocation(self):
        # Setup
        document = Document(56)
        document.standort = "1.2.III-4"
        systematic_identifier = SystematicIdentifier("5.6", 7, 8)
        systematic_node = SystematicPoint(systematic_identifier, "Description")

        # Execution        
        self.service.add_systematic_entry_to_document(document, systematic_node)
        
        # Assertion
        self.assertEqual(document.standort, "1.2.III-4")
        self.document_systematic_references_dao.add_systematik_document_relation.assert_called_with(systematic_identifier, 56)
        
    def no_testRemoveSystematicEntryFromDocumentLocation(self):
        document = Document(56)
        document.standort = "1.2.III-4"
        systematic_identifier = SystematicIdentifier("1.2", 3, 4)
        systematic_point = QualifiedSystematicPoint(SystematicPoint(systematic_identifier, "Description"), True)

        self.service.remove_systematic_entry_from_document(document, systematic_point)
        
        self.assertEqual(document.standort, None)
        self.document_systematic_references_dao.set_signature_for_document_id.assert_called_with(56, None)
        
        
    def no_testRemoveSystematicEntryFromDocumentRelations(self):
        document = Document(56)
        document.standort = "1.2.III-4"
        systematic_identifier = SystematicIdentifier("1.2", 3, 4)
        systematic_point = SystematicPoint(systematic_identifier, "Description")
        qualified_systematic_node = QualifiedSystematicPoint(systematic_point, False)

        self.service.remove_systematic_entry_from_document(document, qualified_systematic_node)
        
        self.document_systematic_references_dao.remove_systematik_document_relation(56, systematic_identifier)
        
    def no_testGetSystematicTree(self):
        
        self.service.get_systematic_tree()
        self.systematic_dao.get_tree.assert_called_once_with()

    def no_test_next_sibling_exists(self):
        
        identifier = SystematicIdentifier("1.2.3")
        sibling = SystematicIdentifier("1.2.4")
        self.systematic_dao.get_node.return_value = SystematicPoint(sibling, "Description")
        self.assertTrue(self.service.next_sibling_exists(identifier))
        self.systematic_dao.get_node.assert_called_once_with(sibling)
        
    def no_test_next_sibling_exists_not(self):
        
        identifier = SystematicIdentifier("1.2.3")
        sibling = SystematicIdentifier("1.2.4")
        self.systematic_dao.get_node = MagicMock(side_effect=NoSuchNodeException(identifier))
        self.assertFalse(self.service.next_sibling_exists(identifier))
        self.systematic_dao.get_node.assert_called_once_with(sibling)
        
    def no_test_save(self):

        identifier = SystematicIdentifier("1.2.3")
        node = SystematicPoint(identifier, "Description")
        self.service.save(node)
        self.systematic_dao.save.assert_called_once_with(node)

    def no_test_delete(self):

        identifier = SystematicIdentifier("1.2.3")
        node = SystematicPoint(identifier, "Description")
        self.service.delete(node)
        self.systematic_dao.delete.assert_called_once_with(identifier)

    def no_test_systematic_id_is_in_use(self):

        identifier = SystematicIdentifier("1.2.3")
        self.document_systematic_references_dao.systematic_id_is_in_use.return_value = True
        self.assertTrue(self.service.systematic_id_is_in_use(identifier))
        self.document_systematic_references_dao.systematic_id_is_in_use.assert_called_once_with(identifier)

    def no_test_potential_new_children_1(self):
        node = Node(SystematicPoint(SystematicIdentifier("1.2", 1, 2), "Description"))
        self.assertEqual(0, len(self.service.get_potential_new_child_identifier(node)))
                
    def no_test_potential_new_children_2(self):
        node = Node(SystematicPoint(SystematicIdentifier("1.2", 1), "Description"))
        new_child_identifiers = self.service.get_potential_new_child_identifier(node)
        self.assertEqual(1, len(new_child_identifiers))
        self.assertEqual(SystematicIdentifier("1.2", 1, 1), new_child_identifiers[0])
        
    def no_test_potential_new_children_3(self):
        node = Node(SystematicPoint(SystematicIdentifier("1.2"), "Description"))
        new_child_identifiers = self.service.get_potential_new_child_identifier(node)
        self.assertEqual(2, len(new_child_identifiers))
        self.assertEqual(SystematicIdentifier("1.2.1"), new_child_identifiers[0])
        self.assertEqual(SystematicIdentifier("1.2", 1), new_child_identifiers[1])

    def no_test_potential_new_children_4(self):
        node = Node(SystematicPoint(SystematicIdentifier("1.2"), "Description"))
        self.systematic_dao.get_children.return_value = [SystematicPoint(SystematicIdentifier("1.2.1"), "Description")]
        new_child_identifiers = self.service.get_potential_new_child_identifier(node)
        self.assertEqual(1, len(new_child_identifiers))
        self.assertEqual(SystematicIdentifier("1.2.2"), new_child_identifiers[0])

    def no_test_potential_new_children_5(self):
        node = Node(SystematicPoint(SystematicIdentifier("1.2"), "Description"))
        self.systematic_dao.get_children.return_value = [SystematicPoint(SystematicIdentifier("1.2", 1), "Description")]
        new_child_identifiers = self.service.get_potential_new_child_identifier(node)
        self.assertEqual(1, len(new_child_identifiers))
        self.assertEqual(SystematicIdentifier("1.2", 2), new_child_identifiers[0])

    def no_test_potential_new_children_6(self):
        node = Node(SystematicPoint(SystematicIdentifier("1.2", 3), "Description"))
        self.systematic_dao.get_children.return_value = [SystematicPoint(SystematicIdentifier("1.2", 3, 1), "Description")]
        new_child_identifiers = self.service.get_potential_new_child_identifier(node)
        self.assertEqual(1, len(new_child_identifiers))
        self.assertEqual(SystematicIdentifier("1.2", 3, 2), new_child_identifiers[0])
        
    def test_fetch_doc_event_references(self):
        
        self.document_event_references_dao.fetch_doc_event_references.return_value = {1: [2 , 3], 4: [5, 6]}
        self.document_systematic_references_dao.fetch_document_ids_for_systematic_id_in_timerange.return_value = {4: [6, 7], 7: [8, 9]} 
        
        test_filter = EventFilter()
        test_filter.signature = "1.1.II-1"
        test_filter.earliest_date = AlexDate(1990)
        test_filter.latest_date = AlexDate(2020)
        
        result = self.service.fetch_doc_event_references(test_filter)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[4]), 3)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
