'''
Created on 05.01.2018

@author: michael
'''
from manual.references_test import ReferenceComponentTest, ReferencesTestRunner
from manualtests.manual.dialogs_test import SystematicServiceStub
from alexplugins.systematic.tkgui import DocumentSystematicReferencesPresenter,\
    SystematicPointSelectionPresenter, SystematicPointSelectionDialog,\
    DocumentSystematicReferenceView
from tkinter.constants import TOP
from tkinter.ttk import Button
from alexpresenters.messagebroker import Message, REQ_SET_DOCUMENT
from alexandriabase.domain import Document

class DocumentSystematicReferencesTest(ReferenceComponentTest):
        
    def __init__(self, window_manager):
        super().__init__(window_manager)
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
            self.window_manager,
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


if __name__ == '__main__':
    test_classes = []
    test_classes.append(DocumentSystematicReferencesTest)
    test_runner = ReferencesTestRunner(test_classes)
    test_runner.run()
