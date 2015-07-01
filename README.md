
Useful tools
============

There are some utilities I use.

Overview
--------


### instant_apache

Create configuration and run Apache webserver with document root in current
or given directory.


### instant_mongodb

Run MongoDB server instance.


### mongo_overview

Gives overview what databases and collections are contained in your MongoDB.
With argument `-s` it also analyzes and prints document structure.


### mongo_print

Dump all documents from MongoDB.


### pararun

Run commands in parallel.

    $ ./pararun.py echo foo :: echo bar
    [echo] foo
    [echo] bar


### trim

Trim excessive whitespace from line ends in text files.


### xwatch

Run one command repeatedly, separate outputs with blank lines.

This is an alternative to the `watch` command, but the fullscreen-like
behavior is done with blank lines, so the output can be easily scrolled.


Installation
------------

There is no `setup.py`. I personally checkout this repository in `~/code/tools`.
You have more options how to run these tools easily from command line:

  - Add the directory to `$PATH`
  - Symlink some or all files to `/usr/local/bin`
  - Use [alias](http://www.gnu.org/software/bash/manual/html_node/Aliases.html)
    or shell function

For example:

    cd ~/code
    git clone https://github.com/messa/tools.git
    cd /usr/local/bin
    sudo ln -s ~/code/tools/instant_apache.py   instant_apache
    sudo ln -s ~/code/tools/instant_mongodb.py  instant_mongodb
    sudo ln -s ~/code/tools/mongo_overview.py   mongoo_overview
    sudo ln -s ~/code/tools/mongo_print.py      mongo_print
    sudo ln -s ~/code/tools/pararun.py          pararun
    sudo ln -s ~/code/tools/trim.py             trim
    sudo ln -s ~/code/tools/xwatch.py           xwatch


Versioning
----------

I've created branch _v01_ where should be introduced no backward-incompatible
changes. Sometimes I include these tools in a project so it is better to include
a specific version branch than _master_.





