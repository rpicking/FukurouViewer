import os
import re
import sys
import json
import time
import queue
import imghdr
import random
import string
import struct
import winsound
import requests
import linecache
import threading
import subprocess
from time import clock, time
from collections import namedtuple
from mimetypes import guess_extension
from watchdog.observers import Observer
from sqlalchemy import insert, select, update
from watchdog.events import FileSystemEventHandler

import FukurouViewer
from FukurouViewer import exceptions
from . import user_database
from .host import Host
from .utils import Utils
from .config import Config
from .logger import Logger
from .foundation import Foundation

from PyQt5 import QtCore, QtMultimedia

class BaseThread(threading.Thread, Logger):
    THREAD_COUNT = 4

    def __init__(self, **kwargs):
        super().__init__()
        self.daemon = True
        self.queue = queue.Queue()

    def setup(self):
        print("base signals?")
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
                # figure out if this shit necessary
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


class MessengerThread(BaseThread, Host):
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
                elif task in ["save", "saveManga"]:
                    download_manager.queue.put(msg)
                    payload = { "task": "empty" }
                else:   # unknown message
                    payload = { "task": "empty" }
                
                self.send_message(payload)

                #response = self.process_message(msg)
                # send response back to messenger
                #self.send_message(response)

            except win32pipe.error as e:    # messenger has closed
                print(e)
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


class DownloadManager(Logger):
    THREAD_COUNT = 3    # number of simultaneous downloads

    def __init__(self):
        self.queue = queue.Queue()

    def setup(self):
        self.threads = []
        for i in range(self.THREAD_COUNT):
            thread = DownloadThread()
            thread.setup()
            thread.start()
            self.threads.append(thread)

    def start(self):
        pass

download_manager = DownloadManager()


