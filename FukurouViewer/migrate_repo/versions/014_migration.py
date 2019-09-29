from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    gallery = Table('gallery', meta, autoload=True)

    tagNamespace = Table(
        'tag_namespace', meta,
        Column('id', Integer, primary_key=True),
        Column('title', Text, unique=True),
        Column('description', Text))
    tagNamespace.create()

    tag = Table(
        'tag', meta,
        Column('id', Integer, primary_key=True),
        Column('title', Text),
        Column('description', Text),
        Column('namespace_id', Integer, ForeignKey('tag_namespace.id')))
    tag.create()

    item = Table(
        'item', meta,
        Column('id', Integer, primary_key=True))
    item.create()

    galleryTagMapping = Table(
        'gallery_tag_mapping', meta,
        Column('gallery_id', Integer, ForeignKey('gallery.id'), primary_key=True),
        Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True))
    galleryTagMapping.create()

    itemTagMapping = Table(
        'item_tag_mapping', meta,
        Column('item_id', Integer, ForeignKey('item.id'), primary_key=True),
        Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True))
    itemTagMapping.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    tagNamespace = Table('tag_namespace', meta, autoload=True)
    tagNamespace.drop()

    tag = Table('tag', meta, autoload=True)
    tag.drop()

    item = Table('item', meta, autoload=True)
    item.drop()

    galleryTagMapping = Table('gallery_tag_mapping', meta, autoload=True)
    galleryTagMapping.drop()

    itemTagMapping = Table('item_tag_mapping', meta, autoload=True)
    itemTagMapping.drop()
