from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    downloads = Table('downloads', meta, autoload=True)

    timestamp_c = Column('timestamp', Integer)
    timestamp_c.create(downloads)

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    downloads = Table('downloads', meta, autoload=True)

    downloads.c.timestamp.drop()
