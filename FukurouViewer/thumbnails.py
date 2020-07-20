import os
from typing import Optional

import ffmpeg
import logging
import zipfile

from hashlib import md5
from datetime import datetime
from urllib.parse import unquote

from PySide2.QtCore import QSize
from sqlalchemy import delete, insert, select, update

from PySide2 import QtQuick, QtGui, QtCore

import FukurouViewer
from .filetype import FileType
from .foundation import FileItem
from .gallery import GalleryArchive
from .utils import Utils
from . import user_database


class ThumbnailProvider(QtQuick.QQuickImageProvider):
    THUMB_DIR = Utils.fv_path("thumbs")

    def __init__(self):
        super().__init__(QtQuick.QQuickImageProvider.Image) #, QtQml.QQmlImageProviderBase.ForceAsynchronousImageLoading)

    def requestImage(self, id, size: QSize, requestedSize: QSize):
        """hash: filepath hash string"""
        id = unquote(id)

        if ThumbnailBuffer.isBufferFilepath(id):
            thumbnail = ThumbnailBuffer.requestThumbnail(id, requestedSize)
        else:
            thumbnail = ThumbnailCache.requestThumbnail(id, requestedSize)

        return thumbnail


class ThumbnailBuffer:

    @staticmethod
    def isBufferFilepath(filepath: str):
        return filepath.startswith(FileItem.BUFFER_SUB_PROVIDER)

    @staticmethod
    def getFilepath(id: str):
        return id[len(FileItem.BUFFER_SUB_PROVIDER):]

    @staticmethod
    def requestThumbnail(id: str, size: QSize) -> Optional[QtGui.QImage]:
        filepath = ThumbnailBuffer.getFilepath(id)
        file = FukurouViewer.app.galleryGridModel.getFile(filepath)
        thumb, _ = ThumbnailCache.getThumbnailCached(file, size)

        return thumb


