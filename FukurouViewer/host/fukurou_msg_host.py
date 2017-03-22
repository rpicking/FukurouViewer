import os
import re
import sys
import time
import json
import imghdr
import random
import string
import struct
import logging
import requests
import linecache
import subprocess
from threading import Thread
from mimetypes import guess_extension

from config import Config
from utils import Utils


logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to send a message to chrome.
def send_message(MSG_DICT = {'type': 'crash'}):
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
        #create_folder("C:/Users/Robert/Sync/New folder")
        payload = {'task': 'sync'}
        payload['folders'] = Config.folder_options
        send_message(payload)
        return

    elif task == 'edit':
        folders = json.loads(msg.get('folders'))
        folder_options = Config.folder_options
        count = 0
        total = 0

        for folder in folders:
            total += len(folder.keys())
            uid = folder.get('uid')
            name = folder.get('name', "")
            order = folder.get('order', "")

            if name:    # renaming folder
                logging.debug("renaming folder with uid: " + uid + " to: " + name)
                for item in folder_options:
                    if uid in folder_options.get(item).values():
                        name = uniqueName(name)
                        count += 1
                        folder_options[name] = folder_options.pop(item)
                        break
            if order:   # changing folder order
                logging.debug("changing order of folder: " + uid + " to order: " + str(order))
                for item in folder_options:
                    if uid in folder_options.get(item).values():
                        count += 1
                        folder_options[item]["order"] = order
                        break

        # if all edits have been made
        if count == total - len(folders):
            Config.folder_options = folder_options
            Config.save()
            send_message({'type': 'success', 'task': 'edit'})
            return
        send_message({'type': 'error', 'msg': 'not all folders found'})
        return

    elif task == 'delete':
        try:
            folders = json.loads(msg.get('folders'))
            save_folders = Config.folders
            folder_options = Config.folder_options
            count = 0
            total = len(folders)

            for folder in folders:
                uid = folder.get('uid')
                logging.debug("deleting folder with uid: " + uid)

                for item in folder_options:
                    if uid in folder_options.get(item).values():
                        count += 1
                        name = item
                        path = folder_options[item].get('path')
                        save_folders.remove(path)
                        folder_options.pop(item)
                        break

            # if all deletes have been made
            if count == total:
                Config.folders = save_folders
                Config.folder_options = folder_options
                Config.save()
                send_message({'type': 'success', 'task': 'delete', 'name': name, 'uid': uid})
                return
            send_message({'type': 'error', 'msg': 'not all folders deleted'})

        except Exception as e:
            send_message({'task': 'delete', 'type': 'crash'})
            log_exception()

    elif task == 'saveManga':
        logging.debug("--- Downloading Manga ---")
        urls = json.loads(msg.get('urls'))

        urls = [Config.doujin_downloader] + urls
        urls.append("nogui")

        subprocess.Popen(urls)
        return
        
    elif task == 'save':
        try:
            headers = {"User-Agent": "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"}
            cookies = {}
            filename = ""

            # process message from extension
            logging.debug("--- Starting Download ---")
            folder = msg.get('folder')
            logging.debug(folder)
            folder_options = Config.folder_options.get(folder)
            dir = folder_options.get('path')
            logging.debug(dir)
            srcUrl = msg.get('srcUrl')
            logging.debug(srcUrl)
            pageUrl = msg.get('pageUrl')
            logging.debug(pageUrl)
            comicLink = msg.get('comicLink')
            logging.debug(comicLink)
            comicName = msg.get('comicName')
            logging.debug(comicName)
            comicPage = msg.get('comicPage')
            logging.debug(comicPage)
            artist = msg.get('artist')
            logging.debug(artist)
            for item in msg.get('cookies'):
                cookies[item[0]] = item[1]

            # fix for downloading from pixiv (extension should be sending headers.  shouldn't be set in here)
            if 'pixiv.net' in pageUrl:
                headers['Referer'] = pageUrl

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
                filename = filename.split('#')[0]   # strip anchor

            # correctly format filename to valid
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            filename = ''.join(c for c in filename if c in valid_chars)

            # get file extension from header of not already found
            filename, ext = os.path.splitext(filename)
            if not ext:
                ext = guess_extension(r.headers['content-type'].split()[0].rstrip(";"))   #get extension from content-type header
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

            filepath = fix_extension(filepath)

            logging.info(filepath + " finished downloading.")
            # send successful download response to extension
            payload = {'task': 'save', 'type': 'success'}
            payload['filename'] = os.path.basename(filepath)
            payload['srcUrl'] = srcUrl
            payload['pageUrl'] = pageUrl
            payload['folder'] = folder
            send_message(payload)
            return

        except requests.exceptions.ReadTimeout:
            send_message({'task': 'save', 'type': 'timeout'})
            logging.error("Request for " + srcUrl + "timed out. ")
            if os.path.isfile(filepath):
                os.remove(filepath)

        except Exception as e:
            send_message({'task': 'save', 'type': 'crash'})
            log_exception()


