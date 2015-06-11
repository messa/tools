There are some utilities I use.

# Overview


## instant_apache

Create configuration and run Apache webserver with document root in current
or given directory.


## mongo_overview

Gives overview what databases and collections are contained in your MongoDB.
With argument `-s` it also analyzes and prints document structure.


## mongo\_export\_all

Pretty-print all contents in a MongoDB. For development/debug purposes.


## trim

Trim excessive whitespace from line ends in text files.


## xwatch

Run one command repeatedly, separate outputs with blank lines.

This is an alternative to the `watch` command, but the fullscreen-like
behavior is done with blank lines, so the output can be easily scrolled.


# Installation

There is no `setup.py`. I personally checkout this repository in `~/code/tools`.
You have more options how to run these tools easily from command line:

  - Add the directory to `$PATH`
  - Symlink some or all files to `/usr/local/bin`
  - Use [alias](http://www.gnu.org/software/bash/manual/html_node/Aliases.html)
    or shell function

