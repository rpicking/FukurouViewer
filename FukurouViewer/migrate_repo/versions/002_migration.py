from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    history = Table('history', meta, Column('folder', Text))
    history.create()
    deadc = Column('dead', Boolean, default=ColumnDefault(False))
    deadc.create(history)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    history = Table('history', meta, autoload=True)
    history.c.collection.drop()
    history.c.dead.drop()
