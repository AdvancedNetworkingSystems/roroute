#!/usr/bin/env bash

sudo apt-get install -y wget git rfkill

git config --global user.name "ANS"
git config --global user.email "ans@ans.disi.unitn.it"
git config --global color.diff auto
git config --global color.status auto
export PATH=$PATH:$HOME/

cd
wget https://storage.googleapis.com/git-repo-downloads/repo
chmod a+x ./repo
mkdir -p wishful
cd wishful
repo init -u https://github.com/AdvancedNetworkingSystems/manifests-wishful
cd .repo/manifests
git checkout alix
cd ../..
repo init -m user.xml
repo sync
repo forall -c 'git checkout master'
cp .repo/manifests/requirements.txt /tmp/
cd
rm -rf $HOME/wishful/.repo $HOME/repo

sudo apt-get install -y python3-dev python3-pip
sudo pip3 install virtualenv
virtualenv -p /usr/bin/python3 ./dev
. ./dev/bin/activate
pip3 install -U -r /tmp/requirements.txt
pip3 install pyric pyroute2 ipaddr netdiff scipy
pip3 install networkx==1.11
