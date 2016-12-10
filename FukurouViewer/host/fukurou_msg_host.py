import os
import re
import sys
import time
import json
import imghdr
import struct
import logging
import requests
from threading import Thread
from mimetypes import guess_extension
from win10notification import WindowsBalloonTip

from config import Config
from utils import Utils

import linecache

logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Function to send a message to chrome.
def send_message(MSG_DICT):
    # Converts dictionary into string containing JSON format.
    msg_json = json.dumps(MSG_DICT, separators=(",", ":"))
    # Encodes string with UTF-8.
    msg_json_utf8 = msg_json.encode("utf-8")
    # Writes the message size. (Writing to buffer because writing bytes object.)
    sys.stdout.buffer.write(struct.pack("i", len(msg_json_utf8)))
    # Writes the message itself. (Writing to buffer because writing bytes object.)
    sys.stdout.buffer.write(msg_json_utf8)
    sys.stdout.flush()


# Function to read a message from chrome.
def read_message():
    # Reads the first 4 bytes of the message (which designates message length).
    text_length_bytes = sys.stdin.buffer.read(4)
    # Unpacks the first 4 bytes that are the message length. [0] required because unpack returns tuple with required data at index 0.
    text_length = struct.unpack("i", text_length_bytes)[0]
    # Reads and decodes the text (which is JSON) of the message.
    text_decoded = sys.stdin.buffer.read(text_length).decode("utf-8")
    return json.loads(text_decoded)

# Processes message from extension returning payload?
def process_message(msg):
    task = msg.get('task')
    if task == 'sync':  # extension requested sync info to be sent
        payload = {}
        payload['task'] = 'sync'
        payload['folders'] = Config.folder_options
        send_message(payload)
    elif task == 'save':
        MAX_RETRIES = 3
        while MAX_RETRIES > 0:
            try:
                headers = {"User-Agent": "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"}
                cookies = {}
                filename = ""

                # process message from extension
                dirname = msg.get('folder')
                dir = Config.folder_options.get(dirname).get('path')
                srcUrl = msg.get('srcUrl')
                pageUrl = msg.get('pageUrl')
                comicLink = msg.get('comicLink')
                comicName = msg.get('comicName')
                comicPage = msg.get('comicPage')
                artist = msg.get('artist')
                for item in msg.get('cookies'):
                    cookies[item[0]] = item[1]

                r = requests.get(srcUrl, headers=headers, cookies=cookies, timeout=10, stream=True)

                headers = r.headers
                # get filename
                if 'Content-Disposition' in headers:    # check for content-disposition header, if exists try and set filename
                    contdisp = re.findall("filename=(.+)", headers['content-disposition'])
                    if len(contdisp) > 0:
                        filename = contdisp[0]
                if not filename:    # if filename still empty
                    filename = srcUrl.split('/')[-1]   # get filename from srcUrl
                    filename = filename.split('?')[0]   # strip query string parameters

                # get file extension from header of not already found
                filename, ext = os.path.splitext(filename)
                if not ext:
                    ext = guess_extension(r.headers['content-type'].split()[0].rstrip(";"))   #get extension from content-type header

                # bad extension naming
                ext = ext_convention(ext)

                filepath = os.path.join(dir, ''.join((filename, ext)))
                # check and rename if file already exists
                count = 1
                while os.path.isfile(filepath):
                    filepath = os.path.join(dir, ''.join((filename, ' (', str(count), ')', ext)))
                    count += 1

                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
        
                fix_extension(filepath)

                balloon = WindowsBalloonTip()
                icon = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'icon_transparent.ico'))
                balloon.balloon_tip("Fukurou Downloader",
                                    os.path.basename(filepath) + " added to " + dirname,
                                    icon_path=icon,
                                    duration=4)
                MAX_RETRIES = 0
                return
            except requests.exceptions.Timeout:
                logging.error("Request for " + srcUrl + "timed out. " + MAX_RETRIES)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                MAX_RETRIES -= 1
            except Exception as e:
                log_exception()



def log_exception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    logging.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

# rename extension based on personal naming convention
def ext_convention(ext):
    if ext in {'.jpeg', '.jpe'}:
        return '.jpg'
    return ext

# checks image file headers and renames to proper extension when necessary
def fix_extension(file):  
    format = ext_convention(''.join(('.', imghdr.what(file))))
    filename, ext = os.path.splitext(file)
    if ext != format:
        os.rename(file, os.path.join(os.path.dirname(file), '.'.join((filename, format))))

# creates folder entry in configs
def create_folder(path, name=''):
    if name == '':
        name = os.path.basename(path)
    path = Utils.norm_path(path)
    folders = Config.folders
    folders.append(path)
    Config.folders = folders

    folder_options = Config.folder_options
    option = {"path": path}
    folder_options[name] = option
    Config.folder_options = folder_options

    Config.save()


class FukurouHost():
    # not necessary each download item will have everything from 1 message
    def __init__(self):
        print("DOGS")


class DownloadItem():

    def __init__(self, msg):
        print("things")

    
# srcUrl: url to item that is being downloaded
# pageUrl: url of the page that item downloaded from
# comicLink: *OPTIONAL* url of comic that item is from
# comicName: *OPTIONAL* name of comic
# comicPage: *OPTIONAL* page number of item
# cookies: cookies from pageUrl domain
if __name__ == '__main__':
    process_message(read_message())


# TODO
# -----
# send message on failure to extension
