'''
Created on 10.11.2016

@author: michael
'''
from tkinter.constants import LEFT

from injector import BoundKey, ClassProvider, singleton, inject
from tkgui.AlexWidgets import AlexLabel, AlexEntry, AlexDateEntry,\
    AlexText, AlexButton, AlexRadioGroup, AlexListBox
from tkgui import guiinjectorkeys
from alexandriabase.domain import AlexDate
from alexplugins import _
from alexplugins.cdexporter.base import GENERATOR_ENGINE_KEY, \
    ExportInfo, CDExporterBasePluginModule, MESSENGER_KEY,\
    load_export_info
from tkgui.PluginManager import EventMenuAddition
from tkinter import Label
from alexplugins.systematic.tkgui import SYSTEMATIC_POINT_SELECTION_DIALOG_KEY
from tkinter.filedialog import asksaveasfilename, askopenfilename
import datetime
from tkgui.guiinjectorkeys import WINDOW_MANAGER_KEY
from alexpresenters.DialogPresenters import AbstractInputDialogPresenter
from tkgui.Dialogs import AbstractInputDialog, Wizard
from alexandriabase import baseinjectorkeys
import re

CHRONO_DIALOG_KEY = BoundKey('chrono_dialog')
CHRONO_DIALOG_PRESENTER_KEY = BoundKey('chrono_dialog_presenter')

CD_EXPORTER_MENU_ADDITIONS_PRESENTER_KEY = BoundKey('cd_exporter_plugin_chrono_presenter')

EXPORT_INFO_WIZARD_KEY = BoundKey('export_wizard')
EXPORT_INFO_WIZARD_PRESENTER = BoundKey('export_info_wizard_presenter')

CD_EXPORTER_MENU_ADDITIONS_GENERIC_PRESENTER_KEY = BoundKey('cd_exporter_plugin_generic_presenter')

TEXT_GENERATOR_KEY = BoundKey('text_generator')

class ChronoInfo(object):
    '''
    Simple data object for generating ASB chronologies.
    '''
    
    def __init__(self):
        self.quarter = 0
        self.year = 0
        
    def __str__(self):
        
        return "%d. %s %d" % (self.quarter, 
                              _('Quarter'),
                              self.year)

class MessageBarMessenger():
    '''
    Messenger implementation that uses the tkgui message_broker
    '''
    
    @inject
    def __init__(self, message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY):
        
        self.message_broker = message_broker
        
    def show(self, message):
        '''
        The display method for messenger classes.
        '''
        
        self.message_broker.show_info(message)


class ChronoDialogPresenter(AbstractInputDialogPresenter):
    '''
    Presenter for the dialog that gets user input on which
    chronology to produce.
    '''
    
    def ok_action(self):
        chrono_info = ChronoInfo()
        chrono_info.quarter = self.view.quarter
        chrono_info.year = self.view.year
        self.view.return_value = chrono_info


class ChronoDialog(AbstractInputDialog):
    '''
    Dialog to get the user input on which chrono to produce.
    '''

    @inject
    def __init__(self,
                 window_manager: guiinjectorkeys.WINDOW_MANAGER_KEY,
                 presenter: CHRONO_DIALOG_PRESENTER_KEY):
        self.quarters = ("%s 1" % _('Quarter'),
                         "%s 2" % _('Quarter'),
                         "%s 3" % _('Quarter'),
                         "%s 4" % _('Quarter')
                         )
        self.current_quarter = 1
        self.quarter_select = None
        self.year_entry = None
        
        super().__init__(window_manager, presenter)
        
    def create_dialog(self):
        super().create_dialog()
        
        AlexButton(self.buttons_frame, text=_("Create chronology"),
                   command=self.presenter.ok_action).pack(side=LEFT)
        AlexButton(self.buttons_frame, text=_("Cancel"),
                   command=self.presenter.cancel_action).pack(side=LEFT)
        
        self.quarter_select = AlexRadioGroup(self.interior,
                                             title=_('Quarter'),
                                             choices=self.quarters)
        self.quarter_select.pack()

        AlexLabel(self.interior,
                  text=_(_("Year"))).pack(side=LEFT, padx=10, pady=10)
        self.year_entry = AlexEntry(self.interior)
        self.year_entry.pack(side=LEFT, padx=10, pady=10)

    def _get_quarter(self):
        return self.quarter_select.get() + 1
    
    def _get_year(self):
        try:
            year = int(self.year_entry.get())
        except ValueError:
            year = 0
        return year
    
    quarter = property(_get_quarter)
    year = property(_get_year)
    
