import base64
import imghdr
import os
import re
from mimetypes import guess_extension
from time import time
from urllib.parse import unquote

import requests
from sqlalchemy import insert, delete

import FukurouViewer
from FukurouViewer import user_database
from FukurouViewer.config import Config
from FukurouViewer.foundation import Foundation
from FukurouViewer.gallery import GenericGallery
from FukurouViewer.user_database import Collection


class DownloadItem:
    FAVICON_PATH = Config.fv_path("favicons")
    ETA_LIMIT = 2592000
    USER_AGENT = "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"

    def __init__(self, downloadManager, msg):
        self.downloadManager = downloadManager
        self.signals = downloadManager.signals

        self.task = msg.get("task")
        self.resume = False

        if self.task == "saveManga":
            self.url = msg.get("url")
            return

        self.id = msg.get("id", None)
        if not self.id:
            self.set_id()

        self.url = msg.get('srcUrl')
        self.page_url = msg.get('pageUrl')
        self.domain = msg.get('domain')

        self.send_headers = dict()
        self.send_headers["User-Agent"] = self.USER_AGENT
        for key, value in msg.get("headers", {}).items():
            self.send_headers[key] = value

        self.cookies = dict()
        for cookie in msg.get('cookies', []):
            self.cookies[cookie[0]] = cookie[1]

        self.favicon_url = msg.get('favicon_url', "")
        self.download_favicon()

        # folder
        self.folder = Collection.get_by_id(msg.get("uid", None))

        self.dir = msg.get("dir", self.folder.absolute_path)
        self.filepath = msg.get("filepath", None)
        self.tmp_filepath = msg.get("tmp_filepath", None)
        self.filename = msg.get("filename", None)  # basename and extension filename.txt
        self.base_name = msg.get("base_name", None)  # filename before .ext
        self.ext = msg.get("ext", None)
        self.total_size = msg.get("total_size", None)
        if self.total_size:
            self.total_size_str = Foundation.format_size(self.total_size)
        self.downloaded = msg.get("downloaded", 0)

        if self.filepath:
            self.resume = True

        self.gallery_url = msg.get("galleryUrl", "")
        self.start_time = time()

        if self.task == "load":
            self.task = "save"
        else:
            self.get_information()
            with user_database.get_session(self) as session:
                session.execute(insert(user_database.Downloads).values(
                    {
                        "id": self.id,
                        "filepath": self.filepath,
                        "filename": self.filename,
                        "base_name": self.base_name,
                        "ext": self.ext,
                        "total_size": self.total_size,
                        "srcUrl": self.url,
                        "pageUrl": self.page_url,
                        "domain": self.domain,
                        "favicon_url": self.favicon_url,
                        "timestamp": self.start_time,
                        "folder_id": self.folder.id
                    }))

    def get_information(self):
        """Downloads item information before downloading gets
             filename, size, tmp_path"""
        response = requests.head(self.url, headers=self.send_headers, cookies=self.cookies, timeout=10,
                                 allow_redirects=True)
        headers = response.headers

        # content-length
        self.total_size = int(headers.get("Content-Length", 0))
        self.total_size_str = Foundation.format_size(self.total_size)

        # filename
        contdisp = re.findall("filename=(.+)", headers.get("Content-Disposition", ""))
        if contdisp:
            self.filename = contdisp[0].split(";")[0].strip('\'"')

        # extension
        if "Content-Type" in headers:
            self.ext = guess_extension(headers.get("Content-Type").split()[0].rstrip(";"))

        if not self.filename:  # no filename in Content-Disposition header
            self.set_filename()
            self.filename = Foundation.remove_invalid_chars(self.filename)

        temp_base_name, ext = os.path.splitext(self.filename)
        if ext:  # have extension
            self.ext = ext
        self.ext = self.ext_convention(self.ext)

        if not self.base_name:  # no recommended basename provided
            self.base_name = temp_base_name

        self.filepath = os.path.join(self.dir, ''.join((self.base_name, self.ext)))

        # check and rename if file already exists and not resume
        count = 1
        while os.path.isfile(self.filepath) or os.path.isfile(self.filepath + ".part"):
            self.filename = ''.join((self.base_name, ' (', str(count), ')', self.ext))
            self.filepath = os.path.join(self.dir, self.filename)
            count += 1
        self.tmp_filepath = self.filepath + ".part"
        open(self.tmp_filepath, 'a').close()  # create .part temp file

    def set_id(self):
        self.id = FukurouViewer.app.downloadsModel.createID()

    def download_favicon(self):
        """Download favicon if not already downloaded"""
        if self.favicon_url:
            favicon_path = os.path.join(self.FAVICON_PATH, self.domain + ".ico")
            encoding = None
            if self.favicon_url.startswith("data:"):
                extension, encoding = self.getDataType(self.favicon_url)
                if extension is not None and encoding is not None:
                    favicon_path = os.path.join(self.FAVICON_PATH, self.domain + extension)

            # always 'update' favicon if it exists

            if encoding is None:
                icon = requests.get(self.favicon_url, headers=self.send_headers, cookies=self.cookies, timeout=10)
                with open(favicon_path, "wb") as f:
                    for chunk in icon:
                        f.write(chunk)
            else:
                byte_obj = self.favicon_url.split(',')[1]
                if encoding == "base64":
                    data = base64.b64decode(byte_obj)
                elif encoding == "base32":
                    data = base64.b32decode(byte_obj)
                elif encoding == "base16":
                    data = base64.b16decode(byte_obj)
                elif encoding == "base85":
                    data = base64.b85decode(byte_obj)
                else:
                    return

                if not data:
                    return

                with open(favicon_path, "wb") as f:
                    f.write(data)

    # Given data string 'data:image/png;base64,BAKFKDSlasd...
    # return tuple of format and encoding
    @staticmethod
    def getDataType(data_str):
        format_regex = re.findall('(?<=:)(.*?)(?=,)', data_str)
        parts = []
        if format_regex:
            parts = format_regex[0].split(";")
        if len(parts) == 0:
            return None, None
        mimetype = parts[0]
        encoding = parts[1]
        return guess_extension(mimetype), encoding

    def set_filename(self):
        """Sets self.filename from url"""
        full_filename = self.url.split('/')[-1]  # get filename from srcUrl
        full_filename = full_filename.split('?')[0]  # strip query string parameters
        full_filename = full_filename.split('#')[0]  # strip anchor
        full_filename = full_filename.split(':')[0]  # string delimiter
        full_filename = unquote(full_filename)
        self.filename = full_filename

    @staticmethod
    def ext_convention(ext):
        """Formats extension using desired convention '.JPG' -> '.jpg' """
        if ext.lower() in ['.jpeg', '.jpe', '.jpglarge']:
            return '.jpg'
        return ext.lower()

    def fix_image_extension(self):
        """checks image file headers and renames image to proper extension when necessary"""
        format = imghdr.what(self.filepath)
        if not format:  # not image so do nothing
            return

        format = self.ext_convention(''.join(('.', format)))
        _, ext = os.path.splitext(self.filepath)

        if ext == format:
            return

        dirpath = os.path.dirname(self.filepath)
        self.filename = ''.join((self.base_name, format))
        newpath = os.path.join(dirpath, self.filename)

        count = 1
        while os.path.isfile(newpath):
            self.filename = ''.join((self.base_name, ' (', str(count), ')', format))
            newpath = os.path.join(dirpath, self.filename)
            count += 1
        os.rename(self.filepath, newpath)
        self.filepath = newpath
        self.signals.update.emit({"id": self.id, "filename": self.filename, "filepath": self.filepath})

    def get_cookie_str(self):
        """returns string of cookies for pycurl"""
        cookies_str = ""
        for key, value in self.cookies.items():
            cookies_str += " %s=%s;" % (key, value)
        return cookies_str

    def finish(self):
        finish_time = time()
        os.rename(self.tmp_filepath, self.filepath)
        self.fix_image_extension()

        self.signals.finish.emit(self.id, finish_time, self.total_size)

        with user_database.get_session(self, acquire=True) as session:
            session.execute(delete(user_database.Downloads).where(user_database.Downloads.id == self.id))

            # add to history table in database
            result = session.execute(insert(user_database.History).values(
                {
                    "filename": self.filename,
                    "src_url": self.url,
                    "page_url": self.page_url,
                    "domain": self.domain,
                    "time_added": finish_time,
                    "filepath": self.filepath,
                    "favicon_url": self.favicon_url,
                    "folder_id": self.folder.id
                }))
            db_id = int(result.inserted_primary_key[0])

        kwargs = {"url": self.page_url,
                  "domain": self.domain,
                  "history_item": db_id,
                  "galleryUrl": self.gallery_url}

        gal = GenericGallery(**kwargs)
        self.downloadManager.queueSearch(gal)
