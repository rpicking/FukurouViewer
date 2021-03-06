import bs4

from .utils import Utils
from .logger import Logger
from .request_manager import ex_request_manager


class Search(Logger):
    BASE_EX_URL = "http://exhentai.org/?inline_set=dm_t&f_doujinshi=1&f_manga=1&f_artistcg=1&f_gamecg=1&f_western=1&f_non-h=1&f_imageset=1&f_cosplay=1&f_asianporn=1&f_misc=0&f_sname=on&adv&f_search=%s&advsearch=1&f_srdd=2&f_apply=Apply+Filter&f_shash=%s&page=%s&fs_smiliar=1&fs_covers=%s"

    def __init(self):
        print("SEARCH")

    @classmethod
    def search_ex_gallery(cls):
        cls = cls()
        title = "titlehere"
        file = "file"
        file2 = "file1"
        
        sha_hash = Utils.generate_sha_hash(file)
        cls.ex_search(title=title, sha_hash=sha_hash, page_num=0, cover_only=1)
        sha_hash = Utils.generate_sha_hash(file2)
        cls.ex_search(sha_hash=sha_hash, page_num=0, cover_only=1)

    @classmethod
    def ex_search(cls, **kwargs):
        title = kwargs.get("title", "")
        sha_hash = kwargs.get("sha_hash", "")
        page_num = kwargs.get("page_num", 0)
        cover_only = kwargs.get("cover_only", 1)
                
        url = cls.BASE_EX_URL % (title, sha_hash, page_num, cover_only)
        response = ex_request_manager.get(url)
        html_results = bs4.BeautifulSoup(response, "html.parser")
        results = [div.a for div in html_results.findAll("div", attrs={"class": "it5"})]
        result_urls = [r['href'] for r in results]

        return result_urls

        # get all galleries matching
        # splice out galid & galtoken
        # api call for tags
        # search tags, eliminating galleries not default lang/japanese
        # pick gallery with most tags (remove if only default lang)
        # add metadata entry in database
        # refresh UI
