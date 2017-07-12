#!/usr/bin/env sh

if [ $# -ge 1 ]; then
	testbed=$1
else
	testbed="twist"
fi

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo service olsrd2 stop
	sudo service olsrd2 start
	if [ "$testbed" = "wilab" ]; then
		sudo ip -6 route add fe80::ec4:7aff:fe6c:a69a dev eno1
		sudo ip -6 route add default via fe80::ec4:7aff:fe6c:a69a dev eno1
	fi
else
	/etc/init.d/olsrd2 stop
	/etc/init.d/olsrd2 start
fi
