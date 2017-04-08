'''
Created on 10.11.2016

@author: michael
'''
from tkinter.constants import LEFT
from threading import Thread
import Pmw

from injector import Key, ClassProvider, singleton, inject, provides
from tkgui.dialogs.abstractdialog import AbstractInputDialog
from tkgui.components.alexwidgets import AlexLabel, AlexEntry, AlexDateEntry,\
    AlexText, AlexButton
from tkgui import guiinjectorkeys
from alexpresenters.dialogs.abstractdialogpresenter import AbstractInputDialogPresenter
from alexandriabase.domain import AlexDate
from alexplugins.cdexporter.base import GENERATOR_ENGINE_KEY, \
    ExportInfo, CDExporterBasePluginModule, CD_EXPORT_CONFIG_KEY, MESSENGER_KEY,\
    AlexEncoder, export_info_object_hook, TEXT_GENERATOR_KEY, load_export_info
from tkgui.PluginManager import DocumentMenuAddition, EventMenuAddition
from tkgui.dialogs.wizard import Wizard
from tkgui.guiinjectorkeys import DOCUMENT_WINDOW_KEY
from tkinter import Label, Frame
from alexplugins.systematic.tkgui import SYSTEMATIC_POINT_SELECTION_DIALOG_KEY
from tkinter.filedialog import asksaveasfilename, askopenfilename
import json
import datetime

CHRONO_DIALOG_KEY = Key('chrono_dialog')
CHRONO_DIALOG_PRESENTER_KEY = Key('chrono_dialog_presenter')

CD_EXPORTER_MENU_ADDITIONS_PRESENTER_KEY = Key('cd_exporter_plugin_chrono_presenter')

EXPORT_INFO_DIALOG_KEY = Key('export_wizard')
EXPORT_INFO_WIZARD_CLASS_KEY = Key('export_info_wizard_class')
EXPORT_INFO_WIZARD_PRESENTER = Key('export_info_wizard_presenter')

CD_EXPORTER_MENU_ADDITIONS_GENERIC_PRESENTER_KEY = Key('cd_exporter_plugin_generic_presenter')

class ChronoInfo(object):
    '''
    Simple data object for generating ASB chronologies.
    '''
    
    def __init__(self):
        self.quarter = 0
        self.year = 0

class MessageBarMessenger():
    '''
    Messenger implementation that uses the tkgui message_broker
    '''
    
    @inject(message_broker=guiinjectorkeys.MESSAGE_BROKER_KEY)
    def __init__(self, message_broker):
        
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
    
    def assemble_return_value(self):
        chrono_info = ChronoInfo()
        chrono_info.quarter = self.view.quarter
        chrono_info.year = self.view.year
        self.view.return_value = chrono_info


class ChronoDialog(AbstractInputDialog):
    '''
    Dialog to get the user input on which chrono to produce.
    '''

    @inject(presenter=CHRONO_DIALOG_PRESENTER_KEY)
    def __init__(self, presenter):
        self.quarters = ("%s 1" % _('Quarter'),
                         "%s 2" % _('Quarter'),
                         "%s 3" % _('Quarter'),
                         "%s 4" % _('Quarter')
                         )
        self.current_quarter = 1
        self.quarter_select = None
        self.year_entry = None
        
        super().__init__(presenter)
        
    def _init_dialog(self, master):
        # We want to reuse the filter dialog if it already exists
        if self.dialog != None:
            return
        # pylint: disable=no-member
        self.dialog = Pmw.Dialog(  # @UndefinedVariable
            buttons=(_("Create chronology"), _("Cancel")))
        
        self.quarter_select = Pmw.RadioSelect(  # @UndefinedVariable
                self.dialog.interior(),
                command=self.set_current_quarter,
                labelpos = 'w',
                label_text = _('Quarter'),
        )
        self.quarter_select.pack(fill='x', 
                                 padx=10, 
                                 pady=10)

        # Add some buttons to the horizontal RadioSelect.
        for quarter in self.quarters:
            self.quarter_select.add(quarter)
        self.quarter_select.invoke(self.quarters[self.current_quarter - 1])
        AlexLabel(self.dialog.interior(),
                  text=_(_("Year"))).pack(side=LEFT, padx=10, pady=10)
        self.year_entry = AlexEntry(self.dialog.interior())
        self.year_entry.pack(side=LEFT, padx=10, pady=10)


    def set_current_quarter(self, label):
        '''
        Callback for the quarter buttons
        with a sort of hackish implementation
        to get the quarter from the button label.
        '''
        
        self.current_quarter = int(label[-1:])
        
    def _get_quarter(self):
        return self.current_quarter
    
    def _get_year(self):
        try:
            year = int(self.year_entry.get())
        except ValueError:
            year = 0
        return year
    
    quarter = property(_get_quarter)
    year = property(_get_year)
    
