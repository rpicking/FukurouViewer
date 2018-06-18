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

    @classmethod
    def uniqueID(cls, items):
        """returns a unique id of length 6 for folder"""
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


    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        """generates a id string"""
        return ''.join(random.choice(chars) for i in range(size))


    @classmethod
    def lastOrder(cls):
        """returns the highest order value + 1 of folders table"""
        with user_database.get_session(cls, acquire=True) as session:
            values = Utils.convert_result(session.execute(
                select([user_database.Folders.order])))
            if not values:
                return 1
            return max([x['order'] for x in values]) + 1


    @staticmethod
    def remove_invalid_chars(filename):
        """Remove invalid characters from string"""
        invalid_chars = '<>:"/\|?*'
        return ''.join(c for c in filename if c not in invalid_chars)
