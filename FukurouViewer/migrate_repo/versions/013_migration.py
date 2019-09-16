from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    thumbnails = Table(
        'thumbnail', meta,
        Column('hash', Text, primary_key=True),
        Column('timestamp', BigInteger))
    thumbnails.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    thumbnails = Table('thumbnail', meta, autoload=True)
    thumbnails.drop()
