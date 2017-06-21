#!/usr/bin/env bash

if [ $# -eq 1 ]; then
	testbed=$1
else
	testbed="twist"
fi

. ./setenv.sh $testbed

for conf in `cat ping-experiments.csv`
do
	rate=`echo $conf | cut -d',' -f 1`
	channel=`echo $conf | cut -d',' -f 2`
	power=`echo $conf | cut -d',' -f 3`
	n=`echo $conf | cut -d',' -f 4`
	int=`echo $conf | cut -d',' -f 5`
	./run setup-interfaces.yaml "rate=${rate} channel=${channel} power=${power} testbed=${testbed}"
	./run start-pop-recv.yaml "testbed=${testbed}"
	# wait a few second to ensure network startup. otherwise results might be wrong
	sleep 5
	./run start-pop-ping.yaml "n=${n} int=${int} testbed=${testbed}"
	./run kill-pop-recv.yaml "testbed=${testbed}"
	./run fetch-experiment-data.yaml "rate=${rate} channel=${channel} power=${power} n=${n} int=${int} testbed=${testbed}"
	rsync -avcz --exclude= -e "ssh -F ${CONFIG_FILE} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --progress ${MASTER_NODE}:${HOME_FOLDER}/results .
done
