__author__ = 'namezys'


class Album(object):
    """Album

    :ivar uuid:
    :ivar name:
    :ivar poster_id: poster photo id
    """

    def __init__(self, uuid, name, album_id, poster_id=None):
        self.uuid = uuid
        self.name = name
        self.id = album_id
        self.poster_id = poster_id

    def __repr__(self):
        return "Album(%r, %r)" % (self.uuid, self.name)

    def __eq__(self, other):
        return self.uuid == other.uuid
