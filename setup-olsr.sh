#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo apt-get install -y git cmake

	if [ ! -d OONF ]; then
		git clone https://github.com/OLSR/OONF.git
		cd OONF
		git checkout 88b68eef207bc76e448bf4237da09180514f7a2d
		mkdir -p build
		cd build
		cmake ..
		make
		sudo ln -s $PWD/olsrd2_static /usr/sbin/olsrd2_static
		sudo ln -s $PWD/olsrd2_dynamic /usr/sbin/olsrd2_dynamic
		sudo ln -s $PWD/olsrd2 /usr/sbin/olsrd2_dynamic
		cd ../..
	fi

	# In order to use the remotecontrol plugin (required for the config
	# command) the olsrd2 service must call olsrd2_dynamic
	cat OONF/src/olsrd2/debian/olsrd2.init | sed \
		-e 's/^DAEMON=.*$/DAEMON=\/usr\/bin\/olsrd2_dynamic/' > \
		/tmp/olsrd2.init
	sudo cp /tmp/olsrd2.init /etc/init.d/olsrd2

	cat OONF/src/olsrd2/debian/olsrd2.service | sed \
		-e 's/\(^.*\)olsrd2_static\(.*$\)/\1olsrd2_dynamic\2/' > \
		/tmp/olsrd2.service
	sudo cp /tmp/olsrd2.service /etc/systemd/system/
	sudo mkdir -p /etc/olsrd2/
	sudo cp olsrd2.conf /etc/olsrd2/
	sudo /bin/systemctl daemon-reload
else
	olsrd2_path=`which olsrd2`
	if [ "$olsrd2_path" == "" ]; then
		opkg install oonf-init-scripts_2016-05-31_ar71xx.ipk
		opkg install oonf-olsrd2-git_2016-05-31_ar71xx.ipk
		ln -s /usr/sbin/olsrd2 /usr/sbin/olsrd2_dynamic
	fi
	sed -i -e "s/--load.*$/--load \/root\/olsrd2.conf/g" /lib/functions/oonf_init.sh
fi
