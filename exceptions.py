
class BaseException(Exception):
    fatal = False
    restart = False
    info = ""
    
    def __init__(self):
        super().__init__()
        # LOG error


class BadCredentials(BaseException):
    "Raised for incorrect/missing login id or password"

    restart = True
    info = "Your username/password hash combination was incorrect"


class UserBanned(BaseException):
    "Raised when user is banned/timed out on Exhentai"

    restart = True
    info = "Your IP address has been banned/timed out on Exhentai"
