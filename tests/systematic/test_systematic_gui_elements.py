'''
Created on 31.10.2016

@author: michael
'''
import unittest
from alexandriabase.domain import Tree, NoSuchNodeException
from integration.baseintegrationtest import BaseIntegrationTest
from unittest.mock import MagicMock
import os
import tempfile
import pytest
from alexpresenters.MessageBroker import ERROR_MESSAGE, Message,\
    CONF_DOCUMENT_CHANGED
from alexplugins import _
from alexplugins.systematic.base import SystematicPoint, SystematicIdentifier,\
    SystematicService, SystematicDao
from alexplugins.systematic.tkgui import SystematicGuiPluginModule,\
    SystematicPointSelectionDialog, DocumentSystematicReferenceView,\
    SystematicMenuAdditionsPresenter, DocumentSystematicReferencesPresenter,\
    SystematicPointSelectionPresenter
from alexpresenters.Module import PresentersModule
from alex_test_utils import load_table_data
from alexandriabase.daos import DocumentDao

class SystematicServiceStub:
            
    def __init__(self):
        self.create_test_data()
        self.related_nodes = {}
    
    def create_test_data(self):
        self.entity_list = []
        self.entity_list.append(SystematicPoint(SystematicIdentifier("1"), "root node"))
        self.entity_list.append(SystematicPoint(SystematicIdentifier("1.1"), "child 1 node"))
        self.entity_list.append(SystematicPoint(SystematicIdentifier("1.2"), "child 2 node"))
        self.systematic_tree = Tree(self.entity_list)
                
    def get_systematic_tree(self):
        return self.systematic_tree
      
    def fetch_systematic_entries_for_document(self, document):
        self.document = document
        if not document in self.related_nodes.keys():
            self.related_nodes[document] = []
        return self.related_nodes[document]
            
    def add_systematic_entry_to_document(self, document, systematic_node):
        self.related_nodes[document].append(systematic_node)
                
    def remove_systematic_entry_from_document(self, document, systematic_node):
        self.related_nodes[document].remove(systematic_node)

