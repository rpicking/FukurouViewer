from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    gallery = Table('gallery', meta, autoload=True)

    gallery.c.romanji_title.drop()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    gallery = Table('gallery', meta, autoload=True)

    romanji_title_c = Column('romanji_title', Text)
    romanji_title_c.create(gallery)
