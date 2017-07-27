#!/usr/bin/env bash

if [ $# -ne 8 ]; then
	echo "Usage: $0 <testbed> <channel> <legacy rate> <txpower> <strategy name> <exp name> <verbose (True|False)> <copy results on local node (True|False)>"
	exit 1
fi

testbed=$1
channel=$2
legacyrate=$3
txpower=$4
killstrategy=$5
expname=$6
if [ "$7" == "True" ]; then
	verbose="--verbose"
else
	verbose=""
fi
copyresults=$8

. ./setenv.sh $testbed

ANSIBLE_FOLDER=${HOME_FOLDER}/ansible/
EXPERIMENT_CONTROLLER=olsr_experiment_controller.py

ssh -A -F ${CONFIG_FILE} ${MASTER_NODE} \
	"cd ${ANSIBLE_FOLDER} &&./${EXPERIMENT_CONTROLLER} --testbed ${testbed} --chan ${channel} --legacyrate ${legacyrate} --txpower ${txpower} --killstrategy ${killstrategy} --expname ${expname} --verbose"

# Probably it is better if we do some preliminary analysis on the master node
# for reducing the size of the results before copying everything on the local
# node
if [ "${copyresults}" == "True" ]; then
	resdir=$(pwd)/${expname}_results

	if [ -d ${resdir} ]; then
		rm -rf ${resdir}
	fi

	echo "Copying results from master node (${MASTER_NODE}) to local directory ${resdir}"
	scp -r -F ${CONFIG_FILE} ${MASTER_NODE}:${expname}_results ${resdir}
fi
