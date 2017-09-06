#!/usr/bin/env sh

start_time=$1
nodes=$2
kill_cmd1="$(which sudo) ip link set dev poprow0 down"

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	host_name=`hostname | cut -d'.' -f 1`
	kill_cmd1="$(which sudo) killall -9 olsrd2_dynamic; ${kill_cmd1}"
	kill_cmd3='sudo service olsrd2 stop'

	kill_cmd2=''
	prince_pid=$(ps aux | grep /usr/bin/prince | grep -v grep | tr -s ' ' | cut -d ' ' -f 2)

	if [ ! -z "${prince_pid}" ]; then
		kill_cmd2="kill ${prince_pid}"
	fi
else
	host_name=`uci get system.@system[0].hostname`
	kill_cmd3='/etc/init.d/olsrd2 stop'

	echo "WARNING: Prince stop mechanism for OpenWRT not implemented yet"
	exit 1
fi

for i in $(echo $nodes | sed -e "s/,/ /g")
do
	node=`echo $i | cut -d'@' -f 1`
	time=`echo $i | cut -d'@' -f 2`
	secs=`echo $time | cut -d'.' -f 1`
	ms=`echo $time | cut -d'.' -f 2`
	unix_time=$(($start_time + $secs))

	if [ "$host_name" = "$node" ]; then
		echo "runat $unix_time $ms '$kill_cmd1'" | at now &> /dev/null

		if [ ! -z "${kill_cmd2}" ]; then
			echo "runat $unix_time $ms '$kill_cmd2'" | at now &> /dev/null
		fi

		echo "runat $unix_time $ms '$kill_cmd3'" | at now &> /dev/null
	fi
done
