'''
Created on 11.10.2015

@author: michael
'''
from sqlalchemy.sql.expression import select
import unittest

from alexandriabase.daos import DOCUMENT_TABLE, EventFilterExpressionBuilder
from daotests.test_base import DatabaseBaseTest
from alex_test_utils import load_table_data
from alexplugins.systematic.base import DocumentSystematicRelationsDao,\
    systematic_string_to_identifier, SystematicIdentifier, SystematicPoint
from alexandriabase.domain import AlexDate


class TestDocumentSystematicRelationsDao(DatabaseBaseTest):
    
    def setUp(self):
        super().setUp()
        load_table_data(['systematik', 'sverweis'], self.engine)
        self.dao = DocumentSystematicRelationsDao(self.engine, EventFilterExpressionBuilder())
        
    def tearDown(self):
        super().tearDown()
        

    def test_fetch_signature_for_document_id_I(self):
        '''
        Tests for existing signature
        '''

        signature = self.dao.fetch_signature_for_document_id(1)
        self.assertEqual(signature, systematic_string_to_identifier('1.1.I'))

    def test_fetch_signature_for_document_id_II(self):
        '''
        Tests for non existing signature
        '''

        signature = self.dao.fetch_signature_for_document_id(8)
        self.assertEqual(signature, None)

    def test_set_signature_for_document_id_I(self):
        '''
        Tests for existing signature
        '''
        systematic_node = SystematicPoint(SystematicIdentifier("1.2"), "desc")
        self.dao.set_signature_for_document_id(1, systematic_node)
        
        table = DOCUMENT_TABLE
        query = select([table.c.standort]).where(table.c.laufnr == 1)
        row = self.dao._get_exactly_one_row(query)
        self.assertEqual('1.2', row[table.c.standort])
        
        signature = self.dao.fetch_signature_for_document_id(1)
        self.assertEqual(signature, systematic_string_to_identifier('1.2'))

    def test_set_signature_for_document_id_II(self):
        '''
        Tests deleting signature
        '''
        self.dao.set_signature_for_document_id(1, None)
        signature = self.dao.fetch_signature_for_document_id(1)
        self.assertEqual(signature, None)

    def test_fetch_document_ids_for_systematic_id(self):
        
        systematik_id = SystematicIdentifier('1.1', 2, 1)
        result = self.dao.fetch_document_ids_for_systematic_id(systematik_id)
        self.assertEqual(len(result), 2)
        self.assertIn(1, result)
        self.assertIn(4, result)
        
        systematik_id = SystematicIdentifier('1.1', 0, 0)
        result = self.dao.fetch_document_ids_for_systematic_id(systematik_id)
        self.assertEqual(len(result), 0)

    def test_fetch_systematic_ids_for_document_id(self):
        systematik_id1 = SystematicIdentifier('1.1', 2, 1)
        systematik_id2 = SystematicIdentifier('1.2', 0, 0)
        
        id_list = self.dao.fetch_systematik_ids_for_document_id(1)
        self.assertEqual(len(id_list), 2)
        self.assertIn(systematik_id1, id_list)
        self.assertIn(systematik_id2, id_list)

        id_list = self.dao.fetch_systematik_ids_for_document_id(8)
        self.assertEqual(len(id_list), 0)
        
    def test_remove_systematic_id(self):
        systematik_id = SystematicIdentifier('1.2')
        document_id = 1
        id_list = self.dao.fetch_systematik_ids_for_document_id(document_id)
        self.assertEqual(len(id_list), 2)
        self.assertIn(systematik_id, id_list)
        self.dao.remove_systematik_document_relation(systematik_id, document_id)
        id_list = self.dao.fetch_systematik_ids_for_document_id(document_id)
        self.assertEqual(len(id_list), 1)
        self.assertNotIn(systematik_id, id_list)
        
    def test_add_systematic_id(self):
        systematik_id = SystematicIdentifier('2')
        document_id = 1
        id_list = self.dao.fetch_systematik_ids_for_document_id(document_id)
        self.assertEqual(len(id_list), 2)
        self.assertNotIn(systematik_id, id_list)
        self.dao.add_systematik_document_relation(systematik_id, document_id)
        id_list = self.dao.fetch_systematik_ids_for_document_id(document_id)
        self.assertEqual(len(id_list), 3)
        self.assertIn(systematik_id, id_list)

    def test_is_in_use_1(self):
        # Nowhere in use
        systematic_id = SystematicIdentifier('2', 1, 0)
        self.assertFalse(self.dao.systematic_id_is_in_use(systematic_id))

    def test_is_in_use_2(self):
        # Only in relations in use
        systematic_id = SystematicIdentifier('2', 0, 0)
        self.assertTrue(self.dao.systematic_id_is_in_use(systematic_id))

    def test_is_in_use_3(self):
        # Only in location in use
        systematic_id = SystematicIdentifier('1.1', 1, 0)
        self.assertTrue(self.dao.systematic_id_is_in_use(systematic_id))
        
    def test_fetch_document_ids_for_systematic_id_in_timerange(self):
        
        references = self.dao.fetch_document_ids_for_systematic_id_in_timerange(systematic_string_to_identifier("1.1.II-1"), AlexDate(1900), AlexDate(2020))
        print(references)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()