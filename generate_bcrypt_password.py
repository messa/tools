#!/usr/bin/env python3

from argparse import ArgumentParser
from bcrypt import hashpw, gensalt
from secrets import token_urlsafe


def main():
    p = ArgumentParser()
    p.add_argument('--length', '-l', type=int, default=9, help='password length')
    p.add_argument('--rounds', '-r', type=int, default=12, help='adjust bcrypt work factor')
    args = p.parse_args()
    password = generate_password(args.length)
    print('Password:', password)
    h = hashpw(password.encode('ascii'), gensalt(args.rounds)).decode('ascii')
    print('Bcrypt hash:', h)


def generate_password(length):
    while True:
        p = token_urlsafe(length)[:length]
        if any(c in p for c in 'il1I0O-_=/+'):
            continue
        return p


if __name__ == '__main__':
    main()
