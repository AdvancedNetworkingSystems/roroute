#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo apt-get install -y git make libjson-c-dev

	if [ ! -d poprouting ]; then
		git clone https://github.com/AdvancedNetworkingSystems/poprouting.git
		cd poprouting
		git checkout poprow
		make -j 4
		cd ..
	fi

	cd poprouting

	if [ -L /usr/lib/libprince_oonf_c.so ]; then
		sudo rm /usr/lib/libprince_oonf_c.so
		sudo rm /usr/lib/libprince_test.so
		sudo rm /usr/lib/libprince_olsr.so
	fi

	if [ -L /usr/bin/prince ]; then
		sudo rm /usr/bin/prince
	fi

	sudo ln -s $PWD/output/libprince_oonf_c.so /usr/lib/libprince_oonf_c.so
	sudo ln -s $PWD/output/libprince_olsr.so /usr/lib/libprince_olsr.so
	sudo ln -s $PWD/output/libprince_test.so /usr/lib/libprince_test.so
	sudo ln -s $PWD/output/prince /usr/bin/prince

	cd ..

	# Prince template configurations for heuristic based and without
	# heuristic respectively are in poprow-scripts/prince_conf_c_h.json and
	# poprow-scripts/prince_conf_c.json
else
	echo "WARNING: Prince installation on OpenWRT not implemented yet"
	exit 1
fi
