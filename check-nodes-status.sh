#!/usr/bin/env bash

if [ $# -ne 2 ]; then
	echo "Usage: $0 <hosts file> <config file>"
	exit 1
fi

hosts_file=$1
config_file=$2

for i in `cat $hosts_file`
do
	res=`ssh -F $config_file $i ls &> /dev/null`
	exit_status=$?
	# echo $i $exit_status
	if [ "$exit_status" == "0" ]; then
		echo $i
	fi
done

