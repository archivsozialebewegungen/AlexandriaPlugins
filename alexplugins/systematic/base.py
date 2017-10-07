'''
Created on 05.11.2016

@author: michael
'''
import re

from injector import inject, Module, ClassProvider, singleton
from sqlalchemy.sql.schema import Table, Column, ForeignKey,\
    ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.sql.expression import select, delete, insert, update, and_
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import Integer, String
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.flowables import PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.paragraph import Paragraph
from alexandriabase import baseinjectorkeys
from alexandriabase.base_exceptions import DataError
from alexandriabase.daos.basedao import GenericDao
from alexandriabase.daos.metadata import ALEXANDRIA_METADATA, DOCUMENT_TABLE
from alexandriabase.domain import Tree, NoSuchNodeException
from alexplugins.systematic import ROMAN_NUMERALS, SYSTEMATIC_DAO_KEY,\
    DOCUMENT_SYSTEMATIC_RELATIONS_DAO_KEY, SYSTEMATIC_SERVICE_KEY,\
    SYSTEMATIC_PDF_GENERATION_SERVICE_KEY

SYSTEMATIC_TABLE = Table(
    'systematik', ALEXANDRIA_METADATA,
    Column('sort', Integer),
    Column('punkt', String),
    Column('roemisch', Integer),
    Column('sub', Integer),
    Column('beschreibung', String),
    Column('textsort', String))

DOCUMENT_SYSTEMATIC_REFERENCE_TABLE = Table(
    'sverweis',
    ALEXANDRIA_METADATA,
    Column('systematik', String),
    Column('roemisch', Integer),
    Column('sub', Integer),
    Column('hauptnr', Integer, ForeignKey('dokument.hauptnr')),
    ForeignKeyConstraint(['systematik', 'roemisch', 'sub'], 
                         ['systematik.punkt', 'systematik.roemisch', 'systematik.sub']),
    UniqueConstraint('systematik', 'roemisch', 'sub', 'hauptnr'))

def systematic_string_to_identifier(raw_systematic_id):
    '''
    Creates a systematic identifier from an identifier string (as stored in database)
    '''
    if not raw_systematic_id:
        return None
    systematic_re = re.compile(r"([0-9.]*\d)(\.([IVXLCM]+))?(-(\d+))?")
    matcher = systematic_re.match(raw_systematic_id)
    if not matcher:
        raise DataError("%s is not a valid systematic id!" % raw_systematic_id)
    point = matcher.group(1)
    roman = matcher.group(3)
    if not roman:
        roman = 0
    else:
        roman = ROMAN_NUMERALS.index(roman)
    subfolder = matcher.group(5)
    if not subfolder:
        subfolder = 0
    else:
        subfolder = int(subfolder)
    return SystematicIdentifier(point, roman, subfolder)

