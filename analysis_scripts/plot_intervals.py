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
import networkx as nx
import os
import numpy as np
import matplotlib.pyplot as plt


def get_name_all_nodes(exp_base_dir_name_str):
    '''Return a list with the names of all the nodes involved in the
    experiment'''
    nodes_name_list = []
    for d in os.listdir(exp_base_dir_name_str):
        if os.path.isdir(exp_base_dir_name_str + '/' + d):
            nodes_name_list.append(d.split('_')[0])

    return nodes_name_list


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--masteridx', dest='masteridx', type=int,
                        help='Master node number')
    parser.add_argument('--stridx', dest='stridx', type=int,
                        help='strategy index')
    parser.add_argument('--expname', dest='expname', type=str,
                        help='''Name of the experiment. Thisparameter is used
                        by the script to find the experiment directory
                        (${resultsbdir}/${expname}_results. Moreover, the
                        script assumes that the names of all the results files
                        produced by the nodes involved in the experiment
                        (.int, .topo, .route) begin with ${expname}''')
    parser.add_argument('--resultsbdir', dest='resultsbdir', type=str,
                        help='''Base directory containint the experiments
                        results. The results of the experiment we want to
                        analyse are in ${resultsbdir/${expname}_results. Inside
                        this directory there must be a directory for each node
                        involved in the experiment and the name each of these
                        directories must begin with the node name (before the
                        '_' character. Inside the directory of a node there
                        must be one or more directories called 0, 1, 2..., one
                        for each kill strategy used during the experiment.
                        Inside the kill strategy directory there must be the
                        following two dorectories: olsrd2_vanilla and prince.
                        Finally, inside these two directories the script
                        assumes to find the actual results file (.int, .topo
                        and .route)''')

    parser.add_argument("-v", "--verbose", dest="verbose",
                        default=False, action="store_true")
    args = parser.parse_args()

    verbose = args.verbose
    expname = args.expname
    resultsbdir = args.resultsbdir
    masteridx = args.masteridx
    stridx = args.stridx
    expdir = resultsbdir + '/' + expname + '_results'

    nodes_name_list = get_name_all_nodes(expdir)

    start_graph_path = expdir + '/nuc0-' + str(masteridx) + '_' + expname +\
        '/' + str(stridx) + '/prince/start_graph.graphml'
    strategy_path = expdir + '/nuc0-' + str(masteridx) + '_' + expname +\
        '/' + str(stridx) + '/prince/strategies'

    deadnode_id = ''
    deadnode_name = ''
    with open(strategy_path, 'r') as df:
        line = df.read()
        deadnode_id = line.split('@')[0]

    sg = nx.read_graphml(start_graph_path)

    node_ip_to_name = {}
    for i in range(1, 100):
        node_ip_to_name['10.1.0.' + str(i)] = 'nuc0-' + str(i)

    deadnode_name = node_ip_to_name[deadnode_id]

    bcn = nx.betweenness_centrality(sg, weight='weight', endpoints=True)
    bcns = [(node_ip_to_name[n], bcn[n]) for (n, bcn[n]) in
            sorted(bcn.items(), key=lambda x: x[1], reverse=True)]

    tc_intervals = {}
    hello_intervals = {}
    for nn in nodes_name_list:
        res_path = expdir + '/' + nn + '_' + expname +\
            '/' + str(stridx) + '/prince/'
        intervals_files_list = []
        for root, dirs, files in os.walk(res_path):
            for file_name in files:
                if file_name.endswith('.int'):
                    intervals_files_list.append(file_name)

        file_prefix = expname + '_' + nn + '_000000'
        for f in intervals_files_list:
            if f.startswith(file_prefix):
                with open(res_path + '/' + f, 'r') as df:
                    for l in df.readlines():
                        if 'hello' in l:
                            hello_intervals[nn] = float(l.split(':')[1])
                        if 'tc' in l:
                            tc_intervals[nn] = float(l.split(':')[1])

    plt.figure(1, figsize=(15, 5))
    plt.grid()
    deadnode_idx = -1
    for i, (nn, c) in enumerate(bcns):
        if nn == deadnode_name:
            deadnode_idx = i
            break
    print("BC:")
    for (nn, c) in bcns:
        print(nn, c)
    print("TC:")
    for (nn, c) in bcns:
        print(nn, tc_intervals[nn])
    print("HELLO:")
    for (nn, c) in bcns:
        print(nn, hello_intervals[nn])
    cs = [c for (nn, c) in bcns]
    tcs = [tc_intervals[nn] for (nn, c) in bcns]
    hs = [hello_intervals[nn] for (nn, c) in bcns]
    x = np.arange(1, len(nodes_name_list) + 1)

    line = plt.plot(x, cs, 'b',
                    x, cs, 'bo',
                    deadnode_idx + 1, cs[deadnode_idx], 'ro')
    plt.legend(['Betweenness centrality'])
    plt.xticks([])
    plt.ylabel('Betweenness centrality')
    plt.xlabel('Nodes sorted for decreasing values of Betweenness centrality')
    plt.savefig('betweenness_centrality.eps')

    plt.figure(2, figsize=(15, 5))
    plt.grid()

    line = plt.plot(x, hs, 'r',
                    x, hs, 'ro',
                    deadnode_idx + 1, hs[deadnode_idx], 'go')
    plt.legend(['HELLO interval'])
    plt.xticks([])
    plt.ylabel('HELLO interval [s]')
    plt.xlabel('Nodes sorted for decreasing values of Betweenness centrality')
    plt.savefig('hello_intervals.eps')

    plt.figure(3, figsize=(15, 5))
    plt.grid()

    line = plt.plot(x, tcs, 'g',
                    x, tcs, 'go',
                    deadnode_idx + 1, tcs[deadnode_idx], 'bo')
    plt.legend(['TC interval'])
    plt.xticks([])
    plt.ylabel('TC interval [s]')
    plt.xlabel('Nodes sorted for decreasing values of Betweenness centrality')
    plt.savefig('tc_intervals.eps')

    plt.figure(4, figsize=(15, 5))
    plt.grid()

    line = plt.plot(x, tcs, 'go',
                    x, hs, 'ro',
                    x, tcs, 'g',
                    x, hs, 'r')
    plt.legend(['TC interval', 'HELLO interval'])
    plt.xticks([])
    plt.ylabel('Interval [s]')
    plt.xlabel('Nodes sorted for decreasing values of Betweenness centrality')
