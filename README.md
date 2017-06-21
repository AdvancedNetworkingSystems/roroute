POPROW Scripts Repo
===

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
For each user listed in the `users` key, there is a corresponding section (names
as the user) containing the specific configuration for that particular user.
For example, in the current template configuration file one of the user is
`segata`, and the corresponding configuration section looks like this:

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

In case you need to add a new user, these are the steps required: 1) append the
new user name in the comma separated list of the `users` key in the `omni`
section; 2) add the user public key to the repository; 3) add to the
`omni_config` file a new section for the new user; 4) commit and push the new
`omni_cinfig` template and the public key of the new user.


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
can be generated automatically thanks to the `gen-rspec.py` script. The script
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

## Automatic Nodes Setup

The repository includes some `ansible` playbooks that are used to automatically
configure the nodes before starting any experiment.

Before running the scripts you need to modify the following files

 * `hosts`: this includes the list of nodes that will be used in the
   experiment, i.e., the nodes that you want `ansible` to work with. By
   default, the file includes all hosts from all testbeds. If you don't want to
   touch it, you can make a copy and the edit `ansible.cfg` and change the
   `inventory` field accordingly.
 * `setenv.sh`: this file contains a few variables that specifies parameters
   used by the `run` command and by the ansible playbooks. This file must be
   modified for setting the correct master node and the ssh configuration file
   used for accessing the testbed. The ansible master node is specified by the
   variable `MASTER_NODE` and the ssh configuration file is specified by the
   `CONFIG_FILE` variable. The `setenv.sh` file already contains a reference
   example that shows how these variables can be set.
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
   any other test.
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
`run-ping-experiment.sh` script.

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
