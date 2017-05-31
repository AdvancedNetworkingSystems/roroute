#!/usr/bin/env bash

sudo apt-get install -y git cmake

if [ ! -d OONF ]; then
	git clone https://github.com/OLSR/OONF.git
	cd OONF
	mkdir -p build
	cd build
	cmake ..
	make
	sudo ln -s $PWD/olsrd2_static /usr/sbin/olsrd2_static
fi
