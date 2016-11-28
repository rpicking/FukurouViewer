import os
import re
import sys
import json
import struct
import requests


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

# srcUrl: url to item that is being downloaded
# pageUrl: url of the page that item downloaded from
# comicLink: *CUSTOM* url of comic that item is from
# comicName: *CUSTOM* name of comic
# comicPage: *CUSTOM* page number of item
# cookies: cookies from pageUrl domain
if __name__ == '__main__':
    dir = 'C:/Users/Robert/Sync/New folder/'
    msg = read_message()
    url = msg.get('srcUrl').strip('"')
    headers = {"User-Agent": "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"}
    cookies = {}
    for item in msg.get('cookies'):
        cookies[item[0]] = item[1]
    try:
        r = requests.get(url, headers=headers, cookies=cookies)
    except:
        with open('squirrel.txt', "w") as file:
            file.write(e)
            sys.exit(0)
    headers = r.headers
    if 'Content-Disposition' in headers:
        filename = re.findall("filename=(.+)", headers['content-disposition'])[0]
    else:
        filename = url.split('/')[-1]
    with open(os.path.join(dir, filename), "wb") as file:
        file.write(r.content)
