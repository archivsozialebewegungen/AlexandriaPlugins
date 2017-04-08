'''
Created on 10.11.2016

@author: michael
'''
import json
from json.encoder import JSONEncoder
import datetime
import os
import zipfile
import sys
import shutil
from markdown import Markdown
from subprocess import call
from injector import Key, Module, ClassProvider, singleton, inject, provides
from alexandriabase.domain import expand_id, AlexDate
from alexandriabase import baseinjectorkeys
from alexandriabase.services.documentfilemanager import DocumentFileNotFound
from alexandriabase.daos.metadata import DOCUMENT_TABLE, EVENT_TABLE
from alexandriabase.baseinjectorkeys import CONFIG_KEY
from alexandriabase.config import NoSuchConfigValue
from alexplugins.systematic.base import SystematicPoint, SystematicIdentifier

CD_EXPORT_CONFIG_KEY = Key("cd_exporter_copnfig")

MESSENGER_KEY = Key("messenger")

EVENT_SORT_RUNNER_KEY = Key("event_sort_runner")
DOCUMENT_SORT_RUNNER_KEY = Key("document_sort_runner")

THUMBNAIL_RUNNER_KEY = Key("thumbnail_runner")
PDF_RUNNER_KEY = Key("pdf_runner")
DISPLAY_FILE_RUNNER_KEY = Key("display_file_runner")

GENERATOR_ENGINE_KEY = Key("generator_engine")
RUNNERS_KEY = Key("runners")

EXPORT_DATA_ASSEMBLER_KEY = Key('JSON_exporter')
TEXT_GENERATOR_KEY = Key('text_generator')

def get_zip_file():
    '''
    Find the zip file with the angular app for the CDs.
    '''
    
    module_path = os.path.abspath(sys.modules['alexplugins.cdexporter'].__file__)
    module_dir = os.path.dirname(module_path)
    return os.path.join(os.path.join(module_dir, "files"), 'app.zip')

class ExportInfo:
    '''
    Simple data class for CD configuration.
    '''
    
    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.location = None
        self.event_filters = []
        self.document_filters = []
        self.additional_event_ids = []
        self.additional_document_ids = []
        self.excluded_event_ids = []
        self.excluded_document_ids = []
        self.threshold_date = None
        self.iterations = 1
        self.cd_name = "AlexandriaCD"
        self.pagecontent = {}
        self.pagecontent['startpage'] = _("""
No startpage defined
====================
""")
        self.pagecontent['imprint'] = _("""
No imprint defined
==================
""")
        

    def __str__(self):
        
        return "%s: %s, %s: %s, %s: %s" % (_("CD Name"),
                                           self.cd_name,
                                           _("Start date"),
                                           self.start_date,
                                           _("End date"),
                                           self.end_date)

    def save_to_file(self, file_name):
        
        file = open(file_name, 'w')
        json.dump(self, file, cls=AlexEncoder)
        file.close()
        

def load_export_info(file_name):
    
    file = open(file_name, 'r')
    export_info = json.load(file, object_hook=export_info_object_hook)
    file.close()
    return export_info
            
class ConsoleMessenger():
    '''
    Simple messenger class that writes to stdout. The
    GUI version overrides this messenger.
    '''
    
    def show(self, message):
        '''
        The messenger output class.
        '''
        print(message)

def export_info_object_hook(obj):
    '''
    This function is used for deserializing ExportInfo json objects
    '''

    if 'cd_name' in obj:
         export_info = ExportInfo()
         export_info.start_date = obj['start_date']
         export_info.end_date = obj['end_date']
         export_info.location = obj['location']
         export_info.cd_name = obj['cd_name']
         export_info.pagecontent = obj['pagecontent']
         return export_info
     
    if '_year' in obj:
        return AlexDate(obj['_year'], obj['_month'], obj['_day'])

    if 'description' in obj:
        return SystematicPoint(obj['id'], obj['description'])
    
    if 'node_id' in obj:
        return SystematicIdentifier(obj['node_id'], obj['roman'], obj['subfolder'])
        
    return obj

