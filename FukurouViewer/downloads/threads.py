import linecache
import os
import subprocess
import sys
from time import time

import certifi
import pycurl
from sqlalchemy import delete

import FukurouViewer
from FukurouViewer import user_database
from FukurouViewer.config import Config
from FukurouViewer.basethread import BaseThread
from FukurouViewer.utils import Utils

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import mixer

mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)


class DownloadThread(BaseThread):
    FAVICON_PATH = Config.fv_path("favicons")
    SUCCESS_CHIME = os.path.join(Utils.base_path("audio"), "success-chime.mp3")

    def __init__(self, downloadManager, signals):
        super().__init__()
        self.downloadManager = downloadManager
        self.signals = signals

        self.download_item = None
        self._last_time = None
        self.paused = False
        self.stopped = False
        self.toBeDeleted = False
        self.max_speed = 1024 * 1024 * 1024
        self.f = None  # file object
        self.headers = {}
        self.status_code = None
        self.status_msg = ""

        self.curl = None

    def setup(self, program):
        super().setup(program)
        program.app_window.downloader_task.connect(self.receive_ui_task)

    def _run(self):
        try:
            while True:
                self.download_item = self.downloadManager.queue.get()
                if self.download_item.task == "save":
                    self.start_download()
                elif self.download_item.task == "saveManga":
                    self.saveManga_task()
        except Exception as e:
            print(e)
            self.log_exception()
            # self.delete_file(self.filepath)

    def receive_ui_task(self, id, task):
        if self.download_item is None or id != self.download_item.id:
            return
        if task == "pause":
            self.togglePause()
        elif task == "stop":
            self.stopDownload(False)
        elif task == "delete":
            self.stopDownload(True)

    def stopDownload(self, deleteAfterStopping):
        print("stop download and remove from queue")
        self.stopped = True
        self.toBeDeleted = deleteAfterStopping
        if deleteAfterStopping:
            with user_database.get_session(self, acquire=True) as session:
                session.execute(
                    delete(user_database.Downloads).where(user_database.Downloads.id == self.download_item.id))

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
        self.toBeDeleted = False
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
        self.curl.setopt(pycurl.HTTPHEADER, [k + ': ' + v for k, v in self.download_item.send_headers.items()])

        if self.download_item.resume:
            self.curl.setopt(pycurl.RESUME_FROM, self.download_item.downloaded)

        mode = "wb"
        if self.download_item.resume:
            mode = "ab"
        self.f = open(self.download_item.tmp_filepath, mode)

        self.signals.start.emit(self.download_item.id)

        try:
            self.curl.perform()
        except pycurl.error as error:
            print(error)
            self.f.close()

            if self.toBeDeleted:
                if os.path.exists(self.download_item.tmp_filepath):
                    os.remove(self.download_item.tmp_filepath)

            if not self.stopped:
                self.logger.error("Failed downloading " + self.download_item.filename + " with error: " + str(error))
            return
        except Exception as error:
            print(error)
            self.logger.error(error)
            self.log_exception()
            return

        self.curl.close()
        self.f.close()
        self.download_item.finish()

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
        else:  # end of headers
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
                  "eta": eta}
        self.signals.update.emit(kwargs)

    def get_status_code(self, status_string):
        # status = self.headers.get("http_code")  # 'HTTP/1.1 200 OK'
        status_parts = status_string.split(" ")
        self.status_code = int(status_parts[1])
        self.status_msg = status_parts[2]

    def saveManga_task(self):
        self.logger.debug("--- Downloading Manga ---")
        url = [self.download_item.url]

        doujin_downloader = [Config.doujin_downloader, url, "nogui"]
        wkdir = os.path.dirname(Config.doujin_downloader)
        subprocess.Popen(doujin_downloader, cwd=wkdir)

    @staticmethod
    def delete_file(filepath):
        """Delete a file by its absolute filepath"""
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
