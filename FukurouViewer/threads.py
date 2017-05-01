import os
import sys
import json
import queue
import struct
import winsound
import threading
import FukurouViewer
from collections import namedtuple
from FukurouViewer import exceptions
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .host import Host
from .utils import Utils
from .config import Config
from .logger import Logger

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


class hostThread(BaseThread, Host):
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
                                1,65536,65536,300,None)
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
                response = self.process_message(msg)
                # send response back to messenger
                self.send_message(response)

                #self.queue.put(text)

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
            winsound.PlaySound("*", winsound.SND_ASYNC)
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


if os.name == 'nt':
    import win32api
    import win32pipe
    import win32file
    host_thread = hostThread()
else:
    host_thread = hostThread(False)


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
    host_thread,
    gallery_thread,
    #watcher_thread,
    #event_thread,
]

def setup():
    for thread in THREADS:
        print("STARTING")
        thread.setup()
        thread.start()