class SystematicIdentifier:
    ''' The systematic is a hierarchical tree with, alas,
    complicated ordering. It consists of a numerical hierarchy,
    for example 5.3.1, followed by a roman numeral (optional)
    and a subfolder id (also optional). A full node identifier
    looks like thus: 5.3.1.IV-7.
    
    For historical reasons there are also identifiers that
    are missing the roman numeral but have a subfolder.
    '''

    separator = "."

    def __init__(self, node_id, roman=0, subfolder=0):
        self.node_id = node_id
        self.roman = roman
        self.subfolder = subfolder

    def _get_parent_identifier(self):
        '''
        Determines the node identifier of the parent node.
        Throws an exception if this is called on the root
        node.
        '''
        if self.subfolder:
            return SystematicIdentifier(self.node_id, self.roman)
        if self.roman:
            return SystematicIdentifier(self.node_id)

        if self.node_id is None:
            return None

        node_points = self.node_id.split(self.separator)
        if len(node_points) == 1:
            return SystematicIdentifier(None)
        parent_id = self.separator.join(node_points[:-1])
        return SystematicIdentifier(parent_id)

    def get_next_sibling_identifier(self):
        '''
        Determines the next sibling for a systematic identifier.
        
        For a subfolder, this will be a subfolder, for a roman
        entry a roman entry and in other cases a simple node
        '''
        if self.subfolder:
            return SystematicIdentifier(self.node_id, self.roman, self.subfolder + 1)
        if self.roman:
            return SystematicIdentifier(self.node_id, self.roman + 1)
        node_points = self.node_id.split(self.separator)
        if len(node_points) == 1:
            return SystematicIdentifier("%d" % (int(node_points[0]) + 1))
        return SystematicIdentifier(
            "%s.%d" % 
            (self.separator.join(node_points[:-1]), int(node_points[-1]) + 1))

    def __eq__(self, other):
        return other != None and \
            self.node_id == other.node_id and \
            self.roman == other.roman and \
            self.subfolder == other.subfolder

    def split_node_ids(self):
        '''
        Helper method to split the nodes in the node id
        into an array.
        '''
        if self.node_id is None:
            return []
        else:
            return self.node_id.split(self.separator)

    def _compare_node_ids(self, other):
        '''
        Helper method. Returns -1, when self.node_id < other.node_id,
        1, when self.node_id > other.node_id and 0 when
        self.node_id == other.node_id
        '''

        if self.node_id == other.node_id:
            return 0

        self_node_ids = self.split_node_ids()
        other_node_ids = other.split_node_ids()

        self_length = len(self_node_ids)
        other_length = len(other_node_ids)

        if self_length > other_length:
            length = other_length
        else:
            length = self_length

        for i in range(length):
            self_id = int(self_node_ids[i])
            other_id = int(other_node_ids[i])
            if self_id < other_id:
                return -1
            if self_id > other_id:
                return 1

        if self_length < other_length:
            return -1
        else:
            return 1

    def _compare_roman_ids(self, other):
        '''
        Comparison helper method. Compares the roman part of the
        id. Returns -1, when self is smaller, 1, when roman is smaller
        and 0 if they are equal.
        '''

        if self.roman == other.roman:
            return 0

        if self.roman and not other.roman:
            return 1
        if other.roman and not self.roman:
            return -1

        if self.roman < other.roman:
            return -1
        else:
            return 1



    def __lt__(self, other):
        # pylint: disable=too-many-return-statements
        if other is None:
            raise Exception("Invalid comparison with None type.")
        if self.__eq__(other):
            return False

        node_comparison_result = self._compare_node_ids(other)
        if node_comparison_result == -1:
            return True
        if node_comparison_result == 1:
            return False

        roman_comparison_result = self._compare_roman_ids(other)
        if roman_comparison_result == -1:
            return True
        if roman_comparison_result == 1:
            return False

        # Node id and roman number are identical
        if self.subfolder and not other.subfolder:
            return False
        if other.subfolder and not self.subfolder:
            return True

        # Both None has already been handled by equaliy check above
        return self.subfolder < other.subfolder

    def __str__(self):
        if self.node_id is None:
            return "Root node!"
        if self.subfolder:
            if self.roman:
                return "%s.%s-%s" % (self.node_id,
                                     ROMAN_NUMERALS[self.roman],
                                     self.subfolder)
            else:
                return "%s-%s" % (self.node_id,
                                  self.subfolder)
        if self.roman:
            return "%s.%s" % (self.node_id, ROMAN_NUMERALS[self.roman])
        return self.node_id

    def __gt__(self, other):
        return not self.__eq__(other) and not self.__lt__(other)

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __hash__(self):
        return self.node_id.__hash__() + \
            self.roman.__hash__() + \
            self.subfolder.__hash__()

    parent_id = property(_get_parent_identifier)
    
class SystematicPoint:
    '''
    Element of the systematic node with references to the
    children and the parent.
    '''

    def __init__(self, identifier, description):
        # pylint: disable=invalid-name
        self.id = identifier
        self.description = description

    def __hash__(self):
        return self.id.__hash__()

    def __str__(self):
        if self.id.node_id:
            return "%s: %s" % (self.id, self.description)
        else:
            return self.description

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        if other is None:
            return False
        return self.id == other.id

    def __gt__(self, other):
        return self.id > other.id

    def __le__(self, other):
        return self.id <= other.id

    def __ge__(self, other):
        return self.id >= other.id

    parent_id = property(lambda self: self.id.parent_id)

