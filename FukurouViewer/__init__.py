import os
import sys
import logging

from .utils import Utils

# Create saved directory
if not os.path.exists(Utils.fv_path()):
    os.mkdir(Utils.fv_path())

from .logger import Logger
from . import program, threads

# setup logging
log_dir = Utils.fv_path("logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

filename = os.path.join(log_dir, "log.log")
logging.basicConfig(handlers=[logging.FileHandler(filename, 'a', 'utf-8')],
                    format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
                    level=logging.INFO)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = False

app = program.Program(sys.argv)
app.setup(sys.argv)
