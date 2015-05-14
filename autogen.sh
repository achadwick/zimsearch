#!/usr/bin/sh

aclocal -I config \
&& automake --gnu --add-missing \
&& autoconf
