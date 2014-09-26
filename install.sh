#!/usr/bin/sh

install -D -m755 zimsearch.py ${DESTDIR}/usr/bin/
install -D -m644 br.com.dsboger.zimsearch.provider.service ${DESTDIR}/usr/share/dbus-1/services/
install -D -m644 br.com.dsboger.zimsearch-search-provider.ini ${DESTDIR}/usr/share/gnome-shell/search-providers/
desktop-file-install --dir=${DESTDIR}/usr/share/applications -m 644 br.com.dsboger.zimsearch.desktop
