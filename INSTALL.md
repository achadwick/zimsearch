# Installation Guide

## Dependencies

You need to install the `dbus` Python 2 module from your OS
distribution, and the standard Python package manager `pip`. You need
[Zim][] too.

### Debian and derivatives

    apt install python-dbus
    apt install python-pip
    apt install zim

### Red Hat and derivatives

    yum install dbus-python
    yum install python-pip
    yum install Zim

## Fetch and install Zimsearch

To fetch and install zimsearch, try:

    cd path/to/src
    git clone https://github.com/achadwick/zimsearch.git
    cd zimsearch
    pip install --system .

You may need to use `sudo`, but it's at your own risk.

All the usual pip and setup.py options are supported, but installations in your personal home folder with `--user` won't work. That's because `gnome-shell`
does not look in user homes for its search providers.

You'll need to log out and back in again after installing.

## Updating Zimsearch

    cd path/to/src/zimsearch
    git pull
    pip install --system --upgrade .

## Uninstalling Zimsearch

    pip uninstall zimsearch

[Zim]: http://zim-wiki.org/
