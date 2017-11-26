import random
import string
from sqlalchemy import insert, select
from sqlalchemy.sql.expression import func
from . import user_database
from .utils import Utils
from .logger import Logger


class Foundation(Logger):
    """Non "foundational" core functions for FukurouViewer application
    Functions that are used in multiple locations
        but are not building blocks for functionality
    """

    # returns a unique id of length 6 for folder
    @classmethod
    def uniqueID(cls, items):
        while True:
            id = cls.id_generator()
            if id not in items:
                return id

    @classmethod
    def uniqueFolderID(cls):
        with user_database.get_session(cls, acquire=True) as session:
            used_ids = Utils.convert_result(session.execute(
                select([user_database.Folders.uid])))

        used_ids = [item['uid'] for item in used_ids]
        return cls.uniqueID(used_ids)

    # generates a id string
    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for i in range(size))


    # returns the highest order value + 1 of folders table
    @classmethod
    def lastOrder(cls):
        with user_database.get_session(cls, acquire=True) as session:
            values = Utils.convert_result(session.execute(
                select([user_database.Folders.order])))
            if not values:
                return 1
            return max([x['order'] for x in values]) + 1

