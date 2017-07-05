#!/usr/bin/env python3

import os
import sys
import json
import time
import struct
import logging
import linecache
import subprocess

from utils import Utils
from logger import Logger

class extensionMessage(Logger):
    """ Exchanges messages with extension over stdio
        Messages are json converted into a byte string 

        sending/receiving taken from this reddit post
        https://www.reddit.com/r/learnpython/comments/4yo4fn/i_cant_write_a_python_35_script_that_works_with/
    """

    # send message to extension
    def send_message(self, MSG):
        # Encode json string with UTF-8.
        msg_json_utf8 = MSG.encode("utf-8")
        # Writes the message size. (Writing to buffer because writing bytes object.)
        sys.stdout.buffer.write(struct.pack("i", len(msg_json_utf8)))
        # Writes the message itself. (Writing to buffer because writing bytes object.)
        sys.stdout.buffer.write(msg_json_utf8)
        sys.stdout.flush()
        
    # read message sent from extension returning stringified json
    def read_message(self):
        # Reads the first 4 bytes of the message (which designates message length).
        text_length_bytes = sys.stdin.buffer.read(4)
        # Unpacks the first 4 bytes that are the message length. [0] required because unpack returns tuple with required data at index 0.
        text_length = struct.unpack("i", text_length_bytes)[0]
        # Reads and decodes the text (which is JSON) of the message.
        return sys.stdin.buffer.read(text_length).decode("utf-8")


class hostMessage():
    """ Exchanges messages with main application over named pipe
        Different implementation of os is windows.
        Functions on assumption that all communcation with host 
            runs in an alternating pattern starting with the 
            messenger talking first then response from host """

    def __init__(self, _windows = True):
        self.windows = _windows
        self.pipe = None

    # send message to host
    def send_message(self, MSG):
        byte_message = str.encode(MSG)
        if self.windows:
            win32file.WriteFile(self.pipe, byte_message)
            return

        with open(self.pipe, "w") as pipe:
            pipe.write(byte_message)


    # returns dict message from host
    def read_message(self):
        if self.windows:
            data = win32file.ReadFile(self.pipe, 4096)[1]
            return data.decode()

        with open(self.pipe, "r") as pipe:
            data = pipe.readline()
            return data.decode()


class Messenger(Logger):
    PIPE_PATH = "/tmp/fukurou.fifo"
    WIN_PIPE_PATH = "\\\\.\\pipe\\fukurou_pipe"

    APP_PATH = "../main.py"
    WIN_APP_PATH = "../scripts/launch_host.bat"

    HOST_STARTING_UP = False

    def __init__(self, _windows = True):
        super().__init__()
        self.windows = _windows

        if self.windows:
            self.launch_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.WIN_APP_PATH)
        else:
            self.launch_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.APP_PATH)
        self.host = hostMessage()
        self.extension = extensionMessage()

        self.connectPipe()
        return
        if self.windows:    # wait till pipe has been created by host then create file
            self.launch_path = os.path.join(self.launch_path, self.WIN_APP_PATH)
            while True:
                try:
                    self.pipe = win32file.CreateFile(self.WIN_PIPE_PATH,
                                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                        0, None,win32file.OPEN_EXISTING,0, None)
                    win32pipe.SetNamedPipeHandleState(self.pipe, 
                                        win32pipe.PIPE_READMODE_MESSAGE, None, None)
                    break
                except win32api.error:  # host is not running, launch
                    subprocess.Popen(self.launch_path)
                    # wait for host to launch
                    time.sleep(1)
            self.host.pipe = self.pipe

        else:   # non-windows
            self.launch_path = os.path.join(self.launch_path, self.APP_PATH)
            self.host.pipe = self.PIPE_PATH
            if not os.path.exists(self.PATH):   # need better way of checking if host is running
                self.launch_path = os.path.join(self.launch_path, self.APP_PATH)
                subprocess.Popen(self.launch_path)
                time.sleep(1)

    def connectPipe(self):
        if self.windows:
            while True:
                try:
                    self.pipe = win32file.CreateFile(self.WIN_PIPE_PATH,
                                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                        0, None,win32file.OPEN_EXISTING,0, None)
                    win32pipe.SetNamedPipeHandleState(self.pipe, 
                                        win32pipe.PIPE_READMODE_MESSAGE, None, None)
                    self.host.pipe = self.pipe
                    self.HOST_STARTING_UP = False
                    return
                except win32api.error:  # host is not running, launch
                        if not self.HOST_STARTING_UP:
                            subprocess.Popen(self.launch_path)
                            self.HOST_STARTING_UP = True
                        # wait for host to launch
                        time.sleep(1)
        else:   # non-windows
            self.host.pipe = self.PIPE_PATH
            if not os.path.exists(self.PATH):   # need better way of checking if host is running
                self.launch_path = os.path.join(self.launch_path, self.APP_PATH)
                subprocess.Popen(self.launch_path)
                time.sleep(1)

    def run(self):
        while True:
            try:
                msg = self.extension.read_message()
                self.host.send_message(msg)
                response = self.host.read_message()
                self.extension.send_message(response)

            except win32pipe.error as e:    # host not running. windows
                win32api.CloseHandle(self.pipe)
                self.connectPipe()
                msg["type"] = msg.get("task")
                msg["task"] = "resend"
                self.extension.send_message(msg)
                continue
            except Exception as e:

                return

    def close(self):
        if self.windows:
            win32api.CloseHandle(self.pipe)
            return


if __name__ == '__main__':
    # setup logging
    if not os.path.exists(Utils.fv_path()):
        os.mkdir(Utils.fv_path())

    log_dir = Utils.fv_path("logs")
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    filename = os.path.join(log_dir, "log.log")
    logging.basicConfig(handlers=[logging.FileHandler(filename, 'a', 'utf-8')],
                        format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
                        level=logging.INFO)

    if os.name == 'nt':
        import win32api
        import win32pipe
        import win32file
        messenger = Messenger()
    else:
        messenger = Messenger(False)

    messenger.run()
    messenger.close()
