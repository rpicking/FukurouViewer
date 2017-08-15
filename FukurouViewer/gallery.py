from enum import Enum
from time import time
from sqlalchemy import delete, insert, select, update

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

class BaseIdentifier():
    identity = None    # data to identify 
    creation_type = None

    class CreationType(Enum):
        URL = 0 # url to gallery

    def __init__(self, **kwargs):
        self.creation_type = kwargs.get('type')

        if self.creation_type == 0:
            identity = kwargs.get('gal_url')  # url to gallery's main page

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

    class GalIdentity():
        PAYLOAD = {"method": "gdata", "gidlist": [], "namespace": 1}

        gid = None   # int
        token = ""  # str
        def __init__(self, **kwargs):
            self.gid = kwargs.get('gid')
            self.token = kwargs.get('token')

        def payload(self):
            payload = self.PAYLOAD
            payload["gidlist"].append([self.gid, self.token])
            return payload

    class PageIdentity():
        PAYLOAD = {"method": "gtoken", "pagelist": []}

        gid = None   # int
        page_token = ""  # str
        page_number = None # int
        def __init__(self, **kwargs):
            self.gid = kwargs.get('gid')
            self.page_token = kwargs.get('page_token')
            self.page_number = kwargs.get('page_number')
        
        def payload(self):
            payload = self.PAYLOAD
            payload["pagelist"].append([self.gid, self.page_token, self.page_number])
            return payload

    class HashIdentity():
        hash = ""   # sha1 str
        path = ""   # str
        def __init__(self, **kwargs):
            self.hash = kwargs.get('hash')
            self.path = kwargs.get('path')

        def payload(self):
            return self.hash
            # FIXME

    def __init__(self, **kwargs):
        if kwargs.get("url"):
            tokens = Utils.split_ex_url(kwargs.get("url"))
            if tokens.get("type") == "g":
                self.creation_type = self.CreationType.GAL
                self.identity = self.GalIdentity(**tokens)
            else:
                self.creation_type = self.CreationType.PAGE
                self.identity = self.PageIdentity(**tokens)
        else:
            self.creation_type = self.CreationType.HASH
            self.identity = self.HashIdentity(**tokens)

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
            response = Search.ex_search(sha_hash=item)
            # FIXME
            # DO STUFF TO GET CORRECT THE GID AND TOKEN
            return False


class ExIdentifier(EHIdentifier):
    BASE_URL = "https://exhentai.org/{}/{}/{}/"
    API_URL = "https://exhentai.org/api.php"
    

class GenericGallery(Logger):
    VALID_SITES = [
        ("e-hentai.org", EHIdentifier),
        ("exhentai.org", ExIdentifier),
    ]

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

    history_items = []
    identifier = None       # identifier for site specific gallery linking
    dead = False
    
    def __init__(self, **kwargs):
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
        for site in self.VALID_SITES:
            if domain == site[0]:
                return site[1](**kwargs)
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
        self.url = info.get("url", "")

        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Gallery]).where( user_database.Gallery.url == self.url)))

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
