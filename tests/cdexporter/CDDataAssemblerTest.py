'''
Created on 23.01.2017

@author: michael
'''
import unittest
from integration.baseintegrationtest import BaseIntegrationTest
from alexplugins.cdexporter.base import CDExporterBasePluginModule,\
    JSON_EXPORTER_KEY, ExportInfo
from alexandriabase.domain import AlexDate
from injector import Module, ClassProvider, singleton
from tkgui import guiinjectorkeys
from alexpresenters.messagebroker import MessageBroker


class CDDataAssemblerTest(BaseIntegrationTest):

    def testName(self):
        
        injector = self.get_injector(CDExporterBasePluginModule())
        cd_data_assembler = injector.get(JSON_EXPORTER_KEY)
        data = {}
        export_info = ExportInfo()
        export_info.start_date = AlexDate(1950)
        export_info.end_date = AlexDate(1960, 2)
        export_info.location = None
        cd_data_assembler.export(export_info, data)
        
        self.assertTrue('documents' in data)
        self.assertTrue('events' in data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()