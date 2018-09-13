import os
import contextlib
import migrate
from migrate.versioning import api
from threading import Lock
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, scoped_session

from FukurouViewer.utils import Utils
from FukurouViewer.logger import Logger

DB_NAME = "db.sqlite"
DATABASE_FILE = Utils.fv_path(DB_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_FILE
MIGRATE_REPO =  Utils.convert_from_relative_path("migrate_repo/")
lock = Lock()


Base = declarative_base()
engine = sqlalchemy.create_engine(DATABASE_URI)
session_maker = sqlalchemy.orm.sessionmaker(bind=engine)

class UserDatabase(Logger):
    "Dummy class for logging"
    pass

Database = UserDatabase()


class History(Base):
    __tablename__ = "history"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    filename = sqlalchemy.Column(sqlalchemy.Text)
    src_url = sqlalchemy.Column(sqlalchemy.Text)
    page_url = sqlalchemy.Column(sqlalchemy.Text)
    domain = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    time_added = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    full_path = sqlalchemy.Column(sqlalchemy.Text)
    favicon_url = sqlalchemy.Column(sqlalchemy.Text, default="-1")
    dead = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    folder_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("folders.id"))
    gallery_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('gallery.id'))

    folder = relationship("Folders", foreign_keys=[folder_id])
    gallery = relationship("Gallery", backref=backref("history_items", lazy="joined"), foreign_keys=[gallery_id])


class Gallery(Base):
    __tablename__ = "gallery"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text)
    origin_title = sqlalchemy.Column(sqlalchemy.Text)
    time_added = sqlalchemy.Column(sqlalchemy.Integer)
    last_modified = sqlalchemy.Column(sqlalchemy.Integer)
    site_rating = sqlalchemy.Column(sqlalchemy.Float)     # rating 0-10 float
    user_rating = sqlalchemy.Column(sqlalchemy.Integer)     # rating 0-10 5 stars set by user
    rating_count = sqlalchemy.Column(sqlalchemy.Integer)    # number of ratings from site at time of import
    total_size = sqlalchemy.Column(sqlalchemy.Float)        # total size in mbs
    file_count = sqlalchemy.Column(sqlalchemy.Integer)
    url = sqlalchemy.Column(sqlalchemy.Text)                # url of import site
    virtual = sqlalchemy.Column(sqlalchemy.Boolean)         # true if gallery doesn't coincide with one on harddrive

    #history_items = relationship("History", backref="gallery")


class Folders(Base):
    __tablename__ = "folders"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text)
    uid = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    path = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    color = sqlalchemy.Column(sqlalchemy.Text)
    order = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.Integer, default=0)   # 0 = both, 1 = ext only, 2 = app only


class Downloads(Base):
    __tablename__ = "downloads"

    id = sqlalchemy.Column(sqlalchemy.Text, primary_key=True)   # ui download item id
    filepath = sqlalchemy.Column(sqlalchemy.Text)
    filename = sqlalchemy.Column(sqlalchemy.Text)
    base_name = sqlalchemy.Column(sqlalchemy.Text)
    ext = sqlalchemy.Column(sqlalchemy.Text)
    total_size = sqlalchemy.Column(sqlalchemy.Integer)
    srcUrl = sqlalchemy.Column(sqlalchemy.Text)
    pageUrl = sqlalchemy.Column(sqlalchemy.Text)
    domain = sqlalchemy.Column(sqlalchemy.Text)
    favicon_url = sqlalchemy.Column(sqlalchemy.Text)
    timestamp = sqlalchemy.Column(sqlalchemy.Integer)
    folder_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(Folders.id))

    folder = relationship("Folders", foreign_keys=[folder_id])


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
    except:
        session.rollback()
        raise
    finally:
        if acquire:
            lock.release()
        session.close()


if __name__ == "__main__":
    setup()
