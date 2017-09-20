#!/usr/bin/env sh

testbed=$1
rate=$2
channel=$3
power=$4
prince_conf=$5
nodes=$6
start_time=$7

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	host_name=`hostname | cut -d'.' -f 1`
else
	host_name=`uci get system.@system[0].hostname`
	echo "WARNING: Wi-Fi restart on OpenWRT not implemented yet"
	exit 1
fi

ip_addr=`cat /etc/hosts | grep "pop-$host_name\$" | cut -d' ' -f 1`

restart_cmd1="$(pwd)/setup-interfaces.sh ${rate} ${channel} ${power}"
restart_cmd2="$(pwd)/start-olsr-v1.sh ${testbed}"
restart_cmd3=""

if [ "${prince_conf}" = "none" ]; then
	restart_cmd3="$(pwd)/start-prince.sh ${prince_conf}"
fi

for i in $(echo $nodes | sed -e "s/,/ /g")
do
	node=`echo $i | cut -d'@' -f 1`
	time=`echo $i | cut -d'@' -f 2`

	secs1=`echo $time | cut -d'.' -f 1`
	ms1=`echo $time | cut -d'.' -f 2`
	unix_time1=$(($start_time + $secs1))

	if [ $ms -lt 997 ]; then
		secs2=$secs1
		ms2=$(($ms1 + 2))
	else
		secs2=$(($secs1 + 1))
		ms2=000
	fi
	unix_time2=$(($start_time + $secs2))

	if [ $ms2 -lt 997 ]; then
		secs3=$secs2
		ms3=$(($ms2 + 2))
	else
		secs3=$(($secs2 + 1))
		ms3=000
	fi
	unix_time3=$(($start_time + $secs3))


	if [ "$host_name" = "$node" ]; then
		echo "runat $unix_time1 $ms1 '$restart_cmd1'" | at now &> /dev/null

		echo "runat $unix_time2 $ms2 '$restart_cmd2'" | at now &> /dev/null

		if [ ! -z "${restart_cmd3}" ]; then
			echo "runat $unix_time3 $ms3 '$restart_cmd3'" | at now &> /dev/null
		fi
	fi
done
