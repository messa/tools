#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import re
import requests
import sys
from time import time, sleep


logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v', action='store_true')
    sub = p.add_subparsers(dest='command')
    p_resize = sub.add_parser('resize', help='resize a droplet')
    p_resize.add_argument('--poweron', '--on', action='store_true', help='power on after resize finishes')
    p_resize.add_argument('droplet_id')
    p_resize.add_argument('new_size', nargs='?')
    p_poweron = sub.add_parser('poweron', help='power on a droplet')
    p_poweron.add_argument('droplet_id')
    args = p.parse_args()
    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)5s: %(message)s',
        level=logging.DEBUG if args.verbose else logging.INFO)
    token = get_digitalocean_access_token()
    transport = DOAPITransport(token)
    if not args.command:
        list_droplets(transport)
    elif args.command == 'resize':
        resize_droplet(transport, args.droplet_id, args.new_size)
        if args.poweron:
            power_on_droplet(transport, args.droplet_id)
    elif args.command == 'poweron':
        power_on_droplet(transport, args.droplet_id)
    else:
        raise Exception(f'Unknown command: {args.command!r}')


def get_digitalocean_access_token():
    if os.environ.get('DO_ACCESS_TOKEN'):
        logger.debug('Using access token from env variable DO_ACCESS_TOKEN')
        return os.environ['DO_ACCESS_TOKEN']
    try_paths = [
        '~/.config/digital_ocean_access_token',
    ]
    for p in try_paths:
        p = Path(p).expanduser()
        if p.is_file():
            token = p.read_text().strip()
            if re.match(r'^[a-zA-Z0-9]+$', token):
                return token
            else:
                logger.warning('Content of file %s does not look like token: %r', p, token[:1000])
    sys.exit('No access tpken found')


class DOAPITransport:

    def __init__(self, token):
        if not token:
            raise Exception('No token')
        self.rs = requests.session()
        self.rs.headers.update({
            'Authorization': f'Bearer {token}',
        })

    def get(self, path):
        url = 'https://api.digitalocean.com' + path
        r = self.rs.get(url)
        self._log_rate_limit(r.headers)
        r.raise_for_status()
        return r.json()

    def post(self, path, payload):
        url = 'https://api.digitalocean.com' + path
        logger.info('Sending %r to %s', payload, url)
        r = self.rs.post(url, json=payload)
        self._log_rate_limit(r.headers)
        try:
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"POST to {url} failed: {e}; response: {r.content[:5000]}")
        return r.json()

    def _log_rate_limit(self, headers):
        try:
            logger.debug(
                'Rate limit: %s/%s (reset in %d s)',
                headers['Ratelimit-Remaining'], headers['Ratelimit-Limit'],
                int(time()) - int(headers['Ratelimit-Reset']))
        except KeyError:
            # some of the rate-limit headers was not sent
            pass


def list_droplets(transport):
    reply = transport.get('/v2/droplets')
    if not reply['droplets']:
        assert reply['meta']['total'] == 0
        print('No dropelts')
        return
    print(f"{reply['meta']['total']} droplets:")
    print_droplet_table(reply['droplets'])


def print_droplet_table(droplets):
    table = []
    for droplet in droplets:
        image_name = f"{droplet['image']['distribution']} {droplet['image']['name']}"
        ip_addresses = [net['ip_address'] for net in droplet['networks']['v4']]
        ip_addresses += [net['ip_address'] for net in droplet['networks']['v6']]
        table.append({
            'region': droplet['region']['slug'],
            'id': droplet['id'],
            'created_at': droplet['created_at'],
            'name': droplet['name'],
            'status': droplet['status'],
            'size': droplet['size']['slug'],
            'price_monthly': '{:6.2f}'.format(droplet['size']['price_monthly']),
            #droplet['memory'] / 1024,
            'image': image_name,
            'IP addresses': ' '.join(ip_addresses),
        })
    print_table(table)


def print_table(table):
    column_names = []
    column_sizes = {}
    for row in table:
        for key, value in row.items():
            value = str(value)
            if key not in column_names:
                column_names.append(key)
            column_sizes[key] = max(len(value), column_sizes.get(key, len(key)))
    header = [name.ljust(column_sizes[name]) for name in column_names]
    print('  ' + '  '.join(header))
    for row in table:
        line = []
        for name in column_names:
            value = str(row.get(name, '-'))
            line.append(value.ljust(column_sizes[name]))
        print('  ' + '  '.join(line))


def resize_droplet(transport, droplet_id, new_size):
    reply = transport.get(f'/v2/droplets/{droplet_id}')
    droplet_before = reply['droplet']
    print('Droplet:')
    print_droplet_table([droplet_before])
    if not new_size:
        reply = transport.get('/v2/sizes?per_page=200')
        print('Available sizes:')
        table = []
        for size in reply['sizes']:
            table.append({
                'current': '>>>>>>>' if size['slug'] == droplet_before['size']['slug'] else '',
                'slug': size['slug'],
                'memory': '{:4} GB'.format(size['memory'] / 1024),
                'vcpus': '{:2}'.format(size['vcpus']),
                'disk': size['disk'],
                'price_monthly': '{:6.2f}'.format(size['price_monthly']),
                'available': size['available'],
                'regions': ','.join(size['regions']),
            })
        print_table(table)
        sys.exit('Please provide new size slug.')
    if new_size == droplet_before['size']['slug']:
        print(f'Droplet size already is {new_size}')
        return
    payload = {
        'type': 'resize',
        'disk': False,
        'size': new_size,
    }
    reply = transport.post(f'/v2/droplets/{droplet_id}/actions', payload)
    action_id = reply['action']['id']
    print(f'Action id: {action_id}')
    while True:
        action_status = reply['action']['status']
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{now} Action status: {action_status}')
        if action_status != 'in-progress':
            break
        sleep(3)
        reply = transport.get(f'/v2/droplets/{droplet_id}/actions/{action_id}')


def power_on_droplet(transport, droplet_id):
    reply = transport.get(f'/v2/droplets/{droplet_id}')
    droplet_before = reply['droplet']
    print('Droplet:')
    print_droplet_table([droplet_before])
    if droplet_before['status'] == 'active':
        print(f'Droplet status is already {droplet_before["status"]}')
        return
    payload = {
        'type': 'power_on',
    }
    reply = transport.post(f'/v2/droplets/{droplet_id}/actions', payload)
    action_id = reply['action']['id']
    print(f'Action id: {action_id}')
    while True:
        action_status = reply['action']['status']
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{now} Action status: {action_status}')
        if action_status != 'in-progress':
            break
        sleep(3)
        reply = transport.get(f'/v2/droplets/{droplet_id}/actions/{action_id}')


if __name__ == '__main__':
    main()
