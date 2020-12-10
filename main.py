import argparse
import logging
import os
import sys

from FukurouViewer.config import Config
from FukurouViewer.setup import setup
from FukurouViewer.program import Program

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--downloader", help="start program in downloader mode", action="store_true")
parser.add_argument("-m", "--main", help="open application on launch", action="store_true")
parser.add_argument("-a", "--appData", type=str, help="Set the FukurouViewer appdata directory")
args = parser.parse_args()

if args.appData:
    Config.appData = args.appData
setup()

# Setup logging
log_dir = Config.fv_path("logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

filename = os.path.join(log_dir, "log.log")
logging.basicConfig(handlers=[logging.FileHandler(filename, 'a', 'utf-8')],
                    format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
                    level=logging.INFO)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = False

# Start Application
app = Program(sys.argv)
app.setup(args)

sys.exit(app.exec_())
