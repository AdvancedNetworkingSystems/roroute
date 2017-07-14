#!/usr/bin/env sh

nodes=$1
testbed="wilab"

delta_start=60
delta_stop=30
now=`date +%s`
start_time=$(($now + $delta_start))

times=""
for i in $(echo $nodes | sed -e "s/,/ /g")
do
	time=`echo $i | cut -d'@' -f 2`
	secs=`echo $time | cut -d'.' -f 1`
	unix_time=$(($start_time + $secs))
	if [ "$times" = "" ]; then
		times=$unix_time
	else
		times="$times $unix_time"
	fi
done

min_time=`echo $times | tr ' ' '\n' | sort -g | head -1`
max_time=`echo $times | tr ' ' '\n' | sort -g | tail -1`

stop_time=$(($max_time + $delta_stop))

echo "Experiment will start at `date -d @$start_time` and will end at `date -d @$stop_time`"

ansible-playbook start-olsr.yaml --extra-vars "testbed=$testbed"
ansible-playbook olsr_experiment.yaml --extra-vars "testbed=$testbed start=$start_time stop=$stop_time prefix=test interval=100"
ansible-playbook kill_myolsr.yaml --extra-vars "testbed=$testbed start=$start_time nodes=$nodes"

echo "Experiment will start at `date -d @$start_time` and will end at `date -d @$stop_time`"
