#!/usr/bin/env sh

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo apt-get install -y git make libjson-c-dev

	if [ ! -d poprouting ]; then
		git clone https://github.com/AdvancedNetworkingSystems/poprouting.git
	else
		cd poprouting
		make clean
		git pull
		cd ..
	fi

	cd poprouting
	# Fix LDFLAGS in Makefile (this was tested for commit 1b1fa863c4bb88d3)
	cat Makefile | sed \
		-e 's/\(^.*\)\$(LDFLAGS) \$(CFLAGS)\(.*$\)/\1 \$(CFLAGS) \2 \$(LDFLAGS)/' \
		-e 's/^CFLAGS\(.*$\)/LDFLAGS\1/' > Makefile.tmp && \
		mv Makefile.tmp Makefile

	# We use IPv4 not IPv6
	cat prince/src/oonf.c | sed -e 's/\(^.*\)ipv6_0\(.*$\)/\1ipv4_0\2/' > \
		/tmp/oonf.c && mv /tmp/oonf.c prince/src/oonf.c

	make

	if [ -L /usr/lib/libprince_oonf_c.so ]; then
		sudo rm /usr/lib/libprince_oonf_c.so
	fi

	if [ -L /usr/bin/prince ]; then
		sudo rm /usr/bin/prince
	fi

	sudo ln -s $PWD/output/libprince_oonf_c.so /usr/lib/libprince_oonf_c.so
	sudo ln -s $PWD/output/prince /usr/bin/prince

	cd ..

	# Prince template configurations for heuristic based and without
	# heuristic respectively are in poprow-scripts/prince_conf_c_h.json and
	# poprow-scripts/prince_conf_c.json
else
	echo "WARNING: Prince installation on OpenWRT not implemented yet"
	exit 1
fi