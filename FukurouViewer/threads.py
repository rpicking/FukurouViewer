import sys
import queue
import threading
import FukurouViewer
from collections import namedtuple
from FukurouViewer import exceptions
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import Config
from .utils import Utils

class BaseThread(threading.Thread):
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
                print("moved")
            elif event.event_type == "deleted":
                print("deleted")
            elif event.event_type == "created":
                print("created")
            elif event.event_type == "modified":
                print("modified")

event_thread = EventThread()


THREADS = [
    gallery_thread,
    watcher_thread,
    event_thread,
]

def setup():
    for thread in THREADS:
        print("STARTING")
        thread.setup()
        thread.start()