class SystematicDao(GenericDao):
    '''
    Dao for the systematic tree.
    '''

    @inject
    def __init__(self, db_engine: baseinjectorkeys.DB_ENGINE_KEY):
        super().__init__(db_engine)
        self.cache = None
        self.table = SYSTEMATIC_TABLE

    def get_tree(self):
        '''
        Returns the complete systematic tree.
        '''
        if not self.cache:
            self.cache = self._load_tree()
        return self.cache
    
    def _load_tree(self):
        
        entity_list = []
        query = select([self.table])
        
        result = self._get_connection().execute(query)
        for row in result.fetchall():
            node_id = row[self.table.c.punkt]
            roman = row[self.table.c.roemisch]
            subfolder = row[self.table.c.sub]
            identifier = SystematicIdentifier(node_id, roman, subfolder)
            description = row[self.table.c.beschreibung]
            entity_list.append(SystematicPoint(identifier, description))
        result.close()

        # Adding virtual root node
        entity_list.append(
            SystematicPoint(SystematicIdentifier(None), 
                            _("Archiv soziale Bewegungen")))
        return Tree(entity_list)
    
    def get_by_id(self, identifier):
        '''
        Gets a systematic point entity
        
        Throws a NoSuchSystematicPointException if the node is not found.
        '''
        
        node = self.get_node(identifier)
        return node.entity
    
    def get_children(self, identifier):
        
        node = self.get_node(identifier)
        return node.children
    
    def get_node(self, identifier):
        '''
        Returns a systematic tree node.
        
        Throws a NoSuchSystematicPointException if the node is not found.
        '''
        if not self.cache:
            self.get_tree()
            
        return self.cache.get_by_id(identifier)

    def delete(self, identifier):
        '''
        Deletes the identifier from the database and cleans up the cache.
        '''
        query = delete(self.table).where(self._where_clause_for_identifier(identifier))
        self.connection.execute(query)
        self.cache = None
            
    def save(self, systematic_point):
        '''
        Saves the systematic_point and rebuilds the cache.
        '''
        if self._need_insert(systematic_point):
            self._insert(systematic_point)
        else:
            self._update(systematic_point)
        self.cache = None
        
    def _need_insert(self, systematic_point):
        try:
            self.get_node(systematic_point.id)
        except NoSuchNodeException:
            return True
        return False
        
    def _insert(self, systematic_point):
        identifier = systematic_point.id
        query = insert(self.table).values(punkt=identifier.node_id,
                                          roemisch=identifier.roman,
                                          sub=identifier.subfolder,
                                          beschreibung=systematic_point.description)
        self._get_connection().execute(query)
            
    def _update(self, systematic_point):
        query = update(self.table)\
            .values(beschreibung=systematic_point.description)\
            .where(self._where_clause_for_identifier(systematic_point.id))
        self._get_connection().execute(query)
        
    def _where_clause_for_identifier(self, identifier):
        
        return and_(self.table.c.punkt == identifier.node_id,
                    self.table.c.roemisch == identifier.roman,
                    self.table.c.sub == identifier.subfolder)


