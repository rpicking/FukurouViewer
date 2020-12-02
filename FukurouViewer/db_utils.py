from typing import Optional, List, Union

from sqlalchemy import select, update, insert

from FukurouViewer import user_database, Utils


class DBUtils:

    @staticmethod
    def select_first(table, where=None, order=None, limit=None, offset=None) -> Optional[dict]:
        results = DBUtils.select(table, where, order, limit, offset)
        if results is not None and len(results) > 0:
            return results[0]
        return None

    @staticmethod
    def select(table, where=None, order=None, limit=None, offset=None) -> Optional[list]:
        with user_database.get_session(DBUtils, acquire=True) as session:
            query = select([table])
            if where is not None:
                query = query.where(where)
            if order is not None:
                query = query.order(order)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            return Utils.convert_result(session.execute(query))

    @staticmethod
    def update(table, values: dict, where=None):
        with user_database.get_session(DBUtils, acquire=True) as session:
            query = update(table)
            if where is not None:
                query = query.where(where)
            session.execute(query.values(values))

    @staticmethod
    def insert(table, values: Union[dict, List[dict]]) -> List[int]:
        """Inserts values dict(s) into given table, returning a list of all primary key(s) inserted"""
        with user_database.get_session(DBUtils, acquire=True) as session:
            query = insert(table)

            results = session.execute(query.values(values))
            return results.inserted_primary_key
