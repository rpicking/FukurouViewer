from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    gallery = Table('gallery', meta, autoload=True)

    romanji_title_c = Column('romanji_title', Text)
    romanji_title_c.create(gallery)

    origin_title_c = Column('origin_title', Text)
    origin_title_c.create(gallery)

    time_added_c = Column('time_added', Integer)
    time_added_c.create(gallery)

    last_modified_c = Column('last_modified', Integer)
    last_modified_c.create(gallery)

    site_rating_c = Column('site_rating', Integer)
    site_rating_c.create(gallery)

    user_rating_c = Column('user_rating', Integer)
    user_rating_c.create(gallery)

    rating_count_c = Column('rating_count', Integer)
    rating_count_c.create(gallery)

    total_size_c = Column('total_size', Float)
    total_size_c.create(gallery)

    file_count_c = Column('file_count', Integer)
    file_count_c.create(gallery)

    url_c = Column('url', Text)
    url_c.create(gallery)

    virtual_c = Column('virtual', Boolean)
    virtual_c.create(gallery)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    gallery = Table('gallery', meta, autoload=True)

    gallery.c.romanji_title.drop()
    gallery.c.origin_title.drop()
    gallery.c.time_added.drop()
    gallery.c.last_modified.drop()
    gallery.c.site_rating.drop()
    gallery.c.user_rating.drop()
    gallery.c.rating_count.drop()
    gallery.c.total_size.drop()
    gallery.c.file_count.drop()
    gallery.c.url.drop()
    gallery.c.virtual.drop()
