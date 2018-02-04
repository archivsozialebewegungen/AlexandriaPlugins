'''
Created on 05.01.2018

@author: michael
'''
from alexplugins.systematic.tkgui import SystematicPointSelectionPresenter,\
    SystematicPointSelectionDialog
from tkinter.ttk import Button
from alexplugins.systematic.base import SystematicIdentifier, SystematicPoint
from alexandriabase.domain import Tree
from manual.dialogs_test import DialogTest, DialogTestRunner
from alexplugins.cdexporter.tkgui import ChronoDialogPresenter, ChronoDialog,\
    ExportInfoWizardPresenter, ExportInfoWizard
from tkgui.Dialogs import GenericStringEditDialog
from alexpresenters.DialogPresenters import GenericInputDialogPresenter
from alexplugins.cdexporter.base import ExportInfo

class SystematicServiceStub():
    
    systematic_points = (SystematicPoint(SystematicIdentifier(None), "Root"),
                         SystematicPoint(SystematicIdentifier("0"), 'Node 0'),
                         SystematicPoint(SystematicIdentifier("1"), 'Node 1'),
                         SystematicPoint(SystematicIdentifier("1.1"), 'Node 1.1'),
                         )
    
    def get_systematic_tree(self):
        
        return Tree(self.systematic_points)
    
    def fetch_systematic_entries_for_document(self, document):
        
        return (self.systematic_points[document.id],)


class SystematicPointSelectionTest(DialogTest):
        
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.name = "Systematic node selection"
        
    def test_component(self, master, message_label):
        self.master = master
        self.message_label = message_label
        presenter = SystematicPointSelectionPresenter(SystematicServiceStub(),
                                                      self.message_broker)
        self.dialog = SystematicPointSelectionDialog(self.window_manager, presenter)
        Button(self.master, text='Start dialog', command=self._start_dialog).pack()

    def _start_dialog(self):
        self.dialog.activate(self._systematic_dialog_callback, label="Test label")
        
    def _systematic_dialog_callback(self, node):
        self.message_label.set("Selection: %s Type: %s" % (node, type(node)))
    
class ChronoDialogTest(DialogTest):

    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.name = "Chrono dialog"
        
    def test_component(self, master, message_label):
        self.master = master
        self.message_label = message_label
        presenter = ChronoDialogPresenter()
        self.dialog = ChronoDialog(self.window_manager, presenter)
        Button(self.master, text='Start dialog', command=self._start_dialog).pack()

    def _start_dialog(self):
        self.dialog.activate(self._chrono_dialog_callback)
        
    def _chrono_dialog_callback(self, info):
        self.message_label.set(info)
        
class ExportInfoWizardTest(DialogTest):
    
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.name = "Export info dialog"
        
    def test_component(self, master, message_label):
        self.master = master
        self.message_label = message_label
        location_dialog = GenericStringEditDialog(self.window_manager, GenericInputDialogPresenter())
        presenter = ExportInfoWizardPresenter()
        self.dialog = ExportInfoWizard(self.window_manager, presenter, location_dialog)
        Button(self.master, text='Start dialog', command=self._start_dialog).pack()

    def _start_dialog(self):
        self.dialog.activate(self._export_info_callback, export_info=ExportInfo())
        
    def _export_info_callback(self, info):
        self.message_label.set(info)
        

if __name__ == '__main__':
    test_classes = []
    test_classes.append(SystematicPointSelectionTest)
    test_classes.append(ChronoDialogTest)
    test_classes.append(ExportInfoWizardTest)
    test_runner = DialogTestRunner(test_classes)
    test_runner.run()
