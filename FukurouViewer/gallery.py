import os
import sys
import linecache
import zipfile

from enum import Enum
from time import time
from pathlib import Path
from typing import List, Union, Optional
from sqlalchemy import delete, insert, select, update

from .foundation import FileItem
from .request_manager import ex_request_manager
from . import user_database
from .utils import Utils
from .logger import Logger
from .config import Config
from .search import Search


class CreationType(Enum):
    FULL = 0    # ex gallery_id and gallery_token
    PAGE = 1    # ex Individual page tokens
    GAL = 2     # ex gallery tokens
    HASH = 3    # file sha1 hash search


class BaseIdentifier:
    identity = None    # data to identify 
    creation_type = None

    class CreationType(Enum):
        URL = 0 # url to gallery

    def __init__(self, **kwargs):
        self.creation_type = kwargs.get('type')

        if self.creation_type == 0:
            identity = kwargs.get("galleryUrl")  # url to gallery's main page

    def get_data(self):
        return self.identity


class EHIdentifier(BaseIdentifier):
    BASE_URL = "https://e-hentai.org/{}/{}/{}/"
    API_URL = "https://api.e-hentai.org/api.php"
    SITE_MAX_ENTRIES = 25

    class CreationType(Enum):
        GAL = 0    # ex gallery_id and gallery_token
        PAGE = 1    # ex Individual page tokens
        HASH = 2    # file sha1 hash search

    class GalIdentity:
        gid = None   # int
        token = ""  # str

        def __init__(self, **kwargs):
            self.gid = kwargs.get('gid')
            self.token = kwargs.get('token')

        def payload(self):
            payload = {"method": "gdata", "gidlist": [], "namespace": 1}
            payload["gidlist"].append([self.gid, self.token])
            return payload

    class PageIdentity:
        gid = None   # int
        page_token = ""  # str
        page_number = None # int

        def __init__(self, **kwargs):
            self.gid = kwargs.get('gid')
            self.page_token = kwargs.get('page_token')
            self.page_number = kwargs.get('page_number')
        
        def payload(self):
            payload = {"method": "gtoken", "pagelist": []}
            payload["pagelist"].append([self.gid, self.page_token, self.page_number])
            return payload

    class HashIdentity:
        hash = ""   # sha1 str
        path = ""   # str

        def __init__(self, **kwargs):
            self.hash = kwargs.get('hash')
            self.path = kwargs.get('path')

        def payload(self):
            return self.hash
            # FIXME

    def __init__(self, **kwargs):
        if kwargs.get("galleryUrl"):
            tokens = Utils.split_ex_url(kwargs.get("galleryUrl"))
            self.creation_type = self.CreationType.GAL
            self.identity = self.GalIdentity(**tokens)
        elif kwargs.get("url"): # non-gallery page url
            tokens = Utils.split_ex_url(kwargs.get("url"))
            if tokens.get("type") == "g":
                self.creation_type = self.CreationType.GAL
                self.identity = self.GalIdentity(**tokens)
            else:
                self.creation_type = self.CreationType.PAGE
                self.identity = self.PageIdentity(**tokens)
        else:
            self.creation_type = self.CreationType.HASH
            self.identity = self.HashIdentity(**kwargs)

    def url(self):
        if self.creation_type == self.CreationType.GAL:
            return self.BASE_URL.format("g", self.identity.gid, self.identity.token)
        elif self.creation_type == self.CreationType.PAGE:
            return self.BASE_URL.format("s", self.identity.page_token, "-".join(self.identity.gid, self.identity.page_number))
        return None

    # searches for gallery information
    # returns data if done
    #   false if need to search again
    def search(self):
        payload = self.identity.payload()
        if self.creation_type == self.CreationType.GAL:
            response = ex_request_manager.post(self.API_URL, payload=payload)
            response = response["gmetadata"][0]
            response["origin_title"] = response.pop("title_jpn")
            response["total_size"] = response.pop("filesize")
            response["site_rating"] = response.pop("rating")
            response["file_count"] = response.pop("filecount")
            response["url"] = self.url()
            return response
        elif self.creation_type == self.CreationType.PAGE:
            response = ex_request_manager.post(self.API_URL, payload=payload)
            response = response["tokenlist"][0]
            self.creation_type = self.CreationType.GAL
            self.identity = self.GalIdentity(**response)
            return False
        elif self.creation_type == self.CreationType.HASH:
            item = "TEST" # NOT SURE IF ITS ACTUALLY BROKEN OR NOT BUT SAID ITEM DOESN'T EXIST
            response = Search.ex_search(sha_hash=item)
            # FIXME
            # DO STUFF TO GET CORRECT THE GID AND TOKEN
            return False


class ExIdentifier(EHIdentifier):
    BASE_URL = "https://exhentai.org/{}/{}/{}/"
    API_URL = "https://exhentai.org/api.php"
    

