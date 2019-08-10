
from PySide2 import QtQuick, QtGui

from .utils import Utils


class ThumbnailProvider(QtQuick.QQuickImageProvider):
    THUMB_DIR = Utils.fv_path("thumbs")

    def __init__(self):
        QtQuick.QQuickImageProvider.__init__(self, QtQuick.QQuickImageProvider.Pixmap)
    
    def requestImage(self, hash, requestedSize):
        """hash: filepath hash string"""
        width = requestedSize.width()
        height = requestedSize.height()


class ThumbnailCache:
    """Interface with thumbnail cache on filesystem.  Provides functionality for generating
          and loading thumbnails for files.
       - Thumbnail Table
          - id
          - thumbnail hash
          - file path
    """
    def requestThumbnail(self, filepath, size):
        """Given filepath return thumbnail loaded from disk or generate, save and return new thumbnail"""

    def generateImageThumbnail(self, thumbnail_path, image_path, size):
        """generates thumbnail of image at requested size."""

    def generateVideoThumbnail(self, thumbnail_path, image_path, size):
        """generates thumbnail of video at requested size."""

    def generatePdfThumbnail(self, thumbnail_path, image_path, size):
        """generates thumbnail of pdf at requested size."""

    def generateFileThumbnail(self, thumbnail_path, image_path, size):
        """generates thumbnail of non video image or pdf file at requested size."""
