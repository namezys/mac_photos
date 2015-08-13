__author__ = 'namezys'

import os
import sqlite3
import shutil
import tempfile

from album import Album
from photo import Photo
from folder import Folder

from logging import getLogger

logger = getLogger(__name__)


UNADJUSTED = "UNADJUSTEDNONRAW"

LIBRARY_FOLDER = "LibraryFolder"
TOP_LEVEL_FOLDER = "TopLevelAlbums"


def thumbnails(path, uid):
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    mini_thumbnail = "thumb_" + name + ext
    thumbnail = name + "_1024" + ext
    return {
        'mini': os.path.join("Thumbnails/", os.path.dirname(path), uid, mini_thumbnail),
        'hd': os.path.join("Thumbnails/", os.path.dirname(path), uid, thumbnail),
    }


class Library(object):

    LIBRARY_DB = "Library.apdb"
    IMAGE_PROXIES = "ImageProxies.apdb"

    def __init__(self, path, tmp_db):
        self.path = path
        library_path = os.path.join(self.path, self.LIBRARY_DB)
        image_proxies_path = os.path.join(self.path, self.IMAGE_PROXIES)
        self.tmp_dir = None
        if tmp_db:
            self.tmp_dir = tempfile.mkdtemp()
            tmp_library_path = os.path.join(self.tmp_dir, self.LIBRARY_DB)
            tmp_image_proxies_path = os.path.join(self.tmp_dir, self.IMAGE_PROXIES)
            shutil.copy(library_path, tmp_library_path)
            shutil.copy(image_proxies_path, tmp_image_proxies_path)
            library_path = tmp_library_path
            image_proxies_path = tmp_image_proxies_path
        self.library_db = sqlite3.connect(library_path)
        self.image_proxies_db = sqlite3.connect(image_proxies_path)

        self.top_folder = self.folder(TOP_LEVEL_FOLDER)
        self.library_folder = self.folder(LIBRARY_FOLDER)
        self.all_photos_album = self.album("allPhotosAlbum")
        self.last_import_album = self.album("lastImportAlbum")
        self.favorites = self.album("favoritesAlbum")

    def __del__(self):
        if self.tmp_dir:
            shutil.rmtree(self.tmp_dir)

    def get_adjustment(self, adjustment):
        cursor = self.image_proxies_db.cursor()
        cursor.execute("SELECT resourceUuid, filename FROM RKModelResource WHERE resourceTag=?", [adjustment])
        uuid, filename = cursor.fetchone()
        p1 = str(ord(uuid[0]))
        p2 = str(ord(uuid[1]))
        return os.path.join("resources/modelresources", p1, p2, uuid, filename)

    def _photo(self, uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, photo_id,
               change_ts, change_meta_ts, tz_offset, favorite):
        logger.debug("Got photo %s (%s)", name, uuid)
        orig_path = os.path.join("Masters", orig_path_db)
        if adjustment == UNADJUSTED:
            path = orig_path
        else:
            path = self.get_adjustment(adjustment)
        return Photo(uuid, name=name, description=description,
                     image_date_ts=data_ts, time_zone=date_tz, time_zone_offset=tz_offset,
                     path=path, original_path=orig_path,
                     thumbnails=thumbnails(orig_path_db, uuid), photo_id=photo_id,
                     export_image_change_date_ts=change_ts, export_metadata_change_date_ts=change_meta_ts,
                     is_favorite=bool(favorite))

    def album(self, uuid):
        cursor = self.library_db.execute("""SELECT name, modelId,
                                                (SELECT modelId FROM RKVersion WHERE uuid = a.posterVersionUuid)
                                            FROM RKAlbum AS a WHERE uuid = ?""", [uuid])
        name, album_id, poster_id = cursor.fetchone()
        return Album(uuid, name=name, album_id=album_id, poster_id=poster_id)

    def folder(self, uuid):
        cursor = self.library_db.execute("SELECT name, modelId FROM RKFolder WHERE uuid = ?", [uuid])
        name, folder_id = cursor.fetchone()
        return Folder(uuid, name=name, folder_id=folder_id)

    def fetch_subfolders(self, folder):
        """Get subfolder of given folder

        :param folder:
        """
        logger.info("Fetch subfolders of %s", folder)
        cursor = self.library_db.execute("""SELECT uuid, name, modelId
                                            FROM RKFolder
                                            WHERE NOT isInTrash AND parentFolderUuid = ?""", [folder.uuid])
        for uuid, name, folder_id in cursor:
            logger.debug("Got folder %s (%s)", name, uuid)
            yield Folder(uuid, name, folder_id=folder_id)

    def fetch_albums(self, folder):
        """Get folder contents

        :param folder:
        """
        logger.info("Fetch albums of %s", folder)
        logger.debug("Get albums")
        cursor = self.library_db.execute("""SELECT uuid, name, modelId,
                                                (SELECT modelId FROM RKVersion WHERE uuid = a.posterVersionUuid)
                                            FROM RKAlbum AS a
                                            WHERE NOT isInTrash AND name NOT NULL
                                                AND NOT EXISTS(SELECT * FROM RKFolder WHERE implicitAlbumUuid = a.uuid)
                                                AND folderUuid = ?""",
                                         [folder.uuid])
        for uuid, name, album_id, poster_id in cursor:
            logger.debug("Got album %s (%s)", name, uuid)
            yield Album(uuid, name, album_id, poster_id=poster_id)

    def fetch_album_photo_id_list(self, album):
        logger.info("Fetch photo ids of %s", album)
        if album == self.all_photos_album:
            cursor = self.library_db.execute("SELECT DISTINCT versionId FROM RKAlbumVersion")
        else:
            # TODO: append video
            cursor = self.library_db.execute("""SELECT av.versionId
                FROM RKAlbumVersion AS av
                JOIN RKAlbum AS a ON a.modelId = av.albumId
                JOIN RKVersion AS v
                WHERE NOT v.isInTrash AND v.type = 2 AND a.uuid = ?""", [album.uuid])
        return (row[0] for row in cursor)

    def fetch_photos(self):
        """Get photos
        """
        logger.info("Fetch photos")
        cursor = self.library_db.cursor()
        cursor.execute("""SELECT v.uuid, v.name,
                v.imageDate, v.lastModifiedDate, v.lastModifiedDate,
                v.imageTimeZoneName, v.imageTimeZoneOffsetSeconds,
                v.extendedDescription, v.isFavorite,
                m.imagePath, v.adjustmentUuid,
                v.modelId
            FROM RKVersion AS v
            JOIN RKMaster AS m ON m.uuid = v.masterUuid
            WHERE NOT v.isInTrash AND v.type = 2""")
        for uuid, name, data_ts, change_ts, change_meta_ts, date_tz, tz_offset,\
                description, favorite, orig_path_db, adjustment, photo_id in cursor:
            yield self._photo(uuid, name, data_ts, date_tz, description, orig_path_db, adjustment, photo_id,
                              change_ts, change_meta_ts, tz_offset, favorite)
