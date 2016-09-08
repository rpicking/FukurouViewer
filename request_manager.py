from copy import deepcopy
import threading
import json
import time
import random
import requests

try:
    from .config import Config
except Exception: #ImportError workaround for VS
    from config import Config

class RequestManager():
    API_WAIT_TIME = 3
    API_MAX_RETRY = 3
    API_REQ_DELAY = 3
    API_MAX_SEQ_REQ = 3
    API_TOO_FAST_WAIT = 100
    SALT_BASE = 10000
    SALT_MULTI = 2
    HEADERS = {"User-Agent": "Mozilla/5.0 ;Windows NT 6.1; WOW64; Trident/7.0; rv:11.0; like Gecko"}
    lock = threading.Lock()
    count = 0

    def salt_time(cls, sleep_time):
        return sleep_time * (random.randint(cls.SALT_BASE, cls.SALT_BASE * cls.SALT_MULTI) / cls.SALT_BASE)

    def rest(self, method, url, **kwargs):
        with self.lock:
            return self.run(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self.rest("get", url, **kwargs)

    def post(self, url, **kwargs):
        return self.rest("post", url, **kwargs)

    def run(self, method, url, **kwargs):
        self.count += 1
        payload = kwargs.pop("payload", None)
        retry_count = self.API_MAX_RETRY
        if payload:
            payload = json.dumps(payload)
        while retry_count > 0:
            time.sleep(self.salt_time(self.API_REQ_DELAY))
            if self.count > self.API_MAX_SEQ_REQ:
                time.sleep(self.salt_time(self.API_WAIT_TIME))
        
            response = getattr(requests, method)(url, data=payload, headers=self.HEADERS, cookies=self.cookies, **kwargs)
            if self.valid_response(response):
                break
            else:
                retry_count -= 1
                # log request fail, retrying
        if retry_count == 0:
            # log ran out or retries
            return
        try:
            return response.json()
        except ValueError:
            pass
        if "text/html" in response.headers["content-type"]:
            return response.text
        return response
            
    def valid_response(self, response):
        if response.status_code != 200:
            # log error code
            return False
        return True
        
    @property
    def cookies(self):
        return {}
        

class ExRequestManager(RequestManager):
    MEMBER_ID_KEY = "ipb_member_id"
    PASS_HASH_KEY = "ipb_pass_hash"
    COOKIES = {"uconfig": ""}
    
    def valid_response(self, response):
        if super().valid_response(response):
            content_type = response.headers["content-type"]
            if "image/gif" in content_type:
                print("bad login")  # log
            if "text/html" in content_type and "Your IP address" in response.text:
                print("ip banned") # log
            try:
                if response.json().get("error") is not None:
                    print("error message")  #log
            except ValueError:
                return True
        return False

    @property
    def cookies(self):
        cookies = deepcopy(self.COOKIES)
        cookies[self.MEMBER_ID_KEY] = Config.ex_member_id
        cookies[self.PASS_HASH_KEY] = Config.ex_pass_hash
        return cookies

exRequestManager = ExRequestManager()