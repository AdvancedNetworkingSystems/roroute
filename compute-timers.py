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

from os import listdir
from os.path import isdir
import networkx as nx
import sys
from math import sqrt


def __get_intervals(nodes, dg, r, bc):
    o_h = sum([v for k, v in dg.iteritems()]) / 2.0
    hello_const = 1/o_h * sum([sqrt(bc[node] * dg[node]) for node in nodes])
    o_lsa = len(nodes) * r / 5.0
    tc_const = 1/o_lsa * sum([sqrt(bc[node] * r) for node in nodes])
    return dict((node, (sqrt(dg[node] / bc[node]) * hello_const,
                        sqrt(r / bc[node]) * tc_const))
                for node in nodes)


def __compute_intervals(graph, return_bc=False, use_degree=True):
    """
    Given a networkx graph, returns the poprouting hello and tc intervals to
    be set for each node
    :param graph: graph
    :return: a dictionary in the form "node: (hello, tc)"
    """
    bc = nx.betweenness_centrality(graph, weight="weight", endpoints=True)

    dg = dict((v, 1) for v in graph.nodes())
    r = len(graph.nodes())
    ints_no_degree = __get_intervals(graph.nodes(), dg, r, bc)
    dg = dict((v, d) for v, d in graph.degree().iteritems())
    r = len(graph.edges())
    ints_degree = __get_intervals(graph.nodes(), dg, r, bc)

    # return a dictionary node -> (hello, tc)
    if not return_bc:
        if use_degree:
            return ints_degree
        else:
            return ints_no_degree
    else:
        ints = dict((node, (ints_degree[node][0], ints_degree[node][1],
                            ints_no_degree[node][0], ints_no_degree[node][1],
                            bc[node], graph.degree()[node]))
                    for node in graph.nodes())
    return ints


def get_strategies(path):
    '''Return the list of repetitions of the experiment'''
    strategies = []
    for d in listdir(path):
        if isdir("%s/%s" % (path, d)):
            try:
                index = int(d)
                strategies.append(index)
            except ValueError:
                continue
    return strategies


def write_timers(graph):

    out_fn = graph.replace(".graphml", "") + ".csv"
    g = nx.read_graphml(graph)
    out = open(out_fn, "w")
    intv = __compute_intervals(g, return_bc=True)
    ap = [x for x in nx.articulation_points(g)]
    no_leaves_nodes = nx.k_core(g, 2).nodes()
    cn = [x for x in g.nodes() if x not in ap and x in no_leaves_nodes]
    out.write("node,h,tc,hnd,tcnd,bc,d,ap\n")
    for n, (h, tc, h2, tc2, bc, d) in intv.iteritems():
        out.write("%s,%f,%f,%f,%f,%f,%d,%d\n" % (n, h, tc, h2, tc2, bc, d,
                                                 0 if n in cn else 1))
    out.close()


if len(sys.argv) < 2:
    print("Usage: %s list of graphml files or list of folders" % sys.argv[0])
    sys.exit(1)

for i in range(1, len(sys.argv)):
    f = sys.argv[i]
    if f.endswith(".graphml"):
        write_timers(sys.argv[i])
    else:
        strategies = get_strategies(f)
        for s in strategies:
            fn = "%s/%d/prince/start_graph.graphml" % (f, s)
            write_timers(fn)
