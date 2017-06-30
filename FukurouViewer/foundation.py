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
    def uniqueId(cls):
        with user_database.get_session(cls, acquire=True) as session:
            used_ids = Utils.convert_result(session.execute(
                select([user_database.Folders.uid])))
        while True:
            id = cls.id_generator()
            if not any(d['uid'] == id for d in used_ids):
                return id


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

    @classmethod
    def testfunction(cls):
        payload = {'task': 'sync'}
        with user_database.get_session(cls, acquire=True) as session:
                payload['folders'] = Utils.convert_result(session.execute(
                    select([user_database.Folders])))
                print("HAY")
