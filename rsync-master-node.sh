#!/usr/bin/env bash

source setenv.sh

ANSIBLE_FOLDER=${HOME_FOLDER}/ansible/

ssh -F ${CONFIG_FILE} ${MASTER_NODE} "mkdir -p ${ANSIBLE_FOLDER}"
rsync -avcz --exclude-from=rsync-ignore -e "ssh -F ${CONFIG_FILE} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --progress ./ ${MASTER_NODE}:${ANSIBLE_FOLDER}
