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


class AlbumData(object):
    def __init__(self, path):
        self.data = copy.deepcopy(BASE)
        db_path = os.path.join(path, "database")
        self.library = Library(db_path)
        self.data[ARCHIVE_PATH] = os.path.abspath(path)

    def build(self):
        self.walk_through_tree(self.library.top_folder)

    def walk_through_tree(self, folder):
        logger.info("Process %s", folder)
        for album in self.library.fetch_albums(folder):
            logger.info("Write %s", album)

        for folder in self.library.fetch_subfolders(folder):
            self.walk_through_tree(folder)


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

    if not args.force and os.path.exists(args.xml_path):
        print "File", args.xml_path, "exists"
        exit(1)
    plistlib.writePlist(album_data.data, args.xml_path)


if __name__ == "__main__":
    main()
