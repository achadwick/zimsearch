#!/usr/bin/sh

mkdir -p config
aclocal -I config \
&& automake --gnu --add-missing \
&& autoconf
