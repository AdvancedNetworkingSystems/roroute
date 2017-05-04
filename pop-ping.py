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

import signal
import sys
import socket
import time
from argparse import ArgumentParser
import ipaddr
from pyroute2.iproute import IPRoute


def main():
    """
    Program entry point when run interactively.
    """

    # prepare option parser
    parser = ArgumentParser(usage="usage: %(prog)s [options]",
                            description="Executes a UDP broadcast to test for "
                                        "connectivity")
    parser.add_argument("-i", "--interface", dest="interface",
                        default="poprow0", action="store", metavar="ifname",
                        help="Interface to use [default: %(default)s]")
    parser.add_argument("-p", "--port", dest="port", type=int, default=12345,
                        action="store", help="UDP port [default: %(default)s]",
                        metavar="PORT")
    parser.add_argument("-n", "--count", dest="count", type=int, default=100,
                        action="store",
                        help="Number of packets to send [default: %(default)s]",
                        metavar="COUNT")
    parser.add_argument("-t", "--interval", dest="interval", type=float,
                        default=0.2, action="store",
                        help="Packet interval [default: %(default)s]")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")

    # parse options
    args = parser.parse_args()

    # copy options
    interface = args.interface
    port = args.port
    count = args.count
    interval = args.interval
    verbose = args.verbose

    ip = IPRoute()
    if_index = ip.link_lookup(ifname=interface)

    if len(if_index) == 0:
        print >> sys.stderr, "Can't find interface %s" % interface
        sys.exit(1)

    # from the given interface find unicast and broadcast addresses
    if_info = ip.get_addr(index=if_index[0])[0]
    address = if_info.get_attr("IFA_ADDRESS")
    netmask = if_info["prefixlen"]
    network = ipaddr.IPv4Network("%s/%d" % (address, netmask))
    broadcast = str(network.broadcast)

    # get hostname as additional information to send in the packets
    hostname = socket.gethostname()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    i = 0
    run = True
    while i < count and run:
        try:
            payload = "POPROWPING %d %s" % (i, hostname)
            if verbose:
                print >> sys.stderr, "Sending packet #%d to %s:%d" % \
                      (i+1, broadcast, port)
            sock.sendto(payload, (broadcast, port))
            i += 1
            time.sleep(interval)
        except SystemExit:
            run = False
            if verbose:
                print >> sys.stderr, "Catching SystemExit. Quitting"
        except KeyboardInterrupt:
            run = False
            if verbose:
                print >> sys.stderr, "Keyboard Interrupt. Quitting"
        except:
            run = False
            if verbose:
                print >> sys.stderr, "Error while sending packet. Quitting"

    sock.close()


def signal_handler(signal, frame):
    sys.exit(1)


# start main() when run interactively
if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    main()
