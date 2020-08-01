import os
import logging

from hashlib import md5
from datetime import datetime
from urllib.parse import unquote

from PySide2.QtCore import QSize
from sqlalchemy import delete, insert, select, update

from PySide2 import QtQuick, QtGui, QtCore, QtQml

from .images import ImageGenerator
from .utils import Utils
from . import user_database


class ThumbnailProvider(QtQuick.QQuickImageProvider):
    def __init__(self):
        super().__init__(QtQuick.QQuickImageProvider.Image)#, QtQml.QQmlImageProviderBase.ForceAsynchronousImageLoading)

    def requestImage(self, id, size: QSize, requestedSize: QSize):
        id = unquote(id)
        thumbnail = ThumbnailCache.requestImage(id, requestedSize)
        return thumbnail


class ThumbnailCache(object):
    logger = logging.getLogger("ThumbnailCache")

    THUMBS_DIR = Utils.fv_path("thumbs")
    THUMBNAIL_EXT = ".png"
    TMP_THUMB_PATH = os.path.join(THUMBS_DIR, "tmp" + THUMBNAIL_EXT)

    """Interface with thumbnail cache on filesystem.  Provides functionality for generating
          and loading thumbnails for files.
       - Thumbnail Table
          - id
          - thumb filename
          - timestamp of thumbnail creation
    """

    @staticmethod
    def requestImage(filepath: str, size: QSize) -> QtGui.QImage:
        """Given filepath return thumbnail loaded from disk or generate, save and return new thumbnail"""
        path_hash = md5(filepath.encode("utf-8")).hexdigest()

        modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        updateItem = False

        with user_database.get_session(ThumbnailCache, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Thumbnail]).where(user_database.Thumbnail.hash == path_hash)))

        if results:
            result = results[0]
            thumb_timestamp = datetime.fromtimestamp(result.get("timestamp"))

            if modified_time == thumb_timestamp:    # file hasn't been changed since thumbnail was created
                thumb = ThumbnailCache.getExistingThumbnail(path_hash)
                if thumb:
                    return thumb
            updateItem = True

        return ThumbnailCache.generateThumbnail(filepath, path_hash, size, modified_time, updateItem)

    @staticmethod
    def getAbsoluteThumbPath(hash: str) -> str:
        thumb_dir = os.path.join(
            ThumbnailCache.THUMBS_DIR,
            hash[:2],
            hash[2:4])

        return os.path.join(thumb_dir, hash + ThumbnailCache.THUMBNAIL_EXT)

    @staticmethod
    def getExistingThumbnail(hash) -> QtGui.QImage or None:
        thumb_path = ThumbnailCache.getAbsoluteThumbPath(hash)

        if not os.path.exists(thumb_path):
            return None

        thumb = QtGui.QImage(thumb_path)
        return thumb

    @staticmethod
    def generateThumbnail(filepath: str, filepath_hash: str, size: QtCore.QSize, modified_time, updateItem=False) -> QtGui.QImage:
        thumb_path = ThumbnailCache.getAbsoluteThumbPath(filepath_hash)

        thumb, file = ImageGenerator.requestImage(filepath, size)

        if thumb and not file.isBuffer:
            ThumbnailCache.saveThumbnail(thumb, thumb_path, filepath_hash, modified_time, updateItem)
        if not thumb:
            thumb = QtGui.QImage(size, QtGui.QImage.Format_RGB32)
            thumb.fill(QtCore.Qt.red)

        return thumb

    @staticmethod
    def saveThumbnail(image: QtGui.QImage, thumb_path: str, hash, modified_time, updateItem):
        """ Save the image to file and either update or create a table entry for the thumbnail """

        thumb_dir = os.path.dirname(thumb_path)
        if not os.path.exists(thumb_dir):
            os.makedirs(thumb_dir)

        saved = image.save(thumb_path)
        if not saved:
            ThumbnailCache.logger.error(thumb_path + " thumbnail not saved")

        payload = {
            "hash": hash,
            "timestamp": modified_time.timestamp()
        }

        with user_database.get_session(ThumbnailCache, acquire=True) as session:
            if updateItem:
                session.execute(update(user_database.Thumbnail).where(
                    user_database.Thumbnail.hash == hash).values({"timestamp": modified_time}))
            else:
                session.execute(insert(user_database.Thumbnail).values(payload))
