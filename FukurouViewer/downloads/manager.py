import os
from queue import Queue

from sqlalchemy import select

import FukurouViewer
from FukurouViewer import Logger, user_database, Utils
from .downloaditem import DownloadItem
from .threads import DownloadThread


class DownloadManager(Logger):
    THREAD_COUNT = 3  # number of simultaneous downloads

    def __init__(self, searchThread, signals):
        self.searchThread = searchThread
        self.signals = signals
        self.queue = Queue()
        self.threads = []

    def setup(self):
        FukurouViewer.app.app_window.resume_download.connect(self.resume_download)
        for i in range(self.THREAD_COUNT):
            thread = DownloadThread(self, self.signals)
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
            tmp_filepath = item.get("filepath") + ".part"
            if os.path.exists(tmp_filepath):
                item["downloaded"] = os.path.getsize(tmp_filepath)
            else:
                item["downloaded"] = 0
                open(tmp_filepath, 'a').close()

            # if not os.path.exists(filepath):
            #     with user_database.get_session(self, acquire=True) as session:
            #         session.execute(
            #         delete(user_database.Downloads).where(user_database.Downloads.id == item.get("id")))
            #     open(filepath, 'a').close()

            item["tmp_filepath"] = tmp_filepath
            download_item = DownloadItem(self, item)
            self.signals.create.emit(download_item)

            percent = int((download_item.downloaded / download_item.total_size) * 100)
            kwargs = {"id": download_item.id,
                      "cur_size": download_item.downloaded,
                      "percent": percent}
            self.signals.update.emit(kwargs)

            self.queue.put(download_item)

    def resume_download(self, id):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Downloads]).where(user_database.Downloads.id == id)))[0]
        results["task"] = "load"
        filepath = results.get("filepath") + ".part"
        if os.path.exists(filepath):
            results["downloaded"] = os.path.getsize(filepath)
        else:
            results["downloaded"] = 0

        download_item = DownloadItem(self, results)
        self.queue.put(download_item)

    def queueItem(self, msg):
        self.queue.put(DownloadItem(self, msg))

    def queueSearch(self, gallery):
        self.searchThread.queue.put(gallery)