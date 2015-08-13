import logging
import plistlib
import shutil

import os
import copy

from argparse import ArgumentParser

from library import Library
from album import Album
from folder import Folder

logger = logging.getLogger(__name__)

DESCR = "Create albums thumbnails for photos db"

BASE = {
    "Application Version": "9.4",
    "ArchiveId": "1",
    "Major Version": 2,
    "Minor Version": 0,
}

ARCHIVE_PATH = "Archive Path"
ALBUMS = "List of Albums"
IMAGES = "Master Image List"
ALBUMS = "List of Albums"


def _iphoto_id(obj):
    if isinstance(obj, Album):
        return obj.id
    if isinstance(obj, Folder):
        return obj.id * 10000


class SaveThumbnails(object):
    def __init__(self, path, photos_path, tmp_db):
        self.path = os.path.abspath(path)
        self.photos_path = photos_path

        db_path = os.path.join(photos_path, "database")
        self.library = Library(db_path, tmp_db)

        self.photos = dict()

    def build(self):
        logger.debug("Fetch photos")
        self.photos = dict((p.id, p) for p in self.library.fetch_photos())

        logger.debug("Save folders and albums")
        self.save_folder(self.library.top_folder, None)

    def save_folder(self, folder, parent_path):
        logger.debug("Save %s with parent %s", folder, parent_path)
        path = os.path.join(parent_path, folder.name) if folder != self.library.top_folder else "."
        logger.debug("Create directory %s", path)
        if not os.path.exists(os.path.join(self.path, path)):
            os.makedirs(os.path.join(self.path, path))
        for sub_folder in self.library.fetch_subfolders(folder):
            self.save_folder(sub_folder, path)
        for album in self.library.fetch_albums(folder):
            self.save_album(album, path)

    def save_album(self, album, parent_path):
        logger.debug("Save %s with parent %s", album, parent_path)
        path = os.path.join(parent_path, album.name)
        logger.debug("Create directory %s", path)
        if not os.path.exists(os.path.join(self.path, path)):
            os.makedirs(os.path.join(self.path, path))
        photos = set(self.photos[i] for i in self.library.fetch_album_photo_id_list(album))
        for photo in sorted(photos, key=lambda  p: p.date):
            self.save_photo(photo, path)

    def save_photo(self, photo, parent_path):
        caption = photo.name or "Photo_%d" % photo.id
        file_name = photo.thumbnails["hd"] or photo.thumbnails["mini"] or photo.original
        src = os.path.join(self.photos_path, file_name)
        ext = os.path.splitext(src)[1]
        dst = os.path.join(self.path, parent_path, caption + ext)
        logger.debug("Copy %s to %s", src, dst)
        shutil.copy(src, dst)


def main():
    parser = ArgumentParser(description=DESCR)
    parser.add_argument("--path", "-p", required=True, help="Path to photos directory", default=".")
    parser.add_argument("--tmp-db", action="store_true", help="Create temp copy of db if it is locked")

    parser.add_argument("--log-level",
                        choices=['INFO', 'WARNING', 'DEBUG', 'ERROR', 'CRITICAL'],
                        help="Logging level",
                        default='INFO')
    parser.add_argument("directory", help="Path to write thumbnails")

    args = parser.parse_args()
    logging.basicConfig(format='%(message)s',
                        level=getattr(logging, args.log_level))

    album_data = SaveThumbnails(args.directory, args.path, tmp_db=args.tmp_db)
    album_data.build()


if __name__ == "__main__":
    main()
