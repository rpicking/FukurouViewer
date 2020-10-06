from typing import Optional

from sqlalchemy import select

from FukurouViewer import user_database, Utils
from FukurouViewer.user_database import Folder


class DBUtils:

    @staticmethod
    def get_folder(folder_uid: str) -> Optional[Folder]:
        folder = DBUtils.select_first(user_database.Folder, where=user_database.Folder.uid == folder_uid)
        if folder is None:
            return None

        return None if folder is None else Folder(**folder)

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
