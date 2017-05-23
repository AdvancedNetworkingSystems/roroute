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

import os
import signal
import sys
import socket
from argparse import ArgumentParser
from pyroute2.iproute import IPRoute
import ipaddr


def main():
    """
    Program entry point when run interactively.
    """

    # prepare option parser
    parser = ArgumentParser(usage="usage: %(prog)s [options]",
                            description="Listens to UDP broadcasts to test for "
                                        "connectivity")
    parser.add_argument("-i", "--interface", dest="interface",
                        default="poprow0", action="store", metavar="ifname",
                        help="Interface to use [default: %(default)s]")
    parser.add_argument("-p", "--port", dest="port", type=int, default=12345,
                        action="store", help="UDP port [default: %(default)s]",
                        metavar="PORT")
    parser.add_argument("-f", "--filename", dest="filename", default="",
                        action="store",
                        help="Output file where to store results [default: "
                             "stdout]", metavar="FILENAME")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    parser.add_argument("-d", "--daemon", dest="daemon", action="store_true",
                        help="Daemonize the process")


    # parse options
    args = parser.parse_args()

    # copy options
    interface = args.interface
    port = args.port
    filename = args.filename
    verbose = args.verbose
    daemon = args.daemon

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

    # get hostname as additional information for the log file
    hostname = socket.gethostname()

    if not daemon:
        signal.signal(signal.SIGTERM, signal_handler)
    else:
        daemonize()

    # setup output file
    if filename == "":
        outfile = sys.stdout
    else:
        outfile = open(filename, "w")

    if verbose:
        print >> sys.stderr, "Host with IP %s listening for packets on " \
                             "broadcast IP %s" % (address, broadcast)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((broadcast, port))

    run = True
    while run:
        try:
            datagram = sock.recvfrom(1024)
            payload = datagram[0].split(' ')
            src = datagram[1][0]
            src_port = datagram[1][1]
            # check that this is really our app message
            if payload[0] != "POPROWPING":
                continue
            count = int(payload[1])
            remote_host = payload[2]
            if verbose:
                print >> sys.stderr, "Received packet #%d from %s:%d" % \
                      (count, src, src_port)
            outfile.write("%s,%s,%s,%s,%d\n" % (hostname, address, remote_host,
                                                src, count))
            outfile.flush()
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
                print >> sys.stderr, "Error while receiving packet. Quitting"

    sock.close()
    outfile.flush()
    outfile.close()


def signal_handler(signal, frame):
    sys.exit(1)


def daemonize():
    cwd = os.getcwd()
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.chdir(cwd)
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)


# start main() when run interactively
if __name__ == '__main__':
    main()
