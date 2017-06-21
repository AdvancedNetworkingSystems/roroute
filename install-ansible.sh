#!/usr/bin/env bash

ansible_path=`which ansible-playbook`

if [ "$ansible_path" == "" ]; then
	echo "Installing ansible on master node..."
	sudo apt-get install -y ansible &> /dev/null
	echo "Done"
fi
