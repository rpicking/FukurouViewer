from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    gallery = Table('gallery', meta, autoload=True)

    gallery.c.site_rating.alter(type=Float)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    gallery = Table('gallery', meta, autoload=True)

    gallery.c.site_rating.alter(type=Integer)
