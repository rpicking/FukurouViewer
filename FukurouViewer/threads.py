import os
import re
import sys
import json
import queue
import imghdr
import pycurl
import random
import string
import struct
import certifi
import requests
import linecache
import threading
import subprocess

from PyQt5 import QtCore
from time import clock, time
from urllib.parse import unquote
from collections import namedtuple
from mimetypes import guess_extension
from watchdog.observers import Observer
from sqlalchemy import delete, insert, select, update
from watchdog.events import FileSystemEventHandler

import FukurouViewer
from FukurouViewer import exceptions
from . import user_database
from .request_manager import request_manager, ex_request_manager
from .utils import Utils
from .config import Config
from .logger import Logger
from .foundation import Foundation
from .search import Search
from .gallery import GenericGallery

import pygame.mixer as mixer

mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)


class BaseThread(threading.Thread, Logger):
    THREAD_COUNT = 4

    def __init__(self, **kwargs):
        super().__init__()
        self.daemon = True
        self.queue = queue.Queue()

    def setup(self):
        pass
        # basesignals.exception.connect

    def _run(self):
        raise NotImplementedError

    def close(self):
        pass

    @classmethod
    def generate_workers(self, global_queue, target):
        worker = namedtuple("worker", "thread data errors")
        workers = []
        for _ in range(0, self.THREAD_COUNT):
            data_queue = queue.Queue()
            error_queue = queue.Queue()
            thread = threading.Thread(target=target, args=(global_queue, data_queue, error_queue))
            workers.append(worker(thread, data_queue, error_queue))
        return workers

    def run(self):
        while True:
            restart = False
            try:
                self._run()
            except (KeyboardInterrupt, SystemExit):
                return
            except Exception:
                return
                # makes sure that error doesn't kill program?
                ex_info = sys.exc_info()
                extype = ex_info[0]
                exvalue = ex_info[1]
                if issubclass(extype, exceptions.BaseException):
                    restart = exvalue.thread_restart
                # basesignal exception emit
                if restart: # empty out queue
                    try:
                        while True:
                            self.queue.get_nowait()
                    except queue.Empty:
                        pass


