import threading
from collections import namedtuple
from queue import Queue

from FukurouViewer.logger import Logger


class BaseThread(threading.Thread, Logger):
    THREAD_COUNT = 4

    def __init__(self, **kwargs):
        super().__init__()
        self.daemon = True
        self.queue = Queue()
        self.program = None

    def setup(self, program):
        self.program = program
        # basesignals.exception.connect

    def _run(self):
        raise NotImplementedError

    def close(self):
        pass

    @classmethod
    def generate_workers(cls, global_queue, target):
        worker = namedtuple("worker", "thread data errors")
        workers = []
        for _ in range(0, cls.THREAD_COUNT):
            data_queue = Queue()
            error_queue = Queue()
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
                if restart:  # empty out queue
                    try:
                        while True:
                            self.queue.get_nowait()
                    except queue.Empty:
                        pass
