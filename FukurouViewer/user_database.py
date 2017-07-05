import os
import contextlib
import sqlalchemy
import migrate
from migrate.versioning import api
from threading import Lock
from sqlalchemy.ext.declarative import declarative_base

from FukurouViewer.utils import Utils
from FukurouViewer.logger import Logger

DB_NAME = "db.sqlite"
DATABASE_FILE = Utils.fv_path(DB_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_FILE
MIGRATE_REPO =  Utils.convert_from_relative_path("migrate_repo/")
lock = Lock()


base = declarative_base()
engine = sqlalchemy.create_engine(DATABASE_URI)
session_maker = sqlalchemy.orm.sessionmaker(bind=engine)

class UserDatabase(Logger):
    "Dummy class for logging"
    pass

Database = UserDatabase()


class History(base):
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
    folder = sqlalchemy.Column(sqlalchemy.Text)
    dead = sqlalchemy.Column(sqlalchemy.Boolean, default=False)


class Folders(base):
    __tablename__ = "folders"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text)
    uid = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    path = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    color = sqlalchemy.Column(sqlalchemy.Text)
    order = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.Integer, default=0)   # 0 = both, 1 = ext only, 2 = app only


def setup():
    Database.logger.debug("Setting up database.")
    if not os.path.exists(DATABASE_FILE):
        base.metadata.create_all(engine)
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
        session = sqlalchemy.orm.scoped_session(session_maker)
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
