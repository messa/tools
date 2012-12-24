#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# TODO bugy: tmp vedle, "pre" prvni radek mimo

import codecs
from contextlib import contextmanager
import logging
import markdown
import optparse
import os
from os.path import abspath, dirname, isdir, isfile
from os.path import join as path_join
from shutil import rmtree
import tempfile
import time
import webbrowser


logger = logging.getLogger("markdown_live_preview")


# CSS stolen from Sublime Markdown preview plugin
# https://github.com/revolunet/sublimetext-markdown-preview

html_start = u"""
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <style type="text/css">
            html {
                font-size: 100%;
                overflow-y: scroll;
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }
            body {
                color:#444;
                font-family:Georgia, Palatino, 'Palatino Linotype', Times,
                    'Times New Roman', serif,
                    "Hiragino Sans GB", "STXihei", "微软雅黑";
                font-size:12px;
                line-height:1.5em;
                background:#fefefe;
                width: 45em;
                margin: 10px auto;
                padding: 1em;
                outline: 1300px solid #FAFAFA;
            }
            a {
                color: #0645ad;
                text-decoration:none;
            }
            a:visited {
                color: #0b0080;
            }
            a:hover{
                color: #06e;
            }
            a:active {
                color:#faa700;
            }
            a:focus {
                outline: thin dotted;
            }
            a:hover, a:active {
                outline: 0;
            }
            span.backtick {
                border:1px solid #EAEAEA;
                border-radius:3px;
                background:#F8F8F8;
                padding:0 3px 0 3px;
            }
            ::-moz-selection {
                background:rgba(255,255,0,0.3);
                color:#000
            }
            ::selection {
                background:rgba(255,255,0,0.3);
                color:#000
            }
            a::-moz-selection {
                background:rgba(255,255,0,0.3);
                color:#0645ad
            }
            a::selection {
                background:rgba(255,255,0,0.3);
                color:#0645ad
            }
            p {
                margin:1em 0;
            }
            img {
                max-width:100%;
            }
            h1,h2,h3,h4,h5,h6 {
                font-weight:normal;
                color:#111;
                line-height:1em;
            }
            h4,h5,h6{ font-weight: bold; }
            h1{ font-size:2.5em; }
            h2{ font-size:2.0em; border-bottom:1px solid silver; padding-bottom: 5px; }
            h3{ font-size:1.7em; }
            h4{ font-size:1.1em; }
            h5{ font-size:1em; }
            h6{ font-size:0.9em; }

            blockquote{
            color:#666666;
            margin:0;
            padding-left: 3em;
            border-left: 0.5em #EEE solid;
            }
            hr { display: block; height: 2px; border: 0; border-top: 1px solid #aaa;border-bottom: 1px solid #eee; margin: 1em 0; padding: 0; }


            pre , code, kbd, samp {
              color: #000;
              font-family: monospace;
              font-size: 0.88em;
              border-radius:3px;
              background-color: #F8F8F8;
              border: 1px solid #CCC;
            }
            pre { white-space: pre; white-space: pre-wrap; word-wrap: break-word; padding: 5px;}
            pre code { border: 0px !important; }
            code { padding: 0 3px 0 3px; }

            b, strong { font-weight: bold; }

            dfn { font-style: italic; }

            ins { background: #ff9; color: #000; text-decoration: none; }

            mark { background: #ff0; color: #000; font-style: italic; font-weight: bold; }

            sub, sup { font-size: 75%; line-height: 0; position: relative; vertical-align: baseline; }
            sup { top: -0.5em; }
            sub { bottom: -0.25em; }

            ul, ol { margin: 1em 0; padding: 0 0 0 2em; }
            li p:last-child { margin:0 }
            dd { margin: 0 0 0 2em; }

            img { border: 0; -ms-interpolation-mode: bicubic; vertical-align: middle; }

            table { border-collapse: collapse; border-spacing: 0; }
            td { vertical-align: top; }

            @media only screen and (min-width: 480px) {
            body{font-size:14px;}
            }

            @media only screen and (min-width: 768px) {
            body{font-size:16px;}
            }

            @media print {
              * { background: transparent !important; color: black !important; filter:none !important; -ms-filter: none !important; }
              body{font-size:12pt; max-width:100%;}
              a, a:visited { text-decoration: underline; }
              hr { height: 1px; border:0; border-bottom:1px solid black; }
              a[href]:after { content: " (" attr(href) ")"; }
              abbr[title]:after { content: " (" attr(title) ")"; }
              .ir a:after, a[href^="javascript:"]:after, a[href^="#"]:after { content: ""; }
              pre, blockquote { border: 1px solid #999; padding-right: 1em; page-break-inside: avoid; }
              tr, img { page-break-inside: avoid; }
              img { max-width: 100% !important; }
              @page :left { margin: 15mm 20mm 15mm 10mm; }
              @page :right { margin: 15mm 10mm 15mm 20mm; }
              p, h2, h3 { orphans: 3; widows: 3; }
              h2, h3 { page-break-after: avoid; }
            }
        </style>
    </head>
    <body>
"""


html_end = u"""
    </body>
</html>
"""


@contextmanager
def create_temp_dir():
    path = tempfile.mkdtemp()
    try:
        logger.debug("Created temp dir %s", path)
        yield path
    finally:
        logger.debug("Removing temp dir %s", path)
        rmtree(path)


def get_file_stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime)


class LivePreview (object):

    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.md = markdown.Markdown()

    def run(self, docs):
        stamps = dict()
        for doc in docs:
            assert isfile(doc), doc
            self.generate(doc)
            stamps[doc] = get_file_stamp(doc)
        while True:
            time.sleep(0.05)
            for doc in docs:
                stamp = get_file_stamp(doc)
                if stamp != stamps[doc]:
                    self.generate(doc)
                    stamps[doc] = stamp


    def generate(self, path):
        output_path = path_join(self.target_dir, path + ".html")

        if not isdir(dirname(output_path)):
            logger.debug("Creating directory %s", dirname(output_path))
            os.makedirs(dirname(output_path))

        with codecs.open(path, encoding="UTF-8") as input_file:
            source = input_file.read()

        html = self.md.convert(source)
        html = self.postprocess_html(html)

        with codecs.open(output_path, "w", encoding="UTF-8") as output_file:
            output_file.write(html)

        logger.info("Processed %s => %s", path, output_path)

        self.open_browser(output_path)


    def postprocess_html(self, html):
        return html_start + html + html_end


    def open_browser(self, path):
        logger.debug("Opening browser for %s", path)
        assert isfile(path)
        webbrowser.open("file://" + abspath(path))


def main():
    logging.getLogger("").addHandler(logging.StreamHandler())
    logging.getLogger("").setLevel(logging.DEBUG)

    op = optparse.OptionParser()
    options, args = op.parse_args()

    with create_temp_dir() as temp_dir:
        live_preview = LivePreview(target_dir=temp_dir)
        live_preview.run(args)


if __name__ == "__main__":
    main()

