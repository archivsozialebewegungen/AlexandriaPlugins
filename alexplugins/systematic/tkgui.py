'''
Created on 05.11.2016

@author: michael
'''
from injector import inject, Key, ClassProvider, singleton, InstanceProvider
from tkgui import guiinjectorkeys
from alexpresenters.messagebroker import CONF_DOCUMENT_CHANGED, Message,\
    ERROR_MESSAGE, REQ_SAVE_CURRENT_DOCUMENT
from alexandriabase.domain import NoSuchNodeException
from tkgui.References import ReferencesWidgetFactory, ReferenceView, Action
from alexplugins.systematic import SYSTEMATIC_SERVICE_KEY,\
    SYSTEMATIC_PDF_GENERATION_SERVICE_KEY
from alexplugins.systematic.base import SystematicPoint,\
    SystematicBasePluginModule
from tkgui.components.alexwidgets import AlexLabel, AlexButton
from tkinter.constants import W
from tkgui.PluginManager import DocumentMenuAddition,\
    DocumentReferenceFactory
from tkgui.Dialogs import GenericFilterDialog, GenericTreeSelectionDialog
from alexpresenters.DialogPresenters import GenericTreeSelectionPresenter

SYSTEMATIC_POINT_SELECTION_PRESENTER_KEY = Key('systematic_point_selection_presenter')
SYSTEMATIC_POINT_SELECTION_DIALOG_KEY = Key('systematic_point_selection_dialog')

SYSTEMATIC_MENU_ADDITIONS_PRESENTER_KEY = Key('systematic_plugin_presenter')

DOCUMENT_SYSTEMATIC_REFERENCES_PRESENTER_KEY = Key('document_systematic_references_presenter')
DOCUMENT_SYSTEMATIC_REFERENCES_VIEW_CLASS_KEY = Key('document_systematic_references_view_class')

SYSTEMATIC_CHANGED = "systematic changed"

class SystematicDocumentFilterDialog(GenericFilterDialog):


    NO_SYSTEMATIC_POINT_SELECTED = _('No systematic point selected')
    
    @inject
    def __init__(self,
                 window_manager: guiinjectorkeys.WINDOW_MANAGER_KEY,
                 presenter: guiinjectorkeys.DOCUMENT_FILTER_DIALOG_PRESENTER_KEY,
                 systematic_dialog: SYSTEMATIC_POINT_SELECTION_DIALOG_KEY):
        super().__init__(window_manager, presenter)
        self.systematic_dialog = systematic_dialog

    def create_dialog(self):
        super().create_dialog()
        AlexLabel(self.interior, text=_("Signature:")).grid(row=3, column=0, sticky=W)
        self.systematic_button = AlexButton(self.interior, command=self._select_signature)
        self.systematic_button.set(self.NO_SYSTEMATIC_POINT_SELECTED)
        self.systematic_button.grid(row=3, column=1, sticky=W)
                   
    def _select_signature(self):
        self.systematic_dialog.activate(self._set_signature,
                                        label=_("Please select systematic point"))
    def _set_signature(self, value):
        if value is None:
            self.systematic_button.set(self.NO_SYSTEMATIC_POINT_SELECTED)
        else:
            self.systematic_button.set(value)
            
    def _get_signature(self):
        
        button_value = self.systematic_button.get()
        if "%s" % button_value == self.NO_SYSTEMATIC_POINT_SELECTED:
            return None
        else:
            return button_value
            
    def _clear_filter_form(self):
        super()._clear_filter_form()
        self.signature_label.set('')
    
    signature = property(_get_signature, _set_signature)

class DocumentSystematicReferencesPresenter:

    @inject
    def __init__(self,
                 message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY,
                 systematic_service: SYSTEMATIC_SERVICE_KEY):
        self.message_broker = message_broker
        self.message_broker.subscribe(self)
        self.systematic_service = systematic_service
        self.view = None # Will be initialized by the view itself
        
    def receive_message(self, message):
        if message.key == CONF_DOCUMENT_CHANGED:
            self.view.current_document = message.document
            self._load_systematic_items()
            
    def _load_systematic_items(self):
        if self.view.current_document == None:
            self.view.items = []
        else:
            try:
                self.view.items = self.systematic_service.\
                    fetch_systematic_entries_for_document(self.view.current_document)
            except NoSuchNodeException as exception:
                self.message_broker.send_message(
                    Message(
                        ERROR_MESSAGE, 
                        messagetype='error',
                        message=_('No systematic point %s' % exception.identifier)))
                self.view.items = []
        
    
    def add_new_systematic_point(self):
        
        if self.view.current_document is None:
            return
        
        systematic_point = self.view.new_systematic_point
        if systematic_point is None:
            return

        if self.view.current_document.id is None:
            self.message_broker.send_message(Message(REQ_SAVE_CURRENT_DOCUMENT))
            assert self.view.current_document.id is not None

        if self._systematic_point_is_already_joined(systematic_point):
            return

        self.systematic_service.add_systematic_entry_to_document(self.view.current_document, systematic_point)
        self._load_systematic_items()
        
    def _systematic_point_is_already_joined(self, systematic_point):
        for item in self.view.items:
            if item == systematic_point:
                return True
        return False
    
    def delete_selected_systematic_point(self):
        if not self.view.selected_item:
            return
        document = self.view.current_document
        if document:
            self.systematic_service.\
                remove_systematic_entry_from_document(document, self.view.selected_item)
        self._load_systematic_items()

