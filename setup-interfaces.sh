#!/usr/bin/env sh

if [ $# -eq 0 ]; then
	rate=54
	channel=1
	power=2000
elif [ $# -eq 3 ]; then
	rate=$1
	channel=$2
	power=$3
else
	echo "Invalid number of arguments. You either need to specify <rate> <channel> <power> (3 arguments) or no argument for the default values"
	exit 1
fi

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	host_name=`hostname | cut -d'.' -f 1`
else
	host_name=`uci get system.@system[0].hostname`
fi

ip_addr=`cat /etc/hosts | grep "pop-$host_name\$" | cut -d' ' -f 1`

$(which sudo) python poprow_setup_interface.py --intcap=HT --chan=$channel --legacyrate=$rate --inet=${ip_addr}/16 --ibssid=poprow --ibssiname=poprow0 --moniname=mon0 --bint=200 --txpower=$power
