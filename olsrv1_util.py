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
import requests
import json
import urlparse

from olsr import OlsrParser


def dump_olsr_topology():
    '''
    Use the OlsrParser for dumping the olsrd topology and return the
    corresponding networkx graph
    '''
    g = OlsrParser(url="http://127.0.0.1:9090/all")
    return g.graph


def dump_olsr_routing_table():
    '''
    Use the http command for dumping the olsrd routing table and
    return the corresponding set of destination/next hop tuples
    '''
    url = urlparse.urlparse("http://127.0.0.1:9090/routes")
    response = requests.get(url.geturl(), verify=False, timeout=10)
    if response.status_code != 200:
        raise Exception("Impossible to retrieve routes from olsrd")
    routing_table = json.loads(response.content.decode())
    routes = set()
    for r in routing_table["routes"]:
        routes.add((r["destination"], r["gateway"]))
    return routes