class ExportInfoWizardPresenter(AbstractInputDialogPresenter):
    
    def __init__(self):
        self.view = None
    
    def ok_action(self):
        
        self.view.return_value = self.view.export_info

class ExportInfoWizard(Wizard):

    ADD_SIGNATURE = _("Add signature")    
    NO_IMAGE_SELECTED = _('No title image selected')
    
    @inject
    def __init__(self,
                 window_manager: guiinjectorkeys.WINDOW_MANAGER_KEY,
                 presenter: EXPORT_INFO_WIZARD_PRESENTER,
                 signature_dialog: SYSTEMATIC_POINT_SELECTION_DIALOG_KEY):
        
        super().__init__(window_manager, presenter, number_of_pages=6, geometry="500x200")
        
        self.signature_dialog = signature_dialog

    def create_dialog(self):
        
        super().create_dialog()        
        
        # Wizard page 1
        Label(self.pages[0], text=_("Start creating a CD")).pack(padx=5, pady=5)

        Label(self.pages[0], text=_("Enter a name for the CD:")).pack()
        self.name_entry = AlexEntry(self.pages[0])
        self.name_entry.pack()
        
        # Wizard page 2
        Label(self.pages[1], text=_("Start page as markdown:")).pack(padx=5, pady=5)
        self.start_page_entry = AlexText(self.pages[1])
        self.start_page_entry.pack()
        
        # Wizard page 3
        Label(self.pages[2], text=_("Impressum as markdown:")).pack(padx=5, pady=5)
        self.imprint_entry = AlexText(self.pages[2])
        self.imprint_entry.pack()
        
        # Wizard page 4
        Label(self.pages[3], text=_("Please enter a data range:")).pack(padx=5, pady=5)
        
        self.start_date_entry = AlexDateEntry(self.pages[3])
        self.start_date_entry.label = _("Enter start date:")
        self.start_date_entry.pack()
        
        self.end_date_entry = AlexDateEntry(self.pages[3])
        self.end_date_entry.label = _("Enter end date:")
        self.end_date_entry.pack()
        
        # Wizard page 5
        Label(self.pages[4], text=_("Please select one or more signatures")).pack(padx=5, pady=5)
        self.signature_button = AlexButton(
            self.pages[4], 
            command=lambda: self.signature_dialog.activate(self._signature_callback, label=self.ADD_SIGNATURE))
        self.signature_button.pack()
        self.signature_list = AlexListBox(self.pages[4], height=2)
        self.signature_list.pack()
        
        # Wizard page 6
        Label(self.pages[5], text=_("Please add additional dokument ids (seperated by a colon)")).pack(padx=5, pady=5)
        self.additional_documents_entry = AlexText(self.pages[5])
        self.additional_documents_entry.pack()

    def config_dialog(self, export_info=None):
        
        self.export_info = export_info
        
    def _signature_callback(self, signature):
        
        if signature is not None:
            self.signature_list.append_item(signature)

    def _get_export_info(self):
        
        export_info = ExportInfo()
        export_info.cd_name = self.name_entry.get()
        export_info.start_date = self.start_date_entry.get()
        export_info.end_date = self.end_date_entry.get()
        export_info.signature = self.signature_list.items
        if len(export_info.signature) == 0:
            export_info.signature = None
        for doc_id_string in re.split("\s*:\s*", self.additional_documents_entry.get()):
            try:
                doc_id = int(doc_id_string)
                export_info.additional_document_ids.append(doc_id)
            except:
                pass
                
        export_info.pagecontent['startpage'] = self.start_page_entry.get()
        export_info.pagecontent['imprint'] = self.imprint_entry.get()
        return export_info
    
    def _set_export_info(self, export_info):
        
        self.name_entry.set(export_info.cd_name)
        self.start_date_entry.set(export_info.start_date)
        self.end_date_entry.set(export_info.end_date)
        self.signature = export_info.signature
        self.start_image = export_info.start_image
        self.start_page_entry.set(export_info.pagecontent['startpage'])
        self.imprint_entry.set(export_info.pagecontent['imprint'])

    def _get_signature(self):
        
        signature = self.signature_list.get_items()
        
        if len(signature) == 0:
            return None
                
        return signature
     
    
    def _set_signature(self, signature):
        
        self.signature_button.set(self.ADD_SIGNATURE)
        if signature is not None:
            self.signature_list.set_items(signature)
        else:
            self.signature_list.set_items([])
            
    signature = property(_get_signature, _set_signature)
    export_info = property(_get_export_info, _set_export_info)

