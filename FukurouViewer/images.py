import os
from abc import abstractmethod
from typing import Optional, Union
from urllib.parse import unquote

import ffmpeg
from PySide2 import QtQuick, QtGui, QtCore
from PySide2.QtCore import QSize

import FukurouViewer
from FukurouViewer import Utils
from FukurouViewer.filetype import FileType
from FukurouViewer.foundation import FileItem, FileSystemItem, DirectoryItem
from FukurouViewer.gallery import ZipArchiveGallery, DirectoryGallery


class FullImageProvider(QtQuick.QQuickImageProvider):
    def __init__(self):
        super().__init__(QtQuick.QQuickImageProvider.Image)#, QtQml.QQmlImageProviderBase.ForceAsynchronousImageLoading)

    def requestImage(self, id, size: QSize, requestedSize: QSize):
        image, file = ImageGenerator.requestImage(id, requestedSize)
        return image


class ImageBuffer(object):

    @staticmethod
    def isBufferFilepath(filepath: str):
        return filepath.startswith(FileItem.BUFFER_SUB_PROVIDER)

    @staticmethod
    def getFilepath(id: str):
        return id[len(FileItem.BUFFER_SUB_PROVIDER):]

    @staticmethod
    def getFileItem(id: str) -> FileSystemItem:
        filepath = ImageBuffer.getFilepath(id)
        return FukurouViewer.app.galleryGridModel.getFile(filepath)


class ImageGenerator(object):
    FFPROBE_PATH = Utils.bin_path("ffprobe")
    FFMPEG_PATH = Utils.bin_path("ffmpeg")

    @staticmethod
    def requestImage(id: str, size: QSize = None) -> (QtGui.QImage, FileSystemItem):
        id = unquote(id)

        if ImageBuffer.isBufferFilepath(id):
            item = ImageBuffer.getFileItem(id)
        else:
            item = FileSystemItem.createItem(id)

        image = ImageGenerator.getImage(item)

        if image is None:
            if size is None:
                size = QSize(200, 280)
            image = QtGui.QImage(size, QtGui.QImage.Format_RGB32)
            image.fill(QtCore.Qt.red)
        elif size is not None:
            image = image.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        return image, item

    @staticmethod
    def getImage(item: Union[FileItem, DirectoryItem]) -> QtGui.QImage or None:
        if item is None or (not item.exists and not item.isBuffer):
            return None

        image = None
        if item.type is FileType.IMAGE:
            image = ImageGenerator.generateFromImage(item)
        elif item.type == FileType.VIDEO:
            image = ImageGenerator.generateFromVideo(item)
        elif item.type is FileType.ARCHIVE:
            image = ImageGenerator.generateFromArchive(item)
        elif item.type is FileType.DOCUMENT:
            image = ImageGenerator.generateFromDocument(item)
        elif item.type is FileType.AUDIO:
            image = ImageGenerator.generateFromAudio(item)
        elif item.type is FileType.FILE:
            image = ImageGenerator.generateFromFile(item)
        elif item.type is FileType.DIRECTORY:
            image = ImageGenerator.generateFromDirectory(item)

        return image

    @staticmethod
    def generateFromImage(file: FileItem) -> QtGui.QImage:
        """generates thumbnail of image at requested size."""
        if file.isBuffer:
            image = QtGui.QImage()
            image.loadFromData(file.data)
        else:
            image = QtGui.QImage(file.filepath)

        return image

    @staticmethod
    def generateFromVideo(file: FileItem) -> QtGui.QImage or None:
        """generates thumbnail of video at requested size."""
        probe = ffmpeg.probe(file.filepath, cmd=ImageGenerator.FFPROBE_PATH)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        total_duration = None
        if video_stream and "duration" in video_stream:
            total_duration = float(video_stream["duration"])
        # some containers store duration in format instead of stream
        elif "format" in probe and "duration" in probe["format"]:
            total_duration = float(probe["format"]["duration"])

        if not total_duration:
            return None

        time_str = Utils.seconds_to_ffmpeg_timestamp(total_duration * 0.24)

        out, error = ffmpeg \
            .input(file.filepath, ss=time_str) \
            .output("pipe:", vframes=1, format='image2', vcodec='png') \
            .run(cmd=ImageGenerator.FFMPEG_PATH, quiet=True, overwrite_output=True)

        if "Output file is empty" in error.decode("utf-8"):
            return None

        thumb = QtGui.QImage.fromData(out)
        return thumb

    @staticmethod
    def generateFromDocument(file: FileItem) -> QtGui.QImage or None:
        """generates thumbnail of pdf at requested size."""
        return None

    @staticmethod
    def generateFromAudio(file: FileItem) -> QtGui.QImage or None:
        """generates thumbnail of pdf at requested size."""
        return None

    @staticmethod
    def generateFromFile(file: FileItem) -> QtGui.QImage or None:
        """generates thumbnail of non video image or pdf file at requested size."""
        return None

    @staticmethod
    def generateFromArchive(file: FileItem) -> QtGui.QImage or None:
        archive = ZipArchiveGallery(file)
        return ImageGenerator.getImage(archive.cover)

    @staticmethod
    def generateFromDirectory(directory: DirectoryItem) -> QtGui.QImage or None:
        gallery = DirectoryGallery(directory)
        return ImageGenerator.getImage(gallery.cover)