class MessengerThread(BaseThread):
    THREAD_COUNT = 1
    PIPE_PATH = "/tmp/fukurou.fifo"
    WIN_PIPE_PATH = r'\\.\pipe\fukurou_pipe'

    def __init__(self, _windows = True):
        super().__init__()
        self.windows = _windows

        if self.windows:
            self.pipe = win32pipe.CreateNamedPipe(self.WIN_PIPE_PATH,
                                win32pipe.PIPE_ACCESS_DUPLEX,
                                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                                win32pipe.PIPE_UNLIMITED_INSTANCES,65536,65536,300,None)
            #win32pipe.ConnectNamedPipe(self.pipe, None)
            return

        # non windows platform
        self.pipe = self.PIPE_PATH
        if not os.path.exists(self.pipe):
            os.mkfifo(self.pipe)

    def setup(self):
        self.signals = Download_UI_Signals()

    def _run(self):
        win32pipe.ConnectNamedPipe(self.pipe, None)
        while True:
            try:
                # read message from messenger
                msg = self.read_message()
                # process message and perform task
                task = msg.get("task")
                if task == "sync":
                    payload = self.sync_task(msg)
                elif task == "edit":
                    payload = self.edit_task(msg)
                elif task == "delete":
                    payload = self.delete_task(msg)
                elif task == "save":
                    item = self.create_download_item(msg)
                    download_manager.queue.put(item)
                    payload = { "task": "none" } 
                elif task == "saveManga":
                    item = DownloadItem(msg)
                    download_manager.queue.put(item)
                else:   # unknown message
                    payload = { "task": "none" }

                self.send_message(payload)

                #response = self.process_message(msg)
                # send response back to messenger
                #self.send_message(response)

            except win32pipe.error as e:    # messenger has closed
                #self.logger.error("Messenger closed")
                #self.logger.error(e)
                self.pipe.Close()
                self.pipe = win32pipe.CreateNamedPipe(self.WIN_PIPE_PATH,
                                win32pipe.PIPE_ACCESS_DUPLEX,
                                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                                1,65536,65536,300,None)
                win32pipe.ConnectNamedPipe(self.pipe, None)

    def close(self):
        if self.windows:
            self.pipe.Close()
            self.logger.info("Pipe closed")
            #winsound.PlaySound("*", winsound.SND_ASYNC)
            return

        os.remove(self.pipe)

    # returns dict message from host
    def read_message(self):
        if self.windows:
            data = win32file.ReadFile(self.pipe, 4096)[1]
            msg = data.decode()
            return json.loads(msg)

        with open(self.pipe, "r") as pipe:
            msg = pipe.readline()
            msg = msg.decode()
            return json.loads(msg)

    # send message to host
    def send_message(self, MSG):
        byte_message = str.encode(json.dumps(MSG))
        if self.windows:
            win32file.WriteFile(self.pipe, byte_message)
            return

        with open(self.pipe, "w") as pipe:
            pipe.write(byte_message)

    def create_download_item(self, msg):
        """creates DownloadItem to put in queue 
            adds download item to UI """
        item = DownloadItem(msg)
        self.signals.create.emit(item)
        return item

    # sync folders with extension
    def sync_task(self, msg):
        payload = {'task': 'sync'}
        with user_database.get_session(self, acquire=True) as session:
            payload['folders'] = Utils.convert_result(session.execute(
                select([user_database.Folders.name, user_database.Folders.uid]).order_by(user_database.Folders.order)))
            #payload['folders'] = Utils.convert_result(session.execute(
                #   select([user_database.Folders]).order_by(user_database.Folders.order)))
        return payload

    # edit folder info in database
    def edit_task(self, msg):
        folders = json.loads(msg.get('folders'))

        for folder in folders:
            name = folder.get('name', "")
            order = folder.get('order', "")

            values = {}
            if name:
                values['name'] = name
            if order:
                values['order'] = order

            try:
                with user_database.get_session(self, acquire=True) as session:
                        session.execute(update(user_database.Folders).where(
                            user_database.Folders.uid == folder.get('uid')).values(values))
            except Exception as e:
                self.log_exception()
                return {'task': 'edit', 'type': 'error', 'msg': 'not all folders found'}
        return {'task': 'edit', 'type': 'success'}

    # delete folder from database
    def delete_task(self, msg):
        try:
            folders = json.loads(msg.get('folders'))

            for folder in folders:
                #uid = folder.get('uid')
                self.logger.debug("deleting folder with uid: " + uid)

                with user_database.get_session(self) as session:
                    session.execute(delete(user_database.Folders).where(user_database.Folders.uid == folder.get('uid')))
                return {'type': 'success', 'task': 'delete', 'name': name, 'uid': uid}

        except Exception as e:
            self.log_exception()
            return {'task': 'delete', 'type': 'crash'}

    # logs raised general exception
    def log_exception(self):
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        self.logger.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))



if os.name == 'nt':
    import win32api
    import win32pipe
    import win32file
    messenger_thread = MessengerThread()
else:
    messenger_thread = MessengerThread(False)



