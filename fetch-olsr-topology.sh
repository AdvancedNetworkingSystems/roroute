#!/usr/bin/env bash

if [ $# -ne 2 ]; then
	echo "Usage: $0 <testbed> <node>"
	exit 1
fi

testbed=$1
node=$2

if [ "$testbed" = "twist" ]; then
	config="twist-ssh.cfg"
elif [ "$testbed" = "wilab" ]; then
	config="wilab1-ssh.cfg"
else
	echo "Invalid testbed: $testbed"
	exit 1
fi

now=`date +%Y%m%d_%H%M%S`
topo=`ssh -F $config $node 'echo "/netjsoninfo filter graph ipv4_0/quit" | nc 127.0.0.1 2009'`

echo $topo