class ExportInfoDialog:
    
    @inject(wizard_class=EXPORT_INFO_WIZARD_CLASS_KEY,
            wizard_presenter=EXPORT_INFO_WIZARD_PRESENTER,
            location_selection_dialog=SYSTEMATIC_POINT_SELECTION_DIALOG_KEY)
    def __init__(self, wizard_class, wizard_presenter, location_selection_dialog):
        
        self.wizard_class = wizard_class
        self.wizard_presenter = wizard_presenter
        self.location_selection_dialog = location_selection_dialog
        
    def activate(self, master, export_info):
        
        self.wizard_class(master, export_info, self.wizard_presenter, self.location_selection_dialog)
        return self.wizard_presenter.export_info

class ExportInfoWizardPresenter:
    
    def __init__(self):
        self.view = None
        self.export_info = None
    
    def close(self):
        self.export_info = self.view.export_info
        self.view.close()

class ExportInfoWizard(Wizard):
    
    def __init__(self, master, export_info, presenter, location_dialog):
        super().__init__(master, presenter, number_of_pages=3, geometry="400x150")
        
        self.location_dialog = location_dialog
        
        # Wizard page 1
        Label(self.pages[0], text=_("Start creating a CD")).pack(padx=5, pady=5)

        input_frame = Frame(self.pages[0])
        Label(input_frame, text=_("Enter a name for the CD:")).grid(row=0, column=0)
        self.name_entry = AlexEntry(input_frame)
        self.name_entry.grid(row=0, column=1)
        Label(input_frame, text=_("Enter a title:")).grid(row=1, column=0)
        self.title_entry = AlexEntry(input_frame)
        self.title_entry.grid(row=1, column=1)
        Label(input_frame, text=_("Enter a subtitle:")).grid(row=2, column=0)
        self.subtitle_entry = AlexEntry(input_frame)
        self.subtitle_entry.grid(row=2, column=1)
        input_frame.pack()
        
        # Wizard page 2
        Label(self.pages[1], text=_("Please enter a data range:")).pack(padx=5, pady=5)
        
        self.start_date_entry = AlexDateEntry(self.pages[1])
        self.start_date_entry.label = _("Enter start date:")
        self.start_date_entry.pack()
        
        self.end_date_entry = AlexDateEntry(self.pages[1])
        self.end_date_entry.label = _("Enter end date:")
        self.end_date_entry.pack()
        
        # Wizard page 2
        Label(self.pages[2], text=_("Please select a location")).pack(padx=5, pady=5)
        self.location = None
        self.location_button = AlexButton(self.pages[2], command=self._select_location)
        self.location_button.set(_("No location selected"))
        self.location_button.pack()
        
        self.export_info = export_info
        
        self.wait_window(self)

    def _select_location(self):

        new_location = self.location_dialog.activate(self)
        if new_location:
            self.location = new_location
        self._configure_location_button()       
        
    def _configure_location_button(self):    
        if not self.location:
            self.location_button.set(_("No location selected"))
        else:
            self.location_button.set("%s" % self.location)
    
    def _get_export_info(self):
        export_info = ExportInfo()
        export_info.cd_name = self.name_entry.get()
        export_info.start_date = self.start_date_entry.get()
        export_info.end_date = self.end_date_entry.get()
        export_info.location = self.location
        export_info.texts['title'] = self.title_entry.get()
        export_info.texts['subtitle'] = self.subtitle_entry.get()
        return export_info
    
    def _set_export_info(self, export_info):
        
        self.start_date_entry.set(export_info.start_date)
        self.end_date_entry.set(export_info.end_date)
        self.location = export_info.location
        self._configure_location_button()
        self.name_entry.set(export_info.cd_name)
        self.title_entry.set(export_info.texts['title'])
        self.subtitle_entry.set(export_info.texts['subtitle'])

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

        pagecontent['impressum'] = """
Impressum
=========

Diese CD wird herausgegeben vom Archiv Soziale Bewegungen in Baden
"""
        return pagecontent
        

