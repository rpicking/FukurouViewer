
from PyQt5 import QtQuick, QtGui


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
    def requestThumbnail(filepath, size):
        """Given filepath return thumbnail loaded from disk or generate, save and return new thumbnail"""

    def generateImageThumbnail(thumbnail_path, image_path, size):
        """generates thumbnail of image at requested size."""

    def generateVideoThumbnail(thumbnail_path, image_path, size):
        """generates thumbnail of video at requested size."""

    def generatePdfThumbnail(thumbnail_path, image_path, size):
        """generates thumbnail of pdf at requested size."""

    def generateFileThumbnail(thumbnail_path, image_path, size):
        """generates thumbnail of non video image or pdf file at requested size."""