class GenericGallery(Logger):

    VALID_SITES = {
        "e-hentai.org": "EHIdentifier",
        "exhentai.org": "ExIdentifier",
    }

    IMAGE_WIDTH = 200
    IMAGE_HEIGHT = 280
    db_id = None
    title = ""
    origin_title = ""
    time_added = None
    last_modified = None
    site_rating = None
    user_rating = None
    rating_count = 0
    total_size = 0
    file_count = 0
    url = ""
    virtual = None

    identifier = None       # identifier for site specific gallery linking
    dead = False
    
    def __init__(self, **kwargs):
        self.history_items = []
        self.url = kwargs.get("galleryUrl", "")

        item = kwargs.get('history_item')
        if item:
            self.history_items.append(item)
        if kwargs.get('local'): # creating from local file/folder
            pass    # fIXME
        else:   # creating virtual from downloaded file
            self.virtual = True
            self.identifier = self.match_site(**kwargs)
                
    def match_site(self, **kwargs):
        domain = kwargs.get("domain")

        if domain in self.VALID_SITES:
            test = globals()[self.VALID_SITES.get(domain)](**kwargs)
            return test
        return None

    # searches for gallery information
    # returns true if done
    #   false if need to search again
    def search(self):
        info = self.identifier.search()
        if not info:
            return False

        self.title = info.get("title", "")
        self.origin_title = info.get("origin_title", "")
        self.time_added = time()
        self.last_modified = self.time_added
        self.site_rating = info.get("site_rating", None)
        self.user_rating = info.get("user_rating", None)
        self.rating_count = info.get("rating_count", 0)
        self.total_size = info.get("total_size", 0)
        self.file_count = info.get("file_count", 0)
        if not self.url:
            self.url = info.get("url", "")

        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Gallery]).where(user_database.Gallery.url == self.url)))

        if results:
            results = results[0]
            self.db_id = results.get("id")
            self.update_history_items()
        else:
            self.insert()
        return True

    def insert(self):   # insert gallery into database
        if not self.db_id:  # only create new row if not in db
            payload = {}
            if self.title:
                payload["title"] = self.title
            if self.origin_title:
                payload["origin_title"] = self.origin_title
            if self.time_added:
                payload["time_added"] = self.time_added
            if self.last_modified:
                payload["last_modified"] = self.last_modified
            if self.site_rating:
                payload["site_rating"] = self.site_rating
            if self.user_rating:
                payload["user_rating"] = self.user_rating
            if self.rating_count:
                payload["rating_count"] = self.rating_count
            if self.total_size:
                payload["total_size"] = self.total_size
            if self.file_count:
                payload["file_count"] = self.file_count
            if self.url:
                payload["url"] = self.url
            if self.virtual:
                payload["virtual"] = self.virtual

            with user_database.get_session(self, acquire=True) as session:
                result = session.execute(insert(user_database.Gallery).values(payload))
                self.db_id = int(result.inserted_primary_key[0])

        self.update_history_items()

    def update(self, **kwargs):
        with user_database.get_session(self, acquire=True) as session:
            session.execute(update(user_database.Gallery).where(
                user_database.Gallery.id == self.db_id).values(kwargs))

    def update_history_items(self):
        try:
            with user_database.get_session(self, acquire=True) as session:
                for item in self.history_items:
                    session.execute(update(user_database.History).where(
                        user_database.History.id == item).values({"gallery_id": self.db_id }))
        except Exception as e:
            pass

    def load_from_db(self):
        pass

    def delete(self):
        with user_database.get_session(self, acquire=True) as session:
            session.execute(delete(user_database.Gallery).where(
                user_database.Gallery.id == self.db_id))
        self.dead = True

    # logs raised general exception
    def log_exception(self):
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        self.logger.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


###############################################################
###############################################################
###############################################################
class GalleryArchive(Logger):
    """ Gallery packaged into a single file in archive format
    """

    def __init__(self, file: Union[FileItem, str], loadAllData=False):
        if isinstance(file, str):
            file = FileItem(file)

        self.file = file
        self.archive = None  # type: Optional[zipfile.ZipFile]
        self.filesDict = {}

        self.coverKey = None

        self.openArchive()
        infoList = self.archive.infolist()  # type: List[zipfile.ZipInfo]

        if len(infoList) > 0:
            coverItem = infoList[0]
            self.coverKey = coverItem.filename

        for item in infoList:
            file = GalleryArchive.createArchiveFileItem(self.archive, item, loadAllData)
            self.filesDict[file.name] = file

        self.archive.close()

    def openArchive(self):
        self.archive = zipfile.ZipFile(self.file.filepath, "r")

    def load(self):
        self.openArchive()
        for file in self.filesDict.values():
            file.load(GalleryArchive.loadArchiveData(self.archive, file))
        self.archive.close()

    def getFile(self, filepath: str) -> Optional[FileItem]:
        return self.filesDict.get(filepath, None)

    @property
    def cover(self) -> FileItem:
        cover = self.filesDict[self.coverKey]
        if not cover.isLoaded:
            cover.load(GalleryArchive.loadArchiveData(self.archive, cover))
        return cover

    @property
    def files(self):
        return self.filesDict.values()

    @property
    def __dict__(self):
        return {
            "cover": vars(self.cover),
            "name": self.file.name,
            #"tags": [],
            #"files": [vars(file) for file in self.files]
        }

    def __del__(self):
        self.archive.close()

    @staticmethod
    def createArchiveFileItem(archive: zipfile.ZipFile, zipInfo: zipfile.ZipInfo, loadData: bool):
        data = archive.read(zipInfo.filename) if loadData else None
        return FileItem(zipInfo.filename, data=data, isBuffer=True)

    @staticmethod
    def loadArchiveData(archive: zipfile.ZipFile, zipInfo: Union[zipfile.ZipInfo, FileItem]):
        filename = zipInfo.filename if isinstance(zipInfo, zipfile.ZipInfo) else zipInfo.filepath
        return archive.read(filename)
