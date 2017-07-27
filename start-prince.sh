#!/usr/bin/env sh

if [ $# -ge 1 ]; then
	prince_conf=$1
else
	prince_conf="prince_conf_c_h.json"
fi

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	prince_pid=$(ps aux | grep /usr/bin/prince | grep -v grep | tr -s ' ' | cut -d ' ' -f 2)

	# Kill prince if it's already running
	if [ ! -z "${prince_pid}" ]; then
		kill ${prince_pid}
	fi

	echo "/usr/bin/prince $(pwd)/${prince_conf}" | at now
else
	echo "WARNING: Prince start mechanism for OpenWRT not implemented yet"
	exit 1
fi
