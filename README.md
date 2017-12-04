POPROW Scripts Repo
===================

```
################################################################################
#                                   WARNING                                    #
################################################################################
```

The documentation, as well as the scripts, are still being written and refined.
Please be aware that they might be incomplete.

# Testbed Resource Allocation

This section summarizes the steps required for reserving resources on the remote
testbeds. Currently the following testbeds are supported:
[TWIST](https://www.twist.tu-berlin.de/) and
[w.iLab1](http://doc.ilabt.iminds.be/ilabt-documentation/wilabfacility.html#w-ilab-1-setup).

The instruction reported below have been tested on Ubuntu 16.04 LTS.

## Omni tool

The [Omni](https://github.com/GENI-NSF/geni-tools/wiki/Omni) command line tool is
required to perform operations on the remote testbeds. Supported operations
include querying for testbed status/available resources, allocating/releasing
resources (slices) and creating/deleting experiments.

### Omni software dependencies

On ubuntu, in order to install the `omni`'s software dependencies run the
following command:

```
sudo apt install python-m2crypto python-dateutil python-openssl libxmlsec1 \
    xmlsec1 libxmlsec1-openssl libxmlsec1-dev autoconf
```

For other operating systems take a look at the official [wiki
page](https://github.com/GENI-NSF/geni-tools/wiki/QuickStart#debian--ubuntu)

### Omni installation

In order to install `omni,` executes the following commands:

```
cd /tmp
wget https://github.com/GENI-NSF/geni-tools/archive/v2.10.tar.gz -O gcf-2.10.tar.gz
tar xvfz gcf-2.10.tar.gz
cd geni-tools-2.10
./autogen.sh
./configure
make
sudo make install
```

Verify that `omni` has been installed correctly by executing `omni --version`.
This command should print something that resembles the following:

```
omni: GENI Omni Command Line Aggregate Manager Tool Version 2.10
Copyright (c) 2011-2015 Raytheon BBN Technologies
```

### Omni configuration file

The `omni_config` file provided in this repository is a template of the `omni`
configuration file. Before running any other `omni` command, this template file
must be modified in order to adapt it to the local host environment.

First of all, we assume that the user running the omni commands has a
valid [iMinds Authority account](https://authority.ilabt.iminds.be/). We also
assume that the user's public and private keys associated with the iMinds
Authority account are located in ~/.ssh/twist.cert and ~/.ssh/twist.prk
respectively (the private key MUST NOT be encrypted
`openssl rsa -in ssl.key.secure -out ssl.key`).

The users whose public keys will be installed on the testbed's nodes are listed
(comma separated list) in the value of the `users` key in the `omni` section.
For each user listed in the `users` key, there is a corresponding section (named
after the user name) containing the specific configuration for that particular
user.  For example, in the current template configuration file one of the user
is `segata`, and the corresponding configuration section looks like this:

```
[segata]
urn = urn:publicid:IDN+wall2.ilabt.iminds.be+user+segata
keys = ~/src/ansible-poprow/segata.pub
```

The value of the field `keys` must be modified to point to the public key of the
user `segata` (which is included in this repository as segata.pub). If we assume
that this repository has been cloned in /home/poprow/poprow-scripts, then the
keys value must be modified to look as follows:

```
keys = /home/poprow/poprow-scripts/segata.pub
```

This process must be repeated for each user listed in the `omni_config` file.

In case you need to add a new user, these are the required steps: 1) append the
new user name in the comma separated list of the `users` key in the `omni`
section; 2) add the user public key to the repository; 3) add to the
`omni_config` file a new section for the new user; 4) commit and push the new
`omni_config` template and the public key of the new user.


## SSH Configuration files

In order to be able to connect to the TWIST and w.iLab1 testbeds you must modify
the corresponding ssh configuration files (`twist-ssh.cfg` and `wilab1-ssh.cfg`)
and copy them in `~/.ssh/.`

In `twist-ssh.cfg` you must modify the following values:

* `IdentityFile` in sections `Host api.twist.tu-berlin.de` and
  `Host tplink nuc` to point to your iMinds Authority account's public key.

* `User` in section `Host tplink nuc` to match your user name.

In `wilab1-ssh.cfg` you must modify the following values:

* `IdentityFile` in sections `Host bastion.test.iminds.be` and `Host nuc` to
  point to your iMinds Authority account's public key.

* `User` in sections `Host bastion.test.iminds.be` and `Host nuc` to match your
  user name.

* `ProxyCommand` in section `Host nuc` to use your user name.


## RSPEC generation

RSPEC files (extension .rspec) are XML files that describes which nodes to
allocate in a given testbed. For the TWIST and w.iLab1 testbeds the .rspec files
can be generated automatically using the `gen-rspec.py` script. The script
supports the following command line parameters:

* `-t` (`--testbed`): specifies which testbed the RSPEC will be generated for.
  Use twist for the TWIST testbed and wilab for w.iLab1;

* `-f` (`--filter`): comma separated list of node name prefixes. Only the
  available nodes whose name starts with one of the specified prefixes are
  inserted in the generated RSPEC. By default all the available nodes are used for
  generating the RSPEC file.

* `-n` (`--nodes`): comma separated list of node names. Only the available nodes
  whose name is listed with the `-n` option are inserted in the RSPEC file. By
  default all the available nodes are used. The `-n` option takes precedence over
  `-f`.

For example, an RSPEC containing all the available nodes in the TWIST testbed
can be generated with the following command:

```
./gen-rspec.py -t twist > twist_all.rspec
```

Instead, an RSPEC containing all the nuc nodes in the TWIST testbed can be
generated with the following command:

```
./gen-rspec.py -t twist -f nuc > twist_nuc.rspec
```

Finally, an RSPEC containing only nuc4 and nuc6 from the TWIST testbed can be
generated with the following command:

```
./gen-rspec.py -t twist -n nuc4,nuc6 > twist_nuc_4_6.rspec
```

Note that, in any case, a node is inserted in the RSPEC only if it is available
in the moment the `gen-rspec.py` command is executed. For this reason the
suggested best practice is to execute `gen-rspec.py` just before allocating the
resources using the `reserve.py` command.


## Resource allocation

The `reserve.py` command can be use to allocate nodes specified in an .rspec
file and to release resources previously allocated. The command supports the
following parameters:

* `-t` (`--testbed`): specifies in which testbed to allocate the nodes. The
  testbed specified here must match the testbed used in the .rspec file
  specified with the parameter `-f`. Use twist for the TWIST testbed and wilab for
  w.iLab1;

* `-d` (`--duration`): it's an integer value that specifies how many hours the
  nodes will be reserved for. The minimum value currently supported is 3.

* `-s` (`--name`): specifies the name that identify the experiment. Every
  experiment whose allocation time overlaps must have a unique name.

* `-f` (`--rspec`): specifies the path to the .rspec file generated with the
  `gen-rspec.py` command.

By default `reserve.py` allocate the resources specified in the .rspec file. The
same command can be used also to release previously allocated resources using
the `-r` (`--release`) parameter.

For example, an experiment called `poprowexp1` that allocates in the TWIST
testbed the nodes specified in the file `twist_nuc_4_6.rspec` for 4 hours can be
created with the following command:

```
./reserve.py -t twist -d 4 -n poprowexp1 -f twist_nuc_4_6.rspec
```

Instead, the resources allocated in `poprowexp1` can be released with the
following command:

```
./reserve.py -t twist -n poprowexp1 -f twist_nuc_4_6.rspec -r
```

The command queries for the status of the testbed every 10 seconds, and reports
when everything is up and running. For large testbeds, e.g., the whole TWIST,
you might need to wait a lot because of the TP-Link devices. As an example, one
attempt to reserve the whole testbed took roughly one hour.

Once the reservation process is completed, the script check-nodes-status.sh can
be used to quickly check if the nodes specified in the .rspec file are reachable
vai ssh. The syntax for using the script is the following:

```
./check-nodes-status.sh <hosts_file> <ssh_config_file>
```

where hosts_file is the file listing the name of all the nodes that will be used
in the experiments and ssh_config_file is the ssh configuration file for
connecting to the testbeds (see Section "SSH Configuration files").

## Automatic Nodes Setup

The repository includes some `ansible` playbooks that are used to automatically
configure the nodes before starting any experiment.

Before running the scripts you need to modify the following files

 * `hosts`: this includes the list of nodes that will be used in the
   experiment, i.e., the nodes that you want `ansible` to work with. By
   default, the file includes all hosts from all testbeds. If you don't want to
   touch it, you can make a copy and then edit `ansible.cfg` and change the
   `inventory` field accordingly.
 * `setenv.sh`: this file sets up environment variables that specifies
   parameters used by the `run` command and by the ansible playbooks. In
   particular it sets the master node (the node of the testbed that runs
   `ansible` playbooks) and the `ssh` configuration file to be used. By
   default it sets the node `nuc0-43` as the master node for the `wilab1`
   testbed and `nuc4` for the `twist` testbed. If you want to use different
   master nodes you need to change this file. The ansible master node is
   specified by the variable `MASTER_NODE` and the ssh configuration file is
   specified by the `CONFIG_FILE` variable.
 * `run`: this works as a launcher for all ansible playbooks. Instead of
   typing `ansible-playbook playbook.yaml` you type `./run playbook.yaml`.
   This copies the content of the whole folder on the master node and
   launches the `ansible-playbook` on the master node, to avoid being blocked
   by a firewall because of the many `ssh` connections.
 * `etchosts`: this file is copied to `/etc/hosts` for easy pings and for
   setting the IP address to a node depending on its hostname. Change this
   according to your needs.

Once these steps are done, you are ready to setup the nodes:

 * `rsync-master-node.sh`: copy all the required support files on the ansible
   master node. In principle this command should be executed only once before
   any other test. The script accepts one parameter, which is the testbed.
   This is used to decide which master node to use. Accepted values are
   `twist` (the default if nothing is specified) or `wilab`.
 * `run copy-files.yaml`: copies the configuration scripts and other files to
    all nodes. By default the command runs ansible on the TWIST testbed. If you
    want to choose a different testbed (in your `hosts` file) use the `testbed`
    parameter, e.g., `run copy-files.yaml "testbed=wilab1"`.
 * `run setup-devices.yaml`: installs required software (e.g., `python`,
   `git`, python packages, etc.) on all nodes. As for `copy-files.yaml`, you can
   choose a different testbed with the `testbed` parameter.
 * `run setup-interfaces.yaml`: configures the network interface according to
   the given parameters to enable networking between testbed nodes. This
   script accepts parameters to configure the wireless interfaces in
   different ways. In particular you can choose rate, channel, and
   transmission power using the following syntax:
   `run setup-interfaces.yaml "rate=54 channel=1 power=2000"`
   The example uses the default parameters used when these are not specified.
   For more information on the possible parameter values, see the next section.
   As for `copy-files.yaml`, you can choose a different testbed with the
   `testbed` parameter.

## Ping Experiment

The purpose of the ping experiment is to compute the transmission success rate
between every pair of nodes for a given channel, transmission rate and
transmission power. The ping experiment is executed by editing the
`ping-experiments.csv` configuration file and by running the
`run-ping-experiment.sh` script. The script accepts one parameter, which is
the testbed name. Accepted values are `twist` (the default if nothing is
specified) or `wilab`.

Each line of the `ping-experiments.csv` configuration file specifies an
experiment configuration and has the following format:

```
<rate>,<channel>,<tx power>,<# of tx packet>,<interval between each transmission>
```

for example, the following line:

```
6,1,2000,10,0.2
```

describe an experiment where every node will transmit 10 frames (one every
200ms) on channel 1 using 6Mb/s and a transmission power of 20 dBm.

the `run-ping-experiment.sh` script will execute an experiment for each line of
the `ping-experiments.csv` configuration file. For each experiment the following
steps are executed:

* The nodes Wi-Fi interfaces are configured in ad-hoc mode for using the
  channel, tx rate and tx power specified in the configuration file.

* On all the nodes the receiver `pop-recv.py` is executed in background and
  configured to log information about the received transmissions.

* On each node in turn the transmitter `pop-ping.py` is executed and configured
  for transmitting the number of packets separated by the time interval
  specified in the configuration file.

* The receiver `pop-recv.py` is stopped on all nodes.

* The ansible master node collects all the logs of `pop-recv.py` from all the
  nodes and saves them in the results directory.

* The results directory is rsync-ed with the local node.

For example, given a configuration file with the following content:

```
6,1,2000,10,0.2
9,1,2000,10,0.2
```

the ping experiment can be executed on the TWIST testbed with the following
command:

```
./run-ping-experiment.sh twist
```

## OLSR/Prince Start/Stop

The repository provides a set of ansible playbooks that can be used for
starting/stopping olsrd2 and Prince on the nodes specified in the `hosts` files
(see Section "Automatic Nodes Setup"). All the following playbooks can be
launched using the `run` command and they accept the testbed parameter (e.g.
`run stop-olsr.yaml "testbed=wilab"`). The provided playbooks are the following:

* `start-olsr.yaml`: starts the olsrd2 service;

* `stop-olsr.yaml`: stops the olsrd2 service;

* `start-prince.yaml`: start the prince process. This playbok accepts also the
  `prince_conf` parameter for specifying which prince configuration file pass as
  argument to the prince process. This repository provides two default
  configurations for prince: `prince_conf_c.json` and `prince_conf_c_h.json`. If
  the `prince_conf` parameter is not used the default configuration is
  `prince_conf_c_h.json`;

* `stop-prince.yaml`: stops the prince process;

## OLSR/Prince Experiment

>### WARNING
>The scripts used for executing this experiment do not currently support devices
>running OperWRT. There are a few thing (e.g., `setup-prince.sh`) that are not
>implemented for OperWRT yet. Currently the scripts described in this section
>have been tested only within the w.iLab1 testbed running exclusively NUC
>devices.

>### WARNING
> From preliminary experiment results we observed that, when a high bitrate and
> a low transmission power are used to make the mesh network less dense, OLSR is
> not able to converge to a stable topology. This makes it impossible to extract
> meaningful results for comparing vanilla OLSR against OLSR+Prince. The idea
> for solving this problem is to execute experiments using the lowest bitrate
> and the highest transmission power possible in order to create an almost
> full-mesh topology and then deploy firewall rules on the nodes of the testbed
> for creating the topology we are interested in. At this moment this
> functionality is not implemented yet.

>### NOTE
>In order to make the experiment execution a little bit faster, be sure to
>increase the value of the `forks` parameter in the `ansible.cgf` file to a
>values at least as big as the number of nodes in the testbed.

>### NOTE
>This tutorial is still under development

The OLSR/Prince experiment can be executed from the local host thanks to the
`run_remote_olsr_experiment.sh` script. This script connects via SSH to the
ansible master node and calls, in turn, `olsr_experiment_controller.py`. This is
a python program that, relying on various ansible playbooks, is responsible of
controlling the whole experiment.
The script `run_remote_olsr_experiment.sh` must be called with the following
syntax:

```
run_remote_olsr_experiment.sh <testbed> \
                                <channel> \
                                <legacy_rate> \
                                <txpower> \
                                <strategy_name> \
                                <graph_type> \
                                <expname> \
                                <resultsdir> \
                                <verbose (True|False)> \
                                <fetch_results (True|False)>"
```

where:

* `testbed`: is the identifier of the testbed where the experiment will be
  executed. Use `twist` for the TWIST testbed and `wilab` for w.iLab1;

* `channel`: channel number used for creating the mesh network. Supported values
  goes from 1 to 11.

* `legacy_rate`: fixed transmission rate used for transmissing frames. Supported
  values are: 6, 9, 12, 18, 24 36, 48 and 54.

* `txpower`: transmission power in in millibel-milliwatts (mBm) (<power in mBm>
  = 100 * <power in dBm>). Accepted values goes from 0 to 2000.

* `strategy_name`: the name of the strategy used for stopping and restarting
  nodes. For details see the dedicated Section "Stretegies for stopping/starting
  nodes".

* `graph_type`: the type of graph that will be created by deploying the proper
  firewall rules on the nodes of the testbed. Currently the only graph type
  supported is `powerlaw`.

* `expname`: the name that identifies the experiment. This name is also used
  for creating the directories used for saving the results of the experiment. In
  particular, on each node involved in the experiment will be created the
  directory `${HOME}/expname`. This directory, in turn, can potentailly contains
  multiple sub-directories based on what `strategy_name` has been used. At the end
  of the experiment, on the ansible master node, a directory called
  `<resultsdir>/expname_results` will be created. This directory will contain an
  archive of the experiment results for ech node involved in the experiment. The
  archives are named using the following format: `node_name_expname.tar.gz`.
  node_name_expname.tar.gz containing,

* `resultsdir`: the full path base directory on the ansible master node where
  all the results will be collected at the end of the experiment. The user must
  select a directory mounted on a partition with enough space for storing the
  results of the esperiments (several GB). For example, on the w.ilab1 testbed
  there is a shared partition mounted in `/proj/wall2-ilabt-iminds-be` that can be
  used for this purpose.

* `verbose`: when this parameter is set to `True` the experiment controller will
  produce a more verbose output.

* `fetch_results`: when this parameter is set to `True` the directory
  `<resultsdir>/expname_results` created on the ansible master node will be
  transferred on the local host in the current directory. Note that, independently
  from the value of this parameter, the directory `<resultsdir>/expname_results`
  on the ansible master node is always created.

The experiment controller (`olsr_experiment_controller.py`), running on the
ansible master node, performs the following steps (except for the first and last
steps, all the others are performed in a loop until the list of strategies that
define how to stop and restart nodes have been completed):

* (NOT IMPLEMENTED YET): Preliminary set up of the network with the best channel
  conditions possible for understanding what is the most dense mesh network
  possible in the testbed. Based on the output of this task a set of firewall
  rules can be generated for creating the topology we are interested in. This
  step will be performed only once before starting the actual experiment.

* Stop OLSR and Prince as a preliminary procedure (`stop-olsr.yaml` and
  `stop-prince.yaml` respectively).

* Network setup using `setup-interfaces.yaml`.

* Start OLSR using `start-olsr.yaml`.

* If this is an odd iteration, the controller starts prince using
  `start-olsr.yaml`. For each strategy that defines how to stop/start the nodes
  two iteration of the loop are executed: one with a vanilla OLSR and the other
  with OLSR+Prince.

* After a 10 seconds sleep, the controller starts waiting for the topology to
  become stable: the controller asks to olsrd2 the topology (`netjsoninfo`) every
  second and if the topology does not change for 10 seconds in a row then it is
  considered stable. Note that the controller wait for a maximum of 120 seconds
  for the topoloby to become stable. After 120 seconds it proceeds with the
  experiment anyway. However the last topology obtained before starting the
  experiment is saved by the controller in the results directory of the ansible
  master node as a `.graphml` file.

* Once the topolgy is stable, or after 120 seconds, if this is the first
  iteration (or an even iteration) of the loop, the function specified by the
  `strategy_name` parameter is called. This function returns the lists of
  strategies that specify how and when the nodes must be stopped and restarted
  (see Section "Stretegies for stopping/starting nodes"). For each element of
  the strategy lists, two experiments are executed: one with a vanilla OLSR and
  the other with OLSR+Prince.

* The experiment controller schedule the start/stop of the `topology_dumper`
  using `start-topology-dumper.yaml`. The `topology_dumper` will dump the olsrd2
  topology every 100ms on every nodes and will save all the obtained topologies in
  the results directory of each node.

* The experiment controller schedule the stop of the nodes using
  `kill-my-wifi.yaml`.

* The experiment controller schedule the restart of the nodes using
  `restart-my-wifi.yaml`.

* The experiment controller fetch the results of the experiment using
  `collect-olsr-results.yaml`: it archives the results on each node used in the
  experiment and transfers the archives on the ansible master node in the
  directory `${HOME}/expname_results`.

### Stretegies for stopping/starting nodes

The parameter `strategy_name` of the script `run_remote_olsr_experiment.sh`
defines which function (defined in `olsr_experiment_controller.py`) will be used
for building the list of strategies that define how and when the nodes must be
stopped and restarted during the experiment. For each element of the list
returned by the `strategy_name` function two experiments are performed: one
using vanilla OLSR and one with OLSR+Prince.
Currently only the following example strategies are implemented:

* `stop_one_random_node_1s`: selects a random node of the mesh network and stops
  it after 1 seconds..

* `stop_one_random_node_1s_start_61s`: selects a random node of the mesh
  network, stops it after 1 second and restarts it after 61 seconds.

* `one_node_stop_1s_start_61s_2mostcentral`: computes the two most central
  (betweenness centrality) nodes of the mesh network and returns a list of two
  strategies. The first strategy stops the most central node after 1 second and
  restarts it after 61 seconds. The second strategy stops the second most central
  node after 1 seconds and restarts it after 61 seconds.

* `two_node_stop_1s_start_61s_2mostcentral`: computes the two most central
  (betweenness centrality) nodes of the mesh network and returns a strategy
  where both the nodes are stopped after 1 second and restarted after 61 seconds.

The best way to learn how to implement new strategy functions is to look in the
code of `olsr_experiment_controller.py` and see how the existing strategy
functions have been implemented. In particular, a little bit of documentation is
provided for the strategy function `stop_one_random_node_1s`. Once a new
strategy function has been implemented, its name must be add to the global list
`strategy_functions`.

In short, a strategy function must return two lists of strings with the same
number of elements. Each element of the first list specify which nodes and when
they must be stopped. The corresponding elements of the second list specify
which nodes and when must be restarted. Note that both the lists can contain
empty strings as elements. However, for each element of the first list, the
corresponding element of the second list must contain only nodes that are
present also in the first list (i.e., a node that is not stopped can not be
restarted). Moreover, the time when a node must be restarted must come after the
time when the same node is stopped. It is responsibility of the strategy
function to comply with these constraints.  The elements of the two list have
the following format:

```
node1_id@seconds.milliseconds,node2_id@seconds.milliseconds,...
```

where the `node#_id` is the id of the node as specified in the graph that is
passed as parameter to the strategy function (the experiment controller will
take care of translating these ids into the corresponding hostnames of the nodes
of the testbed). The `seconds.milliseconds` specifyies after how much time that
node must be stopped or restarted (the time point of reference is when the
`topology_dumper` starts).


### Experiment Example

Let's consider the following command:

```
./run_remote_olsr_experiment.sh wilab \
                                11 \
                                6 \
                                2000 \
                                two_node_stop_1s_start_61s_2mostcentral \
                                powerlaw \
                                test_experiment \
                                /proj/wall2-ilabt-iminds-be/exp/olsrprince1/ \
                                True \
                                False
```

This will executed an experiment on the w.iLab1 testbed and will use a mesh
network configured for operating on channel 11 where the nodes will transmit
frames using a bitrate of 6Mbps and a transmission power of 20dBm. The
experiment will be composed by two sub-experiments (vanilla OLSR and
OLSR+Prince) where the stop/restart strategy defined by
`two_node_stop_1s_start_61s_2mostcentral` will be used: the two most central
nodes of the mesh network will be stopped after 1 second and restarted after 61
seconds. At the end of the experiment the directory
`/proj/wall2-ilabt-iminds-be/exp/olsrprince1//test_experiment_results`
containing all the results of all the nodes will be created on the ansible
master nodes but will not be transferred on the local host. Finally, the
experiment controller will produce a verbose output.

## Wi-Fi Network Interface Configuration

The python script poprow_setup_interface.py can be used for bringing up an
802.11 network interface in adhoc (ibss) mode. Before using this script it is
necessary to install all the required dependencies by executing the
setup-devices.sh script. The script also creates a monitor interface configured
on the same channel as the adhoc interface that can be used for traffic
monitoring. The script requires the following parameters (in the current
implementation, with the exception of --bint, the are all mandatory).

* `--intcap`: possible values are "HT" and "VHT". It is used to specify the
  capabilities that must be supported by the NIC that will be used for
  configuring the interface. Currently the TKN WIreless NetworkS Testbed (TWIST)
  supports only "HT".

* `--chan`: specifies in which channel to configure the network interface.
  Accepted values for --chan are [1-13] (2.4 GHz) and [36, 40 and 44] (5 GHz).

* `--legacyrate`: configures the 802.11g rate to use for frame transmissions.
  Accepted values are [6, 9, 12, 18, 24 36, 48, 54].

* `--txpower`: configures the transmission power in millibel-milliwatts (mBm)
  (<power in mBm> = 100 * <power in dBm>). Accepted values goes from 0 to 3000
  (the actual maximum power depends on selected channel and the actual power
  selection granularity depend on the PHY).

* `--inet`: sets the interface IPv4 address. The accepted format is
  x.y.z.t/nm.

* `--ibssid`: configures the BSSID of the adhoc network.

* `--ibssiname`: configures the name of the local adhoc interface.

* `--moniname`: configures the name of the local monitor interface (this
  interface shares the same PHY as the adhoc interface and can be used for
  traffic monitoring).

* `--bint`: configure the beacon interval in TUs (default values 100TUs).


### Example

An adhoc network interface called _poprow0_ with the following characteristics:

* the underlying PHY supports HT capabilities;
* the adhoc network operates on channel 1 in the 2.4GHz band;
* all the frame are transmitted using 6Mb/s;
* the transmission power is fixed to 20dBm;
* the IPv4 address is 192.168.100.10/24;
* the BSSID is _poprow_;
* the interface transmits a beacon every 200 TUs;
* the monitor interface name is _mon0_.

can be configured by executing the following command (as root):

```
./poprow_setup_interface.py --intcap=HT --chan=1 --legacyrate=6 \
  --txpower=2000 --inet=192.168.100.10/24 --ibssid=poprow --ibssiname=poprow0 \
  --moniname=mon0 --bint=200
```
