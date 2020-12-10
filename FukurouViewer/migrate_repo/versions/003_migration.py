from sqlalchemy import *
from migrate import *


from migrate.changeset import schema

from FukurouViewer.user_database import Collection

meta = MetaData()

folders = Table(
    'folders', meta,
    Column('id', Integer, primary_key=True),
    Column('name', Text),
    Column('uid', Text, nullable=False),
    Column('path', Text, nullable=False),
    Column('color', Text),
    Column('order', Integer),
    Column('type', Enum(Collection.Type), default=0))


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    folders.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    folders.drop()
