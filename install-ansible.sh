#!/usr/bin/env bash

ansible_path=`which ansible-playbook`

if [ "$ansible_path" == "" ]; then
	sudo apt-get install -y ansible
fi
