'''
Created on 10.10.2016

@author: michael
'''
import unittest
from injector import Injector
from alex_test_utils import TestEnvironment, MODE_SIMPLE
from alexandriabase import AlexBaseModule
from alexandriabase.daos import DaoModule
from alexplugins.systematic.tkgui import SystematicGuiPluginModule
from alexplugins.systematic.base import SystematicDao, SystematicService
from tests.test_pdf_generation_service import TestSystematicPdfGenerationService

class TestDaoModuleConfiguration(unittest.TestCase):
    
    def setUp(self):
        self.env = TestEnvironment(mode=MODE_SIMPLE)

    def tearDown(self):
        self.env.cleanup()
            
    def test_configuration(self):
        
        injector = Injector([
                        AlexBaseModule(),
                        DaoModule(),
                        SystematicGuiPluginModule()
                         ])

        injector.get(SystematicDao)    
        injector.get(SystematicService)    
        injector.get(TestSystematicPdfGenerationService)    
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()