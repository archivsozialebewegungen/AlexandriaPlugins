'''
Created on 07.05.2016

@author: michael
'''
import unittest

from daotests.test_base import DatabaseBaseTest
from alex_test_utils import load_table_data
from alexplugins.systematic.base import SystematicDao,\
    SystematicPdfGenerationService


class TestSystematicPdfGenerationService(DatabaseBaseTest):


    def setUp(self):
        super().setUp()
        load_table_data(['systematik', 'sverweis'], self.engine)
        self.systematic_dao = SystematicDao(self.engine)
        self.service = SystematicPdfGenerationService(self.systematic_dao)


    def tearDown(self):
        pass


    def testSystematicGeneration(self):
        self.service.generate_systematic_pdf("/tmp/test.pdf")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()