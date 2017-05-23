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

./kill-pop-recv.sh
$(SUDO) rm experiment.csv

./pop-recv.py --daemon -f experiment.csv
