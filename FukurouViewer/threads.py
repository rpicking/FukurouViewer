import sys
import queue
import threading
import FukurouViewer
from collections import namedtuple
from FukurouViewer import exceptions


class BaseThread(threading.Thread):
    THREAD_COUNT = 4

    def __init(self, **kwargs):
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
        self.running = False
        path = self.queue.get()
        self.running = True
        with FukurouViewer.app.gallery_lock:

            


gallery_thread = GalleryThread()


THREADS = [
    gallery_thread,
]

def setup():
    for thread in THREADS:
        thread.setup()
        thread.start()