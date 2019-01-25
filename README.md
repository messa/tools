
Useful tools
============

There are some utilities I use.


Installation
------------

There is no `setup.py`. I personally checkout this repository in `~/code/tools`.
You have more options how to run these tools easily from command line:

  - Add the directory to `$PATH`
  - Symlink some or all files to `/usr/local/bin`
  - Use [alias](http://www.gnu.org/software/bash/manual/html_node/Aliases.html)
    or shell function

For example - adding to `$PATH` in `~/.bashrc`:

    if [ -d ~/code/tools ]; then
        PATH=$PATH:~/code/tools
        export PATH
    fi

Versioning
----------

I've created branch _v01_ where should be introduced no backward-incompatible
changes. Sometimes I include these tools in a project so it is better to include
a specific version branch than _master_.


Similar repos
-------------

- [github.com/encukou/bin](https://github.com/encukou/bin)
