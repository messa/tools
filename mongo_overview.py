#!/usr/bin/env python3

import argparse
from blessings import Terminal
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
import pymongo
from time import time
from uuid import UUID
import random


assert pymongo.version.startswith('3.'), pymongo.version

secondary_preferred = pymongo.ReadPreference.SECONDARY_PREFERRED

t = Terminal()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mongo_uri', nargs='?', default='mongodb://127.0.0.1:27017/')
    p.add_argument('--structure', '-s', action='store_true', help='analyze document structure')
    args = p.parse_args()
    pr = Printer(t=t)
    client = pymongo.MongoClient(args.mongo_uri,
        read_preference=secondary_preferred,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000)
    print('client: {!r}; server version: {}'.format(client, client.server_info()['version']))
    db_names = sorted(client.database_names())
    for db_name in db_names:
        pr.nl()
        db = client[db_name]
        pr('db: {t.bold}{t.white}{name}{t.normal}', name=db_name)
        with pr.indent():
            c_names = sorted(db.collection_names())
            for c_name in c_names:
                pr.nl()
                c = db[c_name]
                pr('collection: {t.yellow}{db_name}.{t.bold}{name:25}{t.normal}', name=c_name, db_name=db_name)
                if c_name == 'system.indexes' or (db_name == 'local' and c_name == 'startup_log'):
                    continue
                with pr.indent():
                    #pr('documents: {count}', count=c.count())

                    stats = db.command({'collStats': c_name})
                    pr('documents: {count} {t.black}avg size:{t.normal} {avgs} {t.black}total storage:{t.normal} {ts:.2f} MB',
                        count=stats['count'],
                        avgs=to_kbs(stats.get('avgObjSize')),
                        ts=stats['storageSize']/2.**20)

                    for index in sorted(c.list_indexes(), key=lambda index: index['name']):
                        def format_key_item(item):
                            name, order = item
                            return '{}/{}'.format(name, order)
                        desc = ', '.join(format_key_item(item) for item in index['key'].items())
                        pr('index: {t.bold}{t.black}{name}{t.normal} ({key}) {size:.2f} kB',
                            name=index['name'], key=desc, size=stats['indexSizes'][index['name']]/1024.)

                    if args.structure:
                        cursor = c.find()
                        count = cursor.count()
                        sample_indexes = random.sample(range(count), min(count, 100))
                        t0 = time()
                        samples = [cursor[i] for i in sample_indexes if time() - t0 < 5]
                        sa = DocStructureAnalyzer()
                        sa.analyze_docs(samples)
                        pr('{t.blue}document structure{t.normal} {t.black}({n} samples){t.normal}:', n=len(samples))
                        with pr.indent():
                            sa.print_structure(prefix=pr.iprefix)

    pr.nl()


class DocStructureAnalyzer:

    def __init__(self):
        self.root = _DSANode()

    def analyze_docs(self, docs):
        for doc in docs:
            self.analyze_doc(doc)

    def analyze_doc(self, doc):
        self.root.process(doc)

    def print_structure(self, prefix=''):
        self.root.print_(prefix)


class _DSANode:
    '''
    Helper class for DocStructureAnalyzer
    '''

    def __init__(self):
        self.items = defaultdict(lambda: defaultdict(dict))
        self.count = 0

    def process(self, d):
        from bson import ObjectId
        from datetime import datetime
        assert isinstance(d, dict)
        self.count += 1
        for k, v in d.items():
            assert isinstance(k, str)
            desc = self.items[k]
            if v is None:
                desc['null']['count'] = desc['null'].get('count', 0) + 1
            elif v is True:
                desc['true']['count'] = desc['true'].get('count', 0) + 1
            elif v is False:
                desc['false']['count'] = desc['false'].get('count', 0) + 1
            elif isinstance(v, str):
                desc['str']['count'] = desc['str'].get('count', 0) + 1
                desc['str']['sample_content'] = v
            elif isinstance(v, bytes):
                desc['bytes']['count'] = desc['bytes'].get('count', 0) + 1
                desc['bytes']['sample_content'] = v
            elif isinstance(v, dict):
                desc['dict']['count'] = desc['dict'].get('count', 0) + 1
                if not desc['dict'].get('node'):
                    desc['dict']['node'] = _DSANode()
                desc['dict']['node'].process(v)
            elif isinstance(v, list):
                desc['list']['count'] = desc['list'].get('count', 0) + 1
                if not desc['list'].get('node'):
                    desc['list']['node'] = _DSANode()
                for vi in v:
                    desc['list']['node'].process({'[]': vi})
            elif isinstance(v, int):
                desc['int']['count'] = desc['int'].get('count', 0) + 1
                desc['int']['sample_content'] = v
            elif isinstance(v, float):
                desc['float']['count'] = desc['float'].get('count', 0) + 1
                desc['float']['sample_content'] = v
            elif isinstance(v, datetime):
                desc['datetime']['count'] = desc['datetime'].get('count', 0) + 1
                desc['datetime']['sample_content'] = v
            elif isinstance(v, ObjectId):
                desc['ObjectId']['count'] = desc['ObjectId'].get('count', 0) + 1
                desc['ObjectId']['sample_content'] = v
            elif isinstance(v, UUID):
                desc['UUID']['count'] = desc['UUID'].get('count', 0) + 1
                desc['UUID']['sample_content'] = v
            else:
                raise Exception('Unknown type {}'.format(type(v)))

    def print_(self, prefix):
        for key, x in sorted(self.items.items()):
            for type_name, metadata in x.items():
                line = prefix
                line += '{t.green}{k}{t.normal}: {t.black}{t.bold}{tn}{t.normal}'.format(k=key, tn=type_name, t=t)
                line += ' {t.black}({pct:.0f} %){t.normal}'.format(t=t, pct=100*metadata['count']/self.count)
                if 'sample_content' in metadata:
                    sc = metadata['sample_content']
                    if isinstance(sc, datetime):
                        sc = str(sc)
                    else:
                        sc = repr(sc)
                    if len(sc) > 100:
                        sc = sc[:80] + '…'
                    line += ' {sc}'.format(sc=sc)
                print(line)
                if type_name == 'dict':
                    metadata['node'].print_(prefix + '    ')
                if type_name == 'list':
                    metadata['node'].print_(prefix + '    ')


def to_kbs(n):
    if n is None:
        return '-'
    assert isinstance(n, int)
    return '{:.2f} kB'.format(n/1024.)


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




