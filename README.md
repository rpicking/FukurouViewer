FukurouViewer
=====================
This project started off as a learning opportunity to mess around with native message passing between
a chrome extension and a python script.  It has since morphed into a download manager for one click downloading
when paired with the Fukurou Chrome Extension.  The application is controlled with python and uses the PyQt
bindings for Qt/QML to create a GUI interface.

Because of the infancy of this application, the most recent/working branch will most likely be
the develop branch or in some cases the latest feature branch.  Working releases are planned to be implemented 
after Tray Popup Window (Downloads_Tab feature branch) has been implemented.  Development is done during free time
from school and work so, commits and releases might be sporatic and/or infrequent.

[![FukurouViewer Tray Menu](https://i.gyazo.com/ab982cf87e892df507bc01b934df3067.gif)](https://gyazo.com/ab982cf87e892df507bc01b934df3067)

Planned feature expansion includes creation and management of custom galleries and metadata for images, video 
and audio, and the viewing/playing of multimedia files.

Current Features
---------------------
* Favorite Directories
  * Saving directories for one click downloading with extension
* Tray Icon/mini popup Window
  * Download History
  * In progress download infomation (work in progress)
  * Favorite Folders
* Multiple Concurrent Downloading
* Metadata gathering from supported sites

Installation for Development
---------------------
Clone git repository

##### Requirements
* Python 3.6+

##### Windows
1. Install python 3.6+
2. Install python requirements
```pip install -r requirements.txt```

##### Linux
1. Install python 3.6+
2. Install linux python dependencies
```sudo apt install libcurl4-openssl-dev libssl-dev python3-dev```
3. Install python requirements
```pip install -r requirements_linux.txt```

Requirements
---------------------
I plan on being as cross-platform compatible as possible.  Currently no major features limit this plan.  Current
features are known to work on Windows, they haven't been tested yet on linux/mac.  Additionallyinstallation 
instructions havn't been tested on any system.  These are major flaws I hope to rectify ASAP but until then
instructions and/or the python requirements may not be complete or accurate.
* Python 3.xx
* PyQt 5.8 (python module)
* Install python modules from requirements.txt
* Install chrome extension integration
```
pip install -r requirements.txt
```

For integration with chrome extension you need to run install_host script:

##### Windows
```
install_host.bat
```
##### Linux/Mac
```
./install_host.sh
```
This will all the chrome extension to launch the messenger python script to communicate with the FukurouViewer
application.

* TODO: compiling platform specific executable or including all modules with release  

Technologies
---------------------
Some of the technologies that I have learned about and used in the project.
* SQL (SqLite)
  * Database upgrade/migration 
* Threads
* API Querying (Python requests)
* Web Scraping (Beautiful Soup 4)
* PyQt (Python bindings for Qt)
* Qt/QML
* Named Pipes
* Python 3.5

Major Planned Features
---------------------
Some major features that I plan to implement.  List is not complete and not inorder of priority.
* Manga, comic, video viewer and collection manager
* organizing, tagging, browsing, and downloading of multimedia
* Searching, downloading and saving manga/comic metadata to database
  * Storing individual tags and definition
* Identifying individual manga/comics in "shelf" directory
  * Adding individuals to database and linking with metadata
* Basic view of collection
* Gallery info page
* Image/video viewer
* Downloading
  * Website favorites downloading
    * Ongoing
    * Foreign langauge search for chosen language
    * Updating galleries (artist compilations, etc.)
  * RSS and automatic searches based on favorited tags
  * Torrent support
* Embeded formats viewer
* downloading galleries/individual files
* Browsing select websites
* Proxy support

