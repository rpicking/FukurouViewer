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
from time import clock, time
from sqlalchemy import insert, select, update
from mimetypes import guess_extension

import FukurouViewer
from . import user_database
from .logger import Logger
from .config import Config
from .utils import Utils


class Host(Logger):
    """Message processing from Fukurou Chrome Extension

    """
    FAVICON_PATH = Utils.fv_path("favicons")

    # Processes message from extension returning payload?
    def process_message(self, msg):
        task = msg.get('task')
        if task == 'sync':  # extension requested sync info to be sent
            payload = {'task': 'sync'}
            with user_database.get_session(self, acquire=True) as session:
                payload['folders'] = Utils.convert_result(session.execute(
                    select([user_database.Folders.name, user_database.Folders.uid]).order_by(user_database.Folders.order)))
                #payload['folders'] = Utils.convert_result(session.execute(
                 #   select([user_database.Folders]).order_by(user_database.Folders.order)))

            return payload

        elif task == 'edit':
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
                            session.execute(update(user_database.Folders).where(
                                user_database.Folders.uid == folder.get('uid')).values(values))
                except Exception as e:
                    self.log_exception()
                    return {'task': 'edit', 'type': 'error', 'msg': 'not all folders found'}
            return {'task': 'edit', 'type': 'success'}

        elif task == 'delete':
            try:
                folders = json.loads(msg.get('folders'))

                for folder in folders:
                    #uid = folder.get('uid')
                    self.logger.debug("deleting folder with uid: " + uid)

                    with user_database.get_session(self) as session:
                        session.execute(delete(user_database.Folders).where(user_database.Folders.uid == folder.get('uid')))
                    return {'type': 'success', 'task': 'delete', 'name': name, 'uid': uid}

            except Exception as e:
                self.log_exception()
                return {'task': 'delete', 'type': 'crash'}

        elif task == 'saveManga':
            self.logger.debug("--- Downloading Manga ---")
            url = [msg.get('url')]

            doujin_downloader = [Config.doujin_downloader]
            doujin_downloader.append(url)
            doujin_downloader.append("nogui")
            subprocess.Popen(doujin_downloader)
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
                start = clock()

                folder = {} 
                with user_database.get_session(self, acquire=True) as session:
                    folder = Utils.convert_result(session.execute(
                        select([user_database.Folders]).where(user_database.Folders.uid == msg.get('uid'))))[0]

                for item in msg.get('cookies'):
                    cookies[item[0]] = item[1]

                # currently unused
                comicLink = msg.get('comicLink')
                comicName = msg.get('comicName')
                comicPage = msg.get('comicPage')
                artist = msg.get('artist')

                if msg.get('favicon_url'):
                    # DOWNLOAD FAVICON IS FIRST BECAUSE OF UNKNOWN TIMEOUT ERROR IF AFTER FILE DOWNLOAD FIX BY MOVING DOWNLOAD TO OWN CLASS
                    favicon = os.path.join(self.FAVICON_PATH, msg.get('domain') + ".ico")
                    if not os.path.exists(favicon):
                        icon = requests.get(msg.get('favicon_url'), headers=headers, cookies=cookies, timeout=10)
                        with open(favicon, "wb") as f:
                            for chunk in icon:
                                f.write(chunk)


                r = requests.get(msg.get('srcUrl'), headers=headers, cookies=cookies, timeout=10, stream=True)
                #headers = r.headers
                
                # get filename
                if 'Content-Disposition' in r.headers:    # check for content-disposition header, if exists try and set filename
                    contdisp = re.findall("filename=(.+)", r.headers['content-disposition'])
                    if len(contdisp) > 0:
                        filename = contdisp[0]
                if not filename:    # still havn't gotten filename
                    filename = msg.get('srcUrl').split('/')[-1]   # get filename from srcUrl
                    filename = filename.split('?')[0]   # strip query string parameters
                    filename = filename.split('#')[0]   # strip anchor


                # format filename to valid
                valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
                filename = ''.join(c for c in filename if c in valid_chars)
                # get file extension from header if not already found
                filename, ext = os.path.splitext(filename)
                if not ext:
                    ext = guess_extension(r.headers['content-type'].split()[0].rstrip(";"))   #get extension from content-type header

                # set filename to name recommended by ext if available
                filename = msg.get('filename', filename)

                filepath = os.path.join(folder.get("path"), ''.join((filename, ext)))

                # check and rename if file already exists
                count = 1
                while os.path.isfile(filepath):
                    filepath = os.path.join(folder.get("path"), ''.join((filename, ' (', str(count), ')', ext)))
                    count += 1

                # Download file
                total_length = int(r.headers.get('content-length'))
                total_dl = 0
                dl = 0
                prev_time = start
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(1024):
                        if chunk:
                            total_dl += len(chunk)
                            dl += len(chunk)

                            f.write(chunk)
                            duration = clock() - prev_time
                            if duration >= 1 or total_dl == total_length:
                                done = total_dl / total_length
                                cur_speed = int((dl / duration) / 1000)
                                FukurouViewer.app.app_window.updateProgress.emit(done, cur_speed)
                                prev_time = clock()
                                dl = 0
                            
                filepath = self.fix_extension(filepath)
                r.close()

                self.logger.info(filepath + " finished downloading.")
                #from pygame import mixer
                #mixer.init()
                #mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)
                #mixer.music.load(os.path.join(Utils.base_path("audio"), "success-chime.mp3"))
                #mixer.music.play()

                # add to history table in database
                with user_database.get_session(self) as session:
                    result = session.execute(insert(user_database.History).values(
                        {
                            "filename": os.path.basename(filepath),
                            "src_url": msg.get('srcUrl'),
                            "page_url": msg.get('pageUrl'),
                            "domain": msg.get('domain'),
                            "time_added": time(),
                            "full_path": filepath,
                            "favicon_url": msg.get('favicon_url')
                        }))

                # send successful download response to extension
                payload = {'task': 'save', 
                           'type': 'success',
                           'filename': os.path.basename(filepath),
                           'srcUrl': msg.get('srcUrl'),
                           'pageUrl': msg.get('pageUrl'),
                           'folder': folder.get("name") }
                return payload

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                self.logger.error("Request for " + msg.get('srcUrl') + " timed out. ")
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
            newpath = os.path.join(os.path.dirname(imagepath), ''.join((filename, format)))
            os.rename(imagepath, newpath)
            return newpath
        return imagepath

    # rename extension based on personal naming convention
    def ext_convention(self, ext):
        if ext in {'.jpeg', '.jpe'}:
            return '.jpg'
        return ext


    # creates unique name for folder    NO LONGER NEEDED
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
