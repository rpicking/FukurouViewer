from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    history = Table('history', meta, autoload=True)

    history.c.folder.drop()

    folders = Table('folders', meta, autoload=True)
    folder_id_c = Column('folder_id', Integer, ForeignKey('folders.id'))
    folder_id_c.create(history)




def downgrade(migrate_engine):
    meta.bind = migrate_engine
    history = Table('history', meta, autoload=True)

    folder_old_c = Column('folder', Text)
    folder_old_c.create(history)

    history.c.folder_id.drop()