class DownloadItem():
    FAVICON_PATH = Utils.fv_path("favicons")
    ETA_LIMIT = 2592000

    def __init__(self, msg):
        self.signals = Download_UI_Signals()

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

        self.send_headers = {}
        self.send_headers["User-Agent"] = "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"
        for key, value in msg.get("headers", {}).items():
            self.send_headers[key] = value

        self.cookies = {}
        for cookie in msg.get('cookies', []):
            self.cookies[cookie[0]] = cookie[1]
        
        self.favicon_url = msg.get('favicon_url', "")
        self.download_favicon()

        # folder
        self.folder = {} 
        with user_database.get_session(self, acquire=True) as session:
            folder_id = msg.get('uid', None)
            if folder_id:
                self.folder = Utils.convert_result(session.execute(
                    select([user_database.Folders]).where(user_database.Folders.uid == folder_id)))[0]
            else:
                self.folder = Utils.convert_result(session.execute(
                    select([user_database.Folders]).where(user_database.Folders.id == msg.get('folder_id'))))[0]

        self.dir = msg.get("dir", self.folder.get("path"))
        self.filepath = msg.get("filepath", None)
        self.filename =  msg.get("filename", None)    # basename and extension filename.txt
        self.base_name = msg.get("base_name", None)   # filename before .ext
        self.ext =  msg.get("ext", None)
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
                        "folder_id": self.folder.get("id")
                    })) 


    def get_information(self):
        """Downloads item information before downloading gets
             filename, size, tmp_path"""
        response = requests.head(self.url, headers=self.send_headers, cookies=self.cookies, timeout=10, allow_redirects=True)
        headers = response.headers

        # content-length
        self.total_size = int(headers.get("Content-Length", 0))
        self.total_size_str = Foundation.format_size(self.total_size)

        # filename
        contdisp = re.findall("filename=(.+)", headers.get("Content-Disposition", ""))
        if contdisp:
            self.filename = contdisp[0].strip('\'"')

        # extension
        if "Content-Type" in headers:
            self.ext = guess_extension(headers.get("Content-Type").split()[0].rstrip(";"))

        if not self.filename:   # no filename in Content-Disposition header
            self.set_filename()
            self.filename = Foundation.remove_invalid_chars(self.filename)

        temp_base_name, ext = os.path.splitext(self.filename)
        if ext:    # have extension
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
        open(self.filepath + ".part", 'a').close()  # create .part temp file

    def set_id(self):
        self.id = FukurouViewer.app.downloadsModel.createID()

    def download_favicon(self):
        """Download favicon if not already downloaded"""
        if self.favicon_url:
            favicon_path = os.path.join(self.FAVICON_PATH, self.domain + ".ico")
            if not os.path.exists(favicon_path):
                icon = requests.get(self.favicon_url, headers=self.send_headers, cookies=self.cookies, timeout=10)
                with open(favicon_path, "wb") as f:
                    for chunk in icon:
                        f.write(chunk)

    def set_filename(self):
        """Sets self.filename from url"""
        full_filename = self.url.split('/')[-1]   # get filename from srcUrl
        full_filename = full_filename.split('?')[0]   # strip query string parameters
        full_filename = full_filename.split('#')[0]   # strip anchor
        full_filename = unquote(full_filename)
        self.filename = full_filename

    def ext_convention(self, ext):
        """Formats extension using desired convention '.JPG' -> '.jpg' """
        if ext.lower() in ['.jpeg', '.jpe']:
            return '.jpg'
        return ext.lower()

    def fix_image_extension(self):  
        """checks image file headers and renames image to proper extension when necessary"""
        format = imghdr.what(self.filepath)
        if not format:    # not image so do nothing
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

    def finish(self, finish_time):
        os.rename(self.filepath + ".part", self.filepath)
        self.fix_image_extension()

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
                    "full_path": self.filepath,
                    "favicon_url": self.favicon_url,
                    "folder_id": self.folder.get("id")
                }))
            db_id = int(result.inserted_primary_key[0])

        kwargs = { "url": self.page_url,
                "domain": self.domain,
                "history_item": db_id,
                "galleryUrl": self.gallery_url } 

        gal = GenericGallery(**kwargs)
        search_thread.queue.put(gal)



class Download_UI_Signals(QtCore.QObject):
    create = QtCore.pyqtSignal(DownloadItem)
    start = QtCore.pyqtSignal(str)
    update = QtCore.pyqtSignal(dict)    
    finish = QtCore.pyqtSignal(str, float, int)

    def __init__(self):
        super().__init__()
        self.create.connect(FukurouViewer.app.create_download_ui_item)
        self.start.connect(FukurouViewer.app.start_download_ui_item)
        self.update.connect(FukurouViewer.app.update_download_ui_item)        
        self.finish.connect(FukurouViewer.app.finish_download_ui_item)


