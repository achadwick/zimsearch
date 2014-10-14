#!/usr/bin/sh

# plugin file
install -D -m644 gnomeshellsearch.py "${DESTDIR}/usr/lib/python2.7/site-packages/zim/plugins/"

# DBUS service descriptor
install -D -m644 zim.plugins.gnomeshellsearch.provider.service "${DESTDIR}/usr/share/dbus-1/services/"

# GNOME Shell search provider descriptor
install -D -m644 zim.plugins.gnomeshellsearch.provider.ini "${DESTDIR}/usr/share/gnome-shell/search-providers/"

