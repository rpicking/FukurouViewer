from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()

folders = Table(
    'folders', meta,
    Column('id', Integer, primary_key=True),
    Column('name', Text),
    Column('uid', Text, nullable=False),
    Column('path', Text, nullable=False),
    Column('color', Text),
    Column('order', Integer),
    Column('type', Integer, default=0),
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    folders.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    folders.drop()
