import os
import logging
from time import strftime

from .utils import Utils
from .logger import Logger

# setup logging
if not os.path.exists(Utils.fv_path()):
    os.mkdir(Utils.fv_path())

log_dir = Utils.fv_path("logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

filename = os.path.join(log_dir, "log.log")
#filename = os.path.join(log_dir, strftime("%Y-%m-%d-%H.%M.%S") + ".log")
logging.basicConfig(handlers=[logging.FileHandler(filename, 'a', 'utf-8')],
                    format="%(asctime)s - %(levelname)s - %(name)s %(message)s",
                    level=logging.INFO)

from .host import Host
host_app = Host()
host_app.setup()
