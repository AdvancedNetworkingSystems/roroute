#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo service olsrd2 stop
	sudo service olsrd stop
else
	/etc/init.d/olsrd2 stop
	/etc/init.d/olsrd stop
fi