class AlexEncoder(JSONEncoder):
    '''
    Extends the default JSONEncoder to handle
    datetime.date objects.
    '''    
    def __init__(self, **kw):
        super().__init__(sort_keys=True)
        
    def default(self, o):
        # pylint: disable=method-hidden
        if o.__class__ == datetime.date:
            return "%s" % o
        try:
            object_dict = o.__dict__
        except:
            return super().default(o)
        return object_dict

class CDDataAssembler:
    
    @inject(messenger=MESSENGER_KEY,
            document_dao=baseinjectorkeys.DokumentDaoKey,
            event_dao=baseinjectorkeys.EreignisDaoKey,
            document_file_info_dao = baseinjectorkeys.DOCUMENT_FILE_INFO_DAO_KEY,
            references_dao=baseinjectorkeys.RelationsDaoKey,
            event_cross_references_dao=baseinjectorkeys.EventCrossreferencesDaoKey)
    def __init__(self,
                 messenger,
                 document_dao,
                 event_dao,
                 document_file_info_dao,
                 references_dao,
                 event_cross_references_dao):
        self.messenger = messenger
        self.document_dao = document_dao
        self.event_dao = event_dao
        self.document_file_info_dao = document_file_info_dao
        self.references_dao = references_dao
        self.event_cross_references_dao = event_cross_references_dao
    
    def export(self, export_info, data):
        
        self.messenger.show(_("CD generation: Assembling event and document information..."))
        
        location = None
        if export_info.location:
            location = export_info.location.id
        event_references = self.references_dao.fetch_doc_event_references(
            start_date=export_info.start_date,
            end_date=export_info.end_date,
            location="%s" % location
            )
        document_references = {}
        
        document_map = {}
        event_ids = set()
        documents = self.document_dao.find(
            DOCUMENT_TABLE.c.hauptnr.in_(event_references.keys()))  # @UndefinedVariable
        for document in documents:
            document.related_events = event_references[document.id]
            document.file_infos = self.document_file_info_dao.get_file_infos_for_document(document.id)
            document_map[document.id] = document
            for event_id in event_references[document.id]:
                if not event_id in document_references:
                    document_references[event_id] = []
                document_references[event_id].append(document.id)
                event_ids.add(event_id)
        
        events_map = {}
        events = self.event_dao.find(
            EVENT_TABLE.c.ereignis_id.in_(event_ids))  # @UndefinedVariable
        for event in events:
            events_map[event.id] = event
            event.related_documents = document_references[event.id]
            event.related_events = []
            cross_references = self.event_cross_references_dao.get_cross_references(event.id)
            for cross_reference in cross_references:
                if cross_reference in event_ids:
                    event.related_events.append(cross_reference)
        
        data['events'] = events
        data['documents'] = documents
    
            
class ThumbnailRunner:
    
    @inject(messenger=MESSENGER_KEY,
            document_service=baseinjectorkeys.DocumentServiceKey)
    def __init__(self, messenger, document_service):
        self.messenger = messenger
        self.document_service = document_service
        
    def run(self, data_dir, data_dict):
        number_of_documents = len(data_dict['data']['documents'])
        counter = 0
        percentage_old = -1
        for document in data_dict['data']['documents']:
            counter += 1
            percentage = int(counter * 100.0 / number_of_documents)
            if percentage != percentage_old:
                self.messenger.show(_("CD generation: Fetching thumbnail files... %d%% done.") % percentage)
                percentage_old = percentage
            for file_info in document.file_infos:
                try:
                    file_name = os.path.join(os.path.join(data_dir, 'thumbnails'),
                                             "%s.png" % file_info.get_basename())
                    file = open(file_name, "wb")
                    file.write(self.document_service.get_thumbnail(file_info))
                    file.close()
                except DocumentFileNotFound:
                    pass