# logs raised general exception
def log_exception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    logging.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


# checks image file headers and renames to proper extension when necessary
def fix_extension(imagepath):  
    format = imghdr.what(imagepath)
    if not format:    # not image so do nothing
        return imagepath

    format = ext_convention(''.join(('.', format)))
    filename, ext = os.path.splitext(imagepath)
    if ext != format:
        newpath = os.path.join(os.path.dirname(imagepath), '.'.join((filename, format)))
        os.rename(imagepath, newpath)
        return newpath
    return imagepath

# rename extension based on personal naming convention
def ext_convention(ext):
    if ext in {'.jpeg', '.jpe'}:
        return '.jpg'
    return ext

# creates folder entry in configs
def create_folder(path, name=''):
    if not name:
        name = os.path.basename(path)
    path = Utils.norm_path(path)
    folders = Config.folders

    # check if folder already exists, change name if necessary
    if path in folders:
        folder_options = Config.folder_options
        for item in folder_options:
            if path in folder_options.get(item).values():
                folder_options[name] = folder_options.pop(item)
                Config.folder_options = folder_options
                Config.save()
                return

    # sets folders config setting
    folders.append(path)
    Config.folders = folders

    folder_options = Config.folder_options

    # generate unique id for folder
    uid = uniqueId()
    order = uniqueOrder()
    option = {"path": path, "uid": uid, "order": order}
    folder_options[name] = option
    Config.folder_options = folder_options

    Config.save()

# creates unique name for folder
def uniqueName(name, count=0):
    folder_options = Config.folder_options
    if name in folder_options:
        if count != 0:
            name = ''.join([name.rsplit(" ", 1)[0].rstrip(), " (", str(count), ")"])
            count += 1
            return uniqueName(name, count)
        count += 1
        name = ''.join([name, " (", str(count), ")"])
        return uniqueName(name, count)
    return name

# returns next available order index number starting at 1
def uniqueOrder():
    folder_options = Config.folder_options
    largest = 0
    for folder in folder_options:
        curr_order = folder_options.get(folder).get('order')
        if largest < curr_order:
            largest = curr_order

    return largest + 1

# returns a unique id number for folder
def uniqueId():
    used_ids = []
    folder_options = Config.folder_options
    for folder in folder_options:
        used_ids.append(folder_options.get(folder).get('uid'))

    while True:
        id = id_generator()
        if id not in used_ids:
            return id

# generates a id string
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for i in range(size))


class FukurouHost():
    # not necessary each download item will have everything from 1 message
    def __init__(self):
        print("DOGS")


class DownloadItem():

    def __init__(self, msg):
        print("things")

def test(dogs = "dogs"):
    print(dogs)

# ----------------------
# ----- START ----------
# ----------------------
if __name__ == '__main__':
    process_message(read_message())
