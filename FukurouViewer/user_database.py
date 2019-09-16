import os
import contextlib
import migrate
import sqlalchemy

from sqlalchemy import Column, ForeignKey, Text, Integer
from migrate.versioning import api
from threading import Lock
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, scoped_session

from FukurouViewer.utils import Utils
from FukurouViewer.logger import Logger

DB_NAME = "db.sqlite"
DATABASE_FILE = Utils.fv_path(DB_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_FILE
MIGRATE_REPO = Utils.convert_from_relative_path("migrate_repo/")
lock = Lock()


Base = declarative_base()
engine = sqlalchemy.create_engine(DATABASE_URI)
session_maker = sqlalchemy.orm.sessionmaker(bind=engine)


class UserDatabase(Logger):
    """Dummy class for logging"""
    pass


Database = UserDatabase()


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
    folder_id = Column(Integer, ForeignKey("folders.id"))
    gallery_id = Column(Integer, ForeignKey('gallery.id'))

    folder = relationship("Folders", foreign_keys=[folder_id])
    gallery = relationship("Gallery", backref=backref("history_items", lazy="joined"), foreign_keys=[gallery_id])


class Gallery(Base):
    __tablename__ = "gallery"

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

    tags = relationship("Tag", secondary="GalleryTagMapping")
    # history_items = relationship("History", backref="gallery")


class Folders(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    uid = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    color = Column(Text)
    order = Column(Integer)
    type = Column(Integer, default=0)   # 0 = both, 1 = ext only, 2 = app only


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
    folder_id = Column(Integer, ForeignKey(Folders.id))

    folder = relationship("Folders", foreign_keys=[folder_id])


class Thumbnail(Base):
    __tablename__ = "thumbnail"

    hash = Column(Text, primary_key=True)
    timestamp = Column(sqlalchemy.BigInteger)   # timestamp of thumbnail creation


class TagNamespace(Base):
    __tablename__ = "tag_namespace"

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    description = Column(Text)


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    description = Column(Text)
    namespace_id = Column(Integer, ForeignKey(TagNamespace.id))

    namespace = relationship("Namespace", foreign_keys=[namespace_id])

    galleries = relationship("Gallery", secondary="GalleryTagMapping")
    items = relationship("Item", secondary="ItemTagMapping")


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)

    tags = relationship("Tag", secondary="GalleryTagMapping")


class GalleryTagMapping(Base):
    __tablename__ = "gallery_tag_mapping"

    gallery_id = Column(Integer, ForeignKey(Gallery.id), primary_key=True)
    tag_id = Column(Integer, ForeignKey(Tag.id), primary_key=True)


class ItemTagMapping(Base):
    __tablename__ = "item_tag_mapping"

    item_id = Column(Integer, ForeignKey(Item.id), primary_key=True)
    tag_id = Column(Integer, ForeignKey(Tag.id), primary_key=True)


def setup():
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
def get_session(requester, acquire=False):
    Database.logger.debug("New DB session requested from %s" % requester)
    session = None
    try:
        if acquire:
            lock.acquire()
        session = scoped_session(session_maker)
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
    setup()