class DownloadManager(Logger):
    THREAD_COUNT = 3    # number of simultaneous downloads

    def __init__(self):
        self.queue = queue.Queue()

    def setup(self):
        self.signals = Download_UI_Signals()
        FukurouViewer.app.app_window.resume_download.connect(self.resume_download)

        self.threads = []
        for i in range(self.THREAD_COUNT):
            thread = DownloadThread()
            thread.setup()
            thread.start()
            self.threads.append(thread)

        self.load_existing()
        
    def start(self):
        pass

    def load_existing(self):
        """load existing unfinished downloads from db and queue them"""
        with user_database.get_session(self, acquire=True) as session:
            downloads = Utils.convert_result(session.execute(
                select([user_database.Downloads])))

        for item in downloads:
            item["task"] = "load"
            filepath = item.get("filepath") + ".part"
            if os.path.exists(filepath):
                item["downloaded"] = os.path.getsize(filepath)
            else:
                item["downloaded"] = 0

            download_item = DownloadItem(item)
            self.signals.create.emit(download_item)

            if not os.path.exists(item.get("filepath") + ".part"):
                with user_database.get_session(self, acquire=True) as session:
                    session.execute(delete(user_database.Downloads).where(user_database.Downloads.id == item.get("id")))

            percent = int((download_item.downloaded / download_item.total_size) * 100)
            kwargs = {"id": download_item.id, 
                      "cur_size": download_item.downloaded, 
                      "percent": percent }
            self.signals.update.emit(kwargs)

            self.queue.put(download_item)


    def resume_download(self, id):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Downloads]).where( user_database.Downloads.id == id)))[0]
        results["task"] = "load"
        filepath = results.get("filepath") + ".part"
        if os.path.exists(filepath):
            results["downloaded"] = os.path.getsize(filepath)
        else:
            results["downloaded"] = 0

        download_item = DownloadItem(results)
        self.queue.put(download_item)


download_manager = DownloadManager()


class DownloadThread(BaseThread):

    FAVICON_PATH = Utils.fv_path("favicons")
    SUCCESS_CHIME = os.path.join(Utils.base_path("audio"), "success-chime.mp3")

    def __init__(self):
        super().__init__()
        self.download_item = None
        self._last_time = None
        self.paused = False
        self.stopped = False
        self.max_speed = 1024 * 1024 * 1024
        self.f = None   #file object
        self.headers = {}
        self.status_code = None
        self.status_msg = ""

        self._curl = None 


    def setup(self):
        super().setup()
        self.signals = Download_UI_Signals()
        FukurouViewer.app.app_window.downloader_task.connect(self.receive_ui_task)


    def _run(self):
        try:
            while True:
                self.download_item = download_manager.queue.get()                
                if self.download_item.task == "save":
                    self.start_download()
                elif self.download_item.task == "saveManga":
                    self.saveManga_task()
        except Exception as e:
            self.log_exception()
            #self.delete_file(self.filepath)


    def receive_ui_task(self, id, task):
        if self.download_item is None or id != self.download_item.id:
            return
        if task == "pause":
            self.togglePause()
        elif task == "stop":
            self.stopDownload()

    def stopDownload(self):
        print("stop download and remove from queue")
        self.stopped = True

    def togglePause(self):
        print("toggle pause")
        if self.paused:
            self.unpause()
        else:
            self.pause()


    def pause(self):
        self.curl.pause(pycurl.PAUSE_ALL)
        self.paused = True


    def unpause(self):
        self.curl.pause(pycurl.PAUSE_CONT)
        self.paused = False


    def start_download(self):
        self.paused = False
        self.stopped = False
        self._last_time = time()
        self.headers = {}
        self.curl = pycurl.Curl()

        self.curl.setopt(pycurl.CAINFO, certifi.where())
        self.curl.setopt(pycurl.URL, self.download_item.url)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.COOKIE, self.download_item.get_cookie_str())

        self.curl.setopt(pycurl.MAX_RECV_SPEED_LARGE, self.max_speed)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.curl.setopt(pycurl.TIMEOUT, 300)
        self.curl.setopt(pycurl.NOSIGNAL, 1)

        self.curl.setopt(pycurl.WRITEFUNCTION, self.writer)
        self.curl.setopt(pycurl.NOPROGRESS, 0)
        self.curl.setopt(pycurl.XFERINFOFUNCTION, self.progress)
        
        self.curl.setopt(pycurl.HEADERFUNCTION, self.header)
        self.curl.setopt(pycurl.HTTPHEADER, [k+': '+v for k,v in self.download_item.send_headers.items()])

        if self.download_item.resume:
            self.curl.setopt(pycurl.RESUME_FROM, self.download_item.downloaded)

        mode = "wb"
        if self.download_item.resume:
            mode = "ab"
        self.f = open(self.download_item.filepath + ".part", mode)

        self.signals.start.emit(self.download_item.id)

        try:
            self.curl.perform()
        except pycurl.error as error:
            #stop requested
            return
        except Exception as error:
            self.logger.error(error)
            self.log_exception()
            return

        finish_time = time()
        self.signals.finish.emit(self.download_item.id, finish_time, self.download_item.total_size)
        self.curl.close()
        self.f.close()
        self.download_item.finish(finish_time)

        self.logger.info(self.download_item.filepath + " finished downloading.")

        mixer.music.load(os.path.join(Utils.base_path("audio"), "success-chime.mp3"))
        mixer.music.play()


    def writer(self, data):
        if self.stopped:
            return -1
        self.f.write(data)


    def header(self, header):
        header = header.decode("utf-8")
        header = header.strip()
        
        if ":" not in header and header:
            key = "http_code"
            value = header
        elif header:
            key, value = header.split(":", 1)
        else:   # end of headers
            self.get_status_code(self.headers.get("http_code"))
            return

        self.headers[key] = value


    def progress(self, download_t, download_d, upload_t, upload_d):
        if download_t == 0:
            return

        # don't update UI unless request succeeded
        if self.status_code < 200 or self.status_code > 299:
            return
            
        current_time = time()
        # speed
        duration = current_time - self.download_item.start_time + 1
        avg_speed = download_d / duration
        
        
        # update UI entry
        interval = current_time - self._last_time
        if interval < 0.2:
            return

        self._last_time = current_time
        downloaded = self.download_item.downloaded + download_d
        percent = int((downloaded / self.download_item.total_size) * 100)
        
        # ETA
        if avg_speed == 0.0:
            eta = self.download_item.ETA_LIMIT
        else:
            eta = int((self.download_item.total_size - downloaded) / avg_speed)

        kwargs = {"id": self.download_item.id, 
                  "cur_size": downloaded, 
                  "percent": percent, 
                  "speed": avg_speed,
                  "eta": eta }
        self.signals.update.emit(kwargs)


    def get_status_code(self, status_string):
        status = self.headers.get("http_code")  #'HTTP/1.1 200 OK'
        status_parts = status_string.split(" ")
        self.status_code = int(status_parts[1])
        self.status_msg = status_parts[2]


    def saveManga_task(self):
        self.logger.debug("--- Downloading Manga ---")
        url = [self.download_item.url]

        doujin_downloader = [Config.doujin_downloader]
        doujin_downloader.append(url)
        doujin_downloader.append("nogui")
        subprocess.Popen(doujin_downloader)


    # delete file
    def delete_file(self, filepath):
        if os.path.isfile(filepath):
            os.remove(filepath)


    # logs raised general exception
    def log_exception(self):
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        self.logger.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))



