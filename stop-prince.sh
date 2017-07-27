#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	prince_pid=$(ps aux | grep /usr/bin/prince | grep -v grep | tr -s ' ' | cut -d ' ' -f 2)

	if [ ! -z "${prince_pid}" ]; then
		kill ${prince_pid}
	fi
else
	echo "WARNING: Prince stop mechanism for OpenWRT not implemented yet"
	exit 1
fi
