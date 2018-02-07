'''
Created on 29.04.2016

@author: michael
'''
from tkgui import guiinjectorkeys
from injector import inject, Module, ClassProvider, singleton, Key
from alexplugins import _
from alexpresenters.messagebroker import ERROR_MESSAGE, Message
from alexandriabase.services import DocumentFileNotFound
from tempfile import NamedTemporaryFile
from alexandriabase import baseinjectorkeys
from tkgui.PluginManager import DocumentMenuAddition

DOCUMENT_PDF_PLUGIN_PRESENTER_KEY = Key('document_pdf_plugin_presenter')

class DocumentPdfMenuAdditionPresenter(object):
    '''
    classdocs
    '''

    @inject
    def __init__(self,
                 message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY,
                 file_provider: baseinjectorkeys.DOCUMENT_FILE_PROVIDER):
        '''
        Constructor
        '''
        self.message_broker = message_broker
        self.file_provider = file_provider
        self.view = None
        
    def generate_pdf(self):
        '''
        Generates the pdf as a temporary file. The caller needs to delete this file.
        '''
        file = NamedTemporaryFile(mode="wb", suffix="pdf", delete=False)
        try:
            file.write(self.file_provider.get_pdf(self.view.current_document))
            file.close()
            self.view.pdf_file = file.name
        except DocumentFileNotFound as exception:
            self.message_broker.send_message(
                Message(ERROR_MESSAGE,
                        message=_("Document %s not found" % exception.document_file_info),
                        messagetype='error'))

class DocumentPdfMenuAddition(DocumentMenuAddition):
    '''
    classdocs
    '''

    @inject
    def __init__(self,
                 presenter: DOCUMENT_PDF_PLUGIN_PRESENTER_KEY,
                 file_viewers: guiinjectorkeys.DOCUMENT_FILE_VIEWERS_KEY):
        '''
        Constructor
        '''
        self.presenter = presenter
        self.presenter.view = self
        self.file_viewer = file_viewers['pdf']
        
    def attach_to_window(self, parent_window):
        '''
        Interface method for plugins.
        
        This is a hackish implementation to place the command before the
        last menu item.
        '''
        # TODO: Show a wait warning while creating the pdf
        self.parent_window = parent_window
        parent_window.menubar.addmenuitem(
            _('Records'), 
            'command',
            before=_('Quit'),
            label=(_('Show as pdf')),
            command=self.presenter.generate_pdf)

    def get_current_document(self):
        return self.parent_window.entity
    
    def show_pdf(self, pdf_file):
        self.file_viewer.showFile(pdf_file)
        
    current_document = property(get_current_document)
    pdf_file = property(None, show_pdf)

class DocumentPdfPluginModule(Module):
    '''
    Rather complicated injector module that constructs the main
    windows of the application with dialogs and reference widgets.
    '''
    
    def configure(self, binder):
      
        binder.bind(DOCUMENT_PDF_PLUGIN_PRESENTER_KEY,
                    ClassProvider(DocumentPdfMenuAdditionPresenter), scope=singleton)
