import os
import contextlib
import sqlalchemy
from threading import Lock
from sqlalchemy.ext.declarative import declarative_base

from FukurouViewer.utils import Utils
from FukurouViewer.logger import Logger

DB_NAME = "db.sqlite"
#DATABASE_FILE = "./" + DB_NAME
DATABASE_FILE = Utils.fv_path(DB_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_FILE
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


def setup():
    Database.logger.debug("Setting up database.")
    if not os.path.exists(DATABASE_FILE):
        base.metadata.create_all(engine)
        #api.version_control(DATABASE_URI, MIGRATE_REPO, version=api.version(MIGRATE_REPO))
    #else:
        # version migrate


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
