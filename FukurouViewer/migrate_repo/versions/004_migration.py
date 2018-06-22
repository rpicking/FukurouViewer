from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()

gallery = Table(
    'gallery', meta,
    Column('id', Integer, primary_key=True),
    Column('title', Text),
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    history = Table('history', meta, autoload=True)
    gallery_id_c = Column('gallery_id', Integer, ForeignKey('gallery.id'))
    gallery_id_c.create(history)

    gallery.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    history = Table('history', meta, autoload=True)
    history.c.gallery_id.drop()

    gallery.drop()
