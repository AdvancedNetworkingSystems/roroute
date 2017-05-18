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

if [ $tplink -eq 1 ]; then
	opkg install python python-pip
else
	sudo apt-get install python python-pip
	sudo pip install setuptools
fi
${SUDO} pip install pyric pyroute2 ipaddr

# patch a mistake in the official release of pyric
if [ $tplink -eq 1 ]; then
	sed -i -e "s/'sys/'\/sys/g" /usr/lib/python2.7/site-packages/pyric/utils/rfkill.py
fi
