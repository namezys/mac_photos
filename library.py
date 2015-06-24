__author__ = 'namezys'

import datetime
import pytz
import os
import sqlite3

from album import Album
from photo import Photo
from folder import Folder

from logging import getLogger

logger = getLogger(__name__)


TIME_OFFSET = datetime.timedelta(11323)
UNADJUSTED = "UNADJUSTEDNONRAW"

LIBRARY_FOLDER = "LibraryFolder"
TOP_LEVEL_FOLDER = "TopLevelAlbums"


def tz(tzname):
    if not tzname:
        return None
    try:
        return pytz.timezone(tzname)
    except pytz.UnknownTimeZoneError:
        logger.exception("Can't found time zone")
        return None


def thumbnails(path, uid):
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    mini_thumbnail = "thumb_" + name + ext
    thumbnail = "thumb_" + name + "_1024" + ext
    return {
        'mini': os.path.join("Thumbnails/", os.path.dirname(path), uid, mini_thumbnail),
        'hd': os.path.join("Thumbnails/", os.path.dirname(path), uid, thumbnail),
    }


class Library(object):

    LIBRARY_DB = "Library.apdb"
    IMAGE_PROXIES = "ImageProxies.apdb"

    def __init__(self, path):
        self.path = path
        self.library_db = sqlite3.connect(os.path.join(self.path, self.LIBRARY_DB))
        self.image_proxies_db = sqlite3.connect(os.path.join(self.path, self.IMAGE_PROXIES))

        self.top_folder = Folder(TOP_LEVEL_FOLDER, "Top level")
        self.library_folder = Folder(LIBRARY_FOLDER, "Library folder")

    def get_adjustment(self, adjustment):
        cursor = self.image_proxies_db.cursor()
        cursor.execute("SELECT resourceUuid, filename FROM RKModelResource WHERE resourceTag=?", [adjustment])
        uuid, filename = cursor.fetchone()
        p1 = str(ord(uuid[0]))
        p2 = str(ord(uuid[1]))
        return os.path.join("resources/modelresources", p1, p2, uuid, filename)

    def _photo(self, uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, id):
        logger.debug("Got photo %s (%s)", name, uuid)
        date = datetime.datetime.fromtimestamp(data_ts - 3600, tz(date_tz)) + TIME_OFFSET
        orig_path = os.path.join("Masters", orig_path_db)
        if adjustment == UNADJUSTED:
            path = orig_path
        else:
            path = self.get_adjustment(adjustment)
        return Photo(uuid, name=name, description=description, date=date, path=path, originalPath=orig_path,
                     thumbnails=thumbnails(orig_path_db, uuid), id=id)

    def album(self, uuid):
        cursor = self.library_db.execute("SELECT name FROM RKAlbum WHERE uuid = ?", [uuid])
        return Album(uuid, cursor.fetchone()[0])

    def fetch_subfolders(self, folder):
        """Get subfolder of given folder

        :param folder:
        """
        logger.info("Fetch subfolders of %s", folder)
        cursor = self.library_db.execute("SELECT uuid, name FROM RKFolder WHERE parentFolderUuid = ?", [folder.uuid])
        for uuid, name in cursor:
            logger.debug("Got folder %s (%s)", name, uuid)
            yield Folder(uuid, name)

    def fetch_albums(self, folder):
        """Get folder contents

        :param folder:
        """
        logger.info("Fetch albums of %s", folder)
        logger.debug("Get albums")
        cursor = self.library_db.execute("SELECT uuid, name FROM RKAlbum WHERE name NOT NULL AND folderUuid = ?",
                                         [folder.uuid])
        for uuid, name in cursor:
            logger.debug("Got album %s (%s)", name, uuid)
            yield Album(uuid, name)

    def fetch_album_photos(self, album):
        """Get album content

        :param album:
        """
        logger.info("Fetch %s content", album)
        cursor = self.library_db.cursor()
        if album.uuid == "allPhotosAlbum":
            cursor.execute("""SELECT DISTINCT v.uuid, v.name,
                v.imageDate, v.imageTimeZoneName,
                v.extendedDescription,
                m.imagePath, v.adjustmentUuid,
                v.modelId
            FROM RKAlbumVersion AS av
            JOIN RKAlbum AS a ON a.modelId = av.albumId
            JOIN RKVersion AS v ON v.modelId = av.versionId
            JOIN RKMaster AS m ON m.uuid = v.masterUuid""")
        else:
            cursor.execute("""SELECT v.uuid, v.name,
                v.imageDate, v.imageTimeZoneName,
                v.extendedDescription,
                m.imagePath, v.adjustmentUuid,
                v.modelId
            FROM RKAlbumVersion AS av
            JOIN RKAlbum AS a ON a.modelId = av.albumId
            JOIN RKVersion AS v ON v.modelId = av.versionId
            JOIN RKMaster AS m ON m.uuid = v.masterUuid
            WHERE a.uuid = ?""", [album.uuid])
        for uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, id in cursor:
            yield self._photo(uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, id)

    def fetch_photos(self):
        """Get photos
        """
        logger.info("Fetch phtoos")
        cursor = self.library_db.cursor()
        cursor.execute("""SELECT v.uuid, v.name,
                v.imageDate, v.imageTimeZoneName,
                v.extendedDescription,
                m.imagePath, v.adjustmentUuid,
                v.modelId
            FROM RKVersion AS v
            JOIN RKMaster AS m ON m.uuid = v.masterUuid
            WHERE NOT v.isInTrash""")
        for uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, id in cursor:
            yield self._photo(uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, id)