class DownloadThread(BaseThread):
    running = False
    FAVICON_PATH = Utils.fv_path("favicons")
    SUCCESS_CHIME = os.path.join(Utils.base_path("audio"), "success-chime.mp3")

    def _run(self):
        while True:
            msg = download_manager.queue.get()
            task = msg.get("task")
            if task == "save":
                self.save_task(msg)
            elif task == "saveManga":
                self.saveManga_task(msg)


    # download individual file and favicon from site
    def save_task(self, msg):
        while True: #get unique uid for new download in ui
            uid = Foundation.id_generator()
            if id not in []:
                break
        # create item in ui with uid

        try:
            headers = {}
            if "headers" in msg:
                headers = msg.get('headers')

            headers["User-Agent"] = "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"
            cookies = {}
            filename = ""

            # process message from extension
            self.logger.debug("--- Starting Download ---")
            start = clock()

            folder = {} 
            with user_database.get_session(self, acquire=True) as session:
                folder = Utils.convert_result(session.execute(
                    select([user_database.Folders]).where(user_database.Folders.uid == msg.get('uid'))))[0]

            for item in msg.get('cookies'):
                cookies[item[0]] = item[1]

            # currently unused
            comicLink = msg.get('comicLink')
            comicName = msg.get('comicName')
            comicPage = msg.get('comicPage')
            artist = msg.get('artist')

            if msg.get('favicon_url'):
                # DOWNLOAD FAVICON IS FIRST BECAUSE OF UNKNOWN TIMEOUT ERROR IF AFTER FILE DOWNLOAD FIX BY MOVING DOWNLOAD TO OWN CLASS
                favicon = os.path.join(self.FAVICON_PATH, msg.get('domain') + ".ico")
                if not os.path.exists(favicon):
                    icon = requests.get(msg.get('favicon_url'), headers=headers, cookies=cookies, timeout=10)
                    with open(favicon, "wb") as f:
                        for chunk in icon:
                            f.write(chunk)


            r = requests.get(msg.get('srcUrl'), headers=headers, cookies=cookies, timeout=10, stream=True)
            #headers = r.headers
                
            # get filename
            if 'Content-Disposition' in r.headers:    # check for content-disposition header, if exists try and set filename
                contdisp = re.findall("filename=(.+)", r.headers['content-disposition'])
                if len(contdisp) > 0:
                    filename = contdisp[0]
            if not filename:    # still havn't gotten filename
                filename = msg.get('srcUrl').split('/')[-1]   # get filename from srcUrl
                filename = filename.split('?')[0]   # strip query string parameters
                filename = filename.split('#')[0]   # strip anchor


            # format filename to valid
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            filename = ''.join(c for c in filename if c in valid_chars)
            # get file extension from header if not already found
            filename, ext = os.path.splitext(filename)
            if not ext:
                ext = guess_extension(r.headers['content-type'].split()[0].rstrip(";"))   #get extension from content-type header

            # set filename to name recommended by ext if available
            filename = msg.get('filename', filename)

            filepath = os.path.join(folder.get("path"), ''.join((filename, ext)))

            # check and rename if file already exists
            count = 1
            while os.path.isfile(filepath):
                filepath = os.path.join(folder.get("path"), ''.join((filename, ' (', str(count), ')', ext)))
                count += 1

            # Download file
            total_length = int(r.headers.get('content-length'))
            total_dl = 0
            dl = 0
            prev_time = start
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(1024):
                    if chunk:
                        total_dl += len(chunk)
                        dl += len(chunk)

                        f.write(chunk)
                        duration = clock() - prev_time
                        if duration >= 1 or total_dl == total_length:
                            done = total_dl / total_length
                            cur_speed = int((dl / duration) / 1000)
                            FukurouViewer.app.app_window.updateProgress.emit(done, cur_speed)
                            prev_time = clock()
                            dl = 0
                            
            filepath = self.fix_extension(filepath)
            r.close()

            self.logger.info(filepath + " finished downloading.")
            from pygame import mixer
            mixer.init()
            mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)
            mixer.music.load(os.path.join(Utils.base_path("audio"), "success-chime.mp3"))
            mixer.music.play()

            # add to history table in database
            with user_database.get_session(self) as session:
                result = session.execute(insert(user_database.History).values(
                    {
                        "filename": os.path.basename(filepath),
                        "src_url": msg.get('srcUrl'),
                        "page_url": msg.get('pageUrl'),
                        "domain": msg.get('domain'),
                        "time_added": time(),
                        "full_path": filepath,
                        "favicon_url": msg.get('favicon_url')
                    }))
            #winsound.PlaySound(self.SUCCESS_CHIME, winsound.SND_FILENAME)
            from pygame import mixer
            mixer.init()
            mixer.music.load(self.SUCCESS_CHIME)
            mixer.music.play()

            #playsound(os.path.join(Utils.base_path("audio"), "success-chime.mp3"))
            # send successful download response to extension
            payload = {'task': 'save', 
                        'type': 'success',
                        'filename': os.path.basename(filepath),
                        'srcUrl': msg.get('srcUrl'),
                        'pageUrl': msg.get('pageUrl'),
                        'folder': folder.get("name") }
            return payload

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            self.logger.error("Request for " + msg.get('srcUrl') + " timed out. ")
            self.logger.error(e)
            if os.path.isfile(filepath):
                os.remove(filepath)
            return {'task': 'save', 'type': 'timeout'}

        except Exception as e:
            self.log_exception()
            return {'task': 'save', 'type': 'crash'}


    def saveManga_task(self, msg):
        self.logger.debug("--- Downloading Manga ---")
        url = [msg.get('url')]

        doujin_downloader = [Config.doujin_downloader]
        doujin_downloader.append(url)
        doujin_downloader.append("nogui")
        subprocess.Popen(doujin_downloader)


    # logs raised general exception
    def log_exception(self):
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        self.logger.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


    # checks image file headers and renames to proper extension when necessary
    def fix_extension(self, imagepath):  
        format = imghdr.what(imagepath)
        if not format:    # not image so do nothing
            return imagepath

        format = self.ext_convention(''.join(('.', format)))
        filename, ext = os.path.splitext(imagepath)
        if ext != format:
            newpath = os.path.join(os.path.dirname(imagepath), ''.join((filename, format)))
            os.rename(imagepath, newpath)
            return newpath
        return imagepath


    # rename extension based on personal naming convention
    def ext_convention(self, ext):
        if ext in {'.jpeg', '.jpe'}:
            return '.jpg'
        return ext


#download_thread = DownloadThread()


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

gallery_thread = GalleryThread()


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

watcher_thread = WatcherThread()


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

event_thread = EventThread()


THREADS = [
    messenger_thread,
    download_manager,
    #download_thread,
    #gallery_thread,
    #watcher_thread,
    #event_thread,
]

def setup():
    for thread in THREADS:
        print("STARTING")
        thread.setup()
        thread.start()
