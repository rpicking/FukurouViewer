from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    downloads = Table('downloads', meta, autoload=True)

    total_size_c = Column('total_size', Integer)
    total_size_c.create(downloads)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    downloads = Table('downloads', meta, autoload=True)

    downloads.c.total_size.drop()
