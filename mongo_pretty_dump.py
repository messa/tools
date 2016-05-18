#!/usr/bin/env python3

'''

'''

import argparse
from base64 import b64encode
from blessings import Terminal
from bson import ObjectId
from contextlib import contextmanager
from datetime import datetime
import os
import pymongo
from uuid import UUID


secondary_preferred = pymongo.ReadPreference.SECONDARY_PREFERRED

t = Terminal(force_styling=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mongo_uri', nargs='?', default='mongodb://127.0.0.1:27017/')
    p.add_argument('collection', nargs='?')
    args = p.parse_args()
    pr = Printer(t=t)
    mongo_uri = args.mongo_uri
    if not mongo_uri.startswith('mongodb://'):
        mongo_uri = 'mongodb://' + mongo_uri
    client = pymongo.MongoClient(mongo_uri,
        read_preference=secondary_preferred,
        connectTimeoutMS=3000,
        serverSelectionTimeoutMS=3000)
    arg_db_name = pymongo.uri_parser.parse_uri(mongo_uri)['database']
    try:
        for db_name in sorted(client.database_names()):
            if arg_db_name and db_name != arg_db_name:
                continue
            if not arg_db_name and db_name == 'local':
                continue
            pr.nl()
            pr('db: {}', t.white_bold(db_name))
            with pr.indent():
                db = client[db_name]
                for collection_name in sorted(db.collection_names()):
                    if args.collection and collection_names != args.collection:
                        continue
                    pr.nl()
                    pr('collection: {}.{}', t.yellow(db_name), t.yellow_bold(collection_name))
                    c = db[collection_name]
                    with pr.indent():
                        doc_count = c.count()
                        start_index = max(0, doc_count - 30)
                        for n, doc in enumerate(c.find()[start_index:], start=1):
                            pr.nl()
                            pr('document {}/{}:', start_index + n, doc_count)
                            with pr.indent():
                                print_document(pr, doc)
    finally:
        print(t.normal)
    os._exit(0) # do not wait for mongo cleanup etc.


def print_document(pr, doc):
    assert isinstance(doc, dict)
    for k, v in sorted(doc.items()):
        assert isinstance(k, str)
        tk = t.white_bold(k)
        if isinstance(v, ObjectId):
            pr('{}: ObjectId(\'{}\')', tk, t.blue(str(v)))
        elif isinstance(v, UUID):
            pr('{}: UUID(\'{}\')', tk, t.blue(str(v)))
        elif isinstance(v, dict):
            pr('{}:', tk)
            with pr.indent():
                print_document(pr, v)
        elif isinstance(v, list):
            pr('{}:', tk)
            with pr.indent():
                for n, item in enumerate(v, start=1):
                    print_document(pr, {'{}/{}'.format(n, len(v)): item})
        elif isinstance(v, (str, int, float, datetime)) or v in (True, False, None):
            pr('{}: {!r}', tk, v)
        elif isinstance(v, bytes):
            pr('{}: {}', tk, b64encode(v).decode('ascii'))
        else:
            raise Exception('Unsupported type: {}'.format(type(v)))



class Printer:

    def __init__(self, **kwargs):
        self.iprefix = ''
        self.extra = kwargs

    @contextmanager
    def indent(self, s='    '):
        before = self.iprefix
        self.iprefix += s
        try:
            yield
        finally:
            self.iprefix = before

    def nl(self):
        print()

    def __call__(self, msg, *args, **kwargs):
        kwargs = dict(self.extra, **kwargs)
        print(self.iprefix + msg.format(*args, **kwargs))


if __name__ == '__main__':
    main()
