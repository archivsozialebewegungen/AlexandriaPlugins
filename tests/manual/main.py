'''
Created on 22.01.2016

@author: michael
'''
from alexplugins.systematic.tkgui import SystematicPointSelectionPresenter,\
    SystematicPointSelectionDialog, DocumentSystematicReferencesPresenter,\
    DocumentSystematicReferenceView
from tkinter import Button
from manual_tester import AbstractComponentTest, TestRunner
from alexpresenters.MessageBroker import Message, REQ_SET_DOCUMENT
from alexandriabase.domain import Document, Tree
from tkinter.constants import TOP
from alexplugins.systematic.base import SystematicPoint, SystematicIdentifier
from alexplugins.cdexporter.tkgui import ExportInfoWizardPresenter, ExportInfoDialog,\
    ExportInfoWizard
from tkgui.dialogs.GenericInputDialogs import GenericStringEditDialog

class SystematicServiceStub:
    
    def __init__(self):
        self.nodes = [
            SystematicPoint(SystematicIdentifier(None), 
                            "Root"),
            SystematicPoint(SystematicIdentifier("0"), "Node 0"),
            SystematicPoint(SystematicIdentifier("0.1"), "Node 0.1"),
            SystematicPoint(SystematicIdentifier("0.2"), "Node 0.2"),
            SystematicPoint(SystematicIdentifier("1"), "Node 1"),
            SystematicPoint(SystematicIdentifier("1.1"), "Node 1.1"),
            SystematicPoint(SystematicIdentifier("1.2"), "Node 1.2"),
            ]
        self.tree = Tree(self.nodes)
        self.doc_nodes = [[],
                          [self.nodes[2], self.nodes[3]],
                          [self.nodes[4], self.nodes[5]]]    
    def get_systematic_tree(self):
        '''
        Returns all the systematic nodes in form of a tree.
        '''
        return self.tree

    def fetch_systematic_entries_for_document(self, document):
        
        return self.doc_nodes[document.id]
        
    def remove_systematic_entry_from_document(self, document, node):
        self.doc_nodes[document.id].remove(node)
        
    def add_systematic_entry_to_document(self, document, node):
        self.doc_nodes[document.id].append(node)
        
class SystematicPointSelectionTest(AbstractComponentTest):
        
    def __init__(self):
        super().__init__()
        self.name = "Systematic node selection"
        
    def test_component(self, master, message_label):
        self.master = master
        self.message_label = message_label
        presenter = SystematicPointSelectionPresenter(SystematicServiceStub(), self.message_broker)
        self.dialog = SystematicPointSelectionDialog(presenter)
        Button(self.master, text='Start dialog', command=self._start_dialog).pack()

    def _start_dialog(self):
        result = self.dialog.activate()
        self.message_label.set("Selection: %s Type: %s" % (result, type(result)))
    

class DocumentSystematicReferencesTest(AbstractComponentTest):
        
    def __init__(self):
        super().__init__()
        self.name = "Document systematic references"

    def create_mocks_and_stubs(self):
        self.systematic_service = SystematicServiceStub()
    
    def create_widget(self, master):
    
        self.systematic_references_presenter = DocumentSystematicReferencesPresenter(
            self.message_broker,
            self.systematic_service)
        self.systematic_point_selection_presenter = SystematicPointSelectionPresenter(
            self.systematic_service, self.message_broker)
        self.systematic_point_selection_dialog = SystematicPointSelectionDialog(
            self.systematic_point_selection_presenter)
        view = DocumentSystematicReferenceView(
            master,
            self.systematic_references_presenter,
            self.systematic_point_selection_dialog)
        view.pack(side=TOP)

    def add_button(self, master, number):
        Button(master, 
            text='Change to doc %d' % number,
            command=lambda n=number: self.send_message(n)).pack(side=TOP)

    def send_message(self, number):
        message = Message(REQ_SET_DOCUMENT, document=Document(number))
        self.message_broker.send_message(message)
        
    def test_component(self, master, message_label):
        self.message_label = message_label
        self.create_mocks_and_stubs()
        self.create_widget(master)
        self.add_button(master, 1)
        self.add_button(master, 2)

class ExportInfoGenerationTest(AbstractComponentTest):
        
    def __init__(self):
        super().__init__()
        self.name = "Export info dialog"
        
    def test_component(self, master, message_label):
        self.master = master
        self.message_label = message_label
        presenter = ExportInfoWizardPresenter()
        self.dialog = ExportInfoDialog(ExportInfoWizard, presenter, GenericStringEditDialog())
        Button(self.master, text='Start dialog', command=self._start_dialog).pack()

    def _start_dialog(self):
        result = self.dialog.activate(self.master)
        self.message_label.set("ExportInfo: %s" % result)
        
if __name__ == '__main__':
    test_classes = []
    test_classes.append(SystematicPointSelectionTest())
    test_classes.append(DocumentSystematicReferencesTest())
    test_classes.append(ExportInfoGenerationTest())
    test_runner = TestRunner(test_classes)
    test_runner.run()

