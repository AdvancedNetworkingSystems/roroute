#!/usr/bin/env bash

if [ $# -ne 12 ]; then
	echo "Usage: $0 <testbed> <channel> <legacy rate> <txpower> <strategy name> <strategy nrepeat> <graph params> <metrics seed> <exp name> <results_basedir> <verbose (True|False)> <copy results on local node (True|False)>"
	exit 1
fi

testbed=$1
channel=$2
legacyrate=$3
txpower=$4
killstrategy=$5
nrepeat=$6
graphparams=$7
mseed=$8
expname=$9
resultsdir=${10}
if [ "${11}" == "True" ]; then
	verbose="--verbose"
else
	verbose=""
fi
copyresults=${12}

. ./setenv.sh $testbed

ANSIBLE_FOLDER=${HOME_FOLDER}/ansible/
EXPERIMENT_CONTROLLER=olsr_experiment_controller.py

echo "cd ${ANSIBLE_FOLDER} &&./${EXPERIMENT_CONTROLLER} --testbed ${testbed} --chan ${channel} --legacyrate ${legacyrate} --txpower ${txpower} --killstrategy ${killstrategy} --nrepeat ${nrepeat} --graphparams ${graphparams} --metricsseed ${mseed} --expname ${expname} --resultsdir ${resultsdir} --verbose"
ssh -A -F ${CONFIG_FILE} ${MASTER_NODE} \
	"cd ${ANSIBLE_FOLDER} &&./${EXPERIMENT_CONTROLLER} --testbed ${testbed} --chan ${channel} --legacyrate ${legacyrate} --txpower ${txpower} --killstrategy ${killstrategy} --nrepeat ${nrepeat} --graphparams ${graphparams} --metricsseed ${mseed} --expname ${expname} --resultsdir ${resultsdir} --verbose"

# Probably it is better if we do some preliminary analysis on the master node
# for reducing the size of the results before copying everything on the local
# node
if [ "${copyresults}" == "True" ]; then
	resdir=$(pwd)/${expname}_results

	if [ -d ${resdir} ]; then
		rm -rf ${resdir}
	fi

	echo "Copying results from master node (${MASTER_NODE}) to local directory ${resdir}"
	scp -r -F ${CONFIG_FILE} ${MASTER_NODE}:${resultsdir}/${expname}_results ${resdir}
fi
