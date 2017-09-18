#!/usr/bin/env sh

testbed=$1
# rules string format: "IPnode1:IPnd1,IPnd2,...;IPnode2:IPnd1,IPnd2,..."
# Per node rules are separeted by ";"
# Each per node rule is composed by a node IP before ":" (e.g., IPnode1),
# followed by a comma separated list of nodes IPs whose packets must be
# dropped.
rules=$2
iptables_cmd=$(which iptables)

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	host_name=`hostname | cut -d'.' -f 1`
else
	host_name=`uci get system.@system[0].hostname`
	echo "WARNING: firewall rules deployment on OpenWRT not implemented yet"
	exit 1
fi

# Existing rules flushing
$(which sudo) ${iptables_cmd} -F

for n in $(echo $rules | sed -e "s/;/ /g")
do
	node_ip=$(echo ${n} | cut -d ':' -f 1)
	node_name=$(cat /etc/hosts | grep "${node_ip} " | cut -d ' ' -f 2 | sed -e 's/^pop-\(.*$\)/\1/')
	ip_to_drop=$(echo ${n} | cut -d ':' -f 2)

	if [ "$host_name" = "$node_name" ]; then
		for iptd in $(echo ${ip_to_drop} | sed -e "s/,/ /g")
		do
			# ip_to_drop=$(cat /etc/hosts | grep ${ntd} | cut -d ' ' -f 1)
			echo "$(which sudo) $iptables_cmd -I INPUT -i poprow0 -m mac --mac-source $mac -j DROP"
			$(which sudo) $iptables_cmd -I INPUT -i poprow0 -m mac --mac-source $mac -j DROP
		done
	fi
done

