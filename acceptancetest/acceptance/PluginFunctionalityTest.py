'''
Created on 13.12.2015

@author: michael
'''
from acceptance.AcceptanceTestUtils import BaseAcceptanceTest, AcceptanceTestRunner
from alexplugins.cdexporter.tkgui import ExportInfoWizard, ChronoDialog
from alexplugins import _
from alexplugins.cdexporter.base import CD_EXPORT_CONFIG_KEY
from tkgui.WindowManager import WindowManager

class PluginFunctionalityTest(BaseAcceptanceTest):

    def __init__(self):
        super().__init__(additional_modules=['alexplugins.systematic.tkgui',
                                             'alexplugins.cdexporter.tkgui'])
        self.event_window_menubar = self.event_window.menubar
        self.document_window_menubar = self.document_window.menubar
        config = self.injector.get(CD_EXPORT_CONFIG_KEY)
        config.cdexportdir = self.env.tmpdir.name
        config.genisoimage = '/bin/true'

    def test_suite(self):

        # Navigation
        print("\nChecking CD export")
        print("==================")
        self.check_export_menu_exists()
        #self.check_chrono_export()
        #self.check_create_cd_definition()
        
        # Quit
        print("\nChecking quit")
        print("=============")

        self.check_quit_works()
        self.success = True
    
    def check_export_menu_exists(self):
        
        print("Checking export menu exists...", end="")
        if not self.event_window_menubar.hasmenu(_('Export')):
            raise Exception("No export menu entry!")
        print("OK")
        
        

    def check_chrono_export(self):
        print("Checking exporting chronology works...", end='')
        dialog = self.injector.get(ChronoDialog)
        
        self.start_dialog(self.event_window_menubar.get_callback(_('Export'), _('Export chronology')))
        dialog.current_quarter = 3
        dialog.year_entry.set('1960')
        self.close_dialog(dialog)

        print("OK")

    def check_create_cd_definition(self):
        print("Checking creation of cd defininition...", end="")
        wizard = self.injector.get(ExportInfoWizard)
        
        window_manager = self.injector.get(WindowManager)
        self.wait()
        window_manager.run_in_thread(self.event_window_menubar.get_callback(_('Export'), _('Create CD definition')))
        #self.start_dialog(self.event_window_menubar.get_callback(_('Export'), _('Create CD definition')))
        self.wait()
        
        wizard.name_entry.set("TESTCD")
        self.wait()
        wizard._next_page()
        self.wait()
        
        #wizard._next_page()
        #wizard._next_page()
        #wizard._next_page()
        
        print("OK")
        
    def check_quit_works(self):
        print("Checking quit works...", end='')
        self.event_window_presenter.quit()
        print("OK")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    test = PluginFunctionalityTest()
    test_runner = AcceptanceTestRunner(test)
    test_runner.run()