class ThumbnailCache:
    logger = logging.getLogger("ThumbnailCache")

    THUMBNAIL_EXT = ".png"
    THUMBS_DIR = Utils.fv_path("thumbs")
    FFPROBE_PATH = Utils.bin_path("ffprobe")
    FFMPEG_PATH = Utils.bin_path("ffmpeg")

    TMP_THUMB_PATH = os.path.join(THUMBS_DIR, "tmp" + THUMBNAIL_EXT)

    """Interface with thumbnail cache on filesystem.  Provides functionality for generating
          and loading thumbnails for files.
       - Thumbnail Table
          - id
          - thumb filename
          - timestamp of thumbnail creation
    """

    @staticmethod
    def requestThumbnail(filepath: str, size: QSize) -> QtGui.QImage:
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
    def getAbsoluteThumbPath(hash) -> str:
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
    def generateThumbnail(filepath, filepath_hash, size: QtCore.QSize, modified_time, updateItem=False) -> QtGui.QImage:
        thumb_path = ThumbnailCache.getAbsoluteThumbPath(filepath_hash)

        file = FileItem(filepath)
        thumb, thumbExists = ThumbnailCache.getThumbnailCached(file, size, thumb_path)

        if thumb:
            ThumbnailCache.saveThumbnail(thumb, thumb_path, filepath_hash, modified_time, updateItem, thumbExists)
        if not thumb:
            thumb = QtGui.QImage(size, QtGui.QImage.Format_RGB32)
            thumb.fill(QtCore.Qt.red)

        return thumb

    @staticmethod
    def getThumbnailCached(file: FileItem, size: QSize, thumb_path: Optional[str] = None) -> (QtGui.QImage, bool):
        thumb = None
        fileSaved = False

        deleteThumb = thumb_path is None
        if deleteThumb:
            thumb_path = ThumbnailCache.TMP_THUMB_PATH

        # generate thumbnail
        if file.type is FileType.IMAGE:
            thumb = ThumbnailCache.generateImageThumbnail(file, size)
        elif file.type == FileType.VIDEO:
            thumb, fileSaved = ThumbnailCache.generateVideoThumbnail(file, size, thumb_path)
        elif file.type is FileType.ARCHIVE:
            thumb = ThumbnailCache.generateArchiveThumbnail(file, size)
        elif file.type is FileType.DOCUMENT:
            thumb = ThumbnailCache.generateDocumentThumbnail(file, size)
        elif file.type is FileType.AUDIO:
            thumb = ThumbnailCache.generateAudioThumbnail(file, size)
        elif file.type is FileType.FILE:
            thumb = ThumbnailCache.generateFileThumbnail(file, size)

        return thumb, fileSaved

    @staticmethod
    def saveThumbnail(image: QtGui.QImage, thumb_path, hash, modified_time, updateItem, fileSaved):
        """ Save the image to file and either update or create a table entry for the thumbnail """

        if not fileSaved:
            thumb_dir = os.path.dirname(thumb_path)
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)

            saved = image.save(thumb_path, "PNG", -1)
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
                return

            session.execute(insert(user_database.Thumbnail).values(payload))

    @staticmethod
    def generateImageThumbnail(file: FileItem, size: QSize) -> QtGui.QImage:
        """generates thumbnail of image at requested size."""
        if file.isBuffer:
            image = QtGui.QImage()
            image.loadFromData(file.data)
        else:
            image = QtGui.QImage(file.filepath)

        image = image.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return image

    @staticmethod
    def generateVideoThumbnail(file: FileItem, size: QSize, thumb_path: str, deleteThumb=False) -> (QtGui.QImage, bool):
        """generates thumbnail of video at requested size."""

        thumb_dir = os.path.dirname(thumb_path)
        if not os.path.exists(thumb_dir):
            os.makedirs(thumb_dir)

        probe = ffmpeg.probe(file.filepath, cmd=ThumbnailCache.FFPROBE_PATH)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        total_duration = None
        if video_stream and "duration" in video_stream:
            total_duration = float(video_stream["duration"])
        # some containers store duration in format instead of stream
        elif "format" in probe and "duration" in probe["format"]:
            total_duration = float(probe["format"]["duration"])

        if not total_duration:
            return None, False

        time_str = Utils.seconds_to_ffmpeg_timestamp(total_duration * 0.24)

        _, error = ffmpeg \
            .input(file.filepath, ss=time_str) \
            .filter('scale', size.width(), -1) \
            .output(thumb_path, vframes=1) \
            .run(cmd=ThumbnailCache.FFMPEG_PATH, quiet=True, overwrite_output=True)

        if "Output file is empty" in error.decode("utf-8"):
            return None, False

        thumb = QtGui.QImage(thumb_path)

        if deleteThumb:
            os.remove(thumb_path)

        return thumb, True

    @staticmethod
    def generateDocumentThumbnail(pdf_path, size: QSize) -> QtGui.QImage or None:
        """generates thumbnail of pdf at requested size."""
        return None

    @staticmethod
    def generateAudioThumbnail(pdf_path, size: QSize) -> QtGui.QImage or None:
        """generates thumbnail of pdf at requested size."""
        return None

    @staticmethod
    def generateFileThumbnail(file: FileItem, size: QSize) -> QtGui.QImage or None:
        """generates thumbnail of non video image or pdf file at requested size."""
        return None

    @staticmethod
    def generateArchiveThumbnail(file: FileItem, size: QSize) -> QtGui.QImage or None:
        try:

            archive = GalleryArchive(file)
            thumb, _ = ThumbnailCache.getThumbnailCached(archive.cover, size)
            return thumb



            # archive = zipfile.ZipFile(file.filepath, "r")
            # infoList = archive.infolist()
            #
            # if len(infoList) < 1:
            #     return None
            #
            # coverZipInfo = infoList[0]
            # data = archive.read(coverZipInfo.filename)
            # file = FileItem(coverZipInfo.filename, data=data)
            # thumb, _ = ThumbnailCache.getThumbnailBuffered(file, None, size)
            # return thumb

        except (zipfile.BadZipFile, zipfile.LargeZipFile) as e:
            print(e)

        return None
