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
	sudo apt-get install -y python python-pip
	sudo pip install setuptools
	sudo service ntp start
	cd olsr_utilities
	make clean; make
	sudo rm -f /usr/bin/topology_dumper
	sudo rm -f /usr/bin/start_topology_dumper
	sudo rm -f /usr/bin/runat
	sudo ln -s $PWD/topology_dumper /usr/bin/topology_dumper
	sudo ln -s $PWD/start_topology_dumper /usr/bin/start_topology_dumper
	sudo ln -s $PWD/runat /usr/bin/runat
	cd ../
	${SUDO} pip install scipy
fi
${SUDO} pip install pyric pyroute2 ipaddr networkx

# patch a mistake in the official release of pyric
if [ $tplink -eq 1 ]; then
	sed -i -e "s/'sys/'\/sys/g" /usr/lib/python2.7/site-packages/pyric/utils/rfkill.py
fi

# install olsrd2
./setup-olsr.sh

# install Prince
./setup-prince.sh
