#!/usr/bin/sh

# python script that starts DBUS service
install -D -m755 zimsearch.py "${DESTDIR}/usr/bin/"

# DBUS service descriptor
install -D -m644 br.com.dsboger.zimsearch.provider.service "${DESTDIR}/usr/share/dbus-1/services/"

# GNOME Shell search provider descriptor
install -D -m644 br.com.dsboger.zimsearch-search-provider.ini "${DESTDIR}/usr/share/gnome-shell/search-providers/"

# ZimSearch desktop file. NoDisplay and DBusActivatable
desktop-file-install --dir="${DESTDIR}/usr/share/applications" -m 644 br.com.dsboger.zimsearch.desktop

