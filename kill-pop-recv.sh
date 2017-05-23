#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	tplink=0
	SUDO=sudo
else
	tplink=1
	SUDO=""
fi

pid=`ps -ax | grep 'pop-recv.py' | grep -v grep | sed -e "s/^  *//g" | cut -d' ' -f 1`
if [ ! -z "$pid" ]; then
	$(SUDO) kill $pid
fi
