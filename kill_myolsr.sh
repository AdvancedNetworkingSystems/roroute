#!/usr/bin/env sh

start_time=$1
nodes=$2

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	host_name=`hostname | cut -d'.' -f 1`
	kill_cmd='sudo service olsrd2 stop'
else
	host_name=`uci get system.@system[0].hostname`
	kill_cmd='/etc/init.d/olsrd2 stop'
fi

for i in $(echo $nodes | sed -e "s/,/ /g")
do
	node=`echo $i | cut -d'@' -f 1`
	time=`echo $i | cut -d'@' -f 2`
	secs=`echo $time | cut -d'.' -f 1`
	ms=`echo $time | cut -d'.' -f 2`
	unix_time=$(($start_time + $secs))

	if [ "$host_name" = "$node" ]; then
		echo "runat $unix_time $ms '$kill_cmd'" | at now &> /dev/null
	fi
done
