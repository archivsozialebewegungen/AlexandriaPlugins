'''
Created on 15.01.2017

@author: michael
'''
import unittest
from tempfile import NamedTemporaryFile
from alexplugins.cdexporter.tkgui import ChronoCDExporterMenuAdditionsPresenter
from alexpresenters.messagebroker import MessageBroker
from unittest.mock import MagicMock
from alexplugins.cdexporter.base import GenerationEngine, ExportInfo
from alexandriabase.domain import AlexDate
import os
from alexplugins.systematic.base import SystematicPoint, SystematicIdentifier
from alex_test_utils import create_temporary_test_file_name


class MenuAdditionsPresenterTest(unittest.TestCase):

    def setUp(self):

        self.export_info = ExportInfo()
        self.export_info = ExportInfo()
        self.export_info.cd_name = "TEST_CD"
        self.export_info.start_date = AlexDate(1973, 5, 1)
        self.export_info.end_date = AlexDate(1974, 5, 1)
        self.export_info.location_id = SystematicPoint(
            SystematicIdentifier("1.2.3", 4, 5),
            "dummy description")
        
        self.export_info_json = '{%s, %s, %s, %s}' % (
            '"cd_name": "TEST_CD"',
            '"end_date": {"_day": 1, "_month": 5, "_year": 1974}',
            '"location_id": {%s, %s}' % (
                '"description": "dummy description"',
                '"id": {"node_id": "1.2.3", "roman": 4, "subfolder": 5}'),
            '"start_date": {"_day": 1, "_month": 5, "_year": 1973}')
        
        
        self.message_broker = MessageBroker()
        self.generation_engine = MagicMock(spec=GenerationEngine)
        self.presenter = ChronoCDExporterMenuAdditionsPresenter(
            self.message_broker,
            self.generation_engine)

        self.presenter.view = MagicMock()

    def tearDown(self):
        
        try:
            os.unlink(self.presenter.view.existing_export_info_file)
        except:
            pass
        
        try:
            os.unlink(self.presenter.view.new_export_info_file)
        except:
            pass
    

    def testCreateExportInfo(self):
        
        self.presenter.view = MagicMock()
        self.presenter.view.export_info = self.export_info
        self.presenter.view.new_export_info_file = create_temporary_test_file_name()
        
        self.presenter.view = self.presenter.view
        
        self.presenter.create_cd_definition()
        
        self.assertDefinitionFile(self.presenter.view.new_export_info_file,
                                  self.export_info_json)
        
    def testEditExportInfo(self):
        
        self.presenter.view = MagicMock()
        self.presenter.view.export_info = ExportInfo()
        self.presenter.view.existing_export_info_file = create_temporary_test_file_name()
        self.presenter.view.new_export_info_file = create_temporary_test_file_name()
        
        file = open(self.presenter.view.existing_export_info_file, "w")
        file.write(self.export_info_json)
        file.close()
        
        self.presenter.edit_cd_definition()
        
        self.assertDefinitionFile(self.presenter.view.new_export_info_file,
                                  self.export_info_json)
        
    def assertDefinitionFile(self, file_name, json):

        file = open(file_name, "r")
        definition = file.read()
        file.close()
        
        self.assertEqual(definition, json)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()