class DocumentSystematicReferencesWidgetFactory(ReferencesWidgetFactory, DocumentReferenceFactory):
    
    @inject
    def __init__(self,
                 view_class: DOCUMENT_SYSTEMATIC_REFERENCES_VIEW_CLASS_KEY,
                 presenter: DOCUMENT_SYSTEMATIC_REFERENCES_PRESENTER_KEY,
                 systematic_point_dialog: SYSTEMATIC_POINT_SELECTION_DIALOG_KEY):
        super().__init__(view_class, presenter, systematic_point_dialog)
        
class DocumentSystematicReferenceView(ReferenceView):
    
    def __init__(self, parent, presenter, systematic_point_dialog):
        super().__init__(
            parent,
            presenter,
            _('Systematic'))
        self.current_document = None
        self.view = None
        self.new_systematic_point = None
        self.systematic_point_dialog = systematic_point_dialog
        self.add_button(Action(_('New'), self._select_a_new_systematic_point))
        self.add_button(Action(_('Delete'), self.presenter.delete_selected_systematic_point))
        
    def _select_a_new_systematic_point(self):
        
        return self.systematic_point_dialog.activate(self._add_a_new_systematic_point,
                                                     label=_('Please select a systematic point'))
        
    def _add_a_new_systematic_point(self, value):
        if value is not None:
            self.new_systematic_point = value
            self.presenter.add_new_systematic_point()
            self.new_systematic_point = None

class SystematicPointSelectionPresenter(GenericTreeSelectionPresenter):
    
    @inject
    def __init__(self,
                 systematic_service: SYSTEMATIC_SERVICE_KEY,
                 message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY):
        super().__init__()
        self.systematic_service = systematic_service
        self.message_broker = message_broker
        self.message_broker.subscribe(self)
    
    def set_tree(self):
        self._view.tree = self.systematic_service.get_systematic_tree()
        
    def receive_message(self, message):
        if message == SYSTEMATIC_CHANGED:
            self.set_tree()

class SystematicMenuAdditionsPresenter(object):
    '''
    classdocs
    '''

    @inject
    def __init__(self,
                 message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY,
                 systematic_service: SYSTEMATIC_SERVICE_KEY,
                 pdf_generation_service: SYSTEMATIC_PDF_GENERATION_SERVICE_KEY):
        '''
        Constructor
        '''
        self.view = None
        self.message_broker = message_broker
        self.systematic_service = systematic_service
        self.pdf_generation_service = pdf_generation_service
        
    def find_potential_child_ids(self):

        self.view.potential_child_ids = self.systematic_service.get_potential_new_child_identifier(self.view.working_entry)

    def create_new_entry_action(self):
        
        self.view.working_entry = SystematicPoint(self.view.new_child_id, _('No description'))
        
    def delete_entry_action(self):
        deletion_entry = self.view.working_entry
        children = self.systematic_service.get_children(deletion_entry.id)
        if len(children) != 0:
            self.show_message(_("Systematic entry with children may not be deleted"))
            return
        if self.systematic_service.next_sibling_exists(deletion_entry.id):
            self.show_message(_("Can't delete entry when sibling exists"))
            return
        if self.systematic_service.systematic_id_is_in_use(deletion_entry.id):
            self.show_message(_("Entry which is in use by documents may not be deleted"))
            return
        self.systematic_service.delete(deletion_entry)
        self.message_broker.send_message(Message(SYSTEMATIC_CHANGED))
    
    def save_working_entry_action(self):
        
        edit_entry = self.view.working_entry
        self.systematic_service.save(edit_entry)
        self.show_message("Systematic point %s saved!" % edit_entry)
        self.message_broker.send_message(Message(SYSTEMATIC_CHANGED))

    def export_as_pdf(self):
        
        export_file = self.view.pdf_file
        if export_file is None or len(export_file) == 0:
            return
        self.pdf_generation_service.generate_systematic_pdf(export_file)
        
    def show_message(self, message):
        
        self.message_broker.send_message(
            Message(
            ERROR_MESSAGE,
            message=message,
            messagetype='info'))

