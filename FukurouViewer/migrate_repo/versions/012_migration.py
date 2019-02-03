from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    history = Table('history', meta, autoload=True)
    history.c.full_path.alter(name="filepath")


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    history = Table('history', meta, autoload=True)
    history = Table('history', meta, autoload=True)
    history.c.filepath.alter(name="full_path")
