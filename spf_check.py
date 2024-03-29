#!/usr/bin/env python3

'''
Example:

    ./spf_check.py _spf.google.com
    Resolving TXT: _spf.google.com (1)
      Validating: v=spf1 include:_netblocks.google.com include:_netblocks2.google.com include:_netblocks3.google.com ~all
        Resolving TXT: _netblocks.google.com (2)
          Validating: v=spf1 ip4:64.18.0.0/20 ip4:64.233.160.0/19 ip4:66.102.0.0/20 ip4:66.249.80.0/20 ip4:72.14.192.0/18 ip4:74.125.0.0/16 ip4:108.177.8.0/21 ip4:173.194.0.0/16 ip4:207.126.144.0/20 ip4:209.85.128.0/17 ip4:216.58.192.0/19 ip4:216.239.32.0/19 ~all
        Resolving TXT: _netblocks2.google.com (3)
          Validating: v=spf1 ip6:2001:4860:4000::/36 ip6:2404:6800:4000::/36 ip6:2607:f8b0:4000::/36 ip6:2800:3f0:4000::/36 ip6:2a00:1450:4000::/36 ip6:2c0f:fb50:4000::/36 ~all
        Resolving TXT: _netblocks3.google.com (4)
          Validating: v=spf1 ip4:172.217.0.0/19 ip4:108.177.96.0/19 ~all

You see that Google's SPF record requires 4 DNS lookups.

You can validate also the contents of the SPF record:

    ./spf_check.py 'v=spf1 include:_netblocks.google.com ~all'
    Validating: v=spf1 include:_netblocks.google.com ~all
      Resolving TXT: _netblocks.google.com (1)
        Validating: v=spf1 ip4:64.18.0.0/20 ip4:64.233.160.0/19 ip4:66.102.0.0/20 ip4:66.249.80.0/20 ip4:72.14.192.0/18 ip4:74.125.0.0/16 ip4:108.177.8.0/21 ip4:173.194.0.0/16 ip4:207.126.144.0/20 ip4:209.85.128.0/17 ip4:216.58.192.0/19 ip4:216.239.32.0/19 ~all
'''

import argparse
from dns.resolver import Resolver # sudo apt-get install python3-dnspython
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('spf_record')
    args = p.parse_args()

    if ':' in args.spf_record or '=' in args.spf_record:
        ok = validate_spf_record(None, args.spf_record, [])
    else:
        ok = validate_domain_spf(args.spf_record, [], initial=True)
    sys.exit(0 if ok else 1)


def validate_spf_record(domain, spf_record, resolves, indent=''):
    print(indent + 'Validating: {!r} [{} bytes]'.format(spf_record, len(spf_record)))
    ok = True
    if len(spf_record) > 255:
        print(indent + '!!! SPF record is too long - {} characters'.format(len(spf_records)))
        ok = False
    parts = spf_record.split()
    if parts[0] != 'v=spf1':
        raise Exception('Does not begin with v=spf1')
    for part in parts[1:]:
        if part in ['-all', '~all', '?all']:
            continue
        elif part in ['mx', 'a']:
            resolves.append(domain)
            print(indent + 'Would be resolved: {} {} ({})'.format(part, domain, len(resolves)))
            if len(resolves) > 10:
                print(indent + '!!! Too many resolves')
                ok = False
        elif ':' in part:
            t, addr = part.split(':', 1)
            if t in ['ip4', 'ip6']:
                continue
            elif t == 'include':
                res = validate_domain_spf(addr, resolves, indent=indent + '  ')
                if not res:
                    ok = False
            elif t in ['a', 'mx']:
                resolves.append(addr)
                print(indent + 'Would be resolved: {} ({})'.format(part, len(resolves)))
                if len(resolves) > 10:
                    print(indent + '!!! Too many resolves')
                    ok = False
            else:
                raise Exception('Unknown part {!r} in {!r}'.format(part, spf_record))
        else:
            raise Exception('Unknown part {!r}'.format(part))
    return ok


def validate_domain_spf(domain, resolves, indent='', initial=False):
    ok = True
    r = Resolver()
    if not initial:
        resolves.append(domain)
    print(indent + 'Resolving TXT: {} ({})'.format(domain, len(resolves)))
    if len(resolves) > 10:
        print(indent + '!!! Too many resolves')
        ok = False
    try:
        answers = r.resolve(domain, 'TXT')
    except Exception as e:
        print(indent + '!!! Failed to resolve TXT {}: {}'.format(domain, e))
        return False
    answers = [str(item).strip('"') for item in answers]
    if not answers:
        print(indent + '!!! No TXT records for {}'.format(domain))
        return False
    spf_answers = [item for item in answers if item.startswith('v=spf')]
    if not spf_answers:
        print(indent + '!!! No TXT SPF record for {}'.format(domain))
        ok = False
        print(indent + '  Other TXT records:')
        for item in answers:
            print('  -', str(item))
    elif len(spf_answers) > 1:
        print(indent + '!!! Multiple SPF records for {}:'.format(domain))
        ok = False
        for item in spf_answers:
            print(indent + '  -', item)
        spf_record = spf_answers[0]
        validate_spf_record(domain, spf_record, resolves, indent=indent + '  ')
    else:
        spf_record, = spf_answers
        validate_spf_record(domain, spf_record, resolves, indent=indent + '  ')
    return ok


if __name__ == '__main__':
    main()
