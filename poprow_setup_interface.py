#!/usr/bin/env python
#
# Copyright (C) 2017 Michele Segata <msegata@disi.unitn.it>
# Copyright (C) 2017 Nicolo' Facchi <nicolo.facchi@unitn.it>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

import argparse
import subprocess
from pyric import pyw
import pyric.utils.channels as channels


def run_command(command):
    '''
    Method to start the shell commands
    and get the output as iterater object
    '''

    sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, shell=True)
    out, err = sp.communicate()

    if err:
        raise Exception('An error occurred in Dot80211Linux: %s' % err)

    return [sp.returncode, out.decode('utf-8'), err.decode('utf-8')]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--intcap', dest='intcap', choices=['HT', 'VHT'],
                        type=str, help='Interface capabilities',
                        required=True)
    # parser.add_argument('--band', dest='band', choices=['5GHz', '2GHz'],
    #                     type=str, help='Band to use: 2.4GHz or 5GHz',
    #                     required=True)
    allowed_channels_24ghz = range(1, 14)
    allowed_channels_5ghz = [36, 40, 44, 48, 52, 56, 60, 149, 153, 157, 161]
    parser.add_argument('--chan', dest='chan',
                        choices=allowed_channels_24ghz + allowed_channels_5ghz,
                        type=int, help='Channel',
                        required=True)
    # allowed_freqs_24ghz = [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447,
    #                        2452, 2457, 2462, 2467, 2472]
    # allowed_freqs_5ghz = [5180, 5200, 5220]
    # parser.add_argument("--freq", dest="freq",
    #                     choices=allowed_freqs_24ghz + allowed_freqs_5ghz,
    #                     type=int, help="Channel center frequency",
    #                     required=True)
    # parser.add_argument("--mcs", dest="mcs", help="TX MCS", required=True)
    parser.add_argument('--legacyrate', dest='legacyrate',
                        choices=[6, 9, 12, 18, 24, 36, 48, 54], type=int,
                        help='Transmission legacy rate', required=True)
    parser.add_argument('--txpower', dest='txpower', type=int,
                        choices=range(0, 3001), metavar='[1-3001]',
                        help='TX power in millibel-milliwatts (mBm) '
                             '(<power in mBm> = 100 * <power in dBm>)',
                        required=True)
    parser.add_argument('--inet', dest='inet',
                        help='IPv4 address (x.y.z.t/nm)',
                        required=True)
    # parser.add_argument("--nmask", dest="nmask", help="IPv4 netmask",
    #                     required=True)
    # parser.add_argument("--bcast", dest="bcast", help="IPv4 broadcast",
    #                     required=True)
    parser.add_argument('--ibssid', dest='ibssid', help='Hadoc SSID',
                        required=True)
    parser.add_argument('--ibssiname', dest='ibssiname',
                        help='Ad hoc interface name',
                        required=True)
    parser.add_argument('--moniname', dest='moniname',
                        help='Monitor interface name',
                        required=True)
    parser.add_argument('--bint', dest='bint', type=int, default=100,
                        help='Beacon interval in TUs', required=False)
    args = parser.parse_args()

    # Delete all Wi-Fi interfaces
    wifi_int = pyw.winterfaces()
    for wifi_int_name in wifi_int:
        pyw.devdel(pyw.getcard(wifi_int_name))

    band = "2GHz"
    if args.chan > 14:
        band = "5GHz"

    # Look for a candidate PHY (currently based on frequency and capabilities
    # (HT or VHT) support
    phys = pyw.phylist()
    selected_phy = None

    for phy in phys:
        phy_info = pyw.phyinfo(pyw.Card(phy[0], None, 0))
        if bool(phy_info['bands'][band][args.intcap]):
            selected_phy = phy
            # print(selected_phy)
            break

    # Add and configure mesh and monitor interfaces
    if selected_phy is not None:
        phy_info = pyw.phyinfo(pyw.Card(selected_phy[0], None, 0))
        # print(phy_info)

        # Create ibss point interface
        ibss_cmd = 'iw phy ' + selected_phy[1] +\
                   ' interface add ' + args.ibssiname +\
                   ' type ibss'
        print(ibss_cmd)
        [rcode, sout, serr] = run_command(ibss_cmd)

        # Set ibss interface IP address
        ibss_ip_cmd = 'ip addr add ' + args.inet +\
                      ' dev ' + args.ibssiname
        print(ibss_ip_cmd)
        [rcode, sout, serr] = run_command(ibss_ip_cmd)

        # Add monitor interface
        ibss_mon_cmd = 'iw dev ' + args.ibssiname + ' interface add ' +\
                       args.moniname + ' type monitor'
        print(ibss_mon_cmd)
        [rcode, sout, serr] = run_command(ibss_mon_cmd)

        # Bring interfaces up
        ibss_up_cmd = 'ip link set dev ' + args.ibssiname + ' up'
        print(ibss_up_cmd)
        [rcode, sout, serr] = run_command(ibss_up_cmd)
        ibss_mon_up_cmd = 'ip link set dev ' + args.moniname + ' up'
        print(ibss_mon_up_cmd)
        [rcode, sout, serr] = run_command(ibss_mon_up_cmd)

        # ibss_chan_cmd = 'iw dev ' + args.ibssiname + ' set channel ' +\
        #                 str(args.chan)
        # print(ibss_chan_cmd)
        # [rcode, sout, serr] = run_command(ibss_chan_cmd)

        ibss_join_cmd = 'iw dev ' + args.ibssiname + ' ibss join ' +\
                        args.ibssid + ' ' + str(channels.ch2rf(args.chan)) +\
                        ' fixed-freq beacon-interval ' + str(args.bint)
        print(ibss_join_cmd)
        [rcode, sout, serr] = run_command(ibss_join_cmd)

        # Set legacy rate
        legacy_str = 'legacy-'
        if band == '2GHz':
            legacy_str += '2.4'
        else:
            legacy_str += '5'
        ibss_rate_cmd = 'iw dev ' + args.ibssiname + ' set bitrates ' +\
                        legacy_str + ' ' + str(args.legacyrate)
        print(ibss_rate_cmd)
        [rcode, sout, serr] = run_command(ibss_rate_cmd)

        ibss_ps_off_cmd = 'iw dev ' + args.ibssiname + ' set power_safe off'
        print(ibss_ps_off_cmd)
        [rcode, sout, serr] = run_command(ibss_ps_off_cmd)

        ibss_tx_pwr_cmd = 'iw dev ' + args.ibssiname +\
                          ' set txpower fixed ' + str(args.txpower)
        print(ibss_tx_pwr_cmd)
        [rcode, sout, serr] = run_command(ibss_tx_pwr_cmd)

        [rcode, sout, serr] = run_command('iw dev')
        print(sout)
