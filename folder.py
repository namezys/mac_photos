__author__ = 'namezys'


class Folder(object):
    """Folder

    :ivar uuid:
    :ivar name:
    :ivar folders: set of subfolders
    :ivar albums: set of albums
    """

    def __init__(self, uuid, name=None):
        self.name = name
        self.uuid = uuid

    def __repr__(self):
        return "Folder(%r, %r)" % (self.uuid, self.name)

    def __eq__(self, other):
        return self.uuid == other.uuid
