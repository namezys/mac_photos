__author__ = 'namezys'

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
                 originalPath=None,
                 description=None,
                 date=None,
                 thumbnails=None):
        self.uuid = uuid
        self.name = name
        self.path = path
        self.original = originalPath
        self.date = date
        self.description = description
        self.thumbnails = thumbnails

    def __eq__(self, other):
        return self.uuid == other.uuid