class ChronoTextGenerator:
    
    def run(self, export_info):
        
        pagecontent = {}
        pagecontent['startpage'] = """
Auszug aus der Alexandria Datenbank
===================================

Stand der Datenbank: %s
-----------------------

Dieser Datenträger enthält die Dokumente, die für 
den Zeitraum zwischen dem %s und dem %s relevant sind.
""" % (datetime.date.today().strftime('%d. %B %Y.'),
       export_info.start_date,
       export_info.end_date)

        pagecontent['imprint'] = """
Impressum
=========

Diese CD wird herausgegeben von:

     Archiv Soziale Bewegungen in Baden e.V.
     Adlerstr.12
     79098 Freiburg
     
"""
        return pagecontent
        

class CDExporterMenuAdditionsPresenter(object):
    '''
    Presenter for creating CDs from alexandria data.
    Defines callbacks for menu entries.
    '''
    
    start_date_calc = [[4, -1], [7, -1], [10, -1], [1, 0]]
    end_date_calc = [[31, 3], [30, 6], [30, 9], [31, 12]]
    
    @inject
    def __init__(self,
                 message_broker: guiinjectorkeys.MESSAGE_BROKER_KEY,
                 generation_engine: GENERATOR_ENGINE_KEY,
                 text_generator: TEXT_GENERATOR_KEY,
                 window_manager: WINDOW_MANAGER_KEY):
        self.view = None
        self.message_broker = message_broker
        self.generation_engine = generation_engine
        self.text_generator = text_generator
        self.window_manager = window_manager
    
    def export_chronology(self):
        '''
        Callback to create a ASB chronology. It gets the
        necessary information from the view (that activates
        a dialog). Then converts the information to default
        exporter information and then starts the exporter.
        '''
    
        chrono_info = self.view.chrono_info
        if not chrono_info:
            self.message_broker.show_error("Chronology generation aborted.")
            return
        if chrono_info.year < 1500 or chrono_info.year > 2500:
            self.message_broker.show_error("Chronology generation aborted. Invalid year.")
            return
        
        export_info = self._chrono_info_to_export_info(chrono_info)
        export_info.pagecontent = self.text_generator.run(export_info)
        self.view.export_info = export_info

        self._start_export(export_info)            
    
    def save_cdd_file(self):
        
        self.view.export_info.save_to_file(self.view.cdd_file)

    def load_cdd_file(self):
        
        self.view.export_info = load_export_info(self.view.cdd_file)
        
                
    def edit_cd_definition(self):

        file_name = self.view.existing_export_info_file
        if not file_name:
            return

        self.view.export_info = load_export_info(file_name)
        
        self.create_cd_definition()
                 
    def create_cd_from_definition(self):             

        file_name = self.view.existing_export_info_file
        if not file_name:
            return


        export_info = load_export_info(file_name)
        self.view.export_info = export_info
        # Don't use the view here - it starts a dialog
        self._start_export(export_info)        

    def _start_export(self, export_info):
                 
        self.window_manager.run_in_thread(target=self.generation_engine.run, args=(export_info,))

    def _chrono_info_to_export_info(self, chrono_info):
        
        export_info = ExportInfo()
        calc_info = self.start_date_calc[chrono_info.quarter-1]
        export_info.start_date = AlexDate(chrono_info.year + calc_info[1],
                                          calc_info[0],
                                          1)
        calc_info = self.end_date_calc[chrono_info.quarter-1]
        export_info.end_date = AlexDate(chrono_info.year,
                                        calc_info[1],
                                        calc_info[0])
        export_info.cd_name = "CHRONO_%d_%d" % (chrono_info.year, chrono_info.quarter)
        return export_info
        
