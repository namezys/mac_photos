__author__ = 'namezys'


class Album(object):
    """Album

    :ivar uuid:
    :ivar name:
    """

    def __init__(self, uuid, name, album_id):
        self.uuid = uuid
        self.name = name
        self.album_id = album_id

    def __repr__(self):
        return "Album(%r, %r)" % (self.uuid, self.name)

    def __eq__(self, other):
        return self.uuid == other.uuid
