#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo apt-get install -y git cmake

	if [ ! -d OONF ]; then
		git clone https://github.com/AdvancedNetworkingSystems/OONF.git
		cd OONF
		#git checkout netjsoninfo-fix-disable-mpr-plugin
		git checkout v0.14.1
		mkdir -p build
		cd build
		cmake ..
		make -j 4
		cd ../..
	fi

	if [ -L /usr/sbin/olsrd2_static ]; then
		sudo rm /usr/sbin/olsrd2_static
		sudo rm /usr/sbin/olsrd2_dynamic
	fi
	sudo ln -s $PWD/OONF/build/olsrd2_static /usr/sbin/olsrd2_static
	sudo ln -s $PWD/OONF/build/olsrd2_dynamic /usr/sbin/olsrd2_dynamic

	# In order to use the remotecontrol plugin (required for the config
	# command) the olsrd2 service must call olsrd2_dynamic
	cat OONF/src/olsrd2/debian/olsrd2.init | sed \
		-e 's/^DAEMON=.*$/DAEMON=\/usr\/bin\/olsrd2_dynamic/' > \
		/tmp/olsrd2.init
	sudo mv /tmp/olsrd2.init /etc/init.d/olsrd2

	cat OONF/src/olsrd2/debian/olsrd2.service | sed \
		-e 's/\(^.*\)olsrd2_static\(.*$\)/\1olsrd2_dynamic\2/' > \
		/tmp/olsrd2.service
	sudo mv /tmp/olsrd2.service /etc/systemd/system/

	# sudo cp OONF/src/olsrd2/debian/olsrd2.init /etc/init.d/olsrd2
	# sudo cp OONF/src/olsrd2/debian/olsrd2.service /etc/systemd/system/

	sudo mkdir -p /etc/olsrd2/
	sudo cp olsrd2.conf /etc/olsrd2/
	sudo /bin/systemctl daemon-reload

	if [ ! -d olsrd ]; then
		# required to build all plugins
		sudo apt-get install -y libgps-dev
		git clone https://github.com/AdvancedNetworkingSystems/olsrd.git
		cd olsrd
		# git checkout poprow
		# git checkout poprow_validity
		git checkout d7bcd7d795e7073b2250ecbc30ea780fa8104fed
		make -j 4 build_all
		sudo cp lib/*/*.so.* /usr/local/lib
		cd ..
	fi

	if [ -L /usr/sbin/olsrd ]; then
		sudo rm /usr/sbin/olsrd
	fi
	sudo ln -s $PWD/olsrd/olsrd /usr/sbin/olsrd

	sudo cp olsrd.service /etc/systemd/system
	sudo mkdir -p /etc/olsrd/
	sudo cp olsrd.conf /etc/olsrd/
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