class CDExporterMenuAdditions(EventMenuAddition):
    '''
    This is the main plugin class for the CD exporter
    that defines export menu entries for CDs.
    
    This is also gets injected into the presenters as
    view. The view classes then may get the necessary
    information from this class.
    '''

    @inject
    def __init__(self,
                 presenter: CD_EXPORTER_MENU_ADDITIONS_PRESENTER_KEY,
                 chrono_dialog: CHRONO_DIALOG_KEY,
                 export_info_dialog: EXPORT_INFO_WIZARD_KEY):

        self.presenter = presenter
        self.presenter.view = self
        
        self.chrono_dialog = chrono_dialog
        self.export_info_dialog = export_info_dialog
        
        self.parent_window = None
        
        self.chrono_info = None
        self.cdd_file = None
        self.export_info = ExportInfo()
        
    def attach_to_window(self, parent_window):
        '''
        Hook method that the window calls when initializing
        its plugins
        '''

        self.parent_window = parent_window
        menubar = parent_window.menubar
        
        if not menubar.hasmenu(_('Export')):
            menubar.addmenu(_('Export'), '')
            
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Export chronology'),
                            command=self.start_chrono_export)
            
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Create CD definition'),
                            command=self.create_cd_definition)
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Edit CD definition'),
                            command=self.edit_cd_definition)
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Create CD from definition'),
                            command=self.presenter.create_cd_from_definition)

    def start_chrono_export(self):
        
        self.chrono_dialog.activate(self.chrono_export_callback)
    
    def chrono_export_callback(self, chrono_info):
        
        self.chrono_info = chrono_info
        self.presenter.export_chronology()
    
    def create_cd_definition(self):
        
        self.export_info_dialog.activate(self.save_export_info_callback, export_info=self.export_info)
        
    def edit_cd_definition(self):
        
        self.cdd_file = askopenfilename(filetypes=[(_("CD definition file"), ".cdd")])
        
        if self.cdd_file is None:
            return
        self.presenter.load_cdd_file()
        
        self.export_info_dialog.activate(self.save_export_info_callback, export_info=self.export_info)

    def save_export_info_callback(self, export_info):
        
        self.export_info = export_info
        
        if export_info is None:
            return
        
        self.cdd_file = asksaveasfilename(defaultextension='.cdd', 
                                          filetypes=[(_("CD definition file"), ".cdd")])
        if self.cdd_file:
            self.presenter.save_cdd_file()
        
    def _get_new_export_info_file(self):
        
        return asksaveasfilename(defaultextension='.cdd', 
                                 filetypes=[(_("CD definition file"), ".cdd")])

    def _get_existing_export_info_file(self):
        
        return askopenfilename(filetypes=[(_("CD definition file"), ".cdd")])

    new_export_info_file = property(_get_new_export_info_file)
    existing_export_info_file = property(_get_existing_export_info_file)
    
class CDExporterGuiPluginModule(CDExporterBasePluginModule):
    '''
    The injector module class for dependency injection.
    '''
    
    def configure(self, binder):
      
        super().configure(binder)
        
        binder.bind(MESSENGER_KEY,
                    ClassProvider(MessageBarMessenger), scope=singleton)

        binder.bind(CHRONO_DIALOG_PRESENTER_KEY,
                    ClassProvider(ChronoDialogPresenter), scope=singleton)
        binder.bind(CHRONO_DIALOG_KEY,
                    ClassProvider(ChronoDialog), scope=singleton)
        binder.bind(CD_EXPORTER_MENU_ADDITIONS_PRESENTER_KEY,
                    ClassProvider(CDExporterMenuAdditionsPresenter), scope=singleton)
        binder.bind(TEXT_GENERATOR_KEY, ClassProvider(ChronoTextGenerator), scope=singleton)

        binder.bind(EXPORT_INFO_WIZARD_KEY,
                    ClassProvider(ExportInfoWizard), scope=singleton)
        binder.bind(EXPORT_INFO_WIZARD_PRESENTER,
                    ClassProvider(ExportInfoWizardPresenter), scope=singleton)
               
