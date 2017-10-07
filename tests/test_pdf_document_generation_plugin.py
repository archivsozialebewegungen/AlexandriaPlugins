'''
Created on 26.05.2016

@author: michael
'''
import os
from integration.baseintegrationtest import BaseIntegrationTest
from unittest.mock import MagicMock
from alexandriabase import baseinjectorkeys
from genericpath import isfile
from alexpresenters import PresentersModule
from alex_test_utils import TestEnvironment, MODE_FULL
from alexplugins.DocumentPdfPlugin import DocumentPdfPluginModule,\
    DOCUMENT_PDF_PLUGIN_PRESENTER_KEY

class DocumentPdfGenerationTest(BaseIntegrationTest):


    def setUp(self):
        super().setUp()
        self.injector = self.get_injector(PresentersModule(), DocumentPdfPluginModule())
        self.presenter = self.injector.get(DOCUMENT_PDF_PLUGIN_PRESENTER_KEY)
        self.document_service = self.injector.get(baseinjectorkeys.DOCUMENT_SERVICE_KEY)
        self.view = MagicMock()
        self.presenter.view = self.view;

    def setup_environment(self):
        '''
        You may overwrite this in your test class to receive the
        full integration test environment with data files
        '''
        return TestEnvironment(mode=MODE_FULL)

    def tearDown(self):
        try:
            os.remove(self.view.pdf_file)
        except:
            pass
        BaseIntegrationTest.tearDown(self)

    def test_pdf_generation(self):
        
        self.view.current_document = self.document_service.get_by_id(1)
        self.presenter.generate_pdf()
        self.assertTrue(isfile(self.view.pdf_file))
