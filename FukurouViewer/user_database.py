import os
import contextlib
from typing import Optional, List, Union

import migrate
import sqlalchemy
from migrate.versioning import api

from sqlalchemy import Column, ForeignKey, Text, Integer
from sqlalchemy.ext.declarative import as_declarative
from threading import Lock
from sqlalchemy.orm import backref, relationship, scoped_session, Session
from enum import Enum

from FukurouViewer import gallery
from FukurouViewer.config import Config
from FukurouViewer.db_utils import DBUtils
from FukurouViewer.files import DirectoryItem
from FukurouViewer.filetype import FileType
from FukurouViewer.utils import Utils
from FukurouViewer.logger import Logger

DB_NAME = "db.sqlite"
DATABASE_FILE = Config.fv_path(DB_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_FILE
MIGRATE_REPO = Utils.base_path("migrate_repo/")
lock = Lock()


engine = sqlalchemy.create_engine(DATABASE_URI)
session_maker = sqlalchemy.orm.sessionmaker(bind=engine)


class UserDatabase(Logger):
    """Dummy class for logging"""
    pass


Database = UserDatabase()


@as_declarative()
class Base(object):

    @classmethod
    def get(cls, **kwargs):
        return cls(**kwargs)

    def add(self):
        with get_session(self, acquire=True) as session:
            session.add(self)

    def delete(self):
        with get_session(self, acquire=True) as session:
            session.delete(self)

    def save(self):
        with get_session(self, acquire=True) as session:
            session.commit()

    @classmethod
    def select_first(cls, where=None, order=None, limit=None, offset=None) -> Optional['Base']:
        result = DBUtils.select_first(cls, where=where, order=order, limit=limit, offset=offset)
        if result is None:
            return None
        return cls.get(**result)

    @classmethod
    def select(cls, where=None, order=None, limit=None, offset=None) -> Optional[list]:
        results = DBUtils.select(cls, where=where, order=order, limit=limit, offset=offset)
        if results is None:
            return None
        return [cls.get(**item) for item in results]

    @classmethod
    def update(cls, values: dict, where=None):
        return DBUtils.update(cls, values, where=where)

    @classmethod
    def insert(cls, values: Union[dict, List[dict]]) -> List[int]:
        return DBUtils.insert(cls, values)


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    filename = Column(Text)
    src_url = Column(Text)
    page_url = Column(Text)
    domain = Column(Text, nullable=False)
    time_added = Column(Integer)
    type = Column(Integer, default=1)
    filepath = Column(Text)
    favicon_url = Column(Text, default="-1")
    dead = Column(sqlalchemy.Boolean, default=False)
    collection_id = Column(Integer, ForeignKey("collection.id"))
    gallery_id = Column(Integer, ForeignKey("gallery.id"))

    collection = relationship("Collection", foreign_keys=[collection_id])
    gallery = relationship("Gallery", backref=backref("history_items", lazy="joined"), foreign_keys=[gallery_id])

    def __init__(self, id=None, filename="", src_url="", page_url="", domain="", time_added=0, type=1, filepath="",
                 favicon_url=None, dead=False, collection=None, gallery=None):
        self.id = id
        self.filename = filename
        self.src_url = src_url
        self.page_url = page_url
        self.domain = domain
        self.time_added = time_added
        self.type = type
        self.filepath = filepath
        self.favicon_url = favicon_url
        self.dead = dead

        self.collection = None
        if isinstance(collection, Collection):
            self.collection_id = collection.id
            self.collection = collection
        elif isinstance(collection, dict):
            self.collection = Collection(**collection)
            self.collection_id = self.collection.id
        else:
            self.collection_id = collection

        self.gallery = None
        if isinstance(gallery, Gallery):
            self.gallery_id = gallery.id
            self.gallery = gallery
        elif isinstance(gallery, dict):
            self.gallery = Gallery(**gallery)
            self.gallery_id = self.gallery.id
        else:
            self.gallery_id = gallery


class Gallery(Base):
    __tablename__ = "gallery"

    class Type(Enum):
        # Gallery represented as directory with files inside it
        GALLERY = 0
        # Gallery packaged into single file format i.e. cbz, zip, cbr, rar
        GALLERY_ARCHIVE = 1
        # misc. collection of files/folders
        COLLECTION_MISC = 2
        # folder containing only GALLERY or GALLERY_ARCHIVE files/directories.  Other individual items in directory
        # will be ignored
        COLLECTION_GALLERY = 3

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    origin_title = Column(Text)
    time_added = Column(Integer)
    last_modified = Column(Integer)
    site_rating = Column(sqlalchemy.Float)     # rating 0-10 float
    user_rating = Column(Integer)     # rating 0-10 5 stars set by user
    rating_count = Column(Integer)    # number of ratings from site at time of import
    total_size = Column(sqlalchemy.Float)        # total size in mbs
    file_count = Column(Integer)
    url = Column(Text)                # url of import site
    virtual = Column(sqlalchemy.Boolean)         # true if gallery doesn't coincide with one on harddrive

    tags = relationship("Tag", secondary="gallery_tag_mapping")
    # history_items = relationship("History", backref="gallery")

    def __init__(self, id=None, title="", origin_title="", time_added=0, last_modified=0, site_rating=None,
                 user_rating=None, rating_count=0, total_size=0, file_count=0, url="", virtual=False, tags=None):

        self.id = id
        self.title = title
        self.origin_title = origin_title
        self.time_added = time_added
        self.last_modified = last_modified
        self.site_rating = site_rating
        self.user_rating = user_rating
        self.rating_count = rating_count
        self.total_size = total_size
        self.file_count = file_count
        self.url = url
        self.virtual = virtual

        if tags is None:
            tags = []
        self.tags = [tag if isinstance(tag, Tag) else Tag(**tag) for tag in tags]

    def addTag(self, tag):
        galleryTagMap = GalleryTagMapping(self, tag)
        galleryTagMap.add()


class Collection(Base):
    """Collection"""
    __tablename__ = "collection"

    class Type(Enum):
        # Gallery represented as directory with files inside it
        GALLERY = 0
        # folder containing GALLERY or GALLERY_ARCHIVE files/directories.  Other individual items in directory
        # will be ignored
        COLLECTION_GALLERY = 1

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    uid = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    color = Column(Text)
    order = Column(Integer)
    type = Column(sqlalchemy.Enum(Type), default=Type.GALLERY)

    def __init__(self, id=None, name="", uid="", path="", color="", order=None, type=None, recursive=False):
        self.id = id
        self.name = name
        self.uid = uid
        self.path = path
        self.color = color
        self.order = order

        self.directory = DirectoryItem(self.path, recursive=recursive)
        self.type = type if type is not None else Collection.determine_type(self.directory)
        self.galleries: List[gallery.Gallery] = []

    @property
    def count(self):
        return len(self.galleries)

    @staticmethod
    def get_by_id(collection_uid: str) -> Optional['Collection']:
        if collection_uid is None:
            return None
        return Collection.select_first(where=Collection.uid == collection_uid)

    @staticmethod
    def get_by_path(path: str) -> Optional['Collection']:
        if path is None:
            return None

        return Collection.select_first(where=Collection.path == path)

    @staticmethod
    def determine_type(directory: DirectoryItem) -> Type:
        if directory is None or not directory.exists:
            return Collection.Type.GALLERY

        for file in directory.files:
            if file.type is not FileType.ARCHIVE:
                return Collection.Type.GALLERY

        if len(directory.files) > 0:
            return Collection.Type.COLLECTION_GALLERY

        if len(directory.directories) > 0:
            return Collection.Type.COLLECTION_GALLERY

        return Collection.Type.GALLERY


class Downloads(Base):
    __tablename__ = "downloads"

    id = Column(Text, primary_key=True)   # ui download item id
    filepath = Column(Text)
    filename = Column(Text)
    base_name = Column(Text)
    ext = Column(Text)
    total_size = Column(Integer)
    srcUrl = Column(Text)
    pageUrl = Column(Text)
    domain = Column(Text)
    favicon_url = Column(Text)
    timestamp = Column(Integer)
    collection_id = Column(Integer, ForeignKey(Collection.id))

    collection = relationship("Collection", foreign_keys=[collection_id])

    def __init__(self, id=None, filepath="", filename="", base_name="", ext="", total_size=None, srcUrl="", pageUrl="",
                 domain="", favicon_url="", timestamp=None, collection=None):
        self.id = id
        self.filepath = filepath
        self.filename = filename
        self.base_name = base_name
        self.ext = ext
        self.total_size = total_size
        self.srcUrl = srcUrl
        self.pageUrl = pageUrl
        self.domain = domain
        self.favicon_url = favicon_url
        self.timestamp = timestamp

        if isinstance(collection, Collection):
            self.collection_id = collection.id
            self.collection = collection
        elif isinstance(collection, dict):
            self.collection = Collection(**collection)
            self.collection_id = self.collection.id
        else:
            self.collection_id = collection


class Thumbnail(Base):
    __tablename__ = "thumbnail"

    hash = Column(Text, primary_key=True)
    timestamp = Column(sqlalchemy.BigInteger)   # timestamp of thumbnail creation

    def __init__(self, hash=None, timestamp=None):
        self.hash = hash
        self.timestamp = timestamp


class TagNamespace(Base):
    __tablename__ = "tag_namespace"

    id = Column(Integer, primary_key=True)
    title = Column(Text, unique=True)
    description = Column(Text)

    def __init__(self, id=None, title="", description=""):
        self.id = id
        self.title = title
        self.description = description


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    description = Column(Text)
    namespace_id = Column(Integer, ForeignKey(TagNamespace.id))

    namespace = relationship("TagNamespace")
    galleries = relationship("Gallery", secondary="gallery_tag_mapping")
    items = relationship("Item", secondary="item_tag_mapping")

    def __init__(self, id=None, title="", description="", namespace_id=None):
        self.id = id
        self.title = title
        self.description = description
        self.namespace_id = namespace_id

    @staticmethod
    def getTag(id):
        with get_session(Tag, acquire=True) as session:
            return session.query(Tag).filter(Tag.id == id).first()


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)

    tags = relationship("Tag", secondary="item_tag_mapping")

    def addTag(self, tag):
        itemTagMap = ItemTagMapping(self, tag)
        itemTagMap.add()


