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
        return obj.id
    if isinstance(obj, Folder):
        return obj.id * 10000


class AlbumData(object):
    def __init__(self, path, disable_rolls=None, disable_rating=None, tmp_db=None, gen_caption=None):
        self.path = os.path.abspath(path)

        db_path = os.path.join(path, "database")
        self.library = Library(db_path, tmp_db)

        self.data = copy.deepcopy(BASE)
        self.data[ARCHIVE_PATH] = self.path
        self.data[ALBUMS] = []

        self.photos = dict()

        self.disable_rolls = disable_rolls
        self.disable_rating = disable_rating
        self.all_roll_id = 5

        self.generate_caption = gen_caption

    def build(self):
        logger.debug("Fetch photos")
        self.photos = dict((p.id, p) for p in self.library.fetch_photos())

        logger.debug("Save folders and albums")
        self.data[ALBUMS] += [self._all_photos_album, self._flagged_album]
        self.save_folder(self.library.top_folder, None)

        logger.debug("Save rolls")
        if not self.disable_rolls:
            self.data["List of Rolls"] = [self._all_roll]

        logger.debug("Save images")
        self.data[IMAGES] = dict((str(p.id), self._photo(p)) for p in self.photos.values())

    def save_folder(self, folder, parent):
        photo_ids = set()
        if folder != self.library.top_folder:
            data = self._album_base(folder, [], parent=(parent if parent != self.library.top_folder else None))
            self.data[ALBUMS].append(data)
        for sub_folder in self.library.fetch_subfolders(folder):
            photo_ids |= self.save_folder(sub_folder, folder)
        for album in self.library.fetch_albums(folder):
            photo_ids |= self.save_album(album, folder)
        if folder != self.library.top_folder:
            self._append_photos(data, photo_ids)
        logger.debug("Got %s photos for %s", len(photo_ids), folder)
        return photo_ids

    def save_album(self, album, parent):
        photo_ids = set(self.library.fetch_album_photo_id_list(album))
        self.data[ALBUMS].append(self._album_base(album, photo_ids, parent=parent))
        return photo_ids

    def walk_through_tree(self, folder):
        logger.info("Process %s", folder)
        for album in self.library.fetch_albums(folder):
            logger.info("Write %s", album)

        for folder in self.library.fetch_subfolders(folder):
            self.walk_through_tree(folder)

    @property
    def _all_photos_album(self):
        album = self.library.all_photos_album
        photo_ids = self.photos.keys()
        data = self._album_base(album, photo_ids, album_type="99", name="Photos")
        data["Master"] = True
        return data

    @property
    def _flagged_album(self):
        album = self.library.favorites
        photo_ids = list(str(p.id) for p in self.photos.values() if p.is_favorite)
        return self._album_base(album, photo_ids, album_type="Flagged", name="Flagged", sort_order="1")

    @property
    def _last_imported_album(self):
        album = self.library.last_import_album
        photo_ids = set(self.library.fetch_album_photo_id_list(album))
        return self._album_base(album, photo_ids)

    def _album_base(self, album, photo_ids, name=None, album_type=None, sort_order=None, parent=None):
        if album_type is None:
            if isinstance(album, Album):
                album_type = "Regular"
            elif isinstance(album, Folder):
                album_type = "Folder"
        data = {
            "AlbumId": _iphoto_id(album),
            "AlbumName": name or album.name,
            "GUID": album.uuid,
            "Album Type": album_type
        }
        if album.poster_id:
            data["KeyPhotoKey"] = str(album.poster_id)
        if sort_order:
            data["Sort Order"] = sort_order
        if parent:
            data["Parent"] = _iphoto_id(parent)
        if photo_ids:
            self._append_photos(data, photo_ids)
        return data

    def _append_photos(self, data, photo_ids):
        data["KeyList"] = list(str(k) for k in sorted(photo_ids))
        data["PhotoCount"] = len(photo_ids)
        return data

    def _photo(self, photo):
        empty_caption = ""
        if self.generate_caption:
            empty_caption = "photo_%d" % photo.id
        data = {
            "Caption": photo.name or empty_caption,
            "Comment": photo.description or " ",
            "GUID": photo.uuid,
            "Roll": self.all_roll_id,
            "Rating": 5 if photo.is_favorite and not self.disable_rating else 0,
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

    @property
    def _all_roll(self):
        """One fake event"""
        return {
            "RollID": self.all_roll_id,
            "ProjectUuid": "RBoLkXF0QxGHAqJTrs9p0Q",
            "RollName": "Photos",
            "RollDateAsTimerInterval": min(p.image_date_ts for p in self.photos.values()),
            "KeyPhotoKey": str(min(p.id for p in self.photos.values())),
            "PhotoCount": len(self.photos),
            "KeyList": list(str(p.id) for p in self.photos.values())
        }


def main():
    parser = ArgumentParser(description=DESCR)
    parser.add_argument("--path", "-p", required=True, help="Path to photos directory", default=".")
    parser.add_argument("--disable-rolls", action="store_true", help="Disable iPhoto events")
    parser.add_argument("--disable-rating", action="store_true", help="Disable 5-stars iPhoto rating for favorite")
    parser.add_argument("--generate-caption", action="store_true", help="Generate caption like photo_id")
    parser.add_argument("--tmp-db", action="store_true", help="Create temp copy of db if it is locked")

    parser.add_argument("--log-level",
                        choices=['INFO', 'WARNING', 'DEBUG', 'ERROR', 'CRITICAL'],
                        help="Logging level",
                        default='INFO')
    parser.add_argument("--force", action="store_true", help="Rewrite xml if it's exist")
    parser.add_argument("xml_path", help="Path to write xml")

    args = parser.parse_args()
    logging.basicConfig(format='%(message)s',
                        level=getattr(logging, args.log_level))

    album_data = AlbumData(args.path, disable_rolls=args.disable_rolls, disable_rating=args.disable_rating,
                           tmp_db=args.tmp_db, gen_caption=args.generate_caption)
    album_data.build()

    if not args.force and os.path.exists(args.xml_path):
        print "File", args.xml_path, "exists"
        exit(1)
    plistlib.writePlist(album_data.data, args.xml_path)


if __name__ == "__main__":
    main()