class DocumentSystematicRelationsDao(GenericDao):
    '''
    Handles the document to systematic relations
    '''
    
    @inject
    def __init__(self, db_engine: baseinjectorkeys.DB_ENGINE_KEY):
        super().__init__(db_engine)
        self.dsref_table = DOCUMENT_SYSTEMATIC_REFERENCE_TABLE
        self.doc_table = DOCUMENT_TABLE
        
    def fetch_document_ids_for_systematic_id(self, systematic_id):
        '''
        Does what the method name says.
        '''
        where_clause = self._create_systematic_reference_where_clause(systematic_id)
        query = select([self.dsref_table.c.hauptnr]).where(where_clause)  
        result = self._get_connection().execute(query)
        return [row[self.dsref_table.c.hauptnr] for row in result.fetchall()]
    
    def systematic_id_is_in_use(self, systematic_id):
        '''
        Checks if the systematic id is used by a document, either
        as a reference or as the documents location
        '''
        where_clause = self._create_systematic_reference_where_clause(systematic_id)
        query = select([func.count(self.dsref_table.c.hauptnr)]).where(where_clause)
        number_of_relations = self._get_exactly_one_row(query)[0]
        if number_of_relations > 0:
            return True
        where_clause = self.doc_table.c.standort == "%s" % systematic_id
        query = select([func.count(self.doc_table.c.hauptnr)]).where(where_clause)
        number_of_relations = self._get_exactly_one_row(query)[0]
        return number_of_relations > 0
        
    def _create_systematic_reference_where_clause(self, systematic_id):
        where_clause = self.dsref_table.c.systematik == systematic_id.node_id  
        where_clause = and_(self.dsref_table.c.roemisch == systematic_id.roman, where_clause)  
        where_clause = and_(self.dsref_table.c.sub == systematic_id.subfolder, where_clause)
        return where_clause  
    
    def fetch_signature_for_document_id(self, document_id):
        '''
        Does what the method name says.
        '''
        query = select([self.doc_table.c.standort]).\
            where(self.doc_table.c.laufnr == document_id)
        row = self._get_exactly_one_row(query)   
        if row[self.doc_table.c.standort] is None:
            return None
        else:
            return systematic_string_to_identifier(row[self.doc_table.c.standort])
        
    def set_signature_for_document_id(self, document_id, systematic_node):
        '''
        Does what the method name says.
        '''
        if systematic_node is None:
            value = None
        else:
            value = "%s" % systematic_node.id
        query = update(self.doc_table).values(
            standort=value).where(self.doc_table.c.laufnr == document_id)
        self.connection.execute(query)
        
    def fetch_systematik_ids_for_document_id(self, document_id):
        '''
        Does what the method name says.
        '''
        query = select([self.dsref_table]).\
            where(self.dsref_table.c.hauptnr == document_id)  
        result = self._get_connection().execute(query)
        systematic_ids = []
        for row in result.fetchall():
            systematic_ids.append(SystematicIdentifier(
                row[self.dsref_table.c.systematik],  
                row[self.dsref_table.c.roemisch],  
                row[self.dsref_table.c.sub]))  
        return systematic_ids
    
    def remove_systematik_document_relation(self, systematik_id, document_id):
        '''
        Does what the method name says.
        '''
        where_condition = and_(
            self.dsref_table.c.systematik == systematik_id.node_id,  
            self.dsref_table.c.roemisch == systematik_id.roman,  
            self.dsref_table.c.sub == systematik_id.subfolder,  
            self.dsref_table.c.hauptnr == document_id)  
        delete_statement = delete(self.dsref_table).where(where_condition)
        self._get_connection().execute(delete_statement)
        
    def add_systematik_document_relation(self, systematik_id, document_id):
        '''
        Does what the method name says.
        '''
        insert_statement = insert(self.dsref_table).\
            values(systematik=systematik_id.node_id,
                   roemisch=systematik_id.roman,
                   sub=systematik_id.subfolder,
                   hauptnr=document_id)
        self._get_connection().execute(insert_statement)

class QualifiedSystematicPoint(SystematicPoint):
    '''
    Subclass of systematic node used in conjecture with a document.
    This type of node knows, if it describes the physical place where
    the document resides or if it is just attributed to a systematic
    node.
    '''
    
    def __init__(self, systematic_point, is_physical_node=False):
        '''
        Generates a qualified node from a plain node.
        '''
        # pylint: disable=super-init-not-called
        self.id = systematic_point.id
        self.description = systematic_point.description
        self.is_physical_node = is_physical_node
        
    def __str__(self):
        if self.is_physical_node:
            return "%s*: %s" % (self.id, self.description)
        else:
            return super().__str__()        

