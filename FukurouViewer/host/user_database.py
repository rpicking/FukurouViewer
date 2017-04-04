import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

from utils import Utils

DB_NAME = "db.sqlite"
DATABASE_FILE = "./" + DB_NAME
#DATABASE_FILE = Utils.fv_path(DB_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_FILE


Base = declarative_base()
engine = sqlalchemy.create_engine(DATABASE_URI)
session_maker = sqlalchemy.orm.sessionmaker(bind=engine)

class UserDatabase():
    "Dummy class for logging"
    pass

Database = UserDatabase()

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
