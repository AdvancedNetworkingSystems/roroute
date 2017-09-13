#!/usr/bin/env sh

testbed=$1
# metric string format: "IPnode1:IPnd1-cost,IPnd2-cost,...;IPnode2:IPnd1-cost,..."
# Per node metrics are separeted by ";"
# Each per node metric is composed by a node IP before ":" (e.g., IPnode1) that
# identifies the local node,
# followed by a comma separated list of <destination node IPs>-<link cost>
# pairs.
metrics=$2

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
			metrics_out="${metrics_out}      link          ${dst} ${cost}\n"
		done
	fi
done

metrics_out=$(cat <<EOF
[global]
      plugin        constant_metric
      plugin        remotecontrol

[olsrv2]
      originator    -127.0.0.1/8
      originator    -::/0
      originator    default_accept
      nhdp_routable yes
      tc_interval   5.0

[telnet]
      bindto        127.0.0.1
      port          2009

[interface]
      bindto        -127.0.0.1/8
      bindto        -::/0
      bindto        default_accept
      hello_interval 2.0

[remotecontrol]
      acl           default_accept

[constant_metric=poprow0]
${metrics_out}
[interface=poprow0]
EOF
)

echo "${metrics_out}" > /tmp/olsrd2.conf

opkg_path=`which opkg`
if [ -z "$opkg_path" ]; then
	sudo cp /tmp/olsrd2.conf /etc/olsrd2/olsrd2.conf
else
	echo "WARNING: constant metrics deployment not implemented on OpenWRT"
	exit 1
fi