class SystematicService:
    '''
    Service to handle the archive systematic, i.e. a tree of categories,
    where documents may be attached to. It is a hybrid concept that on
    the one hand describes the physical location of a document, on the
    other hand adds it to a sort of thesaurus.
    
    This is a bit of a hybrid, because sometimes it returns SystematicPoints,
    sometimes QualifiedSystematicNodes. The last is always the case, if
    a method has a document context. Perhaps this should be split up into
    two different services.
    '''
    # pylint: disable=invalid-name
    @inject
    def __init__(self,
                 systematic_dao: SYSTEMATIC_DAO_KEY,
                 document_dao: baseinjectorkeys.DOCUMENT_DAO_KEY,
                references_dao: DOCUMENT_SYSTEMATIC_RELATIONS_DAO_KEY):
        self.systematic_dao = systematic_dao
        self.document_dao = document_dao
        self.references_dao = references_dao
        
    def fetch_systematic_entries_for_document(self, document):
        '''
        Fetches all systematic entries for a document. The information
        resides in the document table and also in a joined table. The
        method distinguishes between physical systematic point and
        attached systematic points. In other words: It returns a
        list of QualifiedSystematicNodes.
        '''
        if document is None or document.id is None:
            return []
        systematic_entries = []
        signature = self.references_dao.fetch_signature_for_document_id(document.id)
        if signature:
            systematic_entry = QualifiedSystematicPoint(
                self._fetch_systematic_entry_for_id(signature), 
                True)
            systematic_entries.append(systematic_entry)
        for systematic_id in self.references_dao.fetch_systematik_ids_for_document_id(document.id):
            systematic_entries.append(QualifiedSystematicPoint(
                self.systematic_dao.get_by_id(systematic_id),
                False))
        return systematic_entries
    
    def get_children(self, identifier):
        
        return self.systematic_dao.get_children(identifier)
    
    def add_systematic_entry_to_document(self, document, systematic_node):
        '''
        Adds a systematic entry to a document. If the document already
        has a signature, it will added as just attributed entry, otherwise
        it becomes the signature of the document.
        '''
        signature = self.references_dao.fetch_signature_for_document_id(document.id)
        if signature:
            self._add_systematic_relation(document, systematic_node)
        else:
            self._add_signature(document, systematic_node)
            
    def _add_systematic_relation(self, document, systematic_node):
        '''
        Adds node as attributed systematic entry.
        '''
        self.references_dao.add_systematik_document_relation(
            systematic_node.id,
            document.id)
    
    def _add_signature(self, document, systematic_node):
        '''
        Adds node as signature.
        '''
        self.references_dao.set_signature_for_document_id(
            document.id,
            systematic_node)
        
    def get_potential_new_child_identifier(self, systematic_node):
        '''
        Determines a list of possible SystematicIdentiers where this node
        is the parent.
        '''
        # pylint: disable=no-self-use
        identifier = systematic_node.id
        if identifier.subfolder != 0:
            return [] # Subfolders may not have children
        
        children = self.get_children(systematic_node.id)
        if len(children) == 0:
            if identifier.roman != 0:
                return [SystematicIdentifier(identifier.node_id, identifier.roman, 1)]
            else:
                return [SystematicIdentifier("%s.1" % identifier.node_id),
                        SystematicIdentifier(identifier.node_id, 1)]
        else:
            last_child = children[-1].id
            return [last_child.get_next_sibling_identifier()]
        
        
    def remove_systematic_entry_from_document(self, document, qualified_systematic_entry):
        '''
        Does what the name says.
        '''
        if qualified_systematic_entry.is_physical_node:
            self._delete_location_from_document(document)
        else:
            self._delete_systematic_entry_from_relations(document, qualified_systematic_entry)
            
    def _delete_location_from_document(self, document):
        '''
        Removes signature from document.
        '''
        document.standort = None
        self.references_dao.set_signature_for_document_id(
            document.id,
            None)
        
    def _delete_systematic_entry_from_relations(self, document, qualified_systematic_entry):
        '''
        Removes attributed systematic point from document.
        '''
        self.references_dao.remove_systematik_document_relation(
            qualified_systematic_entry.id,
            document.id)

    def _fetch_systematic_entry_for_id_string(self, id_as_string):
        '''
        Normally the id of a systematic entry is an object. But this
        object has a string representation that might be used instead.
        '''
        systematic_id = systematic_string_to_identifier(id_as_string)
        return self.systematic_dao.get_node(systematic_id)

    def _fetch_systematic_entry_for_id(self, identifier):
        '''
        This is the normal fetch method using an identifier object.
        '''
        return self.systematic_dao.get_by_id(identifier)
    
    def get_systematic_tree(self):
        '''
        Returns all the systematic nodes in form of a tree.
        '''
        return self.systematic_dao.get_tree()

    def save(self, systematic_node):
        '''
        Creates or updates a systematic systematic_point
        '''
        self.systematic_dao.save(systematic_node)

    def systematic_id_is_in_use(self, systematic_id):
        '''
        Checks if a systematic id is in use for a document
        '''
        return self.references_dao.systematic_id_is_in_use(systematic_id)

    def next_sibling_exists(self, systematic_id):
        '''
        Checks if the next sibling already exists (in this case
        a systematic node should not be deleted)
        '''
        
        next_sibling_id = systematic_id.get_next_sibling_identifier()

        try:        
            self.systematic_dao.get_node(next_sibling_id)
        except NoSuchNodeException:
            return False
        
        return True

    def delete(self, systematic_node):
        '''
        Deletes a systematic node.
        '''
        self.systematic_dao.delete(systematic_node.id)

