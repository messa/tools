# -*- coding: utf-8 -*-

import nose

import instant_apache


def test_smoke():
    pass


def test_run():
    port = 9999
    ia = instant_apache.InstantApache(port=port)
    ia.start()


if __name__ == "__main__":
    config = nose.config.Config()
    config.verbosity += 1
    nose.runmodule(config=config)

