POPROW Scripts Repo
===

## Wi-Fi Network Interface Configuration

The python script poprow_setup_interface.py can be used for bringing up an
802.11 network interface in adhoc (ibss) mode. Before using this script it is
necessary to install all the required dependencies by executing the
setup-devices.sh script. The script also creates a monitor interface configured
on the same channel as the adhoc interface that can be used for traffic
monitoring. The script requires the following parameters (in the current
implementation, with the exception of --bint, the are all mandatory).

* __-\-intcap__: possible values are "HT" and "VHT". It is used to specify the
  capabilities that must be supported by the NIC that will be used for
configuring the interface. Currently the TKN WIreless NetworkS Testbed (TWIST)
supports only "HT".

* __-\-band__: specifies which band the network interface will work in. Accepted
  values are "5GHz" and "2GHz" for the 5GHz and the 2.4GHz bands respectively.

* __-\-chan__: specifies in which channel to configure the network interface. If
  the band parameter is "2GHz" the accepted values for --chan are [1-13].
Instead, if the band parameter is "5GHz" the accepted values for --chan are [36,
40 and 44].

* __-\-legacyrate__: configures the 802.11g rate to use for frame transmissions.
  Accepted values are [6, 9, 12, 18, 24 36, 48, 54].

* __-\-txpower__: configures the transmission power in millibel-milliwatts (mBm)
  (<power in mBm> = 100 * <power in dBm>). Accepted values goes from 0 to 3000
(the actual maximum power depends on selected channel and the actual power
selection granularity depend on the PHY).

* __-\-inet__: sets the interface IPv4 address. The accepted format is
  x.y.z.t/nm.

* __-\-ibssid__: configures the BSSID of the adhoc network.

* __-\-ibssiname__: configures the name of the local adhoc interface.

* __-\-moniname__: configures the name of the local monitor interface (this
  interface shares the same PHY as the adhoc interface and can be used for
traffic monitoring).

* __-\-bint__: configure the beacon interval in TUs (default values 100TUs).


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

```bash
./poprow_setup_interface.py --intcap=HT --band=2GHz --chan=1 --legacyrate=6 --txpower=2000 --inet=192.168.100.10/24 --ibssid=poprow --ibssiname=poprow0 --moniname=mon0 --bint=200
```
