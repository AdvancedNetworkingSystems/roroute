#!/usr/bin/env sh

prince_conf="prince_conf_c_h.json"
prince_log="/tmp/prince.log"

if [ $# -eq 1 ]; then
	prince_conf=$1
elif [ $# -eq 2 ]; then
	prince_conf=$1
	prince_log=$2
fi

sudo rm /tmp/prince.conf
cat $(pwd)/${prince_conf} | sed 's@^.*log_file.*$@"log_file":"'"${prince_log}"'"@' > /tmp/prince.conf
cp /tmp/prince.conf $(pwd)/${prince_conf}

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