class SystematicMenuAdditions(DocumentMenuAddition):
    '''
    classdocs
    '''

    @inject
    def __init__(self,
                 presenter: SYSTEMATIC_MENU_ADDITIONS_PRESENTER_KEY,
                 systematic_dialog: SYSTEMATIC_POINT_SELECTION_DIALOG_KEY,
                 string_edit_dialog: guiinjectorkeys.GENERIC_STRING_EDIT_DIALOG_KEY,
                 string_selection_dialog: guiinjectorkeys.GENERIC_STRING_SELECTION_DIALOG_KEY,
                 file_selection_dialog: guiinjectorkeys.FILE_SELECTION_DIALOG_KEY):
        '''
        Constructor
        '''
        self.presenter = presenter
        self.presenter.view = self
        self.systematic_dialog = systematic_dialog
        self.string_edit_dialog = string_edit_dialog
        self.string_selection_dialog = string_selection_dialog
        self.file_selection_dialog = file_selection_dialog
        
        self.working_entry = None
        self.potential_child_ids = []
        self.new_child_id = None
        
    def attach_to_window(self, parent_window):
        
        self.parent_window = parent_window
        parent_window.menubar.addmenu(_('Systematic'), '')
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Create new entry'),
                            command=self._start_creation)
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Delete entry'),
                            command=self._get_deletion_node)
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Edit entry'),
                            command=self._get_edit_node)
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Export as pdf'),
                            command=self.presenter.export_as_pdf)

    def _start_creation(self):
        '''
        This gets a parent node for a new systematic point
        '''
        self.systematic_dialog.activate(self._get_parent_entry_callback, 
                                        label=_("Please select parent entry for new entry"))

    def _get_parent_entry_callback(self, parent_entry):
        if parent_entry is None:
            return
        
        self.working_entry = parent_entry
        self.presenter.find_potential_child_ids()
        if len(self.potential_child_ids) == 0:
            return
        if len(self.potential_child_ids) == 1:
            self._create_new_entry(self.potential_child_ids[0])
        else:
            self.string_selection_dialog.activate(
                self._create_new_entry,
                label=_('Please select which systematic\npoint you want to create'),
                choices=self.potential_child_ids)
            
    def _create_new_entry(self, entry_id):
        
        if entry_id is None:
            return
        self.new_child_id = self.potential_child_ids[0]
        self.presenter.create_new_entry_action()
        self.string_edit_dialog.activate(
            self._change_description,
            label=_("Please enter a description for %s:" % self.new_child_id)
        )
        
    def _get_deletion_node(self):
        
        self.systematic_dialog.activate(self._get_deletion_node_callback,
                                        label=_("Please select entry to delete"))

    def _get_deletion_node_callback(self, deletion_entry):
        if deletion_entry is None:
            return
        self.working_entry = deletion_entry
        self.presenter.delete_entry_action()
        self.working_entry = None

    def _get_edit_node(self):
        
        self.systematic_dialog.activate(self._get_edit_entry_callback, 
                                        label=_("Please select node to edit"))

    def _get_edit_entry_callback(self, edit_entry):
        if edit_entry is None:
            return
        self.working_entry = edit_entry
        self.string_edit_dialog.activate(
            self._change_description,
            label=_("Please change description for %s:") % edit_entry,
            initvalue = edit_entry.description )
        
    def _change_description(self, value):
        if value is None or self.working_entry.description == value:
            return
        self.working_entry.description = value
        self.presenter.save_working_entry_action()
        self.working_entry = None
            
    def get_pdf_file(self):
        return self.file_selection_dialog.activate(self.parent_window, new=True)

    pdf_file = property(get_pdf_file)

class SystematicPointSelectionDialog(GenericTreeSelectionDialog):
    
    @inject
    def __init__(self,
                 window_manager: guiinjectorkeys.WINDOW_MANAGER_KEY,
                 presenter: SYSTEMATIC_POINT_SELECTION_PRESENTER_KEY):
        super().__init__(window_manager, presenter)

class SystematicGuiPluginModule(SystematicBasePluginModule):
    '''
    Injector module to bind the plugin keys
    '''
    def configure(self, binder):
        
        super().configure(binder)

        binder.bind(SYSTEMATIC_POINT_SELECTION_DIALOG_KEY,
                    ClassProvider(SystematicPointSelectionDialog), scope=singleton)
        binder.bind(SYSTEMATIC_POINT_SELECTION_PRESENTER_KEY,
                    ClassProvider(SystematicPointSelectionPresenter), scope=singleton)
                            
        binder.bind(DOCUMENT_SYSTEMATIC_REFERENCES_PRESENTER_KEY,
                    ClassProvider(DocumentSystematicReferencesPresenter), scope=singleton)
        binder.bind(DOCUMENT_SYSTEMATIC_REFERENCES_VIEW_CLASS_KEY,
                    InstanceProvider(DocumentSystematicReferenceView), scope=singleton)

        binder.bind(SYSTEMATIC_MENU_ADDITIONS_PRESENTER_KEY,
                    ClassProvider(SystematicMenuAdditionsPresenter), scope=singleton)
        binder.bind(guiinjectorkeys.DOCUMENT_FILTER_DIALOG_KEY,
                    ClassProvider(SystematicDocumentFilterDialog), scope=singleton)

