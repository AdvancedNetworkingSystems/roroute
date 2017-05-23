POPROW Scripts Repo
===

## Automatic Nodes Setup

The repository includes some `ansible` playbooks that are used to automatically
configure the nodes before starting any experiment.

Before running the scripts you need to modify the following files

 * `hosts`: this includes the list of nodes that will be used in the
   experiment, i.e., the nodes that you want `ansible` to work with. By
   default, the file includes all hosts from all testbeds. If you don't want to
   touch it, you can make a copy and the edit `ansible.cfg` and change the
   `inventory` field accordingly.
 * `run`: this works as a launcher for all ansible playbooks. Instead of
   typing `ansible-playbook playbook.yaml` you type `./run playbook.yaml`.
   This copies the content of the whole folder on the master node and
   launches the `ansible-playbook` on the master node, to avoid being blocked
   by a firewall because of the many `ssh` connections. Before starting you
   need to edit the file to choose the master node. This is done by editing
   the `MASTER_NODE` variable. In addition, you need to edit the
   `CONFIG_FILE` variable, which points to an `ssh` config file which tells
   `ssh` how to properly reach the node.
 * `etchosts`: this file is copied to `/etc/hosts` for easy pings and for
   setting the IP address to a node depending on its hostname. Change this
   according to your needs.

Once these steps are done, you are ready to setup the nodes:

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
