#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse
from pprint import pformat
import pymongo


INDENT = " " * 4


def main():
    op = optparse.OptionParser()
    op.add_option("--host", default="localhost")
    op.add_option("--port", default="27017")
    (options, args) = op.parse_args()

    conn = pymongo.Connection(host=options.host, port=int(options.port))

    print
    for dbName in conn.database_names():
        db = conn[dbName]
        export_database(db)


def export_database(db):
    print "Database:", db.name
    print
    for collectionName in db.collection_names():
        collection = db[collectionName]
        export_collection(collection)


def export_collection(collection):
    print INDENT + "Collection:", collection.name
    for doc in collection.find():
        lines = pformat(doc).splitlines()
        for line in lines:
            print INDENT + INDENT + line
        print
    print



if __name__ == "__main__":
    main()