class DisplayFileRunner:
    
    @inject(messenger=MESSENGER_KEY,
            document_service=baseinjectorkeys.DocumentServiceKey)
    def __init__(self, messenger, document_service):
        self.messenger = messenger
        self.document_service = document_service
        
    def run(self, data_dir, data_dict):
        number_of_documents = len(data_dict['data']['documents'])
        counter = 0
        percentage_old = -1
        for document in data_dict['data']['documents']:
            counter += 1
            percentage = int(counter * 100.0 / number_of_documents)
            if percentage != percentage_old:
                self.messenger.show(_("CD generation: Fetching display files... %d%% done.") % percentage)
                percentage_old = percentage
            for file_info in document.file_infos:
                try:
                    file_name = os.path.join(os.path.join(data_dir, 'screen'),
                                             "%s.png" % file_info.get_basename())
                    file = open(file_name, "wb")
                    file.write(self.document_service.get_display_image(file_info))
                    file.close()
                except DocumentFileNotFound:
                    pass

class PdfFileRunner:
    
    @inject(messenger=MESSENGER_KEY,
            document_service=baseinjectorkeys.DocumentServiceKey)
    def __init__(self, messenger, document_service):
        self.messenger = messenger
        self.document_service = document_service
        
    def run(self, data_dir, data_dict):
        number_of_documents = len(data_dict['data']['documents'])
        counter = 0
        percentage_old = -1
        for document in data_dict['data']['documents']:
            counter += 1
            percentage = int(counter * 100.0 / number_of_documents)
            if percentage != percentage_old:
                self.messenger.show(_("CD generation: Fetching pdf files... %d%% done.") % percentage)
                percentage_old = percentage
            try:
                percentage
                file_name = os.path.join(os.path.join(data_dir, 'pdf'),
                                         "%s.pdf" % expand_id(document.id))
                file = open(file_name, "wb")
                file.write(self.document_service.get_pdf(document))
                file.close()
            except DocumentFileNotFound:
                pass


class EventSortRunner:
    
    @inject(messenger=MESSENGER_KEY)
    def __init__(self, messenger):
        self.messenger = messenger
    
    def run(self, data_dir, data_dict):
        self.messenger.show(_("CD generation: Sorting events..."))
        events = data_dict['data']['events']
        events.sort(key=lambda event: event._id)
        for i in range(0, len(events)):
            if i == 0:
                events[i].previous_id = events[len(events)-1]._id
            else:
                events[i].previous_id = events[i-1]._id
            if i == len(events) - 1:
                events[i].next_id = events[0]._id
            else:
                events[i].next_id = events[i+1]._id
                       
class DocumentSortRunner:
    
    @inject(messenger=MESSENGER_KEY)
    def __init__(self, messenger):
        self.messenger = messenger
    
    def run(self, data_dir, data_dict):
        self.messenger.show(_("CD generation: Sorting documents..."))
        documents = data_dict['data']['documents']
        documents.sort(key=lambda document: document._id)
        for i in range(0, len(documents)):
            if i == 0:
                documents[i].previous_id = documents[len(documents)-1]._id
            else:
                documents[i].previous_id = documents[i-1]._id
            if i == len(documents) - 1:
                documents[i].next_id = documents[0]._id
            else:
                documents[i].next_id = documents[i+1]._id
            
