from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    history = Table('history', meta, autoload=True)
    filepath = Column('filepath', Text)
    filepath.create(history)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    history = Table('history', meta, autoload=True)

    history.c.filepath.drop()
