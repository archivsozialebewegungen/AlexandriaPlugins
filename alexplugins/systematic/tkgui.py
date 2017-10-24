'''
Created on 05.11.2016

@author: michael
'''
from injector import inject, Key, ClassProvider, singleton, InstanceProvider
from tkgui import guiinjectorkeys
from alexpresenters.messagebroker import CONF_DOCUMENT_CHANGED, Message,\
    ERROR_MESSAGE, REQ_SAVE_CURRENT_DOCUMENT
from alexandriabase.domain import NoSuchNodeException
from tkgui.components.references.basereference import ReferencesWidgetFactory,\
    ReferenceView, Action
from alexplugins.systematic import SYSTEMATIC_SERVICE_KEY,\
    SYSTEMATIC_PDF_GENERATION_SERVICE_KEY
from alexpresenters.dialogs.generic_tree_selection_presenter import GenericTreeSelectionPresenter
from alexplugins.systematic.base import SystematicPoint,\
    SystematicBasePluginModule
from tkgui.dialogs.generic_tree_selection_dialog import GenericTreeSelectionDialog
from tkgui.dialogs.filterdialogs import GenericFilterDialog
from tkgui.components.alexwidgets import AlexLabel, AlexButton
from tkinter.constants import W
from tkgui.PluginManager import DocumentMenuAddition,\
    DocumentReferenceFactory

SYSTEMATIC_POINT_SELECTION_PRESENTER_KEY = Key('systematic_point_selection_presenter')
SYSTEMATIC_POINT_SELECTION_DIALOG_KEY = Key('systematic_point_selection_dialog')

SYSTEMATIC_MENU_ADDITIONS_PRESENTER_KEY = Key('systematic_plugin_presenter')

DOCUMENT_SYSTEMATIC_REFERENCES_PRESENTER_KEY = Key('document_systematic_references_presenter')
DOCUMENT_SYSTEMATIC_REFERENCES_VIEW_CLASS_KEY = Key('document_systematic_references_view_class')

SYSTEMATIC_CHANGED = "systematic changed"

class SystematicDocumentFilterDialog(GenericFilterDialog):

    @inject
    def __init__(self,
                 presenter: guiinjectorkeys.DOCUMENT_FILTER_DIALOG_PRESENTER_KEY,
                 systematic_dialog: SYSTEMATIC_POINT_SELECTION_DIALOG_KEY):
        super().__init__(presenter)
        self.systematic_dialog = systematic_dialog

    def _init_dialog(self, master):
        self.master = master
        if self.dialog != None:
            return
        super()._init_dialog(master)
        AlexLabel(self.dialog.interior(), text=_("Signature:")).grid(row=3, column=0, sticky=W)
        self.signature_label = AlexLabel(self.dialog.interior(), text='')
        self.signature_label.grid(row=3, column=1, sticky=W)
        self.systematic_button = AlexButton(self.dialog.interior(), command=self._get_signature)
        self.systematic_button.set(_("Select"))
        self.systematic_button.grid(row=3, column=2, sticky=W)
                   
    def _get_signature(self):
        result = self.systematic_dialog.activate(self.master)
        if result != None:
            self.signature_label.set("%s" % result.id)
        
    def _clear_filter_form(self):
        super()._clear_filter_form()
        self.signature_label.set('')
    
    signature = property(lambda self: self.signature_label.get())



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
        self.systematic_point_dialog = systematic_point_dialog
        self.add_button(Action(_('New'), self.presenter.add_new_systematic_point))
        self.add_button(Action(_('Delete'), self.presenter.delete_selected_systematic_point))
        
    def _select_a_new_systematic_point(self):
        
        return self.systematic_point_dialog.activate(self)
        
    new_systematic_point = property(_select_a_new_systematic_point)