class ChronoCDExporterMenuAdditionsPresenter(object):
    '''
    Presenter for creating CDs from alexandria data.
    Defines callbacks for menu entries.
    '''
    
    start_date_calc = [[4, -1], [7, -1], [10, -1], [1, 0]]
    end_date_calc = [[31, 3], [30, 6], [30, 9], [31, 12]]
    
    @inject(message_broker=guiinjectorkeys.MESSAGE_BROKER_KEY,
            generation_engine=GENERATOR_ENGINE_KEY,
            text_generator=TEXT_GENERATOR_KEY)
    def __init__(self, message_broker, generation_engine, text_generator):
        self.view = None
        self.message_broker = message_broker
        self.generation_engine = generation_engine
        self.text_generator = text_generator
    
    def export_chronology(self):
        '''
        Callback to create a ASB chronology. It gets the
        necessary information from the view (that activates
        a dialog). Then converts the information to default
        exporter information and then starts the exporter.
        '''
    
        chrono_info = self.view.chrono_info
        if not chrono_info:
            self.message_broker.send_error("Chronology generation aborted.")
            return
        if chrono_info.year < 1500 or chrono_info.year > 2500:
            self.message_broker.send_error("Chronology generation aborted. Invalid year.")
            return
        
        export_info = self._chrono_info_to_export_info(chrono_info)
        export_info.pagecontent = self.text_generator.run(export_info)
        self.view.export_info = export_info

        self._start_export(export_info)            
    
    def create_cd_definition(self):
        
        export_info = self.view.export_info
        if not export_info:
            return
        
        file_name = self.view.new_export_info_file
        if not file_name:
            return
        
        export_info.save_to_file(file_name)
        
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
                 
        export_thread = Thread(target=self.generation_engine.run, args=(export_info,))
        export_thread.start()

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

    @inject(presenter=CD_EXPORTER_MENU_ADDITIONS_PRESENTER_KEY,
            chrono_dialog=CHRONO_DIALOG_KEY,
            export_info_dialog=EXPORT_INFO_DIALOG_KEY)
    def __init__(self, presenter, chrono_dialog, export_info_dialog):

        self.presenter = presenter
        self.presenter.view = self
        
        self.chrono_dialog = chrono_dialog
        self.export_info_dialog = export_info_dialog
        
        self.parent_window = None
        
        self._export_info = ExportInfo()
        
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
                            command=self.presenter.export_chronology)
            
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Create CD definition'),
                            command=self.presenter.create_cd_definition)
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Edit CD definition'),
                            command=self.presenter.edit_cd_definition)
        menubar.addmenuitem(_('Export'), 'command', '',
                            label=_('Create CD from definition'),
                            command=self.presenter.create_cd_from_definition)

    def _get_chrono_info(self):
        
        return self.chrono_dialog.activate(self.parent_window)
    
    def _set_export_info(self, export_info):
        
        self._export_info = export_info
    
    def _get_export_info(self):
        
        self._export_info = self.export_info_dialog.activate(self.parent_window, self._export_info)
        return self._export_info
    
    def _get_new_export_info_file(self):
        
        return asksaveasfilename(defaultextension='.cdd', 
                                 filetypes=[(_("CD definition file"), ".cdd")])

    def _get_existing_export_info_file(self):
        
        return askopenfilename(filetypes=[(_("CD definition file"), ".cdd")])

    chrono_info = property(_get_chrono_info)
    export_info = property(_get_export_info, _set_export_info)
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
                    ClassProvider(ChronoCDExporterMenuAdditionsPresenter), scope=singleton)
        binder.bind(TEXT_GENERATOR_KEY, ClassProvider(ChronoTextGenerator), scope=singleton)

        binder.bind(EXPORT_INFO_DIALOG_KEY,
                    ClassProvider(ExportInfoDialog), scope=singleton)
        binder.bind(EXPORT_INFO_WIZARD_PRESENTER,
                    ClassProvider(ExportInfoWizardPresenter), scope=singleton)
               
    @provides(EXPORT_INFO_WIZARD_CLASS_KEY)
    def getExportInfoWizardClass(self):
        
        return ExportInfoWizard
    