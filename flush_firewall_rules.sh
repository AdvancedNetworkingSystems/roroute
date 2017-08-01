#!/usr/bin/env sh

testbed=$1
iptables_cmd=$(which iptables)

# Existing rules flushing
$(which sudo) ${iptables_cmd} -F

