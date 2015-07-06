#!/usr/bin/env python3

import argparse
import requests
import threading


ip_url   = 'https://ip.messa.cz/'
ipv4_url = 'https://ip4.messa.cz/'
ipv6_url = 'https://ip6.messa.cz/'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-1', dest='one', action='store_true', help='print only one IP adress')
    p.add_argument('-4', dest='v4', action='store_true', help='show only IPv4 address')
    p.add_argument('-6', dest='v6', action='store_true', help='show only IPV6 address')
    args = p.parse_args()
    if args.one:
        get(ip_url)
    if args.v4:
        get(ipv4_url)
    if args.v6:
        get(ipv6_url)
    if not any((args.one, args.v4, args.v6)):
        t4 = threading.Thread(target=lambda: get(ipv4_url, 'IPv4'))
        t6 = threading.Thread(target=lambda: get(ipv6_url, 'IPv6'))
        t4.start()
        t6.start()
        t6.join()
        t4.join()


def get(url, prefix=None):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        if prefix:
            print('{}: {}'.format(prefix, r.text.strip()))
        else:
            print(r.text.strip())
    except Exception as e:
        if prefix:
            print('{} failed: {!r}'.format(prefix, e))
        else:
            print('Failed: {!r}'.format(e))


def server_app(env, start_response):
    '''
    How to run this (example):

        $ gunicorn myip:server_app
    '''
    start_response('200 OK', [('Content-Type','text/plain')])
    return ['{}\n'.format(env['REMOTE_ADDR']).encode('ascii')]


if __name__ == '__main__':
    main()

