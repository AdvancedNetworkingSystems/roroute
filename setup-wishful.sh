#!/usr/bin/env bash

# determine whether we are on a NUC or on a TPLINK
opkg_path=`which opkg`
if [ "$opkg_path" == "" ]; then
	tplink=0
else
	tplink=1
fi

sudo apt-get install -y wget git python python-virtualenv python-dev python3-dev python3-pip rfkill
sudo pip install setuptools
sudo pip install pyric pyroute2 ipaddr

git config --global user.name "ANS"
git config --global user.email "ans@ans.disi.unitn.it"
git config --global color.diff auto
git config --global color.status auto
export PATH=$PATH:$HOME/

if [ -d wishful ]; then
	cd wishful
	repo forall -c 'git pull --rebase'
	. ./dev/bin/activate
	pip3 install -U -r ./.repo/manifests/requirements.txt
	pip3 install pyric pyroute2 ipaddr netdiff scipy
	pip3 install networkx==1.11
	cd ..
else
	wget https://storage.googleapis.com/git-repo-downloads/repo
	chmod a+x ./repo
	mkdir -p wishful
	cd wishful
	repo init -u https://github.com/AdvancedNetworkingSystems/manifests-wishful
	repo init -m user.xml
	repo sync
	repo forall -c 'git checkout master'
	virtualenv -p /usr/bin/python3 ./dev
	. ./dev/bin/activate
	pip3 install -U -r ./.repo/manifests/requirements.txt
	pip3 install pyric pyroute2 ipaddr netdiff scipy
	pip3 install networkx==1.11
	cd ..
fi

# mkdir -p wishful
# cd wishful
# repo init -u https://github.com/wishful-project/manifests.git
# repo init -m user.xml
# repo sync
# repo forall -c 'git checkout master'
# virtualenv -p /usr/bin/python3 ./dev
# source ./dev/bin/activate
# pip3 install -U -r ./.repo/manifests/requirements.txt
# cd ..
