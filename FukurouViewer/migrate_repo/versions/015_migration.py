from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    folders = Table("folders", meta, autoload=True)
    folders.rename("collection")

    downloads = Table("downloads", meta, autoload=True)
    downloads.c.collection_id.alter(name="collection_id")

    history = Table("history", meta, autoload=True)
    history.c.collection_id.alter(name="collection_id")


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    collection = Table("collection", meta, autoload=True)
    collection.rename("folders")

    downloads = Table("downloads", meta, autoload=True)
    downloads.c.collection_id.alter(name="folder_id")

    history = Table("history", meta, autoload=True)
    history.c.collection_id.alter(name="folder_id")
