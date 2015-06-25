__author__ = 'namezys'

import datetime
import pytz
import time

from logging import getLogger

logger = getLogger(__name__)

TIME_OFFSET = datetime.timedelta(11323)


def tz(tzname):
    if not tzname:
        return None
    try:
        return pytz.timezone(tzname)
    except pytz.UnknownTimeZoneError:
        logger.debug("Can't found time zone %s", tz)
        return None


class Photo(object):
    """One photo in library

    :ivar title: title of photo
    :ivar description: description of photo
    :ivar data: Datetime of photo
    :ivar path: Path to file with photo
    ;ivar original: Path to original file with photo
    """

    def __init__(self, uuid, name,
                 path=None,
                 original_path=None,
                 description=None,
                 is_favorite=None,
                 thumbnails=None,
                 photo_id=None,
                 time_zone=None,
                 image_date_ts=None,
                 export_image_change_date_ts=None,
                 export_metadata_change_date_ts=None,
                 time_zone_offset=None):
        self.uuid = uuid
        self.name = name
        self.path = path
        self.original = original_path
        self.description = description
        self.is_favorite = is_favorite
        self.thumbnails = thumbnails
        self.id = photo_id

        self.time_zone = time_zone
        self.time_zone_offset = time_zone_offset or 0
        self.image_date_ts = image_date_ts
        self.export_image_change_date_ts = export_image_change_date_ts
        self.export_metadata_change_date_ts = export_metadata_change_date_ts

    @property
    def image_data_gmt_ts(self):
        return self.image_date_ts + self.time_zone_offset

    @property
    def date(self):
        return datetime.datetime.fromtimestamp(self.image_date_ts - 3600, tz(self.time_zone)) + TIME_OFFSET

    def __eq__(self, other):
        return self.uuid == other.uuid
