FukurouViewer
=====================
Manga, comic, video viewer and collection manager.  All in one solution for organizing, tagging, browsing, and downloading of multimedia
collections, comics/manga and videos.  Project started off as a learning opportunity from seangoodwin's PandaViewer

Current Features
---------------------
* Custom save directories
  * Saving directories for one click downloading with extension
* Tray Icon/mini window
  * Download History
  * In progress download infomation
  * Favorite Folders Editing/Viewing/Reordering
* Multiple Concurrent Downloading
* Metadata gathering from supported sites

Major Feature TODO List 
---------------------
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

Requirements
---------------------
We plan on being as cross-platform compatible as possible.  Currently no major features limit this plan.
* Python 3.xx
* PyQt 5.8 (python module)
* install python modules from requirements.txt
```
pip install -r requirements.txt
```
* TODO: compiling platform specific executable or including all modules with release