class SystematicPdfGenerationService(object):
    '''
    Service to create a pdf file from the systematic database
    entries
    '''
    # pylint: disable=no-self-use

    @inject
    def __init__(self, systematic_dao: SYSTEMATIC_DAO_KEY):
        '''
        Constructor
        '''
        self.systematic_dao = systematic_dao
    
    def generate_systematic_pdf(self, filename):
        '''
        The public method to create a pdf file.
        
        Might throw an exception if the file can't be written.
        '''
        
        tree = self.systematic_dao.get_tree()
        
        doc = SimpleDocTemplate(filename)
        story = []
        for child in tree.root_node.children:
            story = self._print_root_node(story, child)
            story.append(PageBreak())
        doc.build(story)        
            
    def _print_root_node(self, story, node):
        style = ParagraphStyle('Normal', None)
        style.fontSize = 24
        style.leading = 26
        style.spaceBefore = 12
        style.spaceAfter = 24
        paragraph = Paragraph("%s" % node, style)
        story.append(paragraph)
        for child in node.children:
            story = self._print_child(story, child)
        return story
    
    def _print_child(self, story, node):
        if node.id.subfolder != 0:
            story = self._print_subfolder_child(story, node)
        else:
            if node.id.roman != 0:
                story = self._print_roman_child(story, node)
            else:
                story = self._print_normal_child(story, node)
        for child in node.children:
            story = self._print_child(story, child)
        return story
        
    
    def _print_normal_child(self, story, node):
        style = ParagraphStyle('Normal', None)
        style.fontSize = 14
        style.leading = 15
        style.spaceBefore = 8
        style.spaceAfter = 14
        paragraph = Paragraph("%s" % node, style)
        story.append(paragraph)
        return story

    def _print_roman_child(self, story, node):
        style = ParagraphStyle('Normal', None)
        style.fontSize = 12
        style.leading = 13
        style.spaceBefore = 6
        style.spaceAfter = 6
        style.leftIndent = 12
        paragraph = Paragraph("%s: %s" % (
            ROMAN_NUMERALS[node.entity.id.roman],
            node.entity.description), style)
        story.append(paragraph)
        return story

    def _print_subfolder_child(self, story, node):
        style = ParagraphStyle('Normal', None)
        style.fontSize = 11
        style.spaceBefore = 6
        style.spaceAfter = 6
        style.leftIndent = 20
        paragraph = Paragraph("- %s" % node.entity.description, style)
        story.append(paragraph)
        return story

class SystematicBasePluginModule(Module):
    '''
    Injector module to bind the plugin keys
    '''
    def configure(self, binder):
        binder.bind(SYSTEMATIC_DAO_KEY,
                    ClassProvider(SystematicDao), scope=singleton)
        binder.bind(DOCUMENT_SYSTEMATIC_RELATIONS_DAO_KEY,
                    ClassProvider(DocumentSystematicRelationsDao), scope=singleton)

        binder.bind(SYSTEMATIC_SERVICE_KEY,
                    ClassProvider(SystematicService), scope=singleton)
        binder.bind(SYSTEMATIC_PDF_GENERATION_SERVICE_KEY,
                    ClassProvider(SystematicPdfGenerationService), scope=singleton)

