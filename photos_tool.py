__author__ = 'namezys'

import logging

from argparse import ArgumentParser

from library import Library

DESCR = "Read photos database"


def print_photo(photo):
    print "Photo: ", photo.name
    print "\tdescription:", photo.description
    print "\tis favorite:", photo.is_favorite
    print "\tpath:", photo.path
    print "\toriginal:", photo.original
    print "\tthumbnails:"
    for t, p in photo.thumbnails.items():
        print "\t\t%s:" % t, p
    print "\tdate:", photo.date
    print "\tid:", photo.id, "uuid:", photo.uuid
    print "\ttime stamps:"
    print "\t\ttime zone offset:", photo.time_zone_offset, "\tname:", photo.time_zone
    print "\t\timage:", photo.image_date_ts
    print "\t\timage gmt:", photo.image_data_gmt_ts
    print "\t\tchange:", photo.export_image_change_date_ts
    print "\t\tchange metadata:", photo.export_metadata_change_date_ts


def print_folder(folder, library, offset, deep=None):
    folders = list(library.fetch_subfolders(folder))
    albums = list(library.fetch_albums(folder))
    for f in folders:
        print offset, "folder '%s': uid=%s" % (f.name, f.uuid)
        if deep is None or deep > 1:
            print_folder(f, library, offset + "\t", deep and (deep - 1))
    for a in albums:
        print offset, "album '%s': uid=%s, poster=%d" % (a.name, a.uuid, a.poster_id)



def main():
    parser = ArgumentParser(description=DESCR)
    parser.add_argument("--db-path", "-p", required=True, help="Path to database directory", default=".")

    action_gr = parser.add_argument_group("Actions")
    action_gr.add_argument("--photos", action="store_true", help="List all photos in library")
    action_gr.add_argument("--tree", action="store_true", help="List all folder and albums")
    action_gr.add_argument("--lib-folder", action="store_true", help="List all system library folder")
    action_gr.add_argument("--album", help="List photos in album")

    parser.add_argument("--log-level",
                        choices=['INFO', 'WARNING', 'DEBUG', 'ERROR', 'CRITICAL'],
                        help="Logging level",
                        default='INFO')
    args = parser.parse_args()
    logging.basicConfig(format='%(message)s',
                        level=getattr(logging, args.log_level))

    library = Library(args.db_path, true)

    if args.photos:
        for photo in library.fetch_photos():
            print_photo(photo)

    if args.tree:
        print "Tree:"
        print_folder(library.top_folder, library, "\t")

    if args.lib_folder:
        print_folder(library.library_folder, library, "", 1)

    if args.album:
        photos = dict((p.id, p) for p in library.fetch_photos())
        for photo_id in library.fetch_album_photo_id_list(library.album(args.album)):
            print_photo(photos[photo_id])

if __name__ == "__main__":
    main()
