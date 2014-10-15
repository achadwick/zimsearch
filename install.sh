#!/usr/bin/sh

rootdir="$1"

# plugin file
install -D -m644 gnomeshellsearch.py "${rootdir}/usr/lib/python2.7/site-packages/zim/plugins/gnomeshellsearch.py"

# DBUS service descriptor
install -D -m644 zim.plugins.gnomeshellsearch.provider.service "${rootdir}/usr/share/dbus-1/services/zim.plugins.gnomeshellsearch.provider.service"

# GNOME Shell search provider descriptor
install -D -m644 zim.plugins.gnomeshellsearch.provider.ini "${rootdir}/usr/share/gnome-shell/search-providers/zim.plugins.gnomeshellsearch.provider.ini"

