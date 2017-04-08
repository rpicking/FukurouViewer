import os
import sys
import logging

from .utils import Utils
from .logger import Logger

# setup logging
if not os.path.exists(Utils.fv_path()):
    os.mkdir(Utils.fv_path())

log_dir = Utils.fv_path("logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

filename = os.path.join(log_dir, "log.log")
logging.basicConfig(handlers=[logging.FileHandler(filename, 'a', 'utf-8')],
                    format="%(asctime)s - %(levelname)s - %(name)s %(message)s",
                    level=logging.INFO)

from . import program, threads
app = program.Program(sys.argv)
app.setup()
threads.setup()
