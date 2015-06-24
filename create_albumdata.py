import logging
import plistlib

import os
import copy

from argparse import ArgumentParser

from library import Library

logger = logging.getLogger(__name__)

DESCR = "Create iPhoto albumdata.xml for photos db"

BASE = {
    "Application Version": "9.4",
    "ArchiveId": "1",
    "Major Version": 2,
    "Minor Version": 0,
}

ARCHIVE_PATH = "Archive Path"
ALBUMS = "List of Albums"
IMAGES = "Master Image List"


class AlbumData(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.data = copy.deepcopy(BASE)
        db_path = os.path.join(path, "database")
        self.library = Library(db_path)
        self.data[ARCHIVE_PATH] = self.path

    def build(self):
        self.walk_through_tree(self.library.top_folder)
        self.data[IMAGES] = dict((str(p.id), self._photo(p)) for p in self.library.fetch_photos())

    def walk_through_tree(self, folder):
        logger.info("Process %s", folder)
        for album in self.library.fetch_albums(folder):
            logger.info("Write %s", album)

        for folder in self.library.fetch_subfolders(folder):
            self.walk_through_tree(folder)

    def _photo(self, photo):
        return {
            "Caption": photo.name,
            "Comment": photo.description,
            "GUID": photo.uuid,
            "Roll": 0, # TODO:
            "Rating": 0, # TODO: Fetch rating
            "ImagePath": os.path.join(self.path, photo.path),
            "MediaType": "Image",
            "ModDateAsTimerInterval": 0.0,
            "MetaModDateAsTimerInterval": 0.0,
            "DateAsTimerInterval": 0.0,
            "DateAsTimerIntervalGMT": 0.0,
            "OriginalPath": os.path.join(self.path, photo.original),
            "ThumbPath": os.path.join(self.path, photo.thumbnails["mini"])
        }


def main():
    parser = ArgumentParser(description=DESCR)
    parser.add_argument("--path", "-p", required=True, help="Path to photos directory", default=".")

    parser.add_argument("--log-level",
                        choices=['INFO', 'WARNING', 'DEBUG', 'ERROR', 'CRITICAL'],
                        help="Logging level",
                        default='INFO')
    parser.add_argument("--force", action="store_true", help="Rewrite xml if it's exist")
    parser.add_argument("xml_path", help="Path to write xml")

    args = parser.parse_args()
    logging.basicConfig(format='%(message)s',
                        level=getattr(logging, args.log_level))

    album_data = AlbumData(args.path)
    album_data.build()

    if not args.force and os.path.exists(args.xml_path):
        print "File", args.xml_path, "exists"
        exit(1)
    plistlib.writePlist(album_data.data, args.xml_path)


if __name__ == "__main__":
    main()
