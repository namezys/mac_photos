import logging
import plistlib

import os
import copy

from argparse import ArgumentParser

from library import Library
from album import Album
from folder import Folder

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
ALBUMS = "List of Albums"


def _iphoto_id(obj):
    if isinstance(obj, Album):
        return obj.album_id
    if isinstance(obj, Folder):
        return obj.folder_id * 10000


class AlbumData(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.data = copy.deepcopy(BASE)
        db_path = os.path.join(path, "database")
        self.library = Library(db_path)
        self.data[ARCHIVE_PATH] = self.path

        self.photos = dict()

        self.albums_list = dict()

    def build(self):
        self.photos = dict((p.id, p) for p in self.library.fetch_photos())
        self.walk_through_tree(self.library.top_folder)

        logger.debug("Save albums")

        albums = [self._all_photos_album, self._flagged_album]

        self.data[ALBUMS] = albums

        self.data[IMAGES] = dict((str(p.id), self._photo(p)) for p in self.photos.values())

    def walk_through_tree(self, folder):
        logger.info("Process %s", folder)
        for album in self.library.fetch_albums(folder):
            logger.info("Write %s", album)

        for folder in self.library.fetch_subfolders(folder):
            self.walk_through_tree(folder)

    @property
    def _all_photos_album(self):
        album = self.library.all_photos_album
        data = self._album_base(album, album_type="99", name="Photos")
        data["Master"] = True
        return data

    @property
    def _flagged_album(self):
        album = self.library.favorites
        return self._album_base(album, album_type="Flagged", name="Flagged", sort_order="1")

    @property
    def _last_imported_album(self):
        album = self.library.last_import_album
        return self._album_base(album)

    def _album_base(self, album, name=None, album_type="Regular", sort_order=None):
        keys = list(str(k) for k in self.library.fetch_album_photo_id_list(album))
        data = {
            "AlbumId": _iphoto_id(album),
            "AlbumName": name or album.name,
            "GUID": album.uuid,
            "Master": True,
            "KeyList": keys,
            "PhotoCount": len(keys),
            "Album Type": album_type
        }
        if sort_order:
            data["Sort Order"] = sort_order
        return data

    def _photo(self, photo):
        data = {
            "Caption": photo.name or "",
            "Comment": photo.description or "",
            "GUID": photo.uuid,
            "Roll": 0, # TODO:
            "Rating": 5 if photo.is_favorite else 0,
            "ImagePath": os.path.join(self.path, photo.path),
            "MediaType": "Image",
            "ModDateAsTimerInterval": photo.export_image_change_date_ts,
            "MetaModDateAsTimerInterval": photo.export_metadata_change_date_ts,
            "DateAsTimerInterval": photo.image_date_ts,
            "DateAsTimerIntervalGMT": photo.image_data_gmt_ts,
            "OriginalPath": os.path.join(self.path, photo.original),
            "ThumbPath": os.path.join(self.path, photo.thumbnails["mini"])
        }
        if photo.is_favorite:
            data["Flagged"] = True
        return data


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
