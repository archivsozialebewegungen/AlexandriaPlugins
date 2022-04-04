'''
Created on 10.10.2016

@author: michael
'''
import unittest
from injector import Injector
from alex_test_utils import TestEnvironment, MODE_SIMPLE,\
    load_table_data
from alexandriabase import AlexBaseModule
from alexandriabase.daos import DaoModule
from alexplugins.systematic.tkgui import SystematicGuiPluginModule
from alexplugins.systematic import SYSTEMATIC_DAO_KEY, SYSTEMATIC_SERVICE_KEY,\
    SYSTEMATIC_PDF_GENERATION_SERVICE_KEY

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

        injector.get(SYSTEMATIC_DAO_KEY)    
        injector.get(SYSTEMATIC_SERVICE_KEY)    
        injector.get(SYSTEMATIC_PDF_GENERATION_SERVICE_KEY)    
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()