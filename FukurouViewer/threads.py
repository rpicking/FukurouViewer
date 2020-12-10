import os
import sys
import json
import linecache

from PySide2 import QtCore
from watchdog.observers import Observer
from sqlalchemy import delete, select, update
from watchdog.events import FileSystemEventHandler

from FukurouViewer import user_database
from FukurouViewer.basethread import BaseThread
from FukurouViewer.db_utils import DBUtils
from FukurouViewer.downloads.downloaditem import DownloadItem
from FukurouViewer.downloads.frontend import Download_UI_Signals
from FukurouViewer.downloads.manager import DownloadManager
from FukurouViewer.files import FileItem
from FukurouViewer.utils import Utils

isWindows = os.name == "nt"
if isWindows:
    import win32pipe
    import win32file


class MessengerThread(BaseThread):
    THREAD_COUNT = 1
    BUFFER_SIZE = 4096
    PIPE_PATH = "/tmp/fukurou.fifo"
    WIN_PIPE_PATH = r'\\.\pipe\fukurou_pipe'

    def __init__(self, downloadManager, signals, _windows=True):
        super().__init__()
        self.downloadManager = downloadManager
        self.signals = signals
        self.windows = _windows

        if self.windows:
            self.pipe = win32pipe.CreateNamedPipe(self.WIN_PIPE_PATH,
                                                  win32pipe.PIPE_ACCESS_DUPLEX,
                                                  win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                                                  win32pipe.PIPE_UNLIMITED_INSTANCES, 65536, 65536, 300, None)
        else:
            # non windows platform
            self.pipe = self.PIPE_PATH
            if not os.path.exists(self.pipe):
                os.mkfifo(self.pipe)

    def _run(self):
        win32pipe.ConnectNamedPipe(self.pipe, None)
        msg = None
        while True:
            try:
                # read message from messenger
                msg = self.read_message()
                # process message and perform task
                task = msg.get("task")
                payload = {"task": "none"}
                if task == "sync":
                    payload = self.sync_task()
                elif task == "edit":
                    payload = self.edit_task(msg)
                elif task == "delete":
                    payload = self.delete_task(msg)
                elif task == "save":
                    item = self.create_download_item(msg)
                    self.downloadManager.queue.put(item)
                    payload = {"task": "none"}
                elif task == "saveManga":
                    self.downloadManager.queueItem(msg)
                elif task == "galleryCheck":
                    payload = self.check_gallery(msg)

                self.send_message(payload)

            except win32pipe.error as e:  # messenger has closed
                # self.logger.error("Messenger closed")
                # self.logger.error(e)
                self.pipe.Close()
                self.pipe = win32pipe.CreateNamedPipe(self.WIN_PIPE_PATH,
                                                      win32pipe.PIPE_ACCESS_DUPLEX,
                                                      win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                                                      1, 65536, 65536, 300, None)
                win32pipe.ConnectNamedPipe(self.pipe, None)
            except Exception as e:
                self.logger.error(e)
                self.logger.error(msg)

    def close(self):
        if self.windows:
            self.pipe.Close()
            self.logger.info("Pipe closed")
            # winsound.PlaySound("*", winsound.SND_ASYNC)
            return

        os.remove(self.pipe)

    # returns dict message from host
    def read_message(self):
        if self.windows:
            result, data = win32file.ReadFile(self.pipe, MessengerThread.BUFFER_SIZE, None)
            buffer = data
            while len(data) == MessengerThread.BUFFER_SIZE:
                result, data = win32file.ReadFile(self.pipe, MessengerThread.BUFFER_SIZE, None)
                buffer += data

            return json.loads(buffer.decode())

        with open(self.pipe, "r") as pipe:
            msg = pipe.readline()
            msg = msg.decode()
            return json.loads(msg)

    # send message to host
    def send_message(self, MSG):
        jsonStr = json.dumps(MSG)
        byte_message = str.encode(jsonStr)
        if self.windows:
            win32file.WriteFile(self.pipe, byte_message)
        else:
            with open(self.pipe, "w") as pipe:
                pipe.write(jsonStr)

    def create_download_item(self, msg):
        """creates DownloadItem to put in queue
            adds download item to UI """
        item = DownloadItem(self.downloadManager, msg)
        self.signals.create.emit(item)
        return item

    # sync folders with extension
    def sync_task(self):
        payload = {'task': 'sync'}
        with user_database.get_session(self, acquire=True) as session:
            payload['folders'] = Utils.convert_result(session.execute(
                select([user_database.Collection.name, user_database.Collection.uid]).order_by(user_database.Collection.order)))
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
                    session.execute(update(user_database.Collection).where(
                        user_database.Collection.uid == folder.get('uid')).values(values))
            except Exception:
                self.log_exception()
                return {'task': 'edit', 'type': 'error', 'msg': 'not all folders found'}
        return {'task': 'edit', 'type': 'success'}

    # delete folder from database
    def delete_task(self, msg):
        try:
            folders = json.loads(msg.get('folders'))
            for folder in folders:
                uid = folder.get("uid", "")
                name = folder.get("name", "")

                self.logger.debug("deleting folder with uid: " + uid)

                with user_database.get_session(self) as session:
                    session.execute(delete(user_database.Collection).where(user_database.Collection.uid == folder.get('uid')))
                return {'type': 'success', 'task': 'delete', 'name': name, 'uid': uid}
        except Exception:
            self.log_exception()
            return {'task': 'delete', 'type': 'crash'}

    def check_gallery(self, msg):
        galleries = DBUtils.select(user_database.Gallery, user_database.Gallery.url == msg.get("url"))
        exists = galleries is not None and len(galleries) > 0
        return {"task": "galleryCheck", "exists": exists}

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


