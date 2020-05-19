import os
import ffmpeg
import logging

from hashlib import md5
from datetime import datetime
from urllib.parse import unquote
from sqlalchemy import delete, insert, select, update

from PySide2 import QtQuick, QtGui, QtCore, QtQml

from .utils import Utils
from . import user_database


class ThumbnailProvider(QtQuick.QQuickImageProvider):
    THUMB_DIR = Utils.fv_path("thumbs")

    def __init__(self):
        super().__init__(QtQuick.QQuickImageProvider.Image, QtQml.QQmlImageProviderBase.ForceAsynchronousImageLoading)

    def requestImage(self, file, size, requestedSize):
        """hash: filepath hash string"""
        filepath = unquote(file)
        thumbnail = ThumbnailCache.requestThumbnail(filepath, requestedSize)

        return thumbnail


class ThumbnailCache:
    logger = logging.getLogger("ThumbnailCache")

    THUMBNAIL_EXT = ".png"
    THUMBS_DIR = Utils.fv_path("thumbs")
    FFPROBE_PATH = Utils.bin_path("ffprobe")
    FFMPEG_PATH = Utils.bin_path("ffmpeg")

    """Interface with thumbnail cache on filesystem.  Provides functionality for generating
          and loading thumbnails for files.
       - Thumbnail Table
          - id
          - thumb filename
          - timestamp of thumbnail creation
    """

    @staticmethod
    def requestThumbnail(filepath, size) -> QtGui.QImage:
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
    def getExistingThumbnail(hash) -> QtGui.QImage:
        thumb_path = ThumbnailCache.getAbsoluteThumbPath(hash)

        if not os.path.exists(thumb_path):
            return None

        thumb = QtGui.QImage(thumb_path)
        return thumb

    @staticmethod
    def generateThumbnail(filepath, filepath_hash, size: QtCore.QSize, modified_time, updateItem=False) -> QtGui.QImage:
        thumb_path = ThumbnailCache.getAbsoluteThumbPath(filepath_hash)

        filetype = "video"
        thumb = None
        fileSaved = False

        imageReader = QtGui.QImageReader(filepath)
        imageReader.setDecideFormatFromContent(True)
        if imageReader.canRead():
            filetype = "image"

        if filetype == "image":
            thumb = ThumbnailCache.generateImageThumbnail(filepath, size)
        elif filetype == "video":
            thumb, fileSaved = ThumbnailCache.generateVideoThumbnail(filepath, size, thumb_path)
        elif filetype == "document":
            thumb = ThumbnailCache.generateDocumentThumbnail(filepath, size)
        elif filetype == "audio":
            thumb = ThumbnailCache.generateAudioThumbnail(filepath, size)
        elif filetype == "file":
            thumb = ThumbnailCache.generateFileThumbnail(filepath, size)

        if thumb:
            ThumbnailCache.saveThumbnail(thumb, thumb_path, filepath_hash, modified_time, updateItem, fileSaved)
        if not thumb:
            thumb = QtGui.QImage(size, QtGui.QImage.Format_RGB32)
            thumb.fill(QtCore.Qt.red)

        return thumb

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
    def generateImageThumbnail(image_path, size: QtCore.QSize) -> QtGui.QImage:
        """generates thumbnail of image at requested size."""
        image = QtGui.QImage(image_path)
        image = image.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return image

    @staticmethod
    def generateVideoThumbnail(video_path, size: QtCore.QSize, thumb_path) -> (QtGui.QImage, bool):
        """generates thumbnail of video at requested size."""

        thumb_dir = os.path.dirname(thumb_path)
        if not os.path.exists(thumb_dir):
            os.makedirs(thumb_dir)

        probe = ffmpeg.probe(video_path, cmd=ThumbnailCache.FFPROBE_PATH)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        total_duration = None
        if video_stream and "duration" in video_stream:
            total_duration = float(video_stream["duration"])
        elif "format" in probe and "duration" in probe["format"]:   # some containers store duration in format instead of stream
            total_duration = float(probe["format"]["duration"])

        if not total_duration:
            return None, False

        time_str = Utils.seconds_to_ffmpeg_timestamp(total_duration * 0.24)

        _, error = ffmpeg \
            .input(video_path, ss=time_str) \
            .filter('scale', size.width(), -1) \
            .output(thumb_path, vframes=1) \
            .run(cmd=ThumbnailCache.FFMPEG_PATH, quiet=True, overwrite_output=True)

        if "Output file is empty" in error.decode("utf-8"):
            return None, False

        thumb = QtGui.QImage(thumb_path)
        return thumb, True

    @staticmethod
    def generateDocumentThumbnail(pdf_path, size: QtCore.QSize) -> QtGui.QImage:
        """generates thumbnail of pdf at requested size."""
        return None

    @staticmethod
    def generateAudioThumbnail(pdf_path, size: QtCore.QSize) -> QtGui.QImage:
        """generates thumbnail of pdf at requested size."""
        return None

    @staticmethod
    def generateFileThumbnail(file_path, size: QtCore.QSize) -> QtGui.QImage:
        """generates thumbnail of non video image or pdf file at requested size."""
        return None
