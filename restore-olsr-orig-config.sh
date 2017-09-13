#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo cp olsrd2.conf /etc/olsrd2/
else
	echo "WARNING: original olsrd2 configuration restoring not implemented on OpenWRT"
	exit 1
fi
