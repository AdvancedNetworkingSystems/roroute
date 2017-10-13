#!/usr/bin/env bash

if [ $# -ne 18 ]; then
	echo "Usage: $0 <testbed> <channel> <legacy rate> <txpower> <strategy name> <strategy nrepeat> <strategy params> <graph params> <metrics seed> <exp name> <results_basedir> <weights (True|False)> <fixed intervals (True|False)> <verbose (True|False)> <copy results on local node (True|False)> <hello validity multiplier> <tc validity multiplier> <single interface (True|False)>"
	exit 1
fi

testbed=$1
channel=$2
legacyrate=$3
txpower=$4
killstrategy=$5
nrepeat=$6
strategyparam=$7
graphparams=$8
mseed=$9
expname=${10}
resultsdir=${11}
if [ "${12}" == "True" ]; then
	weights="--weights"
else
	weights=""
fi
if [ "${13}" == "True" ]; then
	fixedintervals="--fixedintervals"
else
	fixedintervals=""
fi
if [ "${14}" == "True" ]; then
	verbose="--verbose"
else
	verbose=""
fi
copyresults=${15}
hello_mult=${16}
tc_mult=${17}
if [ "${18}" == "True" ]; then
	singleinterface="--singleinterface"
else
	singleinterface=""
fi

. ./setenv.sh $testbed

ANSIBLE_FOLDER=${HOME_FOLDER}/ansible/
EXPERIMENT_CONTROLLER=olsrv1_experiment_controller.py

echo "cd ${ANSIBLE_FOLDER} &&./${EXPERIMENT_CONTROLLER} --testbed ${testbed} --chan ${channel} --legacyrate ${legacyrate} --txpower ${txpower} --killstrategy ${killstrategy} --nrepeat ${nrepeat} --strategyparam ${strategyparam} --graphparams ${graphparams} --metricsseed ${mseed} --expname ${expname} --resultsdir ${resultsdir} ${weights} ${fixedintervals} ${verbose} --hellomult ${hello_mult} --tcmult ${tc_mult} ${singleinterface}"
ssh -A -F ${CONFIG_FILE} ${MASTER_NODE} \
	"cd ${ANSIBLE_FOLDER} &&./${EXPERIMENT_CONTROLLER} --testbed ${testbed} --chan ${channel} --legacyrate ${legacyrate} --txpower ${txpower} --killstrategy ${killstrategy} --nrepeat ${nrepeat} --strategyparam ${strategyparam} --graphparams ${graphparams} --metricsseed ${mseed} --expname ${expname} --resultsdir ${resultsdir} ${weights} ${fixedintervals} ${verbose} --hellomult ${hello_mult} --tcmult ${tc_mult} ${singleinterface}"

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
