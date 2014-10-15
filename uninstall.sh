#!/usr/bin/sh

rootdir="${1}"

rm "${rootdir}/usr/lib/python2.7/site-packages/zim/plugins/gnomeshellsearch.py"
rm "${rootdir}/usr/share/dbus-1/services/zim.plugins.gnomeshellsearch.provider.service"
rm "${rootdir}/usr/share/gnome-shell/search-providers/zim.plugins.gnomeshellsearch.provider.ini"
