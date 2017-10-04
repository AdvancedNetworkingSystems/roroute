#!/usr/bin/env sh

prince_conf="prince_conf_c_h.json"
prince_log="/tmp/prince.log"

hello_mult=$1
tc_mult=$2
if [ $# -eq 3 ]; then
	prince_conf=$3
elif [ $# -eq 4 ]; then
	prince_conf=$3
	prince_log=$4
fi

# set validity multipliers before starting prince
echo "/HelloTimerMult=${hello_mult}" | nc localhost 1234
echo "/TcTimerMult=${tc_mult}" | nc localhost 1234

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
