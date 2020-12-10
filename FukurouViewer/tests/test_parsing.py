import os
from typing import List

from FukurouViewer.gallery import DirectoryGallery, Gallery, ZipArchiveGallery
from FukurouViewer.parser import CollectionParser
from FukurouViewer.tests.testing import DBTest


class ParsingTest(DBTest):
    ROOT_DIRECTORY = os.path.abspath("../../TEST_DIRECTORIES")

    def test_loose_gallery(self):
        """Directory containing loose non-archive files that should create one directory"""

        collection = self.create_collection("misc_gallery")
        self.assertEqual(1, collection.count)

        gallery = collection.galleries[0]

        self.assertIsNotNone(gallery)
        self.assertTrue(isinstance(gallery, DirectoryGallery))

    def test_collection_loose(self):
        """Directory containing multiple loose galleries"""

        collection = self.create_collection("loose")

        self.assertEqual(4, collection.count)
        self.assert_galleries(collection.galleries, DirectoryGallery)

    def test_collection_archive(self):
        """Directory containing multiple gallery archives"""

        collection = self.create_collection("archive")

        self.assertEqual(6, collection.count)
        self.assert_galleries(collection.galleries, ZipArchiveGallery)

    def test_collection_assorted(self):
        """Directory containing multiple galleries in both loose and archive format"""

        collection = self.create_collection("assorted")

        self.assertEqual(5, collection.count)
        self.assert_galleries(collection.galleries)

    def test_gallery_with_info(self):
        """Directory containing galleries with info files"""
        pass

    def test_gallery_without_info(self):
        """Directory containing galleries without info"""
        # check that name is gotten from directory
        pass

    def assert_galleries(self, galleries: List[Gallery], galleryType=None):
        for gallery in galleries:
            self.assertIsNotNone(gallery)
            self.assertGreater(gallery.count, 0)
            self.assertIsNotNone(gallery.cover)
            if galleryType is not None:
                self.assertTrue(isinstance(gallery, galleryType))

    def create_collection(self, path: str):
        path = os.path.join(self.ROOT_DIRECTORY, path)
        return CollectionParser.add(path)
