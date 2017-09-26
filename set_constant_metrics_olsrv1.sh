#!/usr/bin/env sh

testbed=$1
# metric string format: "IPnode1:IPnd1-cost,IPnd2-cost,...;IPnode2:IPnd1-cost,..."
# Per node metrics are separeted by ";"
# Each per node metric is composed by a node IP before ":" (e.g., IPnode1) that
# identifies the local node,
# followed by a comma separated list of <destination node IPs>-<link cost>
# pairs.
metrics=$2

# timers string format: "hostname:hello,tc;..."
timers=$3

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	host_name=`hostname | cut -d'.' -f 1`
else
	host_name=`uci get system.@system[0].hostname`
	echo "WARNING: metrics deployment on OpenWRT not implemented yet"
	exit 1
fi

metrics_out=""
for n in $(echo $metrics | sed -e "s/;/ /g")
do
	node_ip=$(echo ${n} | cut -d ':' -f 1)
	node_name=$(cat /etc/hosts | grep "${node_ip} " | cut -d ' ' -f 2 | sed -e 's/^pop-\(.*$\)/\1/')
	metric_per_dst=$(echo ${n} | cut -d ':' -f 2)

	if [ "$host_name" = "$node_name" ]; then
		for dst_cost in $(echo ${metric_per_dst} | sed -e "s/,/ /g")
		do
			dst=$(echo ${dst_cost} | cut -d '-' -f 1)
			cost=$(echo ${dst_cost} | cut -d '-' -f 2)
			metrics_out="${metrics_out}    LinkQualityMult    ${dst} ${cost}\n"
		done
	fi
done

timers_out=""
if [ $# -eq 3 ]; then
	# we also have to set fixed timers
	for n in $(echo $timers | sed -e "s/;/ /g")
	do
		node_name=$(echo ${n} | cut -d':' -f 1)
		if [ "$host_name" = "$node_name" ]; then
			hello_interval=$(echo ${n} | cut -d':' -f 2 | cut -d',' -f 1)
			tc_interval=$(echo ${n} | cut -d':' -f 2 | cut -d',' -f 2)
			timers_out="HelloInterval ${hello_interval}\nTcInterval ${tc_interval}\n"
		fi
	done
fi

metrics_out=$(cat <<EOF
DebugLevel 0

IpVersion 4

LoadPlugin "olsrd_jsoninfo.so.1.1" {
}
LoadPlugin "olsrd_txtinfo.so.1.1" {
}
LoadPlugin "olsrd_poprouting.so.0.1" {
  PlParam "port" "1234"
}

InterfaceDefaults
{
${metrics_out}
${timers_out}
}
EOF
)

echo "${metrics_out}" | sudo tee /tmp/olsrd.conf

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo cp /tmp/olsrd.conf /etc/olsrd/olsrd.conf
else
	echo "WARNING: constant metrics deployment not implemented on OpenWRT"
	exit 1
fi
