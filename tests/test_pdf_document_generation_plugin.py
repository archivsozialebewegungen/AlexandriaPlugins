'''
Created on 26.05.2016

@author: michael
'''
import os
from integration.baseintegrationtest import BaseIntegrationTest
from unittest.mock import MagicMock
from genericpath import isfile
from alexpresenters.Module import PresentersModule
from alex_test_utils import TestEnvironment, MODE_FULL
from alexandriabase.services import DocumentService
from alexplugins.DocumentPdfPlugin import DocumentPdfMenuAdditionPresenter

class DocumentPdfGenerationTest(BaseIntegrationTest):


    def setUp(self):
        super().setUp()
        self.injector = self.get_injector(PresentersModule())
        self.presenter = self.injector.get(DocumentPdfMenuAdditionPresenter)
        self.document_service = self.injector.get(DocumentService)
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