class GenerationEngine:
    
    @inject(messenger=MESSENGER_KEY,
            config=CD_EXPORT_CONFIG_KEY,
            export_data_assembler=EXPORT_DATA_ASSEMBLER_KEY,
            textgenerator=TEXT_GENERATOR_KEY,
            runners=RUNNERS_KEY)
    def __init__(self, messenger, config, export_data_assembler, textgenerator, runners):
        self.messenger = messenger
        self.runners = runners
        self.export_data_assembler = export_data_assembler
        self.textgenerator = textgenerator
        self.config = config
            
        self.data_dict = {'data': {}}
        
    def run(self, export_info):

        self.messenger.show(_("CD generation started..."))
        
        app_dir = self._unzip_app(export_info.cd_name)
        
        if app_dir is None:
            return
        
        self.export_data_assembler.export(export_info, self.data_dict['data'])
        
        self.data_dict['pagecontent'] = self._convert_page_content(export_info.pagecontent)
        
        data_dir = os.path.join(app_dir, 'alexandria')
        
        for runner in self.runners:
            runner.run(data_dir, self.data_dict)
        
        self._write_data_js(data_dir)
     
        if self._generate_iso_image(export_info.cd_name, app_dir):
            self.messenger.show(_("CD successfully generated"))

    def _convert_page_content(self, pagecontent):
        markdown = Markdown(export_format='xhtml5')
        result = {}
        for pagename in pagecontent:
            result[pagename] = markdown.convert(pagecontent[pagename])
        return result

    def _write_data_js(self, data_dir):

        self.messenger.show(_("CD generation: Writing data..."))
        javascript = "var alexandria = %s" % json.dumps(self.data_dict, cls=AlexEncoder)

        filename = os.path.join(data_dir, 'data.js')
        file = open(filename, "w")
        file.write(javascript)
        file.close()

    def _unzip_app(self, cd_name):
        
        self.messenger.show(_("CD generation: Unzipping app..."))
        app_dir = os.path.join(self.config.cdexportdir, cd_name)
        try:
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)
            os.makedirs(app_dir, exist_ok=True)
        except:
            self.messenger.show(_("CD generation: Can't create new cd directory. Aborting."))
            return None

        zip_ref = zipfile.ZipFile(get_zip_file(), 'r')
        zip_ref.extractall(app_dir)
        zip_ref.close()
        
        return app_dir

    def _generate_iso_image(self, cd_name, app_dir):
        
        self.messenger.show(_("CD generation: Generating iso image..."))
        try: 
            genisoimage = self.config.genisoimage
        except NoSuchConfigValue:
            self.messenger.show(_("CD generation: No iso generating program defined. Aborting."))
            return False
        
        iso_file_name = os.path.join(self.config.cdexportdir, "%s.iso" % cd_name)
        try:
            if os.path.exists(iso_file_name):
                os.unlink(iso_file_name)
        except:
            self.messenger.show(_("CD generation: Can't remove already existing iso image. Aborting."))
            return False

        stdio = open(os.devnull, 'wb')
        call([genisoimage,
             "-J",
             "-joliet-long", 
             "-r", 
             "-apple", 
             "-o", iso_file_name,
             app_dir
             ],
             stdout=stdio,
             stderr=stdio)

        return True
    
class CDExporterBasePluginModule(Module):
    
    def configure(self, binder):
      
        binder.bind(MESSENGER_KEY, ClassProvider(ConsoleMessenger), scope=singleton)
        binder.bind(GENERATOR_ENGINE_KEY, ClassProvider(GenerationEngine), scope=singleton)
        binder.bind(EXPORT_DATA_ASSEMBLER_KEY, ClassProvider(CDDataAssembler), scope=singleton)
        binder.bind(THUMBNAIL_RUNNER_KEY, ClassProvider(ThumbnailRunner), scope=singleton)
        binder.bind(DISPLAY_FILE_RUNNER_KEY, ClassProvider(DisplayFileRunner), scope=singleton)
        binder.bind(PDF_RUNNER_KEY, ClassProvider(PdfFileRunner), scope=singleton)
        binder.bind(EVENT_SORT_RUNNER_KEY, ClassProvider(EventSortRunner), scope=singleton)
        binder.bind(DOCUMENT_SORT_RUNNER_KEY, ClassProvider(DocumentSortRunner), scope=singleton)

    @provides(RUNNERS_KEY)
    @inject(event_sorter=EVENT_SORT_RUNNER_KEY,
            document_sorter=DOCUMENT_SORT_RUNNER_KEY,
            thumbnail=THUMBNAIL_RUNNER_KEY,
            display_file=DISPLAY_FILE_RUNNER_KEY,
            pdf_file=PDF_RUNNER_KEY
            )
    def provide_runners(self, event_sorter, document_sorter, thumbnail, display_file, pdf_file):
        return [event_sorter, document_sorter, thumbnail, display_file, pdf_file]
    
    @provides(CD_EXPORT_CONFIG_KEY)
    @inject(config=CONFIG_KEY)
    def provide_cd_exporter_config(self, config):
        '''
        This patches the configuration for the properties needed
        by the CD export_data_assembler plugin.
        '''
        
        config.__class__.cdexportdir = property(lambda self: self._get_string_value('cdexportdir'), 
                                                lambda self, value: self._set_string_value('cdexportdir', value))
        config.__class__.genisoimage = property(lambda self: self._get_string_value('genisoimage'), 
                                                lambda self, value: self._set_string_value('genisoimage', value))
        return config