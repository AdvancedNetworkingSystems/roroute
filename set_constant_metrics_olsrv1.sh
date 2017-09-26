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
# timers=$3
timers="nuc0-10:2.28,5.64;nuc0-11:2.10,5.20;nuc0-12:2.85,7.06;nuc0-13:2.50,6.19;nuc0-14:3.43,12.02;nuc0-15:3.45,8.55;nuc0-16:1.83,3.71;nuc0-17:1.88,3.80;nuc0-18:1.97,4.88;nuc0-19:1.87,4.64;nuc0-20:1.57,3.89;nuc0-21:1.60,3.96;nuc0-22:1.63,4.05;nuc0-23:1.68,4.15;nuc0-24:1.65,4.08;nuc0-25:1.64,4.07;nuc0-26:1.52,3.77;nuc0-27:1.54,3.82;nuc0-28:1.73,4.28;nuc0-29:1.79,4.44;nuc0-30:3.15,7.81;nuc0-31:3.21,7.94;nuc0-32:3.24,8.03;nuc0-33:3.43,12.02;nuc0-34:2.50,6.19;nuc0-35:2.85,7.06;nuc0-36:3.45,8.55;nuc0-37:3.07,7.60;nuc0-38:2.10,5.20;nuc0-39:2.27,5.62;nuc0-40:1.57,3.89;nuc0-41:1.66,4.10;nuc0-42:1.63,4.05;nuc0-43:1.60,3.96;nuc0-4:1.79,4.44;nuc0-6:1.87,4.64;nuc0-7:1.97,4.88;nuc0-8:1.68,4.15;nuc0-9:1.73,4.28"

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