class GalleryTagMapping(Base):
    __tablename__ = "gallery_tag_mapping"

    gallery_id = Column(Integer, ForeignKey(Gallery.id), primary_key=True)
    tag_id = Column(Integer, ForeignKey(Tag.id), primary_key=True)

    def __init__(self, gallery, tag):
        if isinstance(gallery, Gallery):
            self.gallery_id = gallery.id
        else:
            self.gallery_id = gallery

        if isinstance(tag, Tag):
            self.tag_id = tag.id
        else:
            self.tag_id = tag


class ItemTagMapping(Base):
    __tablename__ = "item_tag_mapping"

    item_id = Column(Integer, ForeignKey(Item.id), primary_key=True)
    tag_id = Column(Integer, ForeignKey(Tag.id), primary_key=True)

    def __init__(self, item, tag):
        if isinstance(item, Item):
            self.item_id = item.id
        else:
            self.item_id = item

        if isinstance(tag, Tag):
            self.tag_id = tag.id
        else:
            self.tag_id = tag


def upgrade():
    Database.logger.debug("Setting up database.")
    if not os.path.exists(DATABASE_FILE):
        Base.metadata.create_all(engine)
        api.version_control(DATABASE_URI, MIGRATE_REPO, version=api.version(MIGRATE_REPO))
    else:
        try:
            api.version_control(DATABASE_URI, MIGRATE_REPO, version=1)
        except migrate.DatabaseAlreadyControlledError:
            pass
    api.upgrade(DATABASE_URI, MIGRATE_REPO)


@contextlib.contextmanager
def get_session(requester, acquire=False) -> session_maker:
    Database.logger.debug("New DB session requested from %s" % requester)
    session = None
    try:
        if acquire:
            lock.acquire()

        session = Session(engine)
        session.expire_on_commit = False
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if acquire:
            lock.release()
        session.close()


if __name__ == "__main__":
    upgrade()