class SystematicPointSelectionPresenter(GenericTreeSelectionPresenter):
    
    @inject
    def __init__(self,
                 systematic_service: SYSTEMATIC_SERVICE_KEY,
                 message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY):
        super().__init__()
        self.systematic_service = systematic_service
        self.message_broker = message_broker
        self.message_broker.subscribe(self)
        
    def get_tree(self):
        self.view.tree = self.systematic_service.get_systematic_tree()
        
    def receive_message(self, message):
        if message == SYSTEMATIC_CHANGED:
            self.get_tree()

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
        
    def create_new_entry(self):
        parent_node = self.view.parent_node
        if not parent_node:
            self.show_message(_("No parent entry selected"))
            return
        self.view.potential_child_ids = self.systematic_service.get_potential_new_child_identifier(parent_node)
        new_entry = self.view.new_entry
        if new_entry is None:
            self.show_message(_("Creating new entry canceled or not possible."))
            return
        self.systematic_service.save(new_entry)
        self.show_message(_("Systematic point %s saved!") % new_entry)
        self.message_broker.send_message(Message(SYSTEMATIC_CHANGED))
        
            
    def delete_node(self):
        deletion_node = self.view.deletion_node
        if not deletion_node:
            self.show_message(_("No entry to delete selected"))
            return
        children = self.systematic_service.get_children(deletion_node.id)
        if len(children) != 0:
            self.show_message(_("Systematic entry with children may not be deleted"))
            return
        if self.systematic_service.next_sibling_exists(deletion_node.id):
            self.show_message(_("Can't delete entry when sibling exists"))
            return
        if self.systematic_service.systematic_id_is_in_use(deletion_node.id):
            self.show_message(_("Entry which is in use by documents may not be deleted"))
            return
        self.systematic_service.delete(deletion_node)
        self.message_broker.send_message(Message(SYSTEMATIC_CHANGED))
    
    def edit_node(self):
        edit_node = self.view.edit_node
        if edit_node is None:
            self.show_message(_("Nothing to save"))
            return
        self.systematic_service.save(edit_node.entity)
        self.show_message("Systematic point %s saved!" % edit_node)
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
        
    def attach_to_window(self, parent_window):
        
        self.parent_window = parent_window
        parent_window.menubar.addmenu(_('Systematic'), '')
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Create new entry'),
                            command=self.presenter.create_new_entry)
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Delete entry'),
                            command=self.presenter.delete_node)
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Edit entry'),
                            command=self.presenter.edit_node)
        parent_window.menubar.addmenuitem(_('Systematic'), 'command', '',
                            label=_('Export as pdf'),
                            command=self.presenter.export_as_pdf)

    def get_parent_node(self):
        
        return self.systematic_dialog.activate(self.parent_window, _("Please select parent entry for new entry"))

    def get_deletion_node(self):
        
        return self.systematic_dialog.activate(self.parent_window, _("Please select entry to delete"))

    def get_edit_node(self):
        
        node = self.systematic_dialog.activate(self.parent_window, _("Please select node to edit"))
        if node is None:
            return None
        new_description = self.string_edit_dialog.activate(
            self.parent_window,
            label=_("Please change description for %s:") % node,
            initvalue = node.entity.description )
        if new_description is None or node.entity.description == new_description:
            return None
        node.entity.description = new_description
        return node
    
    def create_new_entry(self, potential_child_ids):
        self.new_entry = None
        if len(potential_child_ids) == 0:
            return
        if len(potential_child_ids) == 1:
            new_id = potential_child_ids[0]
        else: 
            new_id = self.string_selection_dialog.activate(
                self.parent_window,
                label=_('Please select which systematic\npoint you want to create'),
                choices=potential_child_ids)
        if new_id is None:
            return
        description = self.string_edit_dialog.activate(
            self.parent_window,
            label=_("Please enter a description for %s:" % new_id)
            )
        if description == '' or description is None:
            return
        self.new_entry = SystematicPoint(new_id, description)
            
    def get_pdf_file(self):
        return self.file_selection_dialog.activate(self.parent_window, new=True)

    potential_child_ids = property(None, create_new_entry)
    parent_node = property(get_parent_node)
    deletion_node = property(get_deletion_node)
    edit_node = property(get_edit_node)
    pdf_file = property(get_pdf_file)

class SystematicPointSelectionDialog(GenericTreeSelectionDialog):
    
    @inject
    def __init__(self, presenter: SYSTEMATIC_POINT_SELECTION_PRESENTER_KEY):
        super().__init__(presenter)

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