class SearchThread(BaseThread):
    API_URL = "https://exhentai.org/api.php"
    GAL_PAYLOAD = {"method": "gdata", "gidlist": [], "namespace": 1}
    IND_PAYLOAD = {"method": "gtoken", "pagelist": []}
    API_MAX_ENTRIES = 25


    def _run(self):
        while True:
            gal = self.queue.get()  # generic gallery class
            done = gal.search()
            if not done:
                self.queue.put(gal)

search_thread = SearchThread()

class GalleryThread(BaseThread):
    running = False
    
    def setup(self):
        super().setup()
        # signals for find galleries done in program.py
        # signal for set scan folder in program.py

    def _run(self):
        while True:
            self.running = False
            path = self.queue.get()
            self.running = True
            with FukurouViewer.app.gallery_lock:
                print("HUH")

#gallery_thread = GalleryThread()


class WatcherThread(BaseThread):
    observer = None

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            event_thread.queue.put([event])

    def setup(self):
        super().setup()
        self.observer = Observer()
        self.observer.start()
        self.schedule_folders()

    def schedule_folders(self):
        self.observer.unschedule_all()
        for folder in Config.folders:
            self.observer.schedule(self.Handler(), folder, recursive=True)

#watcher_thread = WatcherThread()


class EventThread(BaseThread):

    def _run(self):
        while True:
            self.process_events(self.queue.get())

    def process_events(self, events):
        for event in events:
            source = Utils.norm_path(event.src_path)
            if event.event_type == "moved":
                self.logger.info("moved")
            elif event.event_type == "deleted":
                self.logger.info("deleted")
            elif event.event_type == "created":
                self.logger.info("created")
            elif event.event_type == "modified":
                self.logger.info("modified")

#event_thread = EventThread()


THREADS = [
    messenger_thread,
    download_manager,
    search_thread,
    #download_thread,
    #gallery_thread,
    #watcher_thread,
]

def setup():
    for thread in THREADS:
        thread.setup()
        thread.start()
