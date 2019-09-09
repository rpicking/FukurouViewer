from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    folders = Table('folders', meta, autoload=True)
    downloads = Table(
        'downloads', meta,
        Column('id', Text, primary_key=True),
        Column('filepath', Text),
        Column('filename', Text),
        Column('base_name', Text),
        Column('ext', Text),
        Column('srcUrl', Text),
        Column('pageUrl', Text),
        Column('domain', Text),
        Column('favicon_url', Text),
        Column('folder_id', Integer, ForeignKey('folders.id')))
    downloads.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    downloads = Table('downloads', meta, autoload=True)
    downloads.drop()
