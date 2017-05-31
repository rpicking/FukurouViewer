import os
import re
import sys
import time
import json
import imghdr
import random
import string
import struct
import requests
import linecache
import subprocess
from threading import Thread
from mimetypes import guess_extension

from .logger import Logger
from .config import Config
from .utils import Utils


class Host(Logger):
    """Message processing from Fukurou Chrome Extension

    """

    # Processes message from extension returning payload?
    def process_message(self, msg):
        task = msg.get('task')
        if task == 'sync':  # extension requested sync info to be sent
            #self.create_folder("C:/Users/Robert/Sync/New folder")
            payload = {'task': 'sync'}
            payload['folders'] = Config.folder_options

            return payload
            #self.send_message(payload)
            #return

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
                    self.logger.debug("renaming folder with uid: " + uid + " to: " + name)
                    for item in folder_options:
                        if uid in folder_options.get(item).values():
                            name = self.uniqueName(name)
                            count += 1
                            folder_options[name] = folder_options.pop(item)
                            break
                if order:   # changing folder order
                    self.logger.debug("changing order of folder: " + uid + " to order: " + str(order))
                    for item in folder_options:
                        if uid in folder_options.get(item).values():
                            count += 1
                            folder_options[item]["order"] = order
                            break

            # if all edits have been made
            if count == total - len(folders):
                Config.folder_options = folder_options
                Config.save()
                return {'task': 'edit', 'type': 'success'}
            return {'task': 'edit', 'type': 'error', 'msg': 'not all folders found'}

        elif task == 'delete':
            try:
                folders = json.loads(msg.get('folders'))
                save_folders = Config.folders
                folder_options = Config.folder_options
                count = 0
                total = len(folders)

                for folder in folders:
                    uid = folder.get('uid')
                    self.logger.debug("deleting folder with uid: " + uid)

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
                    return {'type': 'success', 'task': 'delete', 'name': name, 'uid': uid}
                return {'type': 'error', 'msg': 'not all folders deleted'}

            except Exception as e:
                self.log_exception()
                return {'task': 'delete', 'type': 'crash'}

        elif task == 'saveManga':
            self.debug("--- Downloading Manga ---")
            urls = json.loads(msg.get('urls'))

            urls = [Config.doujin_downloader] + urls
            urls.append("nogui")

            subprocess.Popen(urls)
            return
        
        elif task == 'save':
            try:
                headers = {}
                if "headers" in msg:
                    headers = msg.get('headers')

                headers["User-Agent"] = "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"
                cookies = {}
                filename = ""

                # process message from extension
                self.logger.debug("--- Starting Download ---")
                folder = msg.get('folder')
                self.logger.debug(folder)
                folder_options = Config.folder_options.get(folder)
                dir = folder_options.get('path')
                self.logger.debug(dir)
                srcUrl = msg.get('srcUrl')
                self.logger.debug(srcUrl)
                pageUrl = msg.get('pageUrl')
                self.logger.debug(pageUrl)
                comicLink = msg.get('comicLink')
                self.logger.debug(comicLink)
                comicName = msg.get('comicName')
                self.logger.debug(comicName)
                comicPage = msg.get('comicPage')
                self.logger.debug(comicPage)
                artist = msg.get('artist')
                self.logger.debug(artist)
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

                filepath = self.fix_extension(filepath)

                self.logger.info(filepath + " finished downloading.")
                # send successful download response to extension
                payload = {'task': 'save', 
                           'type': 'success',
                           'filename': os.path.basename(filepath),
                           'srcUrl': srcUrl,
                           'pageUrl': pageUrl,
                           'folder': folder }
                return payload

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                self.logger.error("Request for " + srcUrl + "timed out. ")
                self.logger.error(e)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                return {'task': 'save', 'type': 'timeout'}

            except Exception as e:
                self.log_exception()
                return {'task': 'save', 'type': 'crash'}


    # logs raised general exception
    def log_exception(self):
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        self.logger.error('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


    # checks image file headers and renames to proper extension when necessary
    def fix_extension(self, imagepath):  
        format = imghdr.what(imagepath)
        if not format:    # not image so do nothing
            return imagepath

        format = self.ext_convention(''.join(('.', format)))
        filename, ext = os.path.splitext(imagepath)
        if ext != format:
            newpath = os.path.join(os.path.dirname(imagepath), '.'.join((filename, format)))
            os.rename(imagepath, newpath)
            return newpath
        return imagepath

    # rename extension based on personal naming convention
    def ext_convention(self, ext):
        if ext in {'.jpeg', '.jpe'}:
            return '.jpg'
        return ext

    # creates folder entry in configs
    def create_folder(self, path, name=''):
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
        uid = self.uniqueId()
        order = self.uniqueOrder()
        option = {"path": path, "uid": uid, "order": order}
        folder_options[name] = option
        Config.folder_options = folder_options

        Config.save()

    # creates unique name for folder
    def uniqueName(self, name, count=0):
        folder_options = Config.folder_options
        if name in folder_options:
            if count != 0:
                name = ''.join([name.rsplit(" ", 1)[0].rstrip(), " (", str(count), ")"])
                count += 1
                return self.uniqueName(name, count)
            count += 1
            name = ''.join([name, " (", str(count), ")"])
            return self.uniqueName(name, count)
        return name

    # returns next available order index number starting at 1
    def uniqueOrder(self):
        folder_options = Config.folder_options
        largest = 0
        for folder in folder_options:
            curr_order = folder_options.get(folder).get('order')
            if largest < curr_order:
                largest = curr_order

        return largest + 1

    # returns a unique id number for folder
    def uniqueId(self):
        used_ids = []
        folder_options = Config.folder_options
        for folder in folder_options:
            used_ids.append(folder_options.get(folder).get('uid'))

        while True:
            id = self.id_generator()
            if id not in used_ids:
                return id

    # generates a id string
    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for i in range(size))
