'''
Created on 13.12.2015

@author: michael
'''
from alexandriabase.domain import AlexDate
from tkgui.mainwindows.BaseWindow import BaseWindow
from acceptance.AcceptanceTestUtils import BaseAcceptanceTest, AcceptanceTestRunner,\
    set_date, set_date_range
from tkgui.mainwindows import EventWindow
import os
from alexplugins.cdexporter.tkgui import CHRONO_DIALOG_KEY

class PluginFunctionalityTest(BaseAcceptanceTest):

    def __init__(self):
        super().__init__(additional_modules=['alexplugins.systematic.tkgui',
                                             'alexplugins.cdexporter.tkgui'])
        self.event_window_menubar = self.event_window.menubar
        self.document_window_menubar = self.document_window.menubar

    def test_suite(self):

        # Navigation
        print("\nChecking navigation")
        print("===================")
        self.click_on_export_menu()
        # Quit
        print("\nChecking quit")
        print("=============")

        self.check_quit_works()
        self.success = True
    
    def click_on_export_menu(self):
        
        print("Checking export menu exists...", end="")
        if not self.event_window_menubar.hasmenu(_('Export')):
            raise Exception("No export menu entry!")
        print("OK")
        
        

    def check_chrono_export(self):
        print("Checking exporting chronology works...", end='')
        dialog = self.event_window.dialogs[CHRONO_DIALOG_KEY]

        self.start_dialog(self.event_window_presenter.toggle_filter)
        dialog.earliest_date = AlexDate(1961, 1, 1)
        self.close_dialog(dialog)
        
        self.assert_that_event_is(1961050101)
        self.event_window_presenter.goto_first()
        self.assert_that_event_is(1961050101)

        # Turn filtering off
        self.event_window_presenter.toggle_filter()

        self.assert_that_event_is(1961050101)
        self.event_window_presenter.goto_first()
        self.assert_that_event_is(1940000001)

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