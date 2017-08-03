#!/usr/bin/env python3

import argparse
import dns.resolver # apt-get install python3-dnspython

def main():
    p = argparse.ArgumentParser()
    p.add_argument('spf_record')
    args = p.parse_args()

    resolves = []
    validate_spf_record(args.spf_record, resolves)


def validate_spf_record(spf_record, resolves, indent=''):
    print(indent + 'Validating: {}'.format(spf_record))
    parts = spf_record.split()
    if parts[0] != 'v=spf1':
        raise Exception('Does not begin with v=spf1')
    for part in parts[1:]:
        if part in ['-all', '~all']:
            continue
        if ':' in part:
            t, addr = part.split(':', 1)
            if t in ['ip4', 'ip6']:
                continue
            elif t == 'include':
                validate_domain_spf(addr, resolves, indent=indent + '  ')
            elif t in ['a', 'mx']:
                resolves.append(addr)
                print(indent + 'Would be resolved: {} ({})'.format(part, len(resolves)))
                if len(resolves) > 10:
                    print(indent + '!!! Too many resolves')
            else:
                raise Exception('Unknown part {!r} in {!r}'.format(part, spf_record))
        else:
            raise Exception('Unknown part {!r}'.format(part))


def validate_domain_spf(addr, resolves, indent=''):
    r = dns.resolver.Resolver()
    resolves.append(addr)
    print(indent + 'Resolving TXT: {} ({})'.format(addr, len(resolves)))
    if len(resolves) > 10:
        print(indent + '!!! Too many resolves')
    answers = r.query(addr, 'TXT')
    answers = [str(item).strip('"') for item in answers]
    if not answers:
        print(indent + '!!! No TXT records for {}'.format(addr))
        return
    spf_answers = [item for item in answers if item.startswith('v=spf')]
    if not spf_answers:
        print(indent + '!!! No TXT SPF record for {}'.format(addr))
        print(indent + '  Other TXT records:')
        for item in answers:
            print('  -', str(item))
    elif len(spf_answers) > 1:
        print(indent + '!!! Multiple SPF records for {}:'.format(addr))
        for item in spf_answers:
            print(indent + '  -', item)
        spf_record = spf_answers[0]
        validate_spf_record(spf_record, resolves, indent=indent + '  ')
    else:
        spf_record, = spf_answers
        validate_spf_record(spf_record, resolves, indent=indent + '  ')



if __name__ == '__main__':
    main()
