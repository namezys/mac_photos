__author__ = 'namezys'

import logging

from argparse import ArgumentParser

from library import Library

DESCR = "Read photos database"


def print_photo(photo):
    print "Photo: ", photo.name
    print "\tdescription:", photo.description
    print "\tpath:", photo.path
    print "\toriginal:", photo.original
    print "\tthumbnails:"
    for t, p in photo.thumbnails.items():
        print "\t\t%s:" % t, p
    print "\tdate:", photo.date
    print "\tid:", photo.id, "uuid:", photo.uuid


def print_folder(folder, library, offset):
    folders = list(library.fetch_subfolders(folder))
    albums = list(library.fetch_albums(folder))
    for f in folders:
        print offset, "folder '%s': uid=%s" % (f.name, f.uuid)
        print_folder(f, library, offset + "\t")
    for a in albums:
        print offset, "album '%s': uid=%s" % (a.name, a.uuid)



def main():
    parser = ArgumentParser(description=DESCR)
    parser.add_argument("--db-path", "-p", required=True, help="Path to database directory", default=".")

    action_gr = parser.add_argument_group("Actions")
    action_gr.add_argument("--photos", action="store_true", help="List all photos in library")
    action_gr.add_argument("--tree", action="store_true", help="List all folder and albums")
    action_gr.add_argument("--album", help="List photos in album")

    parser.add_argument("--log-level",
                        choices=['INFO', 'WARNING', 'DEBUG', 'ERROR', 'CRITICAL'],
                        help="Logging level",
                        default='INFO')
    args = parser.parse_args()
    logging.basicConfig(format='%(message)s',
                        level=getattr(logging, args.log_level))

    library = Library(args.db_path)

    if args.photos:
        for photo in library.fetch_photos():
            print_photo(photo)

    if args.tree:
        print "Tree:"
        print_folder(library.top_folder, library, "\t")

    if args.album:
        for photo in library.fetch_album_photos(library.album(args.album)):
            print_photo(photo)

if __name__ == "__main__":
    main()
