'''
Created on 23.01.2017

@author: michael
'''
import unittest
from integration.baseintegrationtest import BaseIntegrationTest
from alexplugins.cdexporter.base import CDExporterBasePluginModule,\
    EXPORT_DATA_ASSEMBLER_KEY, ExportInfo
from alexandriabase.domain import AlexDate


class CDDataAssemblerTest(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        injector = self.get_injector(CDExporterBasePluginModule())
        self.cd_data_assembler = injector.get(EXPORT_DATA_ASSEMBLER_KEY)

    def checkSelection(self, export_info, doc_ids, event_ids):

        data = {}
        self.cd_data_assembler.export(export_info, data)

        self.assertTrue('documents' in data)
        self.assertEqual(len(doc_ids), len(data['documents']))
        self.assertTrue('events' in data)
        self.assertEqual(len(event_ids), len(data['events']))
        for document in data['documents']:
            self.assertTrue(document.id in doc_ids)
        for event in data['events']:
            self.assertTrue(event.id in event_ids)

    def testDateRange(self):
        
        export_info = ExportInfo()
        export_info.start_date = AlexDate(1950)
        export_info.end_date = AlexDate(1960, 2)
        export_info.location = None
        
        self.checkSelection(export_info, (4,), (1960013001,))
        
    def testLocation(self):

        export_info = ExportInfo()
        export_info.start_date = None
        export_info.end_date = None
        export_info.location = "1.1"

        self.checkSelection(export_info, (1, 4), (1940000001, 1960013001))        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()