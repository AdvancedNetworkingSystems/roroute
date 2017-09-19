#!/usr/bin/env sh

if [ $# -ge 1 ]; then
	testbed=$1
else
	testbed="twist"
fi

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo service olsrd stop
	sudo service olsrd start
	if [ "$testbed" = "wilab" ]; then
		def=`ip -6 r | grep 'default via fe80::ec4:7aff:fe6c:a69a'`
		if [ "$def" = "" ]; then
			sudo ip -6 route add fe80::ec4:7aff:fe6c:a69a dev eno1
			sudo ip -6 route add default via fe80::ec4:7aff:fe6c:a69a dev eno1
		fi
	fi
else
	/etc/init.d/olsrd stop
	/etc/init.d/olsrd start
fi