class GalleryThread(BaseThread):
    running = False

    def setup(self, program):
        super().setup(program)
        # signals for find galleries done in program.py
        # signal for set scan folder in program.py

    def _run(self):
        while True:
            self.running = False
            path = self.queue.get()
            self.running = True
            with self.program.gallery_lock:
                print("HUH")


class FolderWatcherThread(BaseThread):
    observer = None

    def __init__(self, eventThread):
        super().__init__()
        self.eventThread = eventThread

    class Handler(FileSystemEventHandler):
        def __init__(self, eventThread):
            super().__init__()
            self.eventThread = eventThread

        def on_any_event(self, event):
            self.eventThread.queue.put([event])

    def setup(self, program):
        super().setup(program)
        self.observer = Observer()
        self.observer.start()
        self.set_folders()

    def _run(self):
        while True:
            self.queue.get()
            self.set_folders()

    def set_folders(self):
        self.observer.unschedule_all()
        with user_database.get_session(self, acquire=True) as session:
            folders = Utils.convert_result(session.execute(
                select([user_database.Collection.path]).order_by(user_database.Collection.order)))
        for folder in folders:
            if os.path.exists(folder.get('path')):
                self.observer.schedule(self.Handler(self.eventThread), folder.get('path'), recursive=True)


class EventThread(BaseThread):
    class Signals(QtCore.QObject):
        moved = QtCore.Signal(str, str)
        created = QtCore.Signal(str)
        deleted = QtCore.Signal(str)
        modified = QtCore.Signal(str)

    def __init__(self, gridModel):
        super().__init__()
        self.gridModel = gridModel
        self.signals = self.Signals()

    def setup(self, program):
        super().setup(program)
        self.signals.moved.connect(self.file_moved_event)
        self.signals.created.connect(self.file_created_event)
        self.signals.deleted.connect(self.file_deleted_event)
        self.signals.modified.connect(self.file_modified_event)

    def _run(self):
        while True:
            self.process_events(self.queue.get())

    def process_events(self, events):
        for event in events:
            if event.is_directory:
                continue
            if event.event_type == "moved":
                self.signals.moved.emit(event.src_path, event.dest_path)
                print("moved")
            elif event.event_type == "deleted":
                self.signals.deleted.emit(event.src_path)
                print("deleted")
            elif event.event_type == "created":
                self.signals.created.emit(event.src_path)
                print("created")
            elif event.event_type == "modified":
                self.signals.modified.emit(event.src_path)
                print("modified")

    def file_moved_event(self, src_path, dst_path):
        try:
            if self.gridModel.isCurrentFolder(src_path):
                self.gridModel.remove_item(FileItem(src_path))
            if self.gridModel.isCurrentFolder(dst_path):
                self.gridModel.insert_new_item(FileItem(dst_path))
        except Exception as e:
            self.logger.error("MovedEvent", e)

    def file_deleted_event(self, filepath):
        try:
            if not self.gridModel.isCurrentFolder(filepath):
                return
            self.gridModel.remove_item(FileItem(filepath))
        except Exception as e:
            self.logger.error("DeletedEvent", e)

    def file_created_event(self, filepath):
        try:
            if not self.gridModel.isCurrentFolder(filepath):
                return
            self.gridModel.insert_new_item(FileItem(filepath))
        except Exception as e:
            self.logger.error("CreatedEvent", e)

    def file_modified_event(self, filepath):
        try:
            if not self.gridModel.isCurrentFolder(filepath):
                return

            item = FileItem(filepath)
            self.gridModel.remove_item(item)

            if not item.exists():
                return
            self.gridModel.insert_new_item(item)
        except Exception as e:
            self.logger.error("ModifiedEvent", e)


class ThreadManager:

    def __init__(self, program):
        self.program = program
        self.signals = Download_UI_Signals(program)

        self.searchThread = SearchThread()
        self.downloadManager = DownloadManager(self.searchThread, self.signals)
        # self.gallery_thread = GalleryThread()
        self.eventThread = EventThread(program.mainFilteredGridModel.gridModel)
        self.folderWatcherThread = FolderWatcherThread(self.eventThread)
        self.messengerThread = MessengerThread(self.downloadManager, self.signals, isWindows)

    def startThreads(self):
        self.startThread(self.messengerThread, self.program)
        self.startThread(self.downloadManager, self.program)
        self.startThread(self.searchThread, self.program)
        self.startThread(self.eventThread, self.program)
        self.startThread(self.folderWatcherThread, self.program)

    @staticmethod
    def startThread(thread, program):
        thread.setup(program)
        thread.start()
