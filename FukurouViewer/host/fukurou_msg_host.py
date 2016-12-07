import os
import re
import sys
import time
import json
import struct
import logging
import requests
from mimetypes import guess_extension
from win10notification import WindowsBalloonTip

from config import Config
from utils import Utils

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


# Function to read a message from chrome.
def read_message():
    # Reads the first 4 bytes of the message (which designates message length).
    text_length_bytes = sys.stdin.buffer.read(4)
    # Unpacks the first 4 bytes that are the message length. [0] required because unpack returns tuple with required data at index 0.
    text_length = struct.unpack("i", text_length_bytes)[0]
    # Reads and decodes the text (which is JSON) of the message.
    text_decoded = sys.stdin.buffer.read(text_length).decode("utf-8")
    text_dict = json.loads(text_decoded)
    return text_dict


def fix_extensions(ext):
    if ext in {'.jpeg', '.jpe'}:
        return '.jpg'
    return ext

def create_folder(path, name):
    path = Utils.norm_path(path)
    folders = Config.folders
    folders.append(path)
    Config.folders = folders

    folder_options = Config.folder_options
    option = {"name": name}
    folder_options[path] = option
    Config.folder_options = folder_options

    Config.save()

# srcUrl: url to item that is being downloaded
# pageUrl: url of the page that item downloaded from
# comicLink: *CUSTOM* url of comic that item is from
# comicName: *CUSTOM* name of comic
# comicPage: *CUSTOM* page number of item
# cookies: cookies from pageUrl domain
if __name__ == '__main__':
    try:
        logging.basicConfig(filename='log.log', level=logging.ERROR)
        dir = Config.folders[0]
        dirname = Config.folder_options[dir]["name"]
        headers = {"User-Agent": "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"}
        cookies = {}
        filename = ""
        msg = read_message()
        url = msg.get('srcUrl').strip('"')
        for item in msg.get('cookies'):
            cookies[item[0]] = item[1]
        try:
            r = requests.get(url, headers=headers, cookies=cookies, stream=True)
        except: # request failed
            with open('squirrel.txt', "w") as file:
                file.write(time.strftime('%a %H:%M:%S'))
                sys.exit(0)


        headers = r.headers
        # get filename
        if 'Content-Disposition' in headers:    # check for content-disposition header, if exists try and set filename
            contdisp = re.findall("filename=(.+)", headers['content-disposition'])
            if len(contdisp) > 0:
                filename = contdisp[0]
        if not filename:    # if filename still empty
            filename = url.split('/')[-1]   # get filename from url
            filename = filename.split('?')[0]   # strip query string parameters

        # get file extension from header of not already found
        filename, ext = os.path.splitext(filename)
        if not ext:
            ext = guess_extension(r.headers['content-type'].split()[0].rstrip(";"))   #get extension from content-type header

        #  bad extension naming
        ext = fix_extensions(ext)

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

        balloon = WindowsBalloonTip()
        icon = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'icon_transparent.ico'))
        balloon.balloon_tip("Fukurou Downloader",
                            os.path.basename(filepath) + " added to " + dirname,
                            icon_path=icon,
                            duration=4)
    except Exception as e:
        logging.error("main crashed {0}".format(str(e)))