class SystematicPointSelectionDialogPresenterTest(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        injector = self.get_injector(PresentersModule(), SystematicGuiPluginModule())
        load_table_data(['systematik', 'sverweis'], self.engine)
        self.presenter = injector.get(SystematicPointSelectionPresenter)
        self.view = MagicMock(spec=SystematicPointSelectionDialog)
        self.presenter.view = self.view


    def test_get_systematic_tree(self):
        self.presenter.set_tree()
        self.assertTrue(not self.view.tree.root_node is None)

    def test_assemble_return_value(self):
        self.presenter.set_tree()
        self.view.input = self.view.tree.root_node.children[0].children[0].children[0]
        self.presenter.ok_action()
        self.assertEqual("1.1.I: 1.1.I", "%s" % self.view.return_value)

class TestSystematicPlugin(BaseIntegrationTest):


    def setUp(self):
        super().setUp()

        self.injector = self.get_injector(PresentersModule(), SystematicGuiPluginModule())
        load_table_data(['systematik', 'sverweis'], self.engine)

        self.presenter = self.injector.get(SystematicMenuAdditionsPresenter)
        self.service = self.injector.get(SystematicService)
        self.view = MagicMock()
        self.presenter.view = self.view;
        self.tree = self.service.get_systematic_tree()

    def test_new_entry(self):
        self.view.working_entry = SystematicPoint(SystematicIdentifier("2.1"), "New entry")
        
        with pytest.raises(NoSuchNodeException):
            self.tree.get_by_id(SystematicIdentifier("2.1"))
            
        self.presenter.save_working_entry_action()
        
        new_tree = self.service.get_systematic_tree()
        new_entry = new_tree.get_by_id(SystematicIdentifier("2.1"))
        self.assertFalse(new_entry is None)

    def test_delete_node(self):
        identifier = SystematicIdentifier("1.1", 2, 3)
        self.tree.get_by_id(identifier) # Assert entry exists
        self.view.working_entry = self.tree.get_by_id(identifier).entity
        
        self.presenter.delete_entry_action()
        
        new_tree = self.service.get_systematic_tree()
        with pytest.raises(NoSuchNodeException):
            new_tree.get_by_id(identifier)

    def test_delete_node_with_children(self):
        identifier = SystematicIdentifier("1.1")
        self.tree.get_by_id(identifier) # Assert entry exists
        self.view.working_entry = self.tree.get_by_id(identifier).entity
        
        self.presenter.delete_entry_action()
        
        self.assertEquals(
            _("Systematic entry with children may not be deleted"),
            self.received_messages[0].message)

    def test_delete_node_with_sibling(self):
        identifier = SystematicIdentifier("1.1", 2, 2)
        self.tree.get_by_id(identifier) # Assert entry exists
        self.view.working_entry = self.tree.get_by_id(identifier).entity
        
        self.presenter.delete_entry_action()
        
        self.assertEquals(
            _("Can't delete entry when sibling exists"),
            self.received_messages[0].message)
        
    def test_delete_used_entry(self):
        identifier = SystematicIdentifier("2")
        self.tree.get_by_id(identifier) # Assert entry exists
        self.view.working_entry = self.tree.get_by_id(identifier).entity
        
        self.presenter.delete_entry_action()
        
        self.assertEquals(
            _("Entry which is in use by documents may not be deleted"),
            self.received_messages[0].message)
        
    def test_edit_entry(self):
        identifier = SystematicIdentifier("2")
        edit_entry = self.tree.get_by_id(identifier).entity
        edit_entry.description = "Totally new description"
        self.view.working_entry = edit_entry
        
        self.presenter.save_working_entry_action()
        
        new_tree = self.service.get_systematic_tree()
        self.assertEqual("Totally new description", new_tree.get_by_id(identifier).entity.description)
        
    def test_export_as_pdf(self):
        (fd, tmp_file) = tempfile.mkstemp("pdf")
        os.remove(tmp_file)
        self.view.pdf_file = tmp_file
        self.presenter.export_as_pdf()
        self.assertTrue(os.path.isfile(tmp_file))
        os.remove(tmp_file)
        
    def test_export_as_pdf_no_selection(self):
        self.view.pdf_file = None
        self.presenter.export_as_pdf()
        self.assertEqual(0, len(self.received_messages))

class DocumentSystematicReferencesPresenterTest(BaseIntegrationTest):


    def setUp(self):
        super().setUp()
        self.injector = self.get_injector(PresentersModule(), SystematicGuiPluginModule())
        load_table_data(['systematik', 'sverweis'], self.engine)
        self.systematic_service = self.injector.get(SystematicService)
        self.document_dao = self.injector.get(DocumentDao)
        self.systematic_dao = self.injector.get(SystematicDao)
        self.presenter = self.injector.get(DocumentSystematicReferencesPresenter)
        self.view = MagicMock(spec=DocumentSystematicReferenceView)
        self.presenter.view = self.view
        
    def testReceiveMessage(self):
        
        self.init_view(1)
        
        self.assertEqual(self.presenter.view.current_document.id, 1)
        self.assertEqual(len(self.presenter.view.items), 3)

    def test_receive_message_edge_case(self):
        message = Message(CONF_DOCUMENT_CHANGED, document=None)
        
        self.presenter.receive_message(message)

        self.assertEqual(self.presenter.view.current_document, None)
        self.assertEqual(len(self.presenter.view.items), 0)


    def init_view(self, document_id):
        
        document = self.document_dao.get_by_id(document_id)
        message = Message(CONF_DOCUMENT_CHANGED, document=document)
        
        self.presenter.receive_message(message)
        
    def testAddSystematicPoint(self):
        
        self.init_view(1)
        systematic_point = self.systematic_dao.get_node(SystematicIdentifier("1.3"))
        self.presenter.view.new_systematic_point = systematic_point
        self.presenter.add_new_systematic_point()

        # Assert view changed
        self.assertEqual(len(self.presenter.view.items), 4)
        extract = [x for x in self.presenter.view.items if x == systematic_point]
        self.assertEqual(len(extract), 1)
        self.assertEqual(extract[0].description, "1.3")
        
    def testReaddingSystematicPoint(self):
        
        self.init_view(1)
        systematic_node = self.systematic_dao.get_node(SystematicIdentifier("1.2"))
        self.presenter.view.new_systematic_point = systematic_node
        self.presenter.add_new_systematic_point()

        # Assert view has not changed
        self.assertEqual(len(self.presenter.view.items), 3)
        
    def testDeletingSystematicPoint(self):
        
        self.init_view(1)
        
        self.assertEqual(len(self.presenter.view.items), 3)

        self.view.selected_item = self.presenter.view.items[0]
        self.presenter.delete_selected_systematic_point()
        
        self.assertEqual(len(self.presenter.view.items), 2)

        self.view.selected_item = self.presenter.view.items[0]
        self.presenter.delete_selected_systematic_point()
        
        self.assertEqual(len(self.presenter.view.items), 1)

        self.view.selected_item = self.presenter.view.items[0]
        self.presenter.delete_selected_systematic_point()
        
        self.assertEqual(len(self.presenter.view.items), 0)
        
        self.view.selected_item = None
        self.presenter.delete_selected_systematic_point()
        
        self.assertEqual(len(self.presenter.view.items), 0)
        
    def test_for_wrong_entry(self):
        
        document = self.document_dao.get_by_id(1)
        systematic_point = SystematicPoint(SystematicIdentifier("35.4.6"), "Not existing")
        self.systematic_service.add_systematic_entry_to_document(document, systematic_point)
        self.presenter.view.current_document = document
        self.presenter._load_systematic_items()
        self.assertMessage(ERROR_MESSAGE)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()