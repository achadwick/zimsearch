# Installation Guide

## Dependencies

You need to install the `dbus` Python 2 module from your OS
distribution, and the standard Python package manager `pip`.

You need [Zim][] too.
This plugin is written for Zim 0.67 and later.

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
    sudo pip install .   # normally uses /usr/local/share

If you normally have write access to `/usr/local` with an
otherwise unprivileged install account, you don't have to use
`sudo`. But please use `--system` where it's supported if
you are doing this.

All the usual pip and setup.py options are supported, but
installations in your personal home folder's `.local` won't
work. That's because `gnome-shell` does not look in user
homes for its search providers.

You may need to run this after install for zim to see it though.

cp /usr/local/share/zim/plugins/gnomeshellsearch.py ~/.local/share/zim/plugins

You'll need to log out and back in again after installing.

## Updating Zimsearch

    cd path/to/src/zimsearch
    git pull
    sudo pip install --upgrade .

## Uninstalling Zimsearch

    pip uninstall zimsearch

[Zim]: http://zim-wiki